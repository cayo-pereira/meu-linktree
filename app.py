from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import json
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = 'chave-super-secreta'  # Altere isso para algo mais seguro

USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

CONFIG_FILE = 'config.json'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def arquivo_permitido(nome_arquivo):
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def carregar_dados():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_dados(dados):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    dados = carregar_dados()
    return render_template('index.html', dados=dados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logado'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', erro='Credenciais inválidas')
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))

    dados = carregar_dados()

    if request.method == 'POST':
        dados['nome'] = request.form['nome']
        dados['bio'] = request.form['bio']
        dados['instagram'] = request.form['instagram']
        dados['linkedin'] = request.form['linkedin']
        dados['github'] = request.form['github']
        dados['email'] = request.form['email']
        dados['whatsapp'] = request.form['whatsapp']
        dados['curriculo'] = request.form['curriculo']

        # Foto de perfil
        if 'foto_upload' in request.files:
            foto_file = request.files['foto_upload']
            if foto_file and arquivo_permitido(foto_file.filename):
                filename = secure_filename(foto_file.filename)
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto_file.save(caminho)
                dados['foto'] = f"uploads/{filename}"

        # Foto de background
        if 'background_upload' in request.files:
            background_file = request.files['background_upload']
            if background_file and arquivo_permitido(background_file.filename):
                filename = secure_filename(background_file.filename)
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                background_file.save(caminho)
                dados['background'] = f"uploads/{filename}"

        salvar_dados(dados)
        return redirect(url_for('index'))

    return render_template('admin.html', dados=dados)


@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
