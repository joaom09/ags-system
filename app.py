db_path = 'database/base.db'

import sqlite3
import os
from werkzeug.utils import secure_filename
from flask import Flask, flash, render_template, url_for, request, redirect, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from database import criar_tabelas, popular_todos,conexao
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

criar_tabelas()
popular_todos()

login_manager = LoginManager(app)
login_manager.login_view = 'login'


app.secret_key = 'secret_key'

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

class User(UserMixin):
    def __init__(self, id, nome, email, senha):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha

@login_manager.user_loader
def load_user(user_id):
    conn = conexao()
    row = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if row:
        return User(row['id'], row['nome'], row['email'], row['senha'])
    return None


@app.route('/')
# @login_required
def home():
    conn = conexao()
    recebimentos = conn.execute('''
        SELECT
            r.id AS recebimento_id,
            c.nome AS nome_cavalo,
            c.imagem AS imagem,
            p.nome AS nome_proprietario,
            r.data,
            GROUP_CONCAT(prod.nome || ' (' || ir.quantidade || ')', '<br>') AS itens
        FROM recebimentos r
        JOIN cavalos c ON r.cavalo_id = c.id
        JOIN proprietario p ON r.proprietario_id = p.id
        LEFT JOIN itens_recebimento ir ON r.id = ir.recebimento_id
        LEFT JOIN produtos prod ON ir.produto_id = prod.id
        GROUP BY r.id, c.nome, c.imagem, p.nome, r.data
        ORDER BY r.data DESC
        LIMIT 5
    ''').fetchall()
    conn.close()

    formatted_recebimentos_data = []
    for recebimento in recebimentos:
        recebimento_dict = dict(recebimento)
        recebimento_dict['data'] = datetime.strptime(recebimento_dict['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        formatted_recebimentos_data.append(recebimento_dict)
    
    return render_template('index.html', recebimentos=formatted_recebimentos_data)

@app.route('/cavalos')
def cavalos():
    conn = conexao()
    cavalos = conn.execute('''
        SELECT
            c.id, 
            c.nome AS nome_cavalo,
            p.nome AS nome_proprietario,
            r.raca AS raca,
            s.sexo AS sexo,
            c.idade,
            pl.pelagem AS pelagem,
            c.imagem
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

@app.route('/ocorrencias')
def ocorrencias():
    conn = conexao()
    ocorrencias = conn.execute('''
        SELECT
            o.id AS ocorrencia_id,
            c.nome AS nome_cavalo,
            p.nome AS nome_proprietario,
            o.tipo,
            o.data
        FROM ocorrencias o
        JOIN cavalos c ON o.cavalo_id = c.id
        JOIN proprietario p ON o.proprietario_id = p.id
        ORDER BY o.data DESC
    ''').fetchall()
    conn.close()

    formatted_ocorrencias_data = []
    for ocorrencia in ocorrencias:
        ocorrencia_dict = dict(ocorrencia)
        ocorrencia_dict['data'] = datetime.strptime(ocorrencia_dict['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        formatted_ocorrencias_data.append(ocorrencia_dict)
    return render_template('ocorrencias.html', ocorrencias=formatted_ocorrencias_data)

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
        
        imagem = request.files['imagem']
        imagem_path = None

        if imagem and imagem.filename != '':
            filename = secure_filename(imagem.filename)
            upload_folder = os.path.join(app.root_path, 'static/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            imagem.save(os.path.join(upload_folder, filename))
            imagem_path = filename

        conn.execute('''
            INSERT INTO cavalos (nome, proprietario_id, sexo_id, raca_id, idade, pelagem_id, imagem)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, proprietario_id, sexo_id, raca_id, idade, pelagem_id, imagem_path))
        conn.commit()
        conn.close()
        return redirect('/cavalos')

    proprietarios = conn.execute('SELECT * FROM proprietario').fetchall()
    sexos = conn.execute('SELECT * FROM sexo').fetchall()
    racas = conn.execute('SELECT * FROM raca').fetchall()
    pelagens = conn.execute('SELECT * FROM pelagem').fetchall()
    conn.close()

    return render_template('cadastrar_cavalos.html', proprietarios = proprietarios, sexos=sexos, racas=racas, pelagens=pelagens)

@app.route('/cavalo/<int:id>/editar', methods=['GET', 'POST'])
def editarCavalo(id):
    conn = conexao()
    if request.method == 'POST':
        nome = request.form['name']
        proprietario_id = request.form['proprietario_id']
        sexo_id = request.form['sexo_id']
        raca_id = request.form['raca_id']
        idade = request.form['idade']
        pelagem_id = request.form['pelagem_id']

        conn.execute('''
            UPDATE cavalos SET nome=?, proprietario_id=?, sexo_id=?, raca_id=?, idade=?, pelagem_id=?
            WHERE id=?
        ''', (nome, proprietario_id, sexo_id, raca_id, idade, pelagem_id, id))
        conn.commit()
        conn.close()
        return redirect('/cavalos')

    cavalo = conn.execute('SELECT * FROM cavalos WHERE id=?', (id,)).fetchone()
    proprietarios = conn.execute('SELECT * FROM proprietario').fetchall()
    sexos = conn.execute('SELECT * FROM sexo').fetchall()
    racas = conn.execute('SELECT * FROM raca').fetchall()
    pelagens = conn.execute('SELECT * FROM pelagem').fetchall()
    conn.close()
    return render_template('editar_cavalo.html', cavalo=cavalo, proprietarios=proprietarios, sexos=sexos, racas=racas, pelagens=pelagens)

@app.route('/cavalo/<int:id>/excluir', methods=['POST'])
def excluirCavalo(id):
    conn = conexao()
    conn.execute('DELETE FROM cavalos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/cavalos')



@app.route('/cavalo/<int:id>')
def detalhesCavalo(id):
    conn = conexao()
    cavalo = conn.execute('''
        SELECT c.*, s.sexo, r.raca, p.pelagem, pr.nome AS nome_proprietario
        FROM cavalos c
        LEFT JOIN sexo s ON c.sexo_id = s.id
        LEFT JOIN raca r ON c.raca_id = r.id
        LEFT JOIN pelagem p ON c.pelagem_id = p.id
        LEFT JOIN proprietario pr ON c.proprietario_id = pr.id
        WHERE c.id = ?
    ''', (id,)).fetchone()

    ocorrencias = conn.execute('''
        SELECT ocorrencias.*, 
        cavalos.nome AS nome_cavalo, 
        proprietario.nome AS nome_proprietario
        FROM ocorrencias
        JOIN cavalos ON ocorrencias.cavalo_id = cavalos.id
        JOIN proprietario ON ocorrencias.proprietario_id = proprietario.id
        WHERE ocorrencias.cavalo_id = ?
        ORDER BY ocorrencias.data DESC
    ''', (id,)).fetchall()

    conn.close()

    formatted_ocorrencias_data = []
    for ocorrencia in ocorrencias:
        ocorrencia_dict = dict(ocorrencia)
        ocorrencia_dict['data'] = datetime.strptime(ocorrencia_dict['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        formatted_ocorrencias_data.append(ocorrencia_dict)
    return render_template('detalhes_cavalos.html', cavalo=cavalo, ocorrencias=formatted_ocorrencias_data)


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

@app.route('/proprietario/<int:id>/editar', methods=['GET', 'POST'])
def editarProprietario(id):
    conn = conexao()
    if request.method == 'POST':
        nome = request.form['name']
        telefone = request.form['number']
        conn.execute('UPDATE proprietario SET nome=?, telefone=? WHERE id=?', (nome, telefone, id))
        conn.commit()
        conn.close()
        return redirect('/proprietarios')

    proprietario = conn.execute('SELECT * FROM proprietario WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('editar_proprietario.html', proprietario=proprietario)

@app.route('/proprietario/<int:id>/excluir', methods=['POST'])
def excluirProprietario(id):
    conn = conexao()
    conn.execute('DELETE FROM proprietario WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/proprietarios')



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
    
@app.route('/editar_recebimento/<int:id>', methods=['GET', 'POST'])
def editarRecebimento(id):
    conn = conexao()
    try:
        if request.method == 'POST':
            data = request.form['data']
            produto_ids = request.form.getlist('produto_id[]')
            quantidades = request.form.getlist('quantidade[]')

            # Atualizar data
            conn.execute("UPDATE recebimentos SET data = ? WHERE id = ?", (data, id))

            # Apagar itens antigos
            conn.execute("DELETE FROM itens_recebimento WHERE recebimento_id = ?", (id,))

            # Inserir novos itens
            for i in range(len(produto_ids)):
                produto_id = produto_ids[i]
                quantidade = quantidades[i]
                conn.execute('''
                    INSERT INTO itens_recebimento (recebimento_id, produto_id, quantidade)
                    VALUES (?, ?, ?)
                ''', (id, produto_id, quantidade))

            conn.commit()
            conn.close()
            return redirect('/recebimentos')

        # GET: buscar dados para exibir
        recebimento = conn.execute('''
            SELECT r.id, r.data, c.nome AS cavalo_nome, p.nome AS proprietario_nome
            FROM recebimentos r
            JOIN cavalos c ON r.cavalo_id = c.id
            JOIN proprietario p ON r.proprietario_id = p.id
            WHERE r.id = ?
        ''', (id,)).fetchone()

        produtos_recebidos = conn.execute('''
            SELECT ir.produto_id, ir.quantidade, pr.nome
            FROM itens_recebimento ir
            JOIN produtos pr ON ir.produto_id = pr.id
            WHERE ir.recebimento_id = ?
        ''', (id,)).fetchall()

        produtos = conn.execute('SELECT * FROM produtos').fetchall()
        conn.close()
        return render_template(
            'editar_recebimento.html',
            recebimento=recebimento,
            produtos_recebidos=produtos_recebidos,
            produtos=produtos
        )
    except sqlite3.Error as e:
        print(f"Erro ao editar recebimento: {e}")
        conn.rollback()
        conn.close()
        return "Erro ao editar recebimento."


@app.route('/recebimento/<int:id>/excluir', methods=['POST'])
def excluirRecebimento(id):
    conn = conexao()
    conn.execute('DELETE FROM itens_recebimento WHERE recebimento_id=?', (id,))
    conn.execute('DELETE FROM recebimentos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/recebimentos')



@app.route('/nova_ocorrencia', methods=['GET', 'POST'])
def novaOcorrencia():
    return novaOcorrenciaInterna()

@app.route('/nova_ocorrencia/<int:cavalo_id>', methods=['GET', 'POST'])
def novaOcorrenciaComCavalo(cavalo_id):
    return novaOcorrenciaInterna(cavalo_id)

def novaOcorrenciaInterna(cavalo_id=None):
    conn = conexao()
    try:
        if request.method == 'POST':
            cavalo_id_form = request.form['cavalo_id']
            data = request.form['data']
            tipo = request.form['tipo']
            descricao = request.form['descricao']

            proprietario_row = conn.execute('SELECT proprietario_id FROM cavalos WHERE id = ?', (cavalo_id_form,)).fetchone()

            proprietario_id = proprietario_row['proprietario_id'] if proprietario_row else None

            if not proprietario_id:
                return "Proprietário não encontrado para o cavalo selecionado."

            conn.execute('''
                INSERT INTO ocorrencias (cavalo_id, proprietario_id, tipo, descricao, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (cavalo_id_form, proprietario_id, tipo, descricao, data))

            conn.commit()
            conn.close()
            return redirect('/ocorrencias')

        # Carrega cavalos e proprietários para o formulário
        cavalos = conn.execute('SELECT * FROM cavalos').fetchall()
        proprietarios = conn.execute('SELECT * FROM proprietario').fetchall()

        cavalo_selecionado = None
        if cavalo_id:
            cavalo_selecionado = conn.execute('SELECT * FROM cavalos WHERE id = ?', (cavalo_id,)).fetchone()

        conn.close()
        return render_template(
            'cadastrar_ocorrencias.html',
            proprietarios=proprietarios,
            cavalos=cavalos,
            cavalo_selecionado=cavalo_selecionado
        )

    except sqlite3.Error as e:
        print(f"Erro ao inserir dados: {e}")
        conn.rollback()
        conn.close()
        return "Erro ao cadastrar ocorrência. Por favor, verifique os dados e tente novamente."
    
@app.route('/ocorrencia/<int:id>/editar', methods=['GET', 'POST'])
def editarOcorrencia(id):
    conn = conexao()

    if request.method == 'POST':
        data = request.form['data']
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        cavalo_id = request.form.get('cavalo_id')  # se quiser permitir edição do cavalo
        conn.execute('''
            UPDATE ocorrencias SET data=?, tipo=?, descricao=? WHERE id=?
        ''', (data, tipo, descricao, id))
        conn.commit()
        conn.close()
        return redirect('/ocorrencias')

    ocorrencia = conn.execute('SELECT * FROM ocorrencias WHERE id=?', (id,)).fetchone()
    cavalos = conn.execute('SELECT * FROM cavalos').fetchall()
    cavalo_selecionado = conn.execute('SELECT * FROM cavalos WHERE id=?', (ocorrencia['cavalo_id'],)).fetchone()

    conn.close()
    return render_template('editar_ocorrencia.html', ocorrencia=ocorrencia, cavalos=cavalos, cavalo_selecionado=cavalo_selecionado)


@app.route('/ocorrencia/<int:id>/excluir', methods=['POST'])
def excluirOcorrencia(id):
    conn = conexao()
    conn.execute('DELETE FROM ocorrencias WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/ocorrencias')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = conexao()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_nivel'] = usuario['nivel']
            return redirect(url_for('home'))
        else:
            flash('Email ou senha inválidos', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form['email']
        conn = conexao()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()

        if usuario:
            flash('Instruções para redefinir sua senha foram enviadas para o e-mail.', 'success')
            # Aqui você pode gerar token e enviar e-mail (ou só mostrar uma próxima tela)
        else:
            flash('E-mail não encontrado.', 'danger')

    return render_template('esqueci_senha.html')



@app.route('/usuarios')
def usuarios():
    conn = conexao()
    usuarios = conn.execute('SELECT * FROM usuarios ORDER BY nome').fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/novo_usuario', methods=['GET', 'POST'])
def novoUsuario():
    conn = conexao()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        nivel = request.form['nivel']

        # Criptografar senha antes de salvar no banco
        senha_hash = generate_password_hash(senha)

        conn.execute('''
            INSERT INTO usuarios (nome, email, senha, nivel)
            VALUES (?, ?, ?, ?)
        ''', (nome, email, senha_hash, nivel))
        conn.commit()
        conn.close()
        return redirect(url_for('usuarios'))

    conn.close()
    return render_template('cadastrar_usuario.html')


@app.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
def editarUsuario(id):
    conn = conexao()

    if request.method == 'POST':
        nome = request.form['name']
        email = request.form['number']
        nivel = request.form['nivel']

        conn.execute('''
            UPDATE usuarios SET nome=?, email=?, nivel=? WHERE id=?
        ''', (nome, email, nivel, id))

        conn.commit()
        conn.close()
        return redirect(url_for('listarUsuarios'))

    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('editar_usuario.html', usuario=usuario)




@app.route('/usuario/<int:id>/excluir', methods=['POST'])
def excluirUsuario(id):
    conn = conexao()
    conn.execute('DELETE FROM usuarios WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('usuarios'))


if __name__ == '__main__':
    app.run(debug=True, port=5050, host = "0.0.0.0")
