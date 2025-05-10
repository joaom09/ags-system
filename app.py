db_path = 'database/base.db'

import sqlite3
from flask import Flask, render_template, url_for, request, redirect
from database import criar_tabelas, popular_todos,conexao
from datetime import datetime

app = Flask(__name__)

criar_tabelas()
popular_todos()

@app.route('/')
def home():
    conn = conexao()
    recebimentos = conn.execute('''
        SELECT
            r.id AS recebimento_id,
            c.nome AS nome_cavalo,
            p.nome AS nome_proprietario,
            r.data,
            GROUP_CONCAT(prod.nome || ' (' || ir.quantidade || ')', '<br>') AS itens
        FROM recebimentos r
        JOIN cavalos c ON r.cavalo_id = c.id
        JOIN proprietario p ON r.proprietario_id = p.id
        LEFT JOIN itens_recebimento ir ON r.id = ir.recebimento_id
        LEFT JOIN produtos prod ON ir.produto_id = prod.id
        GROUP BY r.id, c.nome, p.nome, r.data
        ORDER BY r.data DESC
        LIMIT 5
    ''').fetchall()
    conn.close()

    formatted_recebimentos_data = []
    for recebimento in recebimentos:
        recebimento_dict = dict(recebimento)
        recebimento_dict['data'] = datetime.strptime(recebimento_dict['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        formatted_recebimentos_data.append(recebimento_dict)
    
    return render_template('index.html', recebimentos=recebimentos)

@app.route('/cavalos')
def cavalos():
    conn = conexao()
    cavalos = conn.execute('''
        SELECT 
            c.nome AS nome_cavalo,
            p.nome AS nome_proprietario,
            r.raca AS raca,
            s.sexo AS sexo,
            c.idade,
            pl.pelagem AS pelagem
        FROM cavalos c
        JOIN proprietario p ON c.proprietario_id = p.id
        JOIN raca r ON c.raca_id = r.id
        JOIN sexo s ON c.sexo_id = s.id
        JOIN pelagem pl ON c.pelagem_id = pl.id
        ORDER BY c.nome
    ''').fetchall()
    conn.close()
    return render_template('cavalos.html', cavalos=cavalos)
    

@app.route('/proprietarios')
def proprietarios():
    conn = conexao()
    proprietarios = conn.execute('SELECT * FROM proprietario ORDER BY nome').fetchall()
    conn.close()
    return render_template('proprietarios.html', proprietarios=proprietarios)

@app.route('/recebimentos')
def recebimentos():
    conn = conexao()
    recebimentos = conn.execute('''
        SELECT
            r.id AS recebimento_id,
            c.nome AS nome_cavalo,
            p.nome AS nome_proprietario,
            r.data,
            GROUP_CONCAT(prod.nome || ' (' || ir.quantidade || ')', '<br>') AS itens
        FROM recebimentos r
        JOIN cavalos c ON r.cavalo_id = c.id
        JOIN proprietario p ON r.proprietario_id = p.id
        LEFT JOIN itens_recebimento ir ON r.id = ir.recebimento_id
        LEFT JOIN produtos prod ON ir.produto_id = prod.id
        GROUP BY r.id, c.nome, p.nome, r.data
        ORDER BY r.data DESC
    ''').fetchall()
    conn.close()

    formatted_recebimentos_data = []
    for recebimento in recebimentos:
        recebimento_dict = dict(recebimento)
        recebimento_dict['data'] = datetime.strptime(recebimento_dict['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        formatted_recebimentos_data.append(recebimento_dict)
    return render_template('recebimentos.html', recebimentos=recebimentos)

@app.route('/novo_cavalo', methods=['GET','POST'])
def novoCavalo():
    conn = conexao()
    if request.method == 'POST':
        nome = request.form['name']
        proprietario_id = request.form['proprietario_id']
        sexo_id = request.form['sexo_id']
        raca_id = request.form['raca_id']
        idade = request.form['idade']
        pelagem_id = request.form['pelagem_id']
        
        conn.execute('''
            INSERT INTO cavalos (nome, proprietario_id, sexo_id, raca_id, idade, pelagem_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, proprietario_id, sexo_id, raca_id, idade, pelagem_id))
        conn.commit()
        conn.close()
        return redirect('/cavalos')

    proprietarios = conn.execute('SELECT * FROM proprietario').fetchall()
    sexos = conn.execute('SELECT * FROM sexo').fetchall()
    racas = conn.execute('SELECT * FROM raca').fetchall()
    pelagens = conn.execute('SELECT * FROM pelagem').fetchall()
    conn.close()

    return render_template('cadastrar_cavalos.html', proprietarios = proprietarios, sexos=sexos, racas=racas, pelagens=pelagens)

@app.route('/novo_proprietario', methods=['GET','POST'])
def novoProprietario():
    conn = conexao()
    if request.method == 'POST':
        nome = request.form['name']
        telefone = request.form['number']
        
        conn.execute('''
            INSERT INTO proprietario (nome, telefone)
            VALUES (?, ?)
        ''', (nome, telefone))
        conn.commit()
        conn.close()
        return redirect('/proprietarios')
    return render_template('cadastrar_proprietario.html')

@app.route('/novo_recebimento', methods=['GET', 'POST'])
def novoRecebimento():
    conn = conexao()
    try:
        if request.method == 'POST':
            proprietario_id = request.form['proprietario_id']
            cavalo_id = request.form['cavalo_id']
            data_recebimento = request.form['data']
            produto_ids = request.form.getlist('produto_id[]')
            quantidades = request.form.getlist('quantidade[]')

            # Inserir na tabela de recebimentos
            conn.execute('''
                INSERT INTO recebimentos (proprietario_id, cavalo_id, data)
                VALUES (?, ?, ?)
            ''', (proprietario_id, cavalo_id, data_recebimento))
            recebimento_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Inserir múltiplos itens de recebimento
            for i in range(len(produto_ids)):
                produto_id = produto_ids[i]
                quantidade = quantidades[i]

                conn.execute('''
                    INSERT INTO itens_recebimento (recebimento_id, produto_id, quantidade)
                    VALUES (?, ?, ?)
                ''', (recebimento_id, produto_id, quantidade))

            conn.commit()
            conn.close()
            return redirect('/recebimentos')

        proprietarios = conn.execute('SELECT * FROM proprietario').fetchall()
        cavalos = conn.execute('SELECT * FROM cavalos').fetchall()
        produtos = conn.execute('SELECT * FROM produtos').fetchall()
        conn.close()
        return render_template('cadastrar_recebimentos.html', proprietarios=proprietarios, cavalos=cavalos, produtos=produtos)
    
    except sqlite3.Error as e:
        print(f"Erro ao inserir dados: {e}")
        conn.rollback()
        conn.close()
        return "Erro ao cadastrar recebimento. Por favor, verifique os dados e tente novamente."


if __name__ == '__main__':
    app.run(debug=True, port=5050, host = "0.0.0.0")
