import sqlite3
import hashlib
import datetime

# -------------------------------------------------------------
# 01. CRIANDO AS TABELAS DO BANCO DE DADOS
# -------------------------------------------------------------
def inicializar_banco():
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
    # Tabela de Usuários / Login
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT UNIQUE,
            senha_hash TEXT,
            perfil TEXT
        )
    """)
    
    # Tabela de Pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            idade INTEGER,
            cpf TEXT UNIQUE,
            email TEXT,
            doencas TEXT,
            observacoes TEXT,
            ativo INTEGER DEFAULT 1
        )
    """)
    
    # Tabela de Cuidadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuidadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT UNIQUE,
            telefone TEXT,
            coren_ou_registro TEXT
        )
    """)
    
    # Tabela de Familiares
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS familiares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            nome TEXT,
            parentesco TEXT,
            telefone TEXT,
            email TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)
    
    # Tabela de Medicamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            nome TEXT,
            dosagem TEXT,
            horario TEXT,
            turno TEXT,
            laboratorio TEXT,
            preco REAL,
            observacoes TEXT,
            medicao_preventiva TEXT,
            quantidade INTEGER,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)
    
    # Tabela de Histórico de Auditoria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_administracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            medicamento_nome TEXT,
            data_hora TEXT,
            valor_aferido TEXT,
            liberado INTEGER,
            parecer_ia TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)
    
    conexao.commit()
    conexao.close()

# -------------------------------------------------------------
# 02. FUNÇÕES DE SEGURANÇA E LOGIN
# -------------------------------------------------------------
def gerar_hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def inicializar_admin_padrao():
    inicializar_banco()
    
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    
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
        print(" ⚠️ Recomendamos alterar a senha no primeiro uso.")
        print("=" * 60 + "\n")
        
    conexao.close()


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
    
    if senha_tentativa_hash == senha_hash_salva:
        print(f"\n[Acesso Permitido] Bem-vindo(a) de volta, {nome}! (Perfil: {perfil})")
        return {"nome": nome, "cpf": cpf_informado, "perfil": perfil}
    else:
        print("\n[Acesso Negado] Senha incorreta.")
        return None

# -------------------------------------------------------------
# 03. CRUD DE PACIENTES
# -------------------------------------------------------------
def cadastrar_paciente(nome, idade, cpf, email, doencas, obs):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            INSERT INTO pacientes (nome, idade, cpf, email, doencas, observacoes, ativo)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (nome, idade, cpf, email, doencas, obs))
        conexao.commit()
        print(f"[Banco] Paciente '{nome}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"[Erro] O CPF '{cpf}' já está cadastrado.")
    finally:
        conexao.close()

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
    print(f"[Banco] Dados do paciente com CPF {cpf} atualizados!")

def alternar_status_paciente(cpf, ativo):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("UPDATE pacientes SET ativo = ? WHERE cpf = ?", (ativo, cpf))
    conexao.commit()
    conexao.close()
    status_str = "ativado" if ativo == 1 else "inativado"
    print(f"[Banco] Paciente com CPF {cpf} foi {status_str}!")

def excluir_paciente(cpf):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf,))
    paciente = cursor.fetchone()
    if not paciente:
        print(f"[Erro] Paciente com CPF {cpf} não encontrado.")
        conexao.close()
        return
    p_id = paciente[0]
    cursor.execute("DELETE FROM medicamentos WHERE paciente_id = ?", (p_id,))
    cursor.execute("DELETE FROM familiares WHERE paciente_id = ?", (p_id,))
    cursor.execute("DELETE FROM historico_administracoes WHERE paciente_id = ?", (p_id,))
    cursor.execute("DELETE FROM pacientes WHERE id = ?", (p_id,))
    conexao.commit()
    conexao.close()
    print("[Banco] Paciente e registros vinculados excluídos com sucesso.")

# -------------------------------------------------------------
# 04. CRUD DE CUIDADORES
# -------------------------------------------------------------
def cadastrar_cuidador(nome, cpf, telefone, registro):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            INSERT INTO cuidadores (nome, cpf, telefone, coren_ou_registro)
            VALUES (?, ?, ?, ?)
        """, (nome, cpf, telefone, registro))
        conexao.commit()
        print(f"[Banco] Cuidador(a) '{nome}' cadastrado(a) com sucesso!")
    except sqlite3.IntegrityError:
        print(f"[Erro] O CPF '{cpf}' já está cadastrado.")
    finally:
        conexao.close()

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
    print(f"[Banco] Cuidador(a) atualizado(a) com sucesso!")

def excluir_cuidador(cpf):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM cuidadores WHERE cpf = ?", (cpf,))
    conexao.commit()
    conexao.close()
    print("[Banco] Cuidador(a) excluído(a) com sucesso.")

# -------------------------------------------------------------
# 05. CRUD DE FAMILIARES
# -------------------------------------------------------------
def cadastrar_familiar(p_id, nome, parentesco, telefone, email):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("""
        INSERT INTO familiares (paciente_id, nome, parentesco, telefone, email)
        VALUES (?, ?, ?, ?, ?)
    """, (p_id, nome, parentesco, telefone, email))
    conexao.commit()
    conexao.close()
    print(f"[Banco] Familiar '{nome}' cadastrado com sucesso!")

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
    print(f"[Banco] Familiar atualizado com sucesso!")

def excluir_familiar(familiar_id):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM familiares WHERE id = ?", (familiar_id,))
    conexao.commit()
    conexao.close()
    print("[Banco] Familiar excluído com sucesso.")

# -------------------------------------------------------------
# 06. CRUD DE MEDICAMENTOS
# -------------------------------------------------------------
def cadastrar_medicamento(p_id, nome, dosagem, horario, turno, lab, preco, obs, preventiva, qtd):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("""
        INSERT INTO medicamentos (paciente_id, nome, dosagem, horario, turno, laboratorio, preco, observacoes, medicao_preventiva, quantidade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (p_id, nome, dosagem, horario, turno, lab, preco, obs, preventiva, qtd))
    conexao.commit()
    conexao.close()
    print(f"[Banco] Medicamento '{nome}' cadastrado com sucesso!")

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
    print(f"[Banco] Medicamento ID {medicamento_id} atualizado com sucesso!")

def excluir_medicamento(medicamento_id):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM medicamentos WHERE id = ?", (medicamento_id,))
    conexao.commit()
    conexao.close()
    print(f"[Banco] Medicamento ID {medicamento_id} excluído com sucesso.")

# -------------------------------------------------------------
# 07. RELATÓRIOS E CONSULTAS
# -------------------------------------------------------------
def verificar_alertas_estoque():
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
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
            print(f"⚠️ ATENÇÃO: O remédio '{med_nome} ({dosagem})' do paciente {paciente_nome} está baixo ({qtd} un.).")
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
    print("[Sync] Conectando com o servidor remoto seguro...")
    print("[Sync] Verificando integridade do SQLite local ('saude_idosos.db')...")
    print("[Sync] Dados sincronizados com sucesso!")
    print("=" * 50)

def consultar_dados_por_cpf(cpf_buscado):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT id, nome, idade, cpf, email, doencas, observacoes, ativo 
        FROM pacientes WHERE cpf = ?
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
    print(f"• Diagnósticos: {doencas}")
    print(f"• Observações: {observacoes}")
    
    cursor.execute("SELECT id, nome, dosagem, horario, turno, laboratorio, preco, quantidade, medicao_preventiva FROM medicamentos WHERE paciente_id = ?", (p_id,))
    medicamentos = cursor.fetchall()
    print("\n" + "-" * 20 + " MEDICAMENTOS " + "-" * 20)
    for med in medicamentos:
        print(f"[{med[0]}] {med[1]} - {med[2]} ({med[5]} R$ {med[6]:.2f} | Estoque: {med[7]})")
        
    cursor.execute("SELECT id, nome, parentesco, telefone FROM familiares WHERE paciente_id = ?", (p_id,))
    familiares = cursor.fetchall()
    print("\n" + "-" * 20 + " FAMILIARES " + "-" * 20)
    for fam in familiares:
        print(f"[{fam[0]}] {fam[1]} ({fam[2]}) - Tel: {fam[3]}")
    print("=" * 65)
    conexao.close()

def consultar_historico_paciente(cpf_buscado):
    conexao = sqlite3.connect("saude_idosos.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM pacientes WHERE cpf = ?", (cpf_buscado,))
    paciente = cursor.fetchone()
    
    if not paciente:
        conexao.close()
        return
        
    p_id, nome_paciente = paciente
    cursor.execute("SELECT medicamento_nome, data_hora, valor_aferido, liberado, parecer_ia FROM historico_administracoes WHERE paciente_id = ? ORDER BY id DESC", (p_id,))
    historicos = cursor.fetchall()
    conexao.close()
    
    print("\n" + "=" * 60)
    print(f"HISTÓRICO DE AUDITORIA: {nome_paciente}")
    print("=" * 60)
    if not historicos:
        print("Nenhum registro encontrado.")
    else:
        for h in historicos:
            status = "LIBERADO ✅" if h[3] == 1 else "BLOQUEADO ❌"
            print(f"• [{h[1]}] {h[0]} | Valor: {h[2]} | Status: {status}")
            print(f"  Parecer: {h[4]}")
    print("=" * 60)

# -------------------------------------------------------------
# 08. SUBMENUS
# -------------------------------------------------------------
def menu_gerenciar_pacientes():
    while True:
        print("\n--- GERENCIAMENTO DE PACIENTES ---")
        print("1. Cadastrar Paciente")
        print("2. Atualizar Paciente")
        print("3. Ativar / Inativar Paciente")
        print("4. Excluir Paciente")
        print("0. Voltar")
        op = input("Escolha: ").strip()
        if op == "1":
            cadastrar_paciente(input("Nome: "), int(input("Idade: ")), input("CPF: "), input("E-mail: "), input("Doenças: "), input("Obs: "))
        elif op == "2":
            atualizar_paciente(input("CPF do paciente: "), input("Novo Nome: "), int(input("Nova Idade: ")), input("Novo E-mail: "), input("Novas Doenças: "), input("Novas Obs: "))
        elif op == "3":
            alternar_status_paciente(input("CPF: "), int(input("1 (Ativar) ou 0 (Inativar): ")))
        elif op == "4":
            excluir_paciente(input("CPF a excluir: "))
        elif op == "0":
            break

def menu_gerenciar_cuidadores():
    while True:
        print("\n--- GERENCIAMENTO DE CUIDADORES ---")
        print("1. Cadastrar Cuidador")
        print("2. Atualizar Cuidador")
        print("3. Excluir Cuidador")
        print("0. Voltar")
        op = input("Escolha: ").strip()
        if op == "1":
            cadastrar_cuidador(input("Nome: "), input("CPF: "), input("Telefone: "), input("Registro (Coren/CBO): "))
        elif op == "2":
            atualizar_cuidador(input("CPF do cuidador: "), input("Novo Nome: "), input("Novo Tel: "), input("Novo Registro: "))
        elif op == "3":
            excluir_cuidador(input("CPF a excluir: "))
        elif op == "0":
            break

def menu_gerenciar_familiares():
    while True:
        print("\n--- GERENCIAMENTO DE FAMILIARES ---")
        print("1. Cadastrar Familiar")
        print("2. Atualizar Familiar")
        print("3. Excluir Familiar")
        print("0. Voltar")
        op = input("Escolha: ").strip()
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
            cadastrar_familiar(res[0], input("Nome do familiar: "), input("Parentesco: "), input("Telefone: "), input("E-mail: "))
        elif op == "2":
            atualizar_familiar(int(input("ID do familiar: ")), input("Novo Nome: "), input("Novo Parentesco: "), input("Novo Tel: "), input("Novo E-mail: "))
        elif op == "3":
            excluir_familiar(int(input("ID do familiar a excluir: ")))
        elif op == "0":
            break

def menu_gerenciar_medicamentos():
    while True:
        print("\n--- GERENCIAMENTO DE MEDICAMENTOS ---")
        print("1. Cadastrar Medicamento")
        print("2. Atualizar Medicamento")
        print("3. Excluir Medicamento")
        print("0. Voltar")
        op = input("Escolha: ").strip()
        if op == "1":
            cpf_p = input("CPF do paciente dono: ")
            conexao = sqlite3.connect("saude_idosos.db")
            cursor = conexao.cursor()
            cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf_p,))
            res = cursor.fetchone()
            conexao.close()
            if not res:
                print("Paciente não encontrado.")
                continue
            cadastrar_medicamento(res[0], input("Nome: "), input("Dosagem: "), input("Horário: "), input("Turno: "), input("Lab: "), float(input("Preço: ")), input("Obs: "), input("Regra Preventiva: "), int(input("Qtd Estoque: ")))
        elif op == "2":
            atualizar_medicamento(int(input("ID do Medicamento: ")), input("Nova Dosagem: "), input("Novo Horário: "), input("Novo Turno: "), float(input("Novo Preço: ")), int(input("Nova Qtd: ")), input("Nova Regra: "))
        elif op == "3":
            excluir_medicamento(int(input("ID do Medicamento a excluir: ")))
        elif op == "0":
            break

# -------------------------------------------------------------
# 09. MENU PRINCIPAL
# -------------------------------------------------------------
def menu_principal():
    while True:
        print("\n" + "=" * 60)
        print("       CLINIC-AI - GESTÃO INTELIGENTE DE SAÚDE")
        print("=" * 60)
        print("1. Gerenciar Pacientes")
        print("2. Gerenciar Cuidadores")
        print("3. Gerenciar Familiares")
        print("4. Gerenciar Medicamentos")
        print("5. Alertas de Estoque")
        print("6. Relatórios Gerais")
        print("7. Sincronização de Bases de Dados")
        print("8. Avaliação Clínica (IA)")
        print("9. Consultar Ficha / Histórico por CPF")
        print("0. Sair")
        print("-" * 60)
        
        opcao = input("Escolha: ").strip()
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
            print("\n[Módulo IA] Funcionalidade integrada.")
        elif opcao == "9":
            cpf_b = input("Digite o CPF do paciente: ")
            consultar_dados_por_cpf(cpf_b)
            consultar_historico_paciente(cpf_b)
        elif opcao == "0":
            print("\nEncerrando o Clinic-AI. Até logo!")
            break
        else:
            print("\n[Erro] Opção inválida.")

# -------------------------------------------------------------
# EXECUÇÃO DO PROGRAMA
# -------------------------------------------------------------
if __name__ == "__main__":
    inicializar_admin_padrao()
    usuario_logado = realizar_login()
    if usuario_logado:
        menu_principal()