from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client, Client
import json
import os
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = 'chave-super-secreta'  # Troque por uma chave mais forte em produção

# Configurações Supabase
SUPABASE_URL = "https://loqxzvelrlpabcnocbyv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvcXh6dmVscmxwYWJjbm9jYnl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc0MTYzMTcsImV4cCI6MjA2Mjk5MjMxN30.cOeb8vnFlNYvrBPGjLB-Yyrj48zXSofZNvywdtqvk6w"
SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1/authorize"
REDIRECT_URL = "https://cpages.onrender.com/callback"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Variáveis .env
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError("ADMIN_USERNAME e ADMIN_PASSWORD devem estar definidos no .env")

CONFIG_FILE = 'config.json'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
    if not session.get('logado') and not session.get('access_token'):
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

        # Imagem de fundo
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
    session.clear()
    return redirect(url_for('index'))


@app.route('/login/google')
def login_google():
    url_login = f"{SUPABASE_AUTH_URL}?provider=google&redirect_uri={REDIRECT_URL}"
    return redirect(url_login)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Erro: Código não recebido", 400

    token_url = f"{SUPABASE_URL}/auth/v1/token"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("SUPABASE_CLIENT_ID"),
        "client_secret": os.getenv("SUPABASE_CLIENT_SECRET"),
        "code": code,
        "redirect_uri": REDIRECT_URL
    }

    resp = requests.post(token_url, headers=headers, data=data)
    if resp.status_code != 200:
        return f"Erro ao autenticar: {resp.text}", 400

    token_data = resp.json()
    access_token = token_data.get("access_token")
    session['access_token'] = access_token

    user_resp = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers={"Authorization": f"Bearer {access_token}"})
    if user_resp.status_code != 200:
        return "Erro ao obter dados do usuário", 400

    user_data = user_resp.json()
    session['user_id'] = user_data['id']
    session['email'] = user_data['email']

    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)
