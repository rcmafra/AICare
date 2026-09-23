import os
import sqlite3
import json
#from google import genai
#from google.colab import userdata

def exibir_nome_do_app():  
    print("""      
░█████╗░██╗░█████╗░░█████╗░██████╗░███████╗
██╔══██╗██║██╔══██╗██╔══██╗██╔══██╗██╔════╝
███████║██║██║░░╚═╝███████║██████╔╝█████╗░░
██╔══██║██║██║░░██╗██╔══██║██╔══██╗██╔══╝░░
██║░░██║██║╚█████╔╝██║░░██║██║░░██║███████╗
╚═╝░░╚═╝╚═╝░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝
""")

# ------------------------------------------------------
# 1. Criando o Banco de Dados e as tabelas no SQLite
#-------------------------------------------------------
def inicializar_banco():
    conexao = sqlite3.connect("aicare_saude.db")
    cursor = conexao.cursor()

    # 1. Tabela de Pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            idade INTEGER,
            cpf TEXT,
            email TEXT UNIQUE,
            doencas TEXT,
            observacoes TEXT
        )
    """)

    # 2. Tabela de Medicamentos vinculada ao Paciente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            nome_remedio TEXT,
            dosagem TEXT,
            horario TEXT,
            turno TEXT,
            laboratorio TEXT,
            preco REAL,
            observacoes_remedio TEXT,
            medicao_preventiva TEXT,
            quantidade INTEGER,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)

    # 3. Tabela de Cuidadores vinculada ao Paciente (CORRIGIDO: adicionada a vírgula antes do FOREIGN KEY)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuidadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            nome_cuidador TEXT,
            idade_cuidador INTEGER,
            cpf_cuidador TEXT,
            email_cuidador TEXT UNIQUE,
            observacoes_cuidador TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)

    # 4. Tabela de Familiares vinculada ao Paciente (CORRIGIDO: adicionada a vírgula antes do FOREIGN KEY)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS familiares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            nome_familiar TEXT,
            idade_familiar INTEGER,
            cpf_familiar TEXT,
            email_familiar TEXT UNIQUE,
            observacoes_familiar TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)

    # Salvar (comitar) as alterações e fechar a conexão
    conexao.commit()
    conexao.close()
    print("[Sistema] Banco de dados SQLite inicializado com sucesso!")

def exibir_opcoes():
    print('1. Cadastrar')
    print('2. Consultar')
    print('3. Alterar')
    print('4. Ativar')
    print('5. Sair\n')

def escolher_opcao():
    try:
        opcao_escolhida = int(input('Escolha uma opção: '))

        if opcao_escolhida == 1:
            cadastrar()
        elif opcao_escolhida == 2:    
            print('Consultar')
        elif opcao_escolhida == 3:    
            print('Alterar')
        elif opcao_escolhida == 4:    
            print('Ativar')
        elif opcao_escolhida == 5:  
            finalizar_app()
        else:
            opcao_invalida()
    except ValueError:
        opcao_invalida()

def finalizar_app():
    os.system('cls')
    # os.system('clear') # no mac/linux
    print('Finalizando o app\n')

def opcao_invalida():
    print('Opção inválida!\n')
    input('Digite uma tecla para voltar ao menu principal: ')
    main()

def cadastrar():
    os.system('cls')
    print('cadastro\n')
    try:
        opcao_pessoa = int(input('Escolha uma opção: '))

        if opcao_pessoa == 1:
            os.system('cls')
            print('=== CADASTRO DE NOVO PACIENTE ===\n')

            # 1. Coletando dados do Paciente
            nome = input('Nome do paciente: ')
            idade = int(input('Idade do paciente: '))
            cpf = input('CPF do paciente: ')
            email = input('Email do paciente: ')
            doencas = input('Doenças pré-existentes: ')
            observacoes = input('Observações gerais: ')
            
#                with sqlite3.connect("aicare_saude.db") as conexao:
#                    cursor = conexao.cursor()

                    # Inserindo o paciente e capturando o ID gerado automaticamente
                    cursor.execute("""
                        INSERT INTO pacientes (nome, idade, cpf, email, doencas, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (nome, idade, cpf, email, doencas, observacoes))

                    paciente_id = cursor.lastrowid
                    print(f"\n[Sucesso] Paciente cadastrado com ID: {paciente_id}\n")

        elif opcao_pessoa == 2:    
            cuidador()
        elif opcao_pessoa == 3:    
            familiar()
        else:
            opcao_invalida()
    except ValueError:
        opcao_invalida()

def main():
    # Executando a criação do banco
    inicializar_banco()
    os.system('cls')
    exibir_nome_do_app()
    exibir_opcoes()
    escolher_opcao()

if __name__ == '__main__':
    main()
