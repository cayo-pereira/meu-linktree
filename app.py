from flask import Flask, render_template, request, redirect, session, url_for, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client, Client
from uuid import uuid4
import json
import os
import requests
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or 'dev-secret-key'

# Configurações Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurações do app
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper functions
def arquivo_permitido(nome_arquivo):
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_slug(slug):
    """Verifica se o slug é válido (apenas letras, números e hífens)"""
    return bool(re.match(r'^[a-z0-9-]+$', slug))

def get_user_by_id(user_id):
    """Busca usuário no Supabase pelo ID"""
    res = supabase.table('usuarios').select('*').eq('id', user_id).execute()
    return res.data[0] if res.data else None

def create_user(user_data):
    """Cria novo usuário no Supabase"""
    res = supabase.table('usuarios').insert(user_data).execute()
    return res.data[0] if res.data else None

def slug_exists(slug):
    """Verifica se um slug já está em uso"""
    res = supabase.table('usuarios').select('profile').eq('profile', slug).execute()
    return len(res.data) > 0

def generate_unique_slug(base_slug):
    """Gera um slug único baseado no nome"""
    slug = base_slug.lower().replace(' ', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    if not slug_exists(slug):
        return slug
    
    counter = 1
    while True:
        new_slug = f"{slug}-{counter}"
        if not slug_exists(new_slug):
            return new_slug
        counter += 1

# Rotas públicas

@app.route('/callback_handler')
def callback_handler():
    """Rota que renderiza a página de processamento do token"""
    return render_template('callback.html')

@app.route('/')
def index():
    # Página inicial pode ser um landing page ou redirecionar para um usuário padrão
    return render_template('index.html')

@app.route('/<profile>')
def user_page(profile):
    # Busca os dados do usuário pelo profile (slug)
    res = supabase.table('usuarios').select('*').eq('profile', profile).eq('active', True).execute()
    
    if not res.data:
        abort(404)
    
    user_data = res.data[0]
    return render_template('user_page.html', dados=user_data)

# Autenticação
@app.route('/login/google')
def login_google():
    redirect_url = url_for('callback_handler', _external=True)
    return redirect(f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to={redirect_url}")

@app.route('/callback')
def callback():
    # O token será enviado via POST pelo frontend
    if request.method == 'POST':
        access_token = request.json.get('access_token')
    else:
        # Fallback para desenvolvimento
        access_token = request.args.get('access_token')
    
    if not access_token:
        return "Token de acesso não encontrado", 400
    
    try:
        # Obtém os dados do usuário
        user_resp = supabase.auth.get_user(access_token)
        user = user_resp.user
        
        # Verifica se o usuário já existe
        res = supabase.table('usuarios').select('*').eq('id', user.id).execute()
        user_data = res.data[0] if res.data else None
        
        if not user_data:
            # Cria novo usuário
            slug = generate_unique_slug(user.user_metadata.get('full_name', user.email.split('@')[0]))
            new_user = {
                'id': user.id,
                'nome': user.user_metadata.get('full_name', user.email),
                'profile': slug,
                'email': user.email,
                'foto': user.user_metadata.get('avatar_url', ''),
                'active': True
            }
            supabase.table('usuarios').insert(new_user).execute()
            user_data = new_user
        
        # Configura a sessão
        session['user_id'] = user.id
        session['access_token'] = access_token
        
        return redirect(url_for('admin_panel', username=user_data['profile']))
    
    except Exception as e:
        app.logger.error(f"Erro na autenticação: {str(e)}")
        return "Falha na autenticação", 400

# Painel administrativo
@app.route('/admin/<username>')
def admin_panel(username):
    # Verifica se o usuário está logado e tem permissão
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    if not user or user['profile'] != username:
        abort(403)  # Forbidden
    
    return render_template('admin.html', dados=user)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)