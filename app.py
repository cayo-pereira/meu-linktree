from flask import Flask, render_template, request, redirect, session, url_for, abort, jsonify, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from uuid import uuid4
import json
import os
import requests
import re
import logging

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or 'dev-secret-key'

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options=ClientOptions(
        postgrest_client_timeout=10,
        headers={'Prefer': 'return=representation'}
    )
)

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
    try:
        res = supabase.table('usuarios').select('*').eq('id', user_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {str(e)}")
        return None

def create_user(user_data):
    """Cria novo usuário no Supabase"""
    try:
        res = supabase.table('usuarios').insert(user_data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return None

def slug_exists(slug):
    """Verifica se um slug já está em uso"""
    try:
        res = supabase.table('usuarios').select('profile').eq('profile', slug).execute()
        return len(res.data) > 0
    except Exception as e:
        logger.error(f"Erro ao verificar slug: {str(e)}")
        return True

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

# ROTA DE TESTE
@app.route('/test-insert', methods=['GET'])
def test_insert():
    try:
        # Verifica se o usuário está autenticado
        if 'user_id' not in session:
            return jsonify({"error": "Não autenticado"}), 401

        test_user = {
            'id': session['user_id'],  # Usa o ID da sessão
            'nome': 'Teste API Python',
            'profile': 'teste-python',
            'email': 'teste-python@api.com',
            'active': True,
            # ... outros campos obrigatórios
        }

        # Debug: Mostra o usuário que será inserido
        print("Tentando inserir:", test_user)

        # Faz a inserção
        response = supabase.table('usuarios').insert(test_user).execute()
        
        if response.data:
            return jsonify({
                "status": "success",
                "data": response.data
            })
        else:
            return jsonify({
                "status": "error",
                "error": str(response.error),
                "details": str(response)
            }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "session_user": session.get('user_id')
        }), 500

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/<profile>')
def user_page(profile):
    try:
        # Busca os dados do usuário pelo profile (slug)
        res = supabase.table('usuarios').select('*').eq('profile', profile).eq('active', True).execute()
        
        if not res.data:
            logger.warning(f"Perfil não encontrado: {profile}")
            abort(404)
        
        user_data = res.data[0]
        logger.info(f"Dados carregados para {profile}: {user_data}")
        
        # Debug: Verifique os dados antes de renderizar
        print("Dados sendo enviados para o template:", user_data)
        
        return render_template('user_page.html', dados=user_data)
    
    except Exception as e:
        logger.error(f"Erro ao carregar perfil {profile}: {str(e)}")
        abort(500)

# Autenticação
@app.route('/login/google')
def login_google():
    """Inicia o fluxo de login com Google"""
    try:
        redirect_url = url_for('callback_handler', _external=True)
        auth_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to={redirect_url}"
        logger.info(f"Redirecionando para: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Erro no login Google: {str(e)}")
        return redirect(url_for('index'))

@app.route('/callback_handler')
def callback_handler():
    """Rota que renderiza a página de processamento do token"""
    return render_template('callback.html')

@app.route('/callback', methods=['GET', 'POST'])
def callback():
    """Rota de callback para processar o token de autenticação"""
    try:
        # Obter token do request
        if request.method == 'POST':
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            access_token = request.json.get('access_token')
        else:
            access_token = request.args.get('access_token')
        
        if not access_token:
            logger.error("Token não encontrado na requisição")
            return jsonify({"error": "Token não fornecido"}), 400
        
        logger.info(f"Token recebido (início): {access_token[:15]}...")
        
        # Obter dados do usuário
        user_resp = supabase.auth.get_user(access_token)
        if not user_resp.user:
            logger.error("Falha ao obter usuário do token")
            return jsonify({"error": "Autenticação falhou"}), 401
            
        user = user_resp.user
        logger.info(f"Usuário autenticado: {user.email} (ID: {user.id})")
        
        # Verificar/Criar usuário no banco de dados
        user_data = get_user_by_id(user.id)
        
        if not user_data:
            logger.info("Criando novo usuário...")
            slug = generate_unique_slug(user.user_metadata.get('full_name', user.email.split('@')[0]))
            
            new_user = {
                'id': user.id,
                'nome': user.user_metadata.get('full_name', user.email),
                'profile': slug,
                'email': user.email,
                'foto': user.user_metadata.get('avatar_url', ''),
                'active': True,
                'instagram': '',
                'linkedin': '',
                'github': '',
                'whatsapp': '',
                'curriculo': '',
                'bio': 'Olá! Esta é minha página pessoal.'
            }
            
            created_user = create_user(new_user)
            if not created_user:
                raise Exception("Falha ao criar usuário no banco de dados")
                
            user_data = created_user
            logger.info(f"Novo usuário criado: {user_data['profile']}")
        
        # Configurar sessão
        session['user_id'] = user.id
        session['access_token'] = access_token
        session['profile'] = user_data['profile']  # Adiciona o profile na sessão
        session['logado'] = True
        
        logger.info(f"Sessão configurada para: {user_data['profile']}")
        
        # Retornar URL para redirecionamento
        return jsonify({
            "redirect": url_for('admin_panel', username=user_data['profile']),
            "profile": user_data['profile']
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no callback: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno no servidor"}), 500

# Painel administrativo
@app.route('/admin/<username>', methods=['GET', 'POST'])
def admin_panel(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        # 1. Busca dados atuais (com tratamento de erro reforçado)
        res = supabase.table('usuarios').select('*').eq('id', session['user_id']).execute()
        if not res.data:
            logger.error(f"Usuário não encontrado no banco: {session['user_id']}")
            abort(404)
        
        user_data = res.data[0]
        
        if user_data['profile'] != username:
            abort(403)

        if request.method == 'POST':
            # 2. Prepara dados com fallback para valores existentes
            update_data = {
                'nome': request.form.get('nome', user_data['nome']),
                'profile': request.form.get('profile', user_data['profile']),
                'bio': request.form.get('bio', user_data['bio']),
                'instagram': request.form.get('instagram', user_data['instagram']),
                'linkedin': request.form.get('linkedin', user_data['linkedin']),
                'github': request.form.get('github', user_data['github']),
                'whatsapp': request.form.get('whatsapp', user_data['whatsapp']),
                'curriculo': request.form.get('curriculo', user_data['curriculo']),
                'email': request.form.get('email', user_data['email']),
                'updated_at': 'now()'  # Campo especial do Supabase
            }

            # 3. Processamento de arquivos (com verificação reforçada)
            for file_field in ['foto_upload', 'background_upload']:
                if file_field in request.files:
                    file = request.files[file_field]
                    if file and arquivo_permitido(file.filename):
                        filename = f"{session['user_id']}_{secure_filename(file.filename)}"
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        update_data[file_field.split('_')[0]] = f"uploads/{filename}"

            # 4. DEBUG Avançado (registra TUDO)
            logger.info(f"Update payload: {update_data}")
            print("Dados preparados para update:", update_data)

            # 5. Executa o UPDATE com tratamento especial
            try:
                response = supabase.table('usuarios').update(update_data).eq('id', session['user_id']).execute()
                
                # Verificação PROFUNDA da resposta
                if hasattr(response, 'data') and response.data:
                    logger.info(f"Update bem-sucedido! Resposta: {response.data}")
                    flash("✅ Dados salvos com sucesso!", "success")
                    
                    # Atualiza cache imediatamente
                    new_profile = update_data.get('profile')
                    if new_profile and new_profile != username:
                        session['profile'] = new_profile
                        return redirect(url_for('admin_panel', username=new_profile))
                    
                    # Recarrega dados atualizados
                    res = supabase.table('usuarios').select('*').eq('id', session['user_id']).execute()
                    user_data = res.data[0]
                else:
                    logger.error(f"Resposta inesperada: {response}")
                    flash("⚠️ Dados foram salvos, mas não houve confirmação", "warning")

            except Exception as update_error:
                logger.error(f"ERRO no update: {str(update_error)}")
                flash("❌ Falha crítica ao salvar - contate o suporte", "error")

    except Exception as e:
        logger.error(f"ERRO GERAL: {str(e)}", exc_info=True)
        flash("⚡ Erro inesperado - tente novamente", "danger")

    return render_template('admin.html', dados=user_data)

# Logout
@app.route('/logout')
def logout():
    """Encerra a sessão do usuário"""
    session.clear()
    return redirect(url_for('index'))

# Rota de debug
@app.route('/debug/session')
def debug_session():
    """Rota para debug da sessão (remover em produção)"""
    return jsonify(dict(session))

if __name__ == '__main__':
    app.run(debug=True)