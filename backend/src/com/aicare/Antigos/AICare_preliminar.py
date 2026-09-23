import sqlite3
import hashlib
from datetime import datetime


DB_NAME = "saude_idosos.db"


# -------------------------------------------------------------
# 01. BANCO DE DADOS
# -------------------------------------------------------------

def conectar():
    """Abre a conexão com o banco SQLite."""
    return sqlite3.connect(DB_NAME)


def inicializar_banco():
    """Cria todas as tabelas utilizadas pelo sistema."""
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            idade INTEGER NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            email TEXT,
            doencas TEXT,
            observacoes TEXT,
            ativo INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuidadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            telefone TEXT,
            coren_ou_registro TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS familiares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            parentesco TEXT,
            telefone TEXT,
            email TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            dosagem TEXT,
            horario TEXT,
            turno TEXT,
            laboratorio TEXT,
            preco REAL DEFAULT 0,
            quantidade INTEGER DEFAULT 0,
            medicao_preventiva TEXT,
            observacoes TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_administracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            medicamento_nome TEXT,
            data_hora TEXT,
            valor_aferido REAL,
            liberado INTEGER,
            parecer_ia TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)

    conexao.commit()
    conexao.close()


# -------------------------------------------------------------
# 02. UTILITÁRIOS
# -------------------------------------------------------------

def exibir_nome_do_app():
    print("""
░█████╗░██╗░█████╗░░█████╗░██████╗░███████╗
██╔══██╗██║██╔══██╗██╔══██╗██╔══██╗██╔════╝
███████║██║██║░░╚═╝███████║██████╔╝█████╗░░
██╔══██║██║██║░░██╗██╔══██║██╔══██╗██╔══╝░░
██║░░██║██║╚█████╔╝██║░░██║██║░░██║███████╗
╚═╝░░╚═╝╚═╝░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝
""")


def gerar_hash_senha(senha):
    """Gera hash SHA-256 da senha."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def ler_inteiro(mensagem, minimo=None):
    while True:
        try:
            valor = int(input(mensagem).strip())
            if minimo is not None and valor < minimo:
                print(f"Informe um valor maior ou igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("Digite um número inteiro válido.")


def ler_float(mensagem, minimo=None):
    while True:
        try:
            valor = float(input(mensagem).strip().replace(",", "."))
            if minimo is not None and valor < minimo:
                print(f"Informe um valor maior ou igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("Digite um número válido.")


# -------------------------------------------------------------
# 03. USUÁRIOS / LOGIN
# -------------------------------------------------------------

def inicializar_admin_padrao():
    inicializar_banco()

    conexao = conectar()
    cursor = conexao.cursor()

    # Verifica se já existe o administrador padrão
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE cpf = ?", ("00000000000",))
    existe_admin = cursor.fetchone()[0]

    if existe_admin == 0:
        nome_admin = "Administrador Master"
        cpf_admin = "00000000000"
        senha_padrao = "admin123"

        cursor.execute("""
            INSERT INTO usuarios (nome, cpf, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
        """, (
            nome_admin,
            cpf_admin,
            gerar_hash_senha(senha_padrao),
            "Administrador"
        ))

        conexao.commit()

        print("\n" + "=" * 60)
        print("[SEGURANÇA] Administrador padrão criado automaticamente!")
        print(f"CPF de Acesso: {cpf_admin}")
        print(f"Senha Temporária: {senha_padrao}")
        print("Altere a senha antes de utilizar o sistema em produção.")
        print("=" * 60)

    conexao.close()

#*********************************CORRIGIDO**************************************
#def inicializar_admin_padrao():
#    inicializar_banco()

#    conexao = conectar()#
#    cursor = conexao.cursor()
#    cursor.execute("SELECT COUNT(*) FROM usuarios")
#    total_usuarios = cursor.fetchone()[0]

#    if total_usuarios == 0:
#        nome_admin = "Administrador Master"
#        cpf_admin = "000.000.000-00"
#        senha_padrao = "admin123"

#        cursor.execute("""
#            INSERT INTO usuarios (nome, cpf, senha_hash, perfil)
#            VALUES (?, ?, ?, ?)
#        """, (
#            nome_admin,
#            cpf_admin,
#            gerar_hash_senha(senha_padrao),
#            "Administrador"
#        ))

#        conexao.commit()

#        print("\n" + "=" * 60)
#        print("[SEGURANÇA] Primeiro acesso detectado!")
#        print(f"Senha Temporária: {senha_padrao}")
#        print("Altere a senha antes de utilizar o sistema em produção.")
#        print("=" * 60)
#
#    conexao.close()
#****************************************************************************************

def cadastrar_usuario(nome, cpf, senha, perfil):
    conexao = conectar()
    try:
        conexao.execute("""
            INSERT INTO usuarios (nome, cpf, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
        """, (nome, cpf, gerar_hash_senha(senha), perfil))
        conexao.commit()
        print(f"[Sucesso] Usuário '{nome}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"[Erro] O CPF '{cpf}' já possui cadastro no sistema.")
    finally:
        conexao.close()


def realizar_login():
    print("\n" + "=" * 40)
    print("      LOGIN NO APP AICare")
    print("=" * 40)

    cpf_informado = input("Digite o seu CPF: ").strip()
    senha_informada = input("Digite a sua senha: ").strip()

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT nome, cpf, senha_hash, perfil
        FROM usuarios
        WHERE cpf = ?
    """, (cpf_informado,))
    usuario = cursor.fetchone()
    conexao.close()

    if not usuario:
        print("\n[Acesso Negado] CPF não encontrado no sistema.")
        return None

    nome, cpf, senha_hash_salva, perfil = usuario

    if gerar_hash_senha(senha_informada) == senha_hash_salva:
        print(
            f"\n[Acesso Permitido] Bem-vindo(a), {nome}! "
            f"(Perfil: {perfil})"
        )
        return {"nome": nome, "cpf": cpf, "perfil": perfil}

    print("\n[Acesso Negado] Senha incorreta.")
    return None


# -------------------------------------------------------------
# 04. PACIENTES
# -------------------------------------------------------------

def cadastrar_paciente(nome, idade, cpf, email, doencas, observacoes):
    conexao = conectar()
    try:
        conexao.execute("""
            INSERT INTO pacientes
            (nome, idade, cpf, email, doencas, observacoes, ativo)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (nome, idade, cpf, email, doencas, observacoes))
        conexao.commit()
        print(f"[Sucesso] Paciente '{nome}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"[Erro] O CPF '{cpf}' já possui cadastro.")
    finally:
        conexao.close()


def atualizar_paciente(cpf, novo_nome, nova_idade, novo_email,
                       novas_doencas, novas_obs):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE pacientes
        SET nome = ?, idade = ?, email = ?, doencas = ?, observacoes = ?
        WHERE cpf = ?
    """, (
        novo_nome, nova_idade, novo_email,
        novas_doencas, novas_obs, cpf
    ))

    conexao.commit()
    alterado = cursor.rowcount
    conexao.close()

    if alterado:
        print(f"[Sucesso] Paciente com CPF {cpf} atualizado.")
    else:
        print(f"[Aviso] Paciente com CPF {cpf} não encontrado.")


def alternar_status_paciente(cpf, ativo):
    if ativo not in (0, 1):
        print("[Erro] O status deve ser 0 ou 1.")
        return

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "UPDATE pacientes SET ativo = ? WHERE cpf = ?",
        (ativo, cpf)
    )
    conexao.commit()
    alterado = cursor.rowcount
    conexao.close()

    if alterado:
        status_str = "ativado" if ativo == 1 else "inativado"
        print(f"[Sucesso] Paciente com CPF {cpf} foi {status_str}.")
    else:
        print(f"[Aviso] Paciente com CPF {cpf} não encontrado.")


def excluir_paciente(cpf):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf,))
    paciente = cursor.fetchone()

    if not paciente:
        conexao.close()
        print(f"[Erro] Paciente com CPF {cpf} não encontrado.")
        return

    paciente_id = paciente[0]

    # Remove primeiro os registros dependentes.
    cursor.execute(
        "DELETE FROM medicamentos WHERE paciente_id = ?",
        (paciente_id,)
    )
    cursor.execute(
        "DELETE FROM familiares WHERE paciente_id = ?",
        (paciente_id,)
    )
    cursor.execute(
        "DELETE FROM historico_administracoes WHERE paciente_id = ?",
        (paciente_id,)
    )
    cursor.execute(
        "DELETE FROM pacientes WHERE id = ?",
        (paciente_id,)
    )

    conexao.commit()
    conexao.close()

    print("[Sucesso] Paciente e registros vinculados foram excluídos.")


# -------------------------------------------------------------
# 05. CUIDADORES
# -------------------------------------------------------------

def cadastrar_cuidador(nome, cpf, telefone, registro):
    conexao = conectar()
    try:
        conexao.execute("""
            INSERT INTO cuidadores
            (nome, cpf, telefone, coren_ou_registro)
            VALUES (?, ?, ?, ?)
        """, (nome, cpf, telefone, registro))
        conexao.commit()
        print(f"[Sucesso] Cuidador(a) '{nome}' cadastrado(a).")
    except sqlite3.IntegrityError:
        print(f"[Erro] O CPF '{cpf}' já possui cadastro.")
    finally:
        conexao.close()


def atualizar_cuidador(cpf, novo_nome, novo_telefone, novo_registro):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE cuidadores
        SET nome = ?, telefone = ?, coren_ou_registro = ?
        WHERE cpf = ?
    """, (novo_nome, novo_telefone, novo_registro, cpf))

    conexao.commit()
    alterado = cursor.rowcount
    conexao.close()

    if alterado:
        print(f"[Sucesso] Cuidador(a) com CPF {cpf} atualizado(a).")
    else:
        print(f"[Aviso] Cuidador(a) com CPF {cpf} não encontrado(a).")


def excluir_cuidador(cpf):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM cuidadores WHERE cpf = ?", (cpf,))
    conexao.commit()
    removido = cursor.rowcount
    conexao.close()

    if removido:
        print(f"[Sucesso] Cuidador(a) com CPF {cpf} excluído(a).")
    else:
        print(f"[Aviso] Cuidador(a) com CPF {cpf} não encontrado(a).")


# -------------------------------------------------------------
# 06. FAMILIARES
# -------------------------------------------------------------

def cadastrar_familiar(paciente_id, nome, parentesco, telefone, email):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT id FROM pacientes WHERE id = ?",
        (paciente_id,)
    )
    if cursor.fetchone() is None:
        conexao.close()
        print("[Erro] Paciente não encontrado.")
        return

    cursor.execute("""
        INSERT INTO familiares
        (paciente_id, nome, parentesco, telefone, email)
        VALUES (?, ?, ?, ?, ?)
    """, (paciente_id, nome, parentesco, telefone, email))

    conexao.commit()
    conexao.close()
    print(f"[Sucesso] Familiar '{nome}' cadastrado.")


def atualizar_familiar(familiar_id, novo_nome, novo_parentesco,
                       novo_telefone, novo_email):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE familiares
        SET nome = ?, parentesco = ?, telefone = ?, email = ?
        WHERE id = ?
    """, (
        novo_nome, novo_parentesco,
        novo_telefone, novo_email, familiar_id
    ))

    conexao.commit()
    alterado = cursor.rowcount
    conexao.close()

    if alterado:
        print(f"[Sucesso] Familiar ID {familiar_id} atualizado.")
    else:
        print(f"[Aviso] Familiar ID {familiar_id} não encontrado.")


def excluir_familiar(familiar_id):
    conexao = conectar()
    cursor = conexao.cursor()

    # Correção do SQL original: "id = ?0" era inválido.
    cursor.execute(
        "DELETE FROM familiares WHERE id = ?",
        (familiar_id,)
    )

    conexao.commit()
    removido = cursor.rowcount
    conexao.close()

    if removido:
        print(f"[Sucesso] Familiar ID {familiar_id} excluído.")
    else:
        print(f"[Aviso] Familiar ID {familiar_id} não encontrado.")


# -------------------------------------------------------------
# 07. MEDICAMENTOS
# -------------------------------------------------------------

def cadastrar_medicamento(paciente_id, nome, dosagem, horario, turno,
                          laboratorio, preco, observacoes,
                          preventiva, quantidade):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT id FROM pacientes WHERE id = ?",
        (paciente_id,)
    )
    if cursor.fetchone() is None:
        conexao.close()
        print("[Erro] Paciente não encontrado.")
        return

    cursor.execute("""
        INSERT INTO medicamentos
        (paciente_id, nome, dosagem, horario, turno, laboratorio,
         preco, quantidade, medicao_preventiva, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        paciente_id, nome, dosagem, horario, turno, laboratorio,
        preco, quantidade, preventiva, observacoes
    ))

    conexao.commit()
    conexao.close()
    print(f"[Sucesso] Medicamento '{nome}' cadastrado.")


def atualizar_medicamento(medicamento_id, nova_dosagem, novo_horario,
                          novo_turno, novo_preco, nova_qtd, nova_regra):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE medicamentos
        SET dosagem = ?, horario = ?, turno = ?, preco = ?,
            quantidade = ?, medicao_preventiva = ?
        WHERE id = ?
    """, (
        nova_dosagem, novo_horario, novo_turno,
        novo_preco, nova_qtd, nova_regra, medicamento_id
    ))

    conexao.commit()
    alterado = cursor.rowcount
    conexao.close()

    if alterado:
        print(f"[Sucesso] Medicamento ID {medicamento_id} atualizado.")
    else:
        print(f"[Aviso] Medicamento ID {medicamento_id} não encontrado.")


def excluir_medicamento(medicamento_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "DELETE FROM medicamentos WHERE id = ?",
        (medicamento_id,)
    )
    conexao.commit()
    removido = cursor.rowcount
    conexao.close()

    if removido:
        print(f"[Sucesso] Medicamento ID {medicamento_id} excluído.")
    else:
        print(f"[Aviso] Medicamento ID {medicamento_id} não encontrado.")


# -------------------------------------------------------------
# 08. ALERTAS, RELATÓRIOS E SINCRONIZAÇÃO
# -------------------------------------------------------------

def verificar_alertas_estoque():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT p.nome, m.nome, m.dosagem, m.quantidade
        FROM medicamentos m
        JOIN pacientes p ON m.paciente_id = p.id
        WHERE m.quantidade <= 5
        ORDER BY m.quantidade ASC
    """)

    alertas = cursor.fetchall()
    conexao.close()

    print("\n" + "=" * 60)
    print("      ALERTAS DE ESTOQUE DE MEDICAMENTOS")
    print("=" * 60)

    if not alertas:
        print("Nenhum medicamento com estoque crítico no momento.")
    else:
        for paciente_nome, med_nome, dosagem, qtd in alertas:
            print(
                f"ATENÇÃO: '{med_nome} ({dosagem})' - "
                f"paciente: {paciente_nome} - estoque: {qtd} un."
            )

    print("=" * 60)


def gerar_relatorio_geral():
    conexao = conectar()
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
    print("          RELATÓRIO GERAL DO SISTEMA - AICare")
    print("=" * 50)
    print(f"Pacientes ativos: {total_pacientes}")
    print(f"Cuidadores cadastrados: {total_cuidadores}")
    print(f"Medicamentos cadastrados: {total_medicamentos}")
    print(f"Registros de auditoria: {total_auditorias}")
    print("=" * 50)


def sincronizar_base_dados():
    print("\n" + "=" * 50)
    print("       SINCRONIZAÇÃO DE BASES DE DADOS")
    print("=" * 50)
    print("[Sync] Conectando com o servidor remoto seguro...")
    print(f"[Sync] Verificando SQLite local: '{DB_NAME}'...")
    print("[Sync] Rotina de sincronização simulada com sucesso.")
    print("=" * 50)


# -------------------------------------------------------------
# 09. CONSULTAS
# -------------------------------------------------------------

def consultar_dados_por_cpf(cpf_buscado):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome, idade, cpf, email, doencas, observacoes, ativo
        FROM pacientes
        WHERE cpf = ?
    """, (cpf_buscado,))

    paciente = cursor.fetchone()

    if not paciente:
        conexao.close()
        print(f"\n[Aviso] Nenhum paciente encontrado: {cpf_buscado}")
        return

    p_id, nome, idade, cpf, email, doencas, observacoes, ativo = paciente
    status = "ATIVO" if ativo == 1 else "INATIVO"

    print("\n" + "=" * 65)
    print(f"FICHA COMPLETA DO PACIENTE: {nome}")
    print("=" * 65)
    print(f"CPF: {cpf} | Idade: {idade} anos | Status: {status}")
    print(f"E-mail: {email}")
    print(f"Diagnósticos/Doenças: {doencas}")
    print(f"Observações: {observacoes}")

    print("\n" + "-" * 65)
    print("MEDICAMENTOS CADASTRADOS")
    print("-" * 65)

    cursor.execute("""
        SELECT id, nome, dosagem, horario, turno, laboratorio,
               preco, quantidade, medicao_preventiva
        FROM medicamentos
        WHERE paciente_id = ?
    """, (p_id,))

    medicamentos = cursor.fetchall()

    if not medicamentos:
        print("Nenhum medicamento cadastrado.")
    else:
        for med in medicamentos:
            (
                m_id, m_nome, dosagem, horario, turno,
                laboratorio, preco, quantidade, preventiva
            ) = med

            print(
                f"[{m_id}] {m_nome} - {dosagem} "
                f"({turno} às {horario})"
            )
            print(
                f"    Laboratório: {laboratorio} | "
                f"Preço: R$ {preco:.2f} | Estoque: {quantidade}"
            )
            print(f"    Regra preventiva: {preventiva}")

    print("\n" + "-" * 65)
    print("FAMILIARES RESPONSÁVEIS")
    print("-" * 65)

    cursor.execute("""
        SELECT id, nome, parentesco, telefone, email
        FROM familiares
        WHERE paciente_id = ?
    """, (p_id,))

    familiares = cursor.fetchall()

    if not familiares:
        print("Nenhum familiar cadastrado.")
    else:
        for fam in familiares:
            f_id, f_nome, parentesco, telefone, email_fam = fam
            print(
                f"[{f_id}] {f_nome} ({parentesco}) - "
                f"Tel: {telefone} | E-mail: {email_fam}"
            )

    print("=" * 65)
    conexao.close()


def consultar_historico_paciente(cpf_buscado):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT id, nome FROM pacientes WHERE cpf = ?",
        (cpf_buscado,)
    )
    paciente = cursor.fetchone()

    if not paciente:
        conexao.close()
        print(f"\n[Aviso] Nenhum paciente encontrado: {cpf_buscado}")
        return

    paciente_id, nome_paciente = paciente

    cursor.execute("""
        SELECT medicamento_nome, data_hora, valor_aferido,
               liberado, parecer_ia
        FROM historico_administracoes
        WHERE paciente_id = ?
        ORDER BY id DESC
    """, (paciente_id,))

    historicos = cursor.fetchall()
    conexao.close()

    print("\n" + "=" * 70)
    print(f"HISTÓRICO DE AUDITORIA: {nome_paciente}")
    print("=" * 70)

    if not historicos:
        print("Nenhum registro encontrado.")
        return

    for i, hist in enumerate(historicos, start=1):
        med_nome, data_hora, valor, liberado, parecer = hist
        status = "LIBERADO" if liberado == 1 else "BLOQUEADO"

        print(f"{i}. Data/Hora: {data_hora}")
        print(f"   Medicamento: {med_nome}")
        print(f"   Valor aferido: {valor}")
        print(f"   Status da IA: {status}")
        print(f"   Parecer: {parecer}")
        print("-" * 65)


# -------------------------------------------------------------
# 10. MENUS
# -------------------------------------------------------------

def menu_gerenciar_pacientes():
    while True:
        print("\n--- GERENCIAMENTO DE PACIENTES ---")
        print("1. Cadastrar Paciente")
        print("2. Atualizar Paciente")
        print("3. Ativar / Inativar Paciente")
        print("4. Excluir Paciente")
        print("0. Voltar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            nome = input("Nome completo: ").strip()
            idade = ler_inteiro("Idade: ", 0)
            cpf = input("CPF: ").strip()
            email = input("E-mail: ").strip()
            doencas = input("Doenças/Diagnósticos: ").strip()
            obs = input("Observações: ").strip()
            cadastrar_paciente(nome, idade, cpf, email, doencas, obs)

        elif opcao == "2":
            cpf = input("CPF do paciente: ").strip()
            nome = input("Novo nome: ").strip()
            idade = ler_inteiro("Nova idade: ", 0)
            email = input("Novo e-mail: ").strip()
            doencas = input("Novas doenças: ").strip()
            obs = input("Novas observações: ").strip()
            atualizar_paciente(cpf, nome, idade, email, doencas, obs)

        elif opcao == "3":
            cpf = input("CPF do paciente: ").strip()
            status = ler_inteiro("1 para ATIVAR ou 0 para INATIVAR: ")
            alternar_status_paciente(cpf, status)

        elif opcao == "4":
            cpf = input("CPF do paciente a excluir: ").strip()
            excluir_paciente(cpf)

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


def menu_gerenciar_cuidadores():
    while True:
        print("\n--- GERENCIAMENTO DE CUIDADORES ---")
        print("1. Cadastrar Cuidador(a)")
        print("2. Atualizar Cuidador(a)")
        print("3. Excluir Cuidador(a)")
        print("0. Voltar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            nome = input("Nome: ").strip()
            cpf = input("CPF: ").strip()
            telefone = input("Telefone: ").strip()
            registro = input("Registro (Coren/CBO): ").strip()
            cadastrar_cuidador(nome, cpf, telefone, registro)

        elif opcao == "2":
            cpf = input("CPF do cuidador: ").strip()
            nome = input("Novo nome: ").strip()
            telefone = input("Novo telefone: ").strip()
            registro = input("Novo registro: ").strip()
            atualizar_cuidador(cpf, nome, telefone, registro)

        elif opcao == "3":
            cpf = input("CPF do cuidador: ").strip()
            excluir_cuidador(cpf)

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


def obter_id_paciente_por_cpf():
    cpf = input("CPF do paciente vinculado: ").strip()

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf,))
    resultado = cursor.fetchone()
    conexao.close()

    if not resultado:
        print("Paciente não encontrado.")
        return None

    return resultado[0]


def menu_gerenciar_familiares():
    while True:
        print("\n--- GERENCIAMENTO DE FAMILIARES ---")
        print("1. Cadastrar Familiar")
        print("2. Atualizar Familiar")
        print("3. Excluir Familiar")
        print("0. Voltar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            paciente_id = obter_id_paciente_por_cpf()
            if paciente_id is None:
                continue

            nome = input("Nome do familiar: ").strip()
            parentesco = input("Parentesco: ").strip()
            telefone = input("Telefone: ").strip()
            email = input("E-mail: ").strip()

            cadastrar_familiar(
                paciente_id, nome, parentesco, telefone, email
            )

        elif opcao == "2":
            familiar_id = ler_inteiro("ID do familiar: ", 1)
            nome = input("Novo nome: ").strip()
            parentesco = input("Novo parentesco: ").strip()
            telefone = input("Novo telefone: ").strip()
            email = input("Novo e-mail: ").strip()

            atualizar_familiar(
                familiar_id, nome, parentesco, telefone, email
            )

        elif opcao == "3":
            familiar_id = ler_inteiro("ID do familiar: ", 1)
            excluir_familiar(familiar_id)

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


def menu_gerenciar_medicamentos():
    while True:
        print("\n--- GERENCIAMENTO DE MEDICAMENTOS ---")
        print("1. Cadastrar Medicamento")
        print("2. Atualizar Medicamento")
        print("3. Excluir Medicamento")
        print("0. Voltar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            paciente_id = obter_id_paciente_por_cpf()
            if paciente_id is None:
                continue

            nome = input("Nome do medicamento: ").strip()
            dosagem = input("Dosagem: ").strip()
            horario = input("Horário: ").strip()
            turno = input("Turno: ").strip()
            laboratorio = input("Laboratório: ").strip()
            preco = ler_float("Preço (R$): ", 0)
            observacoes = input("Observações: ").strip()
            preventiva = input("Regra Preventiva: ").strip()
            quantidade = ler_inteiro("Quantidade em estoque: ", 0)

            cadastrar_medicamento(
                paciente_id, nome, dosagem, horario, turno,
                laboratorio, preco, observacoes,
                preventiva, quantidade
            )

        elif opcao == "2":
            medicamento_id = ler_inteiro("ID do medicamento: ", 1)
            dosagem = input("Nova dosagem: ").strip()
            horario = input("Novo horário: ").strip()
            turno = input("Novo turno: ").strip()
            preco = ler_float("Novo preço: ", 0)
            quantidade = ler_inteiro("Nova quantidade: ", 0)
            regra = input("Nova regra preventiva: ").strip()

            atualizar_medicamento(
                medicamento_id, dosagem, horario, turno,
                preco, quantidade, regra
            )

        elif opcao == "3":
            medicamento_id = ler_inteiro("ID do medicamento: ", 1)
            excluir_medicamento(medicamento_id)

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


# -------------------------------------------------------------
# 11. MENU PRINCIPAL
# -------------------------------------------------------------

def menu_principal():
    while True:
        print("\n" + "=" * 60)
        print("       AICare - GESTÃO INTELIGENTE DE SAÚDE")
        print("=" * 60)
        print("1. Gerenciar Pacientes")
        print("2. Gerenciar Cuidadores")
        print("3. Gerenciar Familiares")
        print("4. Gerenciar Medicamentos")
        print("5. Alertas de Estoque")
        print("6. Relatórios Gerais")
        print("7. Sincronização de Bases")
        print("8. Avaliação Clínica e Auditoria (IA)")
        print("9. Consultar Ficha / Histórico por CPF")
        print("0. Sair")
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
            print("\n[Módulo IA] Funcionalidade de avaliação clínica integrada.")
            print("A integração com o modelo de IA ainda precisa ser implementada.")

        elif opcao == "9":
            cpf = input("CPF do paciente: ").strip()
            consultar_dados_por_cpf(cpf)
            consultar_historico_paciente(cpf)

        elif opcao == "0":
            print("\nEncerrando o AICare. Até logo!")
            break

        else:
            print("\n[Erro] Opção inválida. Tente novamente.")


# -------------------------------------------------------------
# 12. PONTO DE ENTRADA
# -------------------------------------------------------------

if __name__ == "__main__":
    inicializar_banco()
    inicializar_admin_padrao()
    exibir_nome_do_app()

    usuario_logado = realizar_login()

    if usuario_logado:
        menu_principal()
    else:
        print("Login não realizado. Sistema encerrado.")
