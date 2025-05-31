from flask import Flask, render_template, request, redirect, session, url_for, abort, jsonify, flash, make_response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions # Ensure this is imported
from uuid import uuid4
import json
import os
# import requests # Not used, can be removed
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

# Configuração otimizada do cliente Supabase
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options=ClientOptions( # Ensure ClientOptions is used correctly
        postgrest_client_timeout=10,
        storage_client_timeout=10, # Added for consistency if you use storage heavily
        headers={ # This header might be default, but good to be explicit
            'Prefer': 'return=representation',
        }
    )
)

# Configurações do app
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- VALORES PADRÃO PARA FONTES E CORES ---
DEFAULT_FONT = "Inter, sans-serif"
DEFAULT_TEXT_COLOR_PAGE = "#333333"
DEFAULT_BIO_COLOR_PAGE = "#555555"
DEFAULT_TEXT_COLOR_CARD = "#FFFFFF"
DEFAULT_TITLE_COLOR_CARD = "#EEEEEE"
DEFAULT_REG_COLOR_CARD = "#BBBBBB"
DEFAULT_CARD_BG_COLOR = "#4361ee"
DEFAULT_CARD_LINK_TEXT_COLOR = "#FFFFFF" # NOVO: Cor padrão para texto dos links do cartão
# --- FIM VALORES PADRÃO ---

def upload_to_supabase(file, user_id, field_type):
    try:
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        unique_filename = f"{user_id}_{field_type}_{uuid4().hex[:8]}{file_ext}"
        
        file.seek(0)
        file_bytes = file.read()

        response = supabase.storage.from_("usuarios").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": file.content_type, "upsert": "true"} # x-upsert is often just upsert
        )

        public_url = supabase.storage.from_("usuarios").get_public_url(unique_filename)
        return public_url
            
    except Exception as e:
        if "Duplicate" in str(e) or "The resource already exists" in str(e): # Adapt based on actual error messages
             logger.warning(f"Arquivo {unique_filename} já existe. Tentando obter URL pública. Erro: {str(e)}")
             try:
                public_url = supabase.storage.from_("usuarios").get_public_url(unique_filename)
                return public_url
             except Exception as e_url:
                logger.error(f"Erro ao obter URL pública de arquivo existente ({field_type}): {str(e_url)}", exc_info=True)
                return None
        logger.error(f"EXCEÇÃO NO UPLOAD ({field_type}) para o arquivo {secure_filename(file.filename)} como {unique_filename}: {str(e)}", exc_info=True)
        return None

def arquivo_permitido(nome_arquivo):
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_slug(slug):
    return bool(re.match(r'^[a-z0-9-]+$', slug))

def get_user_by_id(user_id):
    try:
        res = supabase.table('usuarios').select('*').eq('id', user_id).limit(1).single().execute()
        return res.data if res.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar usuário por ID ({user_id}): {str(e)}")
        return None

def slug_exists(slug, current_user_id=None):
    try:
        query = supabase.table('usuarios').select('id').eq('profile', slug)
        if current_user_id:
            query = query.neq('id', current_user_id)
        res = query.execute()
        return len(res.data) > 0
    except Exception as e:
        logger.error(f"Erro ao verificar slug '{slug}': {str(e)}")
        return True

def generate_unique_slug(base_slug, user_id=None):
    slug = base_slug.lower().replace(' ', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    if not slug:
        slug = f"user-{uuid4().hex[:6]}"

    if not slug_exists(slug, user_id):
        return slug
    
    counter = 1
    while True:
        new_slug = f"{slug}-{counter}"
        if not slug_exists(new_slug, user_id):
            return new_slug
        counter += 1

@app.template_filter('style_safe')
def style_safe_filter(value):
    return value


@app.route('/delete_page', methods=['POST'])
def delete_page():
    if 'user_id' not in session or 'access_token' not in session:
        flash("❌ Sessão inválida. Por favor, faça login novamente.", "error")
        return redirect(url_for('login_google'))
    
    try:
        user_id = session['user_id']
        supabase.auth.set_session(session['access_token'], session['refresh_token'])

        user_data = get_user_by_id(user_id)
        if user_data:
            files_to_delete = []
            if user_data.get('foto') and supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['foto'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['foto'].split('/')[-1])
            if user_data.get('background') and supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['background'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['background'].split('/')[-1])
            if user_data.get('card_background_type') == 'image' and user_data.get('card_background_value') and \
               supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['card_background_value'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['card_background_value'].split('/')[-1])
            
            if files_to_delete:
                try:
                    supabase.storage.from_("usuarios").remove(files_to_delete)
                    logger.info(f"Arquivos de storage removidos para o usuário {user_id}: {files_to_delete}")
                except Exception as e_storage:
                    logger.error(f"Erro ao remover arquivos do storage para usuário {user_id}: {str(e_storage)}")
        
        response = supabase.table('usuarios').delete().eq('id', user_id).execute()
        logger.info(f"Usuário {user_id} deletado da tabela 'usuarios'. Resposta: {len(response.data)} registros afetados.")
        
        try:
            supabase_admin_client = create_client(SUPABASE_URL, os.getenv("SUPABASE_SERVICE_KEY") or SUPABASE_KEY)
            supabase_admin_client.auth.admin.delete_user(user_id)
            logger.info(f"Usuário {user_id} (UUID) deletado do Supabase Auth.")
        except Exception as e_auth_delete:
            logger.warning(f"Não foi possível deletar o usuário {user_id} do Supabase Auth (pode ser permissão ou chave de serviço não configurada): {str(e_auth_delete)}")

        session.clear()
        flash("✅ Sua página foi apagada com sucesso.", "success")
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Erro ao deletar página para o usuário {session.get('user_id')}: {str(e)}", exc_info=True)
        flash("⚠️ Erro ao apagar sua página. Tente novamente ou contate o suporte.", "error")
        return redirect(url_for('admin_panel', username=session.get('profile', '')))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<profile>')
def user_page(profile):
    if profile == 'favicon.ico':
        return abort(404)
    try:
        res = supabase.table('usuarios').select('*').eq('profile', profile).limit(1).single().execute()
        
        if not res.data:
            logger.warning(f"Perfil público não encontrado: {profile}")
            abort(404)
        
        user_data = res.data
        
        user_data['nome_font'] = user_data.get('nome_font') or DEFAULT_FONT
        user_data['nome_color'] = user_data.get('nome_color') or DEFAULT_TEXT_COLOR_PAGE
        user_data['bio_font'] = user_data.get('bio_font') or DEFAULT_FONT
        user_data['bio_color'] = user_data.get('bio_color') or DEFAULT_BIO_COLOR_PAGE
        user_data['card_nome_font'] = user_data.get('card_nome_font') or DEFAULT_FONT
        user_data['card_nome_color'] = user_data.get('card_nome_color') or DEFAULT_TEXT_COLOR_CARD
        user_data['card_titulo_font'] = user_data.get('card_titulo_font') or DEFAULT_FONT
        user_data['card_titulo_color'] = user_data.get('card_titulo_color') or DEFAULT_TITLE_COLOR_CARD
        user_data['card_registro_font'] = user_data.get('card_registro_font') or DEFAULT_FONT
        user_data['card_registro_color'] = user_data.get('card_registro_color') or DEFAULT_REG_COLOR_CARD
        user_data['card_link_text_color'] = user_data.get('card_link_text_color') or DEFAULT_CARD_LINK_TEXT_COLOR # NOVO

        for key_json in ['custom_buttons', 'social_links', 'card_links']:
            if key_json in user_data and user_data[key_json]:
                try:
                    if isinstance(user_data[key_json], str):
                        user_data[key_json] = json.loads(user_data[key_json])
                    if key_json == 'custom_buttons' and isinstance(user_data[key_json], list):
                        for button in user_data[key_json]: # Ensure all fields have defaults for rendering
                            button.setdefault('bold', False)
                            button.setdefault('italic', False)
                            button.setdefault('hasBorder', False)
                            button.setdefault('hasHoverEffect', False)
                            button.setdefault('fontSize', 16)
                            button.setdefault('borderWidth', 2)
                            button.setdefault('textColor', '#FFFFFF')
                            button.setdefault('borderColor', '#000000')
                            button.setdefault('shadowType', 'none')
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar {key_json} para perfil {profile}: {str(e)}")
                    user_data[key_json] = []
            else:
                user_data[key_json] = []
        
        response = make_response(render_template('user_page.html', dados=user_data))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    except Exception as e:
        if "PGRST116" in str(e):
            logger.warning(f"Perfil público não encontrado (PGRST116): {profile}")
            abort(404)
        logger.error(f"Erro ao carregar perfil público {profile}: {str(e)}", exc_info=True)
        abort(500)

@app.route('/login/google')
def login_google():
    try:
        redirect_url = url_for('callback_handler', _external=True, _scheme='https' if not app.debug else 'http')
        auth_response = supabase.auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {
                'redirect_to': redirect_url
            }
        })
        return redirect(auth_response.url)
    except Exception as e:
        logger.error(f"Erro no login Google: {str(e)}", exc_info=True)
        flash("❌ Ocorreu um erro inesperado durante o login. Tente mais tarde.", "error")
        return redirect(url_for('index'))

@app.route('/callback_handler')
def callback_handler():
    return render_template('callback.html')


@app.route('/callback', methods=['POST'])
def callback():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 415
        
        data = request.get_json()
        received_access_token = data.get('access_token')
        received_refresh_token = data.get('refresh_token')
        auth_code = data.get('auth_code')

        user = None
        access_token_to_store = None
        refresh_token_to_store = None

        if auth_code:
            logger.info(f"Recebido auth_code: {auth_code[:20]}...")
            try:
                exchanged_session_response = supabase.auth.exchange_code_for_session({'auth_code': auth_code})
                if exchanged_session_response and exchanged_session_response.user and exchanged_session_response.session:
                    user = exchanged_session_response.user
                    access_token_to_store = exchanged_session_response.session.access_token
                    refresh_token_to_store = exchanged_session_response.session.refresh_token
                    logger.info(f"Sessão trocada com sucesso para user ID: {user.id}")
                else:
                    logger.error("Falha ao trocar código: resposta inválida do Supabase.")
                    return jsonify({"error": "Falha ao trocar código por sessão"}), 401
            except Exception as e_exchange_code:
                logger.error(f"Falha ao trocar código por sessão no Supabase: {str(e_exchange_code)}", exc_info=True)
                return jsonify({"error": "Autenticação com Supabase falhou ao trocar código"}), 401
        
        elif received_access_token:
            logger.info(f"Recebido access_token direto: {received_access_token[:20]}...")
            try:
                session_response = supabase.auth.set_session(received_access_token, received_refresh_token)
                if session_response and session_response.user:
                     user = session_response.user
                     access_token_to_store = received_access_token
                     refresh_token_to_store = received_refresh_token
                else:
                    logger.error("Falha ao definir sessão com token: resposta inválida do Supabase.")
                    return jsonify({"error": "Falha ao definir sessão com token"}), 401
            except Exception as e_set_session:
                logger.error(f"Falha ao definir sessão no Supabase com token: {str(e_set_session)}", exc_info=True)
                return jsonify({"error": "Autenticação com Supabase falhou ao definir sessão"}), 401
        else:
            logger.warning("Nem token de acesso nem código de autorização recebidos no callback.")
            return jsonify({"error": "Token ou código não fornecido"}), 400

        if not user:
            logger.error("Usuário não autenticado após tentativa de callback.")
            return jsonify({"error": "Falha na autenticação do usuário"}), 401
            
        user_data = get_user_by_id(user.id)
        
        if not user_data:
            slug = generate_unique_slug(user.user_metadata.get('full_name', user.email.split('@')[0] if user.email else 'usuario'))
            
            new_user_payload = {
                'id': user.id,
                'nome': user.user_metadata.get('full_name', user.email if user.email else 'Usuário Anônimo'),
                'profile': slug,
                'email': user.email,
                'foto': user.user_metadata.get('avatar_url', ''),
                'active': True,
                'bio': 'Olá! Bem-vindo(a) à minha página pessoal.',
                'social_links': json.dumps([]),
                'custom_buttons': json.dumps([]),
                'card_nome': user.user_metadata.get('full_name', user.email if user.email else 'Usuário Anônimo'),
                'card_titulo': '',
                'card_registro_profissional': '',
                'card_links': json.dumps([]),
                'card_background_type': 'color',
                'card_background_value': DEFAULT_CARD_BG_COLOR,
                'nome_font': DEFAULT_FONT,
                'nome_color': DEFAULT_TEXT_COLOR_PAGE,
                'bio_font': DEFAULT_FONT,
                'bio_color': DEFAULT_BIO_COLOR_PAGE,
                'card_nome_font': DEFAULT_FONT,
                'card_nome_color': DEFAULT_TEXT_COLOR_CARD,
                'card_titulo_font': DEFAULT_FONT,
                'card_titulo_color': DEFAULT_TITLE_COLOR_CARD,
                'card_registro_font': DEFAULT_FONT,
                'card_registro_color': DEFAULT_REG_COLOR_CARD,
                'card_link_text_color': DEFAULT_CARD_LINK_TEXT_COLOR # NOVO
            }
            
            try:
                insert_response = supabase.table('usuarios').insert(new_user_payload).execute()
                if not insert_response.data:
                    logger.error(f"Falha ao criar perfil para {user.id} no banco. Resposta: {insert_response}")
                    return jsonify({"error": "Falha ao criar perfil no banco de dados"}), 500
                user_data = insert_response.data[0]
            except Exception as e_insert:
                logger.error(f"Erro ao inserir novo usuário {user.id} na tabela 'usuarios': {str(e_insert)}", exc_info=True)
                return jsonify({"error": "Erro interno ao criar perfil"}), 500
        
        session['user_id'] = user.id
        session['access_token'] = access_token_to_store
        session['refresh_token'] = refresh_token_to_store
        session['profile'] = user_data['profile']
        session['logado'] = True
        
        logger.info(f"Usuário {user.id} ({user_data['profile']}) logado com sucesso via callback.")
        return jsonify({
            "message": "Login bem-sucedido!",
            "redirect": url_for('admin_panel', username=user_data['profile']),
            "profile": user_data['profile']
        }), 200
        
    except Exception as e:
        logger.error(f"Erro CRÍTICO no callback: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno crítico no servidor durante o callback"}), 500

@app.route('/admin/<username>', methods=['GET', 'POST'])
def admin_panel(username):
    if 'user_id' not in session or not session.get('access_token'):
        flash("🔒 Sua sessão expirou ou é inválida. Por favor, faça login novamente.", "error")
        session.clear()
        return redirect(url_for('login_google'))
    
    try:
        supabase.auth.set_session(session['access_token'], session['refresh_token'])
        user_auth_check = supabase.auth.get_user()

        if not user_auth_check or not user_auth_check.user:
            logger.warning(f"Sessão inválida (get_user falhou) para Flask session user_id {session.get('user_id')}. Deslogando.")
            session.clear()
            flash("🔑 Sua sessão expirou ou não pôde ser validada. Por favor, faça login novamente.", "error")
            return redirect(url_for('login_google'))
        
    except Exception as e_auth:
        logger.warning(f"Erro ao verificar/restaurar sessão para Flask session user_id {session.get('user_id')}: {str(e_auth)}. Deslogando.", exc_info=True)
        session.clear()
        flash("🔑 Ocorreu um erro com sua sessão. Por favor, faça login novamente.", "error")
        return redirect(url_for('login_google'))


    user_id_from_session = session['user_id']
    
    try:
        target_user_res = supabase.table('usuarios').select('id, profile').eq('profile', username).limit(1).single().execute()
        if not target_user_res.data:
            logger.warning(f"Tentativa de acesso ao painel de admin para perfil inexistente: {username}")
            abort(404)
        
        if target_user_res.data['id'] != user_id_from_session:
            logger.warning(f"Usuário {user_id_from_session} (perfil {session.get('profile')}) tentou acessar painel de {username} (ID {target_user_res.data['id']}). Acesso negado.")
            flash("🚫 Você não tem permissão para acessar esta página.", "error")
            return redirect(url_for('admin_panel', username=session.get('profile')) if session.get('profile') else url_for('login_google'))

    except Exception as e_fetch_target:
        logger.error(f"Erro ao buscar dados do perfil '{username}' para validação no admin_panel: {str(e_fetch_target)}")
        flash("⚠️ Ocorreu um erro ao verificar as permissões da página. Tente novamente.", "warning")
        return redirect(url_for('index'))


    user_data = get_user_by_id(user_id_from_session)
    if not user_data:
        logger.error(f"Não foi possível carregar dados para o usuário logado {user_id_from_session} no admin_panel.")
        flash("❌ Erro ao carregar seus dados. Tente fazer login novamente.", "error")
        session.clear()
        return redirect(url_for('login_google'))

    user_data['nome_font'] = user_data.get('nome_font') or DEFAULT_FONT
    user_data['nome_color'] = user_data.get('nome_color') or DEFAULT_TEXT_COLOR_PAGE
    user_data['bio_font'] = user_data.get('bio_font') or DEFAULT_FONT
    user_data['bio_color'] = user_data.get('bio_color') or DEFAULT_BIO_COLOR_PAGE
    user_data['card_nome_font'] = user_data.get('card_nome_font') or DEFAULT_FONT
    user_data['card_nome_color'] = user_data.get('card_nome_color') or DEFAULT_TEXT_COLOR_CARD
    user_data['card_titulo_font'] = user_data.get('card_titulo_font') or DEFAULT_FONT
    user_data['card_titulo_color'] = user_data.get('card_titulo_color') or DEFAULT_TITLE_COLOR_CARD
    user_data['card_registro_font'] = user_data.get('card_registro_font') or DEFAULT_FONT
    user_data['card_registro_color'] = user_data.get('card_registro_color') or DEFAULT_REG_COLOR_CARD
    user_data['card_link_text_color'] = user_data.get('card_link_text_color') or DEFAULT_CARD_LINK_TEXT_COLOR # NOVO
    user_data['card_background_type'] = user_data.get('card_background_type') or 'color'
    user_data['card_background_value'] = user_data.get('card_background_value') or DEFAULT_CARD_BG_COLOR
    if user_data['card_background_type'] == 'color' and not re.match(r'^#[0-9a-fA-F]{6}$', str(user_data.get('card_background_value',''))):
        user_data['card_background_value'] = DEFAULT_CARD_BG_COLOR

    for key_json in ['custom_buttons', 'social_links', 'card_links']:
        if key_json in user_data and user_data[key_json]:
            try:
                if isinstance(user_data[key_json], str):
                    user_data[key_json] = json.loads(user_data[key_json])
                if key_json == 'custom_buttons' and isinstance(user_data[key_json], list):
                    for button in user_data[key_json]:
                        button.setdefault('bold', False)
                        button.setdefault('italic', False)
                        button.setdefault('hasBorder', False)
                        button.setdefault('hasHoverEffect', False)
                        button.setdefault('fontSize', 16)
                        button.setdefault('borderWidth', 2)
                        button.setdefault('textColor', '#FFFFFF')
                        button.setdefault('borderColor', '#000000')
                        button.setdefault('shadowType', 'none')
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"Erro ao processar {key_json} no admin para {username}: {str(e)}")
                user_data[key_json] = []
        else:
            user_data[key_json] = []


    if request.method == 'POST':
        try:
            update_data = {
                'nome': request.form.get('nome'),
                'bio': request.form.get('bio'),
                'profile': request.form.get('profile', '').strip().lower(),
                'card_nome': request.form.get('card_nome'),
                'card_titulo': request.form.get('card_titulo'),
                'card_registro_profissional': request.form.get('card_registro_profissional'),
                'card_background_type': request.form.get('card_background_type'),
                'nome_font': request.form.get('nome_font', DEFAULT_FONT),
                'nome_color': request.form.get('nome_color', DEFAULT_TEXT_COLOR_PAGE),
                'bio_font': request.form.get('bio_font', DEFAULT_FONT),
                'bio_color': request.form.get('bio_color', DEFAULT_BIO_COLOR_PAGE),
                'card_nome_font': request.form.get('card_nome_font', DEFAULT_FONT),
                'card_nome_color': request.form.get('card_nome_color', DEFAULT_TEXT_COLOR_CARD),
                'card_titulo_font': request.form.get('card_titulo_font', DEFAULT_FONT),
                'card_titulo_color': request.form.get('card_titulo_color', DEFAULT_TITLE_COLOR_CARD),
                'card_registro_font': request.form.get('card_registro_font', DEFAULT_FONT),
                'card_registro_color': request.form.get('card_registro_color', DEFAULT_REG_COLOR_CARD),
                'card_link_text_color': request.form.get('card_link_text_color', DEFAULT_CARD_LINK_TEXT_COLOR), # NOVO
            }

            novo_profile = update_data['profile']
            
            if not is_valid_slug(novo_profile):
                flash("❌ URL da página inválida. Use apenas letras minúsculas, números e hífens.", "error")
                current_form_data = user_data.copy()
                current_form_data.update(request.form.to_dict())
                for key_json_form in ['custom_buttons', 'social_links', 'card_links']:
                     current_form_data[key_json_form] = json.loads(request.form.get(key_json_form, '[]')) if isinstance(request.form.get(key_json_form), str) else request.form.get(key_json_form, [])
                for field in ['nome_font', 'nome_color', 'bio_font', 'bio_color', 'card_nome_font', 'card_nome_color', 'card_titulo_font', 'card_titulo_color', 'card_registro_font', 'card_registro_color', 'card_link_text_color']: # NOVO campo adicionado
                    current_form_data[field] = request.form.get(field, user_data.get(field))
                return render_template('admin.html', dados=current_form_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR)
            
            if novo_profile != username and slug_exists(novo_profile, user_id_from_session):
                flash(f"❌ A URL '{novo_profile}' já está em uso. Escolha outra.", "error")
                update_data['profile'] = username
                current_form_data = user_data.copy()
                current_form_data.update(update_data)
                for key_json_form in ['custom_buttons', 'social_links', 'card_links']:
                     current_form_data[key_json_form] = json.loads(request.form.get(key_json_form, '[]')) if isinstance(request.form.get(key_json_form), str) else request.form.get(key_json_form, [])
                for field in ['nome_font', 'nome_color', 'bio_font', 'bio_color', 'card_nome_font', 'card_nome_color', 'card_titulo_font', 'card_titulo_color', 'card_registro_font', 'card_registro_color', 'card_link_text_color']: # NOVO campo adicionado
                    current_form_data[field] = request.form.get(field, user_data.get(field))
                return render_template('admin.html', dados=current_form_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR)

            if update_data['card_background_type'] == 'color':
                update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)
            elif update_data['card_background_type'] == 'image':
                update_data['card_background_value'] = user_data.get('card_background_value', '')

            social_links_list = []
            social_icon_names = request.form.getlist('social_icon_name[]')
            social_icon_urls = request.form.getlist('social_icon_url[]')
            for i in range(len(social_icon_names)):
                social_links_list.append({'icon': social_icon_names[i], 'url': social_icon_urls[i].strip()})
            update_data['social_links'] = json.dumps(social_links_list)

            custom_buttons_list = []
            button_texts = request.form.getlist('custom_button_text[]')
            for i in range(len(button_texts)):
                custom_buttons_list.append({
                    'text': button_texts[i].strip(),
                    'link': request.form.getlist('custom_button_link[]')[i].strip(),
                    'color': request.form.getlist('custom_button_color[]')[i],
                    'radius': int(request.form.getlist('custom_button_radius[]')[i]),
                    'textColor': request.form.getlist('custom_button_text_color[]')[i],
                    'bold': str(request.form.getlist('custom_button_text_bold[]')[i]).lower() == 'true',
                    'italic': str(request.form.getlist('custom_button_text_italic[]')[i]).lower() == 'true',
                    'fontSize': int(request.form.getlist('custom_button_font_size[]')[i]),
                    'hasBorder': str(request.form.getlist('custom_button_has_border[]')[i]).lower() == 'true',
                    'borderColor': request.form.getlist('custom_button_border_color[]')[i],
                    'borderWidth': int(request.form.getlist('custom_button_border_width[]')[i]),
                    'hasHoverEffect': str(request.form.getlist('custom_button_has_hover[]')[i]).lower() == 'true',
                    'shadowType': request.form.getlist('custom_button_shadow_type[]')[i]
                })
            update_data['custom_buttons'] = json.dumps(custom_buttons_list)
            
            card_links_list = []
            card_icon_names = request.form.getlist('card_icon_name[]')
            for i in range(len(card_icon_names)):
                card_links_list.append({
                    'icon': card_icon_names[i],
                    'url': request.form.getlist('card_icon_url[]')[i].strip(),
                    'at_text': request.form.getlist('card_icon_at_text[]')[i].strip()
                })
            update_data['card_links'] = json.dumps(card_links_list)


            foto_file = request.files.get('foto_upload')
            if foto_file and foto_file.filename != '' and arquivo_permitido(foto_file.filename):
                file_url = upload_to_supabase(foto_file, user_id_from_session, 'foto')
                if file_url: update_data['foto'] = file_url
                else: flash("❌ Erro ao fazer upload da foto de perfil.", "error")
            
            background_file = request.files.get('background_upload')
            if background_file and background_file.filename != '' and arquivo_permitido(background_file.filename):
                file_url = upload_to_supabase(background_file, user_id_from_session, 'background')
                if file_url: update_data['background'] = file_url
                else: flash("❌ Erro ao fazer upload da imagem de fundo da página.", "error")
            
            if update_data['card_background_type'] == 'image':
                card_bg_file = request.files.get('card_background_upload')
                if card_bg_file and card_bg_file.filename != '' and arquivo_permitido(card_bg_file.filename):
                    file_url = upload_to_supabase(card_bg_file, user_id_from_session, 'card_background')
                    if file_url: update_data['card_background_value'] = file_url
                    else:
                        flash("❌ Erro ao fazer upload da imagem de fundo do cartão. Usando cor sólida.", "error")
                        update_data['card_background_type'] = 'color'
                        update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)
                elif not (user_data.get('card_background_value') and supabase.storage.from_("usuarios").get_public_url("").startswith(str(user_data.get('card_background_value','')).rsplit('/',1)[0])):
                    if not (user_data.get('card_background_value') and supabase.storage.from_("usuarios").get_public_url("").startswith(str(user_data.get('card_background_value','')).rsplit('/',1)[0])):
                        update_data['card_background_type'] = 'color'
                        update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)

            if request.form.get('remove_card_background_image') == 'true':
                if user_data.get('card_background_type') == 'image' and str(user_data.get('card_background_value','')).startswith(f"{SUPABASE_URL}/storage/v1/object/public/usuarios/"):
                    try:
                        old_card_bg_filename = user_data['card_background_value'].split('/')[-1]
                        supabase.storage.from_("usuarios").remove([old_card_bg_filename])
                        logger.info(f"Imagem de fundo do cartão antiga '{old_card_bg_filename}' removida do storage.")
                    except Exception as e_storage_remove:
                        logger.error(f"Erro ao remover imagem de fundo do cartão antiga do storage: {str(e_storage_remove)}")
                update_data['card_background_type'] = 'color'
                update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)

            db_response = supabase.table('usuarios').update(update_data).eq('id', user_id_from_session).execute()
            
            if db_response.data:
                if 'profile' in update_data and update_data['profile'] != username:
                    session['profile'] = update_data['profile']
                    username = update_data['profile']
                flash("✅ Alterações salvas com sucesso!", "success")
                return redirect(url_for('admin_panel', username=username))
            else:
                logger.error(f"Falha ao salvar dados para {username}. Supabase response: {db_response.error if db_response.error else 'Sem dados de erro específicos.'}")
                flash("❌ Erro ao salvar os dados. Verifique os logs do servidor.", "error")
        
        except Exception as e_post:
            logger.error(f"Erro GERAL no POST do admin_panel para {username}: {str(e_post)}", exc_info=True)
            flash(f"⚠️ Ocorreu um erro inesperado ao salvar: Verifique os logs.", "error")
            
            failed_update_form_data = user_data.copy()
            failed_update_form_data.update(request.form.to_dict())
            
            failed_update_form_data['social_links'] = json.loads(request.form.get('social_links_json_hidden', '[]'))
            failed_update_form_data['custom_buttons'] = json.loads(request.form.get('custom_buttons_json_hidden', '[]'))
            failed_update_form_data['card_links'] = json.loads(request.form.get('card_links_json_hidden', '[]'))

            for field in ['nome_font', 'nome_color', 'bio_font', 'bio_color', 'card_nome_font', 'card_nome_color', 'card_titulo_font', 'card_titulo_color', 'card_registro_font', 'card_registro_color', 'card_link_text_color']: # NOVO campo adicionado
                failed_update_form_data[field] = request.form.get(field, user_data.get(field))
            
            failed_update_form_data['card_background_type'] = request.form.get('card_background_type', user_data.get('card_background_type', 'color'))
            if failed_update_form_data['card_background_type'] == 'color':
                failed_update_form_data['card_background_value'] = request.form.get('card_background_value_color', user_data.get('card_background_value', DEFAULT_CARD_BG_COLOR))
            else:
                failed_update_form_data['card_background_value'] = user_data.get('card_background_value')

            return render_template('admin.html', dados=failed_update_form_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR)

    return render_template('admin.html', dados=user_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR) # Passando a constante


@app.route('/logout')
def logout():
    try:
        if 'access_token' in session:
            sign_out_response = supabase.auth.sign_out()
            logger.info(f"Usuário {session.get('user_id')} deslogado do Supabase. Resposta: {type(sign_out_response)}")
    except Exception as e:
        logger.error(f"Erro ao tentar deslogar do Supabase para usuário {session.get('user_id')}: {str(e)}")
    finally:
        session.clear()
        flash("👋 Você foi desconectado.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    is_production = os.getenv('FLASK_ENV') == 'production'
    app.run(debug=not is_production, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))