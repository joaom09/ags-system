import sqlite3
import os

db_path = 'database/base.db'

def conexao():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    os.makedirs('database', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    conn = conexao()

    conn.executescript('''
        CREATE TABLE IF NOT EXISTS cavalos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sexo_id INTEGER,
            raca_id INTEGER,
            idade INTEGER,
            pelagem_id INTEGER,
            proprietario_id INTEGER,
            imagem TEXT,
            FOREIGN KEY (sexo_id) REFERENCES sexo(id),
            FOREIGN KEY (raca_id) REFERENCES raca(id),
            FOREIGN KEY (pelagem_id) REFERENCES pelagem(id),
            FOREIGN KEY (proprietario_id) REFERENCES proprietario(id)
        );
                       
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cavalo_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT,
            data TEXT DEFAULT CURRENT_TIMESTAMP,
            proprietario_id INTEGER,
            FOREIGN KEY (cavalo_id) REFERENCES cavalos(id)
            FOREIGN KEY (proprietario_id) REFERENCES proprietario(id)
        );

        CREATE TABLE IF NOT EXISTS proprietario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            usuario_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
        
        CREATE TABLE IF NOT EXISTS sexo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sexo TEXT NOT NULL
        );
                       
        CREATE TABLE IF NOT EXISTS raca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raca TEXT NOT NULL
        );
                       
        CREATE TABLE IF NOT EXISTS pelagem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pelagem TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recebimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proprietario_id INTEGER,
            cavalo_id INTEGER NOT NULL,
            data TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proprietario_id) REFERENCES proprietario(id),
            FOREIGN KEY (cavalo_id) REFERENCES cavalos(id)
        );

        CREATE TABLE IF NOT EXISTS itens_recebimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recebimento_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            FOREIGN KEY (recebimento_id) REFERENCES recebimentos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        );
                       
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nivel TEXT CHECK(nivel IN ('Administrador', 'Proprietario', 'Funcionario')) NOT NULL        
        );
    ''')

    conn.commit()
    conn.close()

def popular_produtos():
    conn = conexao()
    count = conn.execute('SELECT COUNT(*) FROM produtos').fetchone()[0]
    if count == 0:
        produtos = ['Feno', 'Ração', 'Sal Mineral', 'Aveia']
        for nome in produtos:
            conn.execute('INSERT INTO produtos (nome) VALUES (?)', (nome,))
        conn.commit()
    conn.close()

def popular_sexo():
    conn = conexao()
    count = conn.execute('SELECT COUNT(*) FROM sexo').fetchone()[0]
    if count == 0:
        sexos = ['Macho', 'Fêmea']
        for s in sexos:
            conn.execute('INSERT INTO sexo (sexo) VALUES (?)', (s,))
        conn.commit()
    conn.close()

def popular_raca():
    conn = conexao()
    count = conn.execute('SELECT COUNT(*) FROM raca').fetchone()[0]
    if count == 0:
        racas = ['Quarto de Milha', 'Mangalarga', 'SRD', 'Appaloosa']
        for r in racas:
            conn.execute('INSERT INTO raca (raca) VALUES (?)', (r,))
        conn.commit()
    conn.close()

def popular_pelagem():
    conn = conexao()
    count = conn.execute('SELECT COUNT(*) FROM pelagem').fetchone()[0]
    if count == 0:
        pelagens = ['Tordilho', 'Zaino', 'Castanho', 'Alazão', 'Baio', 'Preto']
        for p in pelagens:
            conn.execute('INSERT INTO pelagem (pelagem) VALUES (?)', (p,))
        conn.commit()
    conn.close()

def popular_todos():
    popular_produtos()
    popular_sexo()
    popular_raca()
    popular_pelagem()