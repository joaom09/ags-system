db_path = 'database/base.db'

from flask import Flask, render_template, url_for, request, redirect
from database import criar_tabelas, popular_todos

app = Flask(__name__)

criar_tabelas()
popular_todos()

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/cavalos')
def cavalos():
    return render_template('listar_cavalos.html')

@app.route('/recebimentos')
def recebimentos():
    # conn = conexao()
    # categoria = conn.execute('SELECT * FROM categorias ORDER BY id').fetchall()
    # conn.close()

    return render_template('recebimentos.html')

@app.route('/novo_cavalo', methods=['GET','POST'])
def novoCavalo():
    # if request.method == 'POST':
    #     nome = request.form['name']
    #     descricao = request.form['description']

    #     conn = conexao()
    #     conn.execute('''
    #         INSERT INTO categorias (nome, descricao) VALUES (?, ?)
    #     ''', (nome, descricao))
    #     conn.commit()
    #     conn.close()
    #     return redirect(url_for('categorias'))
    return render_template('cadastrar_cavalos.html')



if __name__ == '__main__':
    app.run(debug=True, port=5050, host = "0.0.0.0")
