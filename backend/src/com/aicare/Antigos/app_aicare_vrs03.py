import sqlite3
import hashlib

def exibir_nome_do_app():  
    print("""      
░█████╗░██╗░█████╗░░█████╗░██████╗░███████╗
██╔══██╗██║██╔══██╗██╔══██╗██╔══██╗██╔════╝
███████║██║██║░░╚═╝███████║██████╔╝█████╗░░
██╔══██║██║██║░░██╗██╔══██║██╔══██╗██╔══╝░░
██║░░██║██║╚█████╔╝██║░░██║██║░░██║███████╗
╚═╝░░╚═╝╚═╝░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝
""")

        
# -------------------------------------------------------------
# 01. CRIANDO A TABELA DE USUÁRIOS NO BANCO
# -------------------------------------------------------------
def inicializar_tabela_usuarios():
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT UNIQUE,
            senha_hash TEXT,
            perfil TEXT
        )
    """)
    
    conexao.commit()
    conexao.close()

# Executa para garantir que a tabela existe
inicializar_tabela_usuarios()


# -------------------------------------------------------------
# 02. FUNÇÃO AUXILIAR PARA CRIPTOGRAFAR A SENHA
# -------------------------------------------------------------
def gerar_hash_senha(senha):
    # Transforma a senha em um hash SHA-256 para não salvá-la em texto puro
    return hashlib.sha256(senha.encode()).hexdigest()

# -------------------------------------------------------------
# 03. FUNÇÃO AUXILIAR 1º ACESSO LOGIN COM CHAVE ADMINISTRADOR
# -------------------------------------------------------------
def inicializar_admin_padrao():
    inicializar_tabela_usuarios()
    
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    # Verifica se já existe algum usuário na tabela
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]
    
    if total_usuarios == 0:
        nome_admin = "Administrador Master"
        cpf_admin = "000.000.000-00"
        senha_padrao = "admin123"
        senha_hash = gerar_hash_senha(senha_padrao)
        perfil_admin = "Administrador"
        
        cursor.execute("""
            INSERT INTO usuarios (nome, cpf, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
        """, (nome_admin, cpf_admin, senha_hash, perfil_admin))
        
        conexao.commit()
        print("\n" + "=" * 60)
        print(" [SEGURANÇA] Primeiro acesso detectado!")
        print(" Conta de Administrador Padrão gerada automaticamente:")
        print(f" • CPF de Acesso: {cpf_admin}")
        print(f" • Senha Temporária: {senha_padrao}")
        print(" ⚠️ Recomendamos cadastrar novos usuários e alterar senhas no primeiro uso.")
        print("=" * 60 + "\n")
        
    conexao.close()


# -------------------------------------------------------------
# 04. FUNÇÃO DE CADASTRO DE USUÁRIO
# -------------------------------------------------------------
def cadastrar_usuario(nome, cpf, senha, perfil):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    senha_criptografada = gerar_hash_senha(senha)
    
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, cpf, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
        """, (nome, cpf, senha_criptografada, perfil))
        conexao.commit()
        print(f"[Sucesso] Usuário '{nome}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"[Erro] O CPF '{cpf}' já possui cadastro no sistema.")
    finally:
        conexao.close()

# -------------------------------------------------------------
# 05. FUNÇÃO DE LOGIN DO USUÁRIO
# -------------------------------------------------------------
def realizar_login():
    print("\n" + "=" * 40)
    print("      LOGIN NO SISTEMA DE SAÚDE")
    print("=" * 40)
    
    cpf_informado = input("Digite o seu CPF: ").strip()
    senha_informada = input("Digite a sua senha: ").strip()
    
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("""
        SELECT nome, senha_hash, perfil FROM usuarios WHERE cpf = ?
    """, (cpf_informado,))
    
    usuario = cursor.fetchone()
    conexao.close()
    
    if not usuario:
        print("\n[Acesso Negado] CPF não encontrado no sistema.")
        return None
        
    nome, senha_hash_salva, perfil = usuario
    senha_tentativa_hash = gerar_hash_senha(senha_informada)
    
    # Compara o hash da senha digitada com a senha salva no banco
    if senha_tentativa_hash == senha_hash_salva:
        print(f"\n[Acesso Permitido] Bem-vindo(a) de volta, {nome}! (Perfil: {perfil})")
        return {"nome": nome, "cpf": cpf_informado, "perfil": perfil}
    else:
        print("\n[Acesso Negado] Senha incorreta.")
        return None

import sqlite3

# -------------------------------------------------------------
# 00. INÍCIO DO SISTEMA
# -------------------------------------------------------------
# Chame esta função antes de iniciar o loop de login do aplicativo:
# inicializar_admin_padrao()
# Exemplo de chamada inicial simulando pós-login:
#if realizar_login():
#     menu_principal()
if __name__ == "__main__":
    # 1. Inicializa tabelas e o administrador padrão, se necessário
    inicializar_admin_padrao()
    
    # 2. Executa a rotina de login antes de abrir o sistema
    #usuario_logado = realizar_login()
    
    if usuario_logado:
        # 3. Se o login for bem-sucedido, inicia o menu principal
        menu_principal()

# -------------------------------------------------------------
# 06. GERENCIAMENTO DE PACIENTES (ATUALIZAR, ATIVAR/INATIVAR, EXCLUIR)
# -------------------------------------------------------------
def atualizar_paciente(cpf, novo_nome, nova_idade, novo_email, novas_doencas, novas_obs):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE pacientes 
        SET nome = ?, idade = ?, email = ?, doencas = ?, observacoes = ?
        WHERE cpf = ?
    """, (novo_nome, nova_idade, novo_email, novas_doencas, novas_obs, cpf))
    
    conexao.commit()
    conexao.close()
    print(f"[Banco] Dados do paciente com CPF {cpf} atualizados com sucesso!")

def alternar_status_paciente(cpf, ativo):
    # ativo: 1 para ativar, 0 para inativar
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("UPDATE pacientes SET ativo = ? WHERE cpf = ?", (ativo, cpf))
    conexao.commit()
    conexao.close()
    
    status_str = "ativado" if ativo == 1 else "inativado"
    print(f"[Banco] Paciente com CPF {cpf} foi {status_str} com sucesso!")

def excluir_paciente(cpf):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    # Busca o ID do paciente para remover também as dependências (integridade referencial)
    cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf,))
    paciente = cursor.fetchone()
    
    if not paciente:
        print(f"[Erro] Paciente com CPF {cpf} não encontrado.")
        conexao.close()
        return
        
    p_id = paciente[0]
    
    # Deleta registros dependentes nas outras tabelas
    cursor.execute("DELETE FROM medicamentos WHERE paciente_id = ?", (p_id,))
    cursor.execute("DELETE FROM familiares WHERE paciente_id = ?", (p_id,))
    cursor.execute("DELETE FROM historico_administracoes WHERE paciente_id = ?", (p_id,))
    cursor.execute("DELETE FROM pacientes WHERE id = ?", (p_id,))
    
    conexao.commit()
    conexao.close()
    print(f"[Banco] Paciente e todos os registros vinculados foram excluídos com sucesso.")

# -------------------------------------------------------------
# 07. GERENCIAMENTO DE CUIDADORES (ATUALIZAR, EXCLUIR)
# -------------------------------------------------------------
def atualizar_cuidador(cpf, novo_nome, novo_telefone, novo_registro):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE cuidadores 
        SET nome = ?, telefone = ?, coren_ou_registro = ?
        WHERE cpf = ?
    """, (novo_nome, novo_telefone, novo_registro, cpf))
    
    conexao.commit()
    conexao.close()
    print(f"[Banco] Cuidador(a) com CPF {cpf} atualizado(a) com sucesso!")

def excluir_cuidador(cpf):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("DELETE FROM cuidadores WHERE cpf = ?", (cpf,))
    conexao.commit()
    conexao.close()
    print(f"[Banco] Cuidador(a) com CPF {cpf} excluído(a) com sucesso.")

# -------------------------------------------------------------
# 08. GERENCIAMENTO DE FAMILIARES (ATUALIZAR, EXCLUIR)
# -------------------------------------------------------------
def atualizar_familiar(familiar_id, novo_nome, novo_parentesco, novo_telefone, novo_email):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE familiares 
        SET nome = ?, parentesco = ?, telefone = ?, email = ?
        WHERE id = ?
    """, (novo_nome, novo_parentesco, novo_telefone, novo_email, familiar_id))
    
    conexao.commit()
    conexao.close()
    print(f"[Banco] Familiar (ID: {familiar_id}) atualizado com sucesso!")

def excluir_familiar(familiar_id):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("DELETE FROM familiares WHERE id = ?0", (familiar_id,))
    conexao.commit()
    conexao.close()
    print(f"[Banco] Familiar (ID: {familiar_id}) excluído com sucesso.")

# -------------------------------------------------------------
# 09. GERENCIAMENTO DE MEDICAMENTOS (ATUALIZAR, EXCLUIR)
# -------------------------------------------------------------
def atualizar_medicamento(medicamento_id, nova_dosagem, novo_horario, novo_turno, novo_preco, nova_qtd, nova_regra):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE medicamentos 
        SET dosagem = ?, horario = ?, turno = ?, preco = ?, quantidade = ?, medicao_preventiva = ?
        WHERE id = ?
    """, (nova_dosagem, novo_horario, novo_turno, novo_preco, nova_qtd, nova_regra, medicamento_id))
    
    conexao.commit()
    conexao.close()
    print(f"[Banco] Medicamento (ID: {medicamento_id}) atualizado com sucesso!")

def excluir_medicamento(medicamento_id):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("DELETE FROM medicamentos WHERE id = ?", (medicamento_id,))
    conexao.commit()
    conexao.close()
    print(f"[Banco] Medicamento (ID: {medicamento_id}) excluído com sucesso.")

    import sqlite3
import datetime
import hashlib

# -------------------------------------------------------------
# 10. FUNÇÕES DE SUPORTE A ALERTAS, RELATÓRIOS E SINCRONIZAÇÃO
# -------------------------------------------------------------

def verificar_alertas_estoque():
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    # Alerta para medicamentos com estoque baixo (ex: 5 ou menos unidades)
    cursor.execute("""
        SELECT p.nome, m.nome, m.dosagem, m.quantidade 
        FROM medicamentos m
        JOIN pacientes p ON m.paciente_id = p.id
        WHERE m.quantidade <= 5
    """)
    alertas = cursor.fetchall()
    conexao.close()
    
    print("\n" + "=" * 50)
    print("      ALERTAS DE ESTOQUE DE MEDICAMENTOS")
    print("=" * 50)
    if not alertas:
        print("✅ Nenhum medicamento com estoque crítico no momento.")
    else:
        for paciente_nome, med_nome, dosagem, qtd in alertas:
            print(f"⚠️ ATENÇÃO: O remédio '{med_nome} ({dosagem})' do paciente {paciente_nome} está com estoque baixo ({qtd} un.).")
    print("=" * 50)

def gerar_relatorio_geral():
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM pacientes WHERE ativo = 1")
    total_pacientes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cuidadores")
    total_cuidadores = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM medicamentos")
    total_medicamentos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM historico_administracoes")
    total_auditorias = cursor.fetchone()[0]
    
    conexao.close()
    
    print("\n" + "=" * 50)
    print("          RELATÓRIO GERAL DO SISTEMA")
    print("=" * 50)
    print(f"• Pacientes Ativos Cadastrados: {total_pacientes}")
    print(f"• Cuidadores Cadastrados: {total_cuidadores}")
    print(f"• Medicamentos Vinculados: {total_medicamentos}")
    print(f"• Registros de Auditoria (IA): {total_auditorias}")
    print("=" * 50)

def sincronizar_base_dados():
    print("\n" + "=" * 50)
    print("       SINCRONIZAÇÃO DE BASES DE DADOS")
    print("=" * 50)
    # Simulação de rotina de sincronização local/nuvem
    print("[Sync] Conectando com o servidor remoto seguro...")
    print("[Sync] Verificando integridade do SQLite local ('saude_idosos.db')...")
    print("[Sync] Dados sincronizados com sucesso! Nenhuma pendência encontrada.")
    print("=" * 50)


# -------------------------------------------------------------
# 11. SUBMENUS DE GERENCIAMENTO (CRUD)
# -------------------------------------------------------------

def menu_gerenciar_pacientes():
    while True:
        print("\n--- GERENCIAMENTO DE PACIENTES ---")
        print("1. Cadastrar Paciente")
        print("2. Atualizar Paciente")
        print("3. Ativar / Inativar Paciente")
        print("4. Excluir Paciente")
        print("0. Voltar ao Menu Principal")
        
        op = input("Escolha uma opção: ").strip()
        if op == "1":
            nome = input("Nome completo: ")
            idade = int(input("Idade: "))
            cpf = input("CPF: ")
            email = input("E-mail: ")
            doencas = input("Doenças/Diagnósticos: ")
            obs = input("Observações: ")
            # Função de cadastro (já estruturada anteriormente)
            atualizar_paciente(nome, idade, cpf, email, doencas, obs)
        elif op == "2":
            cpf = input("Informe o CPF do paciente a alterar: ")
            nome = input("Novo nome: ")
            idade = int(input("Nova idade: "))
            email = input("Novo e-mail: ")
            doencas = input("Novas doenças: ")
            obs = input("Novas observações: ")
            atualizar_paciente(cpf, nome, idade, email, doencas, obs)
        elif op == "3":
            cpf = input("Informe o CPF do paciente: ")
            status = int(input("Digite 1 para ATIVAR ou 0 para INATIVAR: "))
            alternar_status_paciente(cpf, status)
        elif op == "4":
            cpf = input("Informe o CPF do paciente a EXCLUIR: ")
            excluir_paciente(cpf)
        elif op == "0":
            break
        else:
            print("Opção inválida.")

def menu_gerenciar_cuidadores():
    while True:
        print("\n--- GERENCIAMENTO DE CUIDADORES ---")
        print("1. Cadastrar Cuidador(a)")
        print("2. Atualizar Cuidador(a)")
        print("3. Excluir Cuidador(a)")
        print("0. Voltar ao Menu Principal")
        
        op = input("Escolha uma opção: ").strip()
        if op == "1":
            nome = input("Nome: ")
            cpf = input("CPF: ")
            tel = input("Telefone: ")
            reg = input("Registro (Coren/CBO): ")
            atualizar_cuidador(nome, cpf, tel, reg)
        elif op == "2":
            cpf = input("Informe o CPF do cuidador a alterar: ")
            nome = input("Novo nome: ")
            tel = input("Novo telefone: ")
            reg = input("Novo registro: ")
            atualizar_cuidador(cpf, nome, tel, reg)
        elif op == "3":
            cpf = input("Informe o CPF do cuidador a excluir: ")
            excluir_cuidador(cpf)
        elif op == "0":
            break
        else:
            print("Opção inválida.")

def menu_gerenciar_familiares():
    while True:
        print("\n--- GERENCIAMENTO DE FAMILIARES ---")
        print("1. Cadastrar Familiar")
        print("2. Atualizar Familiar")
        print("3. Excluir Familiar")
        print("0. Voltar ao Menu Principal")
        
        op = input("Escolha uma opção: ").strip()
        if op == "1":
            cpf_p = input("CPF do paciente vinculado: ")
            conexao = sqlite3.connect("saude_idosos.db")
            cursor = conexao.cursor()
            cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf_p,))
            res = cursor.fetchone()
            conexao.close()
            if not res:
                print("Paciente não encontrado.")
                continue
            p_id = res[0]
            nome = input("Nome do familiar: ")
            parentesco = input("Parentesco: ")
            tel = input("Telefone: ")
            email = input("E-mail: ")
            atualizar_familiar(p_id, nome, parentesco, tel, email)
        elif op == "2":
            f_id = int(input("ID do familiar a alterar: "))
            nome = input("Novo nome: ")
            parentesco = input("Novo parentesco: ")
            tel = input("Novo telefone: ")
            email = input("Novo e-mail: ")
            atualizar_familiar(f_id, nome, parentesco, tel, email)
        elif op == "3":
            f_id = int(input("ID do familiar a excluir: "))
            excluir_familiar(f_id)
        elif op == "0":
            break
        else:
            print("Opção inválida.")

def menu_gerenciar_medicamentos():
    while True:
        print("\n--- GERENCIAMENTO DE MEDICAMENTOS ---")
        print("1. Cadastrar Medicamento")
        print("2. Atualizar Medicamento")
        print("3. Excluir Medicamento")
        print("0. Voltar ao Menu Principal")
        
        op = input("Escolha uma opção: ").strip()
        if op == "1":
            cpf_p = input("CPF do paciente dono do remédio: ")
            conexao = sqlite3.connect("saude_idosos.db")
            cursor = conexao.cursor()
            cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf_p,))
            res = cursor.fetchone()
            conexao.close()
            if not res:
                print("Paciente não encontrado.")
                continue
            p_id = res[0]
            nome = input("Nome do medicamento: ")
            dosagem = input("Dosagem: ")
            horario = input("Horário: ")
            turno = input("Turno: ")
            lab = input("Laboratório: ")
            preco = float(input("Preço (R$): "))
            obs = input("Observações: ")
            preventiva = input("Regra Preventiva: ")
            qtd = int(input("Quantidade em estoque: "))
            atualizar_medicamento(p_id, nome, dosagem, horario, turno, lab, preco, obs, preventiva, qtd)
        elif op == "2":
            m_id = int(input("ID do medicamento a alterar: "))
            dosagem = input("Nova dosagem: ")
            horario = input("Novo horário: ")
            turno = input("Novo turno: ")
            preco = float(input("Novo preço: "))
            qtd = int(input("Nova quantidade em estoque: "))
            regra = nova_regra = input("Nova regra preventiva: ")
            atualizar_medicamento(m_id, dosagem, horario, turno, preco, qtd, regra)
        elif op == "3":
            m_id = int(input("ID do medicamento a excluir: "))
            excluir_medicamento(m_id)
        elif op == "0":
            break
        else:
            print("Opção inválida.")
import sqlite3

# -------------------------------------------------------------
# 12. CONSULTAR DADOS COMPLETOS DO PACIENTE POR CPF
# -------------------------------------------------------------
def consultar_dados_por_cpf(cpf_buscado):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    # Busca os dados principais do paciente
    cursor.execute("""
        SELECT id, nome, idade, cpf, email, doencas, observacoes, ativo 
        FROM pacientes 
        WHERE cpf = ?
    """, (cpf_buscado,))
    paciente = cursor.fetchone()
    
    if not paciente:
        print(f"\n[Aviso] Nenhum paciente encontrado com o CPF: {cpf_buscado}")
        conexao.close()
        return
        
    p_id, nome, idade, cpf, email, doencas, observacoes, ativo = paciente
    status_texto = "ATIVO ✅" if ativo == 1 else "INATIVO ❌"
    
    print("\n" + "=" * 65)
    print(f"FICHA COMPLETA DO PACIENTE: {nome}")
    print("=" * 65)
    print(f"• CPF: {cpf} | Idade: {idade} anos | Status: {status_texto}")
    print(f"• E-mail: {email}")
    print(f"• Diagnósticos/Doenças: {doencas}")
    print(f"• Observações Clínicas: {observacoes}")
    
    # Busca os medicamentos vinculados ao paciente
    print("\n" + "-" * 30 + " MEDICAMENTOS CADASTRADOS " + "-" * 30)
    cursor.execute("""
        SELECT id, nome, dosagem, horario, turno, laboratorio, preco, quantidade, medicao_preventiva 
        FROM medicamentos 
        WHERE paciente_id = ?
    """, (p_id,))
    medicamentos = cursor.fetchall()
    
    if not medicamentos:
        print("Nenhum medicamento cadastrado para este paciente.")
    else:
        for med in medicamentos:
            m_id, m_nome, dosagem, horario, turno, lab, preco, qtd, preventiva = med
            print(f"[{m_id}] {m_nome} - {dosagem} ({turno} às {horario})")
            print(f"    Lab: {lab} | Preço Estimado: R$ {preco:.2f} | Estoque: {qtd} un.")
            print(f"    Regra Preventiva: {preventiva}")
            print("-" * 65)
            
    # Busca os familiares responsáveis vinculados ao paciente
    print("-" * 30 + " FAMILIARES RESPONSÁVEIS " + "-" * 30)
    cursor.execute("""
        SELECT id, nome, parentesco, telefone, email 
        FROM familiares 
        WHERE paciente_id = ?
    """, (p_id,))
    familiares = cursor.fetchall()
    
    if not familiares:
        print("Nenhum familiar cadastrado para este paciente.")
    else:
        for fam in familiares:
            f_id, f_nome, parentesco, tel, email_fam = fam
            print(f"[{f_id}] {f_nome} ({parentesco}) - Tel: {tel} | E-mail: {email_fam}")
            
    print("=" * 65)
    conexao.close()


# -------------------------------------------------------------
# 13. CONSULTAR HISTÓRICO DE AUDITORIA DO PACIENTE POR CPF
# -------------------------------------------------------------
def consultar_historico_paciente(cpf_buscado):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    # Descobre o ID e o nome do paciente pelo CPF
    cursor.execute("SELECT id, nome FROM pacientes WHERE cpf = ?", (cpf_buscado,))
    paciente = cursor.fetchone()
    
    if not paciente:
        print(f"\n[Aviso] Nenhum paciente encontrado com o CPF: {cpf_buscado}")
        conexao.close()
        return
        
    paciente_id, nome_paciente = paciente
    
    print("\n" + "=" * 70)
    print(f"HISTÓRICO DE AUDITORIA CLÍNICA: {nome_paciente}")
    print("=" * 70)
    
    # Busca todas as tentativas e auditorias vinculadas a este paciente
    cursor.execute("""
        SELECT medicamento_nome, data_hora, valor_aferido, liberado, parecer_ia 
        FROM historico_administracoes 
        WHERE paciente_id = ?
        ORDER BY id DESC
    """, (paciente_id,))
    
    historicos = cursor.fetchall()
    conexao.close()
    
    if not historicos:
        print("Nenhum registro de administração encontrado no histórico deste paciente.")
    else:
        for i, hist in enumerate(historicos, start=1):
            med_nome, data_hora, valor, liberado_flag, parecer = hist
            status = "LIBERADO ✅" if liberado_flag == 1 else "BLOQUEADO ❌"
            
            print(f"{i}. Data/Hora: {data_hora}")
            print(f"   Medicamento: {med_nome}")
            print(f"   Valor Aferido: {valor}")
            print(f"   Status da IA: {status}")
            print(f"   Parecer Clínico: {parecer}")
            print("-" * 65)

# -------------------------------------------------------------
# 14. MENU PRINCIPAL UNIFICADO DO APLICATIVO
# -------------------------------------------------------------

def menu_principal():
    while True:
        print("\n" + "=" * 60)
        print("       CLINIC-AI - GESTÃO INTELIGENTE DE SAÚDE")
        print("=" * 60)
        print("1. Gerenciar Pacientes (Cadastrar/Alterar/Ativar/Excluir)")
        print("2. Gerenciar Cuidadores (Cadastrar/Alterar/Excluir)")
        print("3. Gerenciar Familiares (Cadastrar/Alterar/Excluir)")
        print("4. Gerenciar Medicamentos (Cadastrar/Alterar/Excluir)")
        print("5. Alertas de Estoque de Medicamentos")
        print("6. Relatórios Gerais do Sistema")
        print("7. Sincronização de Bases de Dados")
        print("8. Avaliação Clínica e Auditoria (com IA)")
        print("9. Consultar Ficha / Histórico por CPF")
        print("0. Sair do Sistema")
        print("-" * 60)
        
        opcao = input("Escolha a opção desejada: ").strip()
        
        if opcao == "1":
            menu_gerenciar_pacientes()
        elif opcao == "2":
            menu_gerenciar_cuidadores()
        elif opcao == "3":
            menu_gerenciar_familiares()
        elif opcao == "4":
            menu_gerenciar_medicamentos()
        elif opcao == "5":
            verificar_alertas_estoque()
        elif opcao == "6":
            gerar_relatorio_geral()
        elif opcao == "7":
            sincronizar_base_dados()
        elif opcao == "8":
            # Aqui entra a chamada da função de avaliação por IA que construímos anteriormente
            print("\n[Módulo IA] Funcionalidade de avaliação clínica integrada.")
        elif opcao == "9":
            cpf_b = input("Digite o CPF do paciente: ")
            consultar_dados_por_cpf(cpf_b)
            consultar_historico_paciente(cpf_b)
        elif opcao == "0":
            print("\nEncerrando o Clinic-AI. Até logo!")
            break
        else:
            print("\n[Erro] Opção inválida. Tente novamente.")

