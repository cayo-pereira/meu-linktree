from flask import Flask, render_template, request, redirect, session, url_for, abort, jsonify, flash, make_response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from uuid import uuid4
import json
import os
import re
import logging

# Configurar loggers de bibliotecas antes de qualquer outra coisa
logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("werkzeug").setLevel(logging.WARNING)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or 'dev-secret-key'


# Configurações Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options=ClientOptions(
        postgrest_client_timeout=10,
        storage_client_timeout=10,
        headers={
            'Prefer': 'return=representation',
        }
    )
)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEFAULT_FONT = "Inter, sans-serif"
DEFAULT_TEXT_COLOR_PAGE = "#333333"
DEFAULT_BIO_COLOR_PAGE = "#555555"
DEFAULT_TEXT_COLOR_CARD = "#FFFFFF" # Usado para nome, título, registro E como padrão para itens de link
DEFAULT_TITLE_COLOR_CARD = "#EEEEEE"
DEFAULT_REG_COLOR_CARD = "#BBBBBB"
DEFAULT_CARD_BG_COLOR = "#4361ee"
DEFAULT_CARD_LINK_TEXT_COLOR = "#FFFFFF" # Cor global para links do cartão (fallback)


def upload_to_supabase(file, user_id, field_type):
    try:
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        unique_filename = f"{user_id}_{field_type}_{uuid4().hex[:8]}{file_ext}"
        
        file.seek(0)
        file_bytes = file.read()

        response = supabase.storage.from_("usuarios").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )

        public_url = supabase.storage.from_("usuarios").get_public_url(unique_filename)
        return public_url
            
    except Exception as e:
        if "Duplicate" in str(e) or "The resource already exists" in str(e):
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
    
    user_id_to_delete = session.get('user_id') 
    profile_to_redirect_to_admin = session.get('profile', '')

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
        
        response_db_delete = supabase.table('usuarios').delete().eq('id', user_id).execute()
        affected_rows = len(response_db_delete.data) if hasattr(response_db_delete, 'data') and response_db_delete.data is not None else 0
        logger.info(f"Usuário {user_id} deletado da tabela 'usuarios'. Registros afetados: {affected_rows}.")

        
        try:
            supabase_admin_key = os.getenv("SUPABASE_SERVICE_KEY")
            if not supabase_admin_key:
                logger.warning("Chave de serviço SUPABASE_SERVICE_KEY não configurada. Tentando com a chave anônima, o que pode falhar.")
                supabase_admin_key = SUPABASE_KEY

            supabase_admin_client = create_client(SUPABASE_URL, supabase_admin_key)
            supabase_admin_client.auth.admin.delete_user(user_id) 
            logger.info(f"Usuário {user_id} (UUID) deletado do Supabase Auth.")
        except Exception as e_auth_delete:
            logger.warning(f"Não foi possível deletar o usuário {user_id} do Supabase Auth (pode ser permissão ou chave de serviço não configurada): {str(e_auth_delete)}")

        session.clear()
        flash("✅ Sua página foi apagada com sucesso.", "success")
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Erro ao deletar página para o usuário {user_id_to_delete}: {str(e)}", exc_info=True)
        flash("⚠️ Erro ao apagar sua página. Tente novamente ou contate o suporte.", "error")
        return redirect(url_for('admin_panel', username=profile_to_redirect_to_admin) if profile_to_redirect_to_admin else url_for('index') )


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
        
        # Populando com padrões
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
        user_data['card_link_text_color'] = user_data.get('card_link_text_color') or DEFAULT_CARD_LINK_TEXT_COLOR # Cor global

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
                    
                    # Adicionando padrões para font e color em card_links individuais
                    if key_json == 'card_links' and isinstance(user_data[key_json], list):
                        for link_item in user_data[key_json]:
                            link_item.setdefault('font', DEFAULT_FONT)
                            link_item.setdefault('color', DEFAULT_TEXT_COLOR_CARD) # Cor padrão para item individual
                
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar {key_json} para perfil {profile}: {str(e)}")
                    user_data[key_json] = []
            else:
                user_data[key_json] = []
        
        response = make_response(render_template('user_page.html', 
                                                dados=user_data, 
                                                DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD, 
                                                DEFAULT_FONT=DEFAULT_FONT))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    except Exception as e:
        if "PGRST116" in str(e): # Erro do Supabase para "zero rows"
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
            logger.debug(f"Recebido auth_code para processamento.")
            try:
                exchanged_session_response = supabase.auth.exchange_code_for_session({'auth_code': auth_code})
                if exchanged_session_response and exchanged_session_response.user and exchanged_session_response.session:
                    user = exchanged_session_response.user
                    access_token_to_store = exchanged_session_response.session.access_token
                    refresh_token_to_store = exchanged_session_response.session.refresh_token
                    logger.debug(f"Sessão trocada com sucesso para user ID: {user.id}")
                else:
                    logger.error("Falha ao trocar código: resposta inválida do Supabase.")
                    return jsonify({"error": "Falha ao trocar código por sessão"}), 401
            except Exception as e_exchange_code:
                logger.error(f"Falha ao trocar código por sessão no Supabase: {str(e_exchange_code)}", exc_info=True)
                return jsonify({"error": "Autenticação com Supabase falhou ao trocar código"}), 401
        
        elif received_access_token:
            logger.debug(f"Recebido access_token direto para processamento.")
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
                'card_links': json.dumps([]), # Será populado com font e color padrão no GET
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
                'card_link_text_color': DEFAULT_CARD_LINK_TEXT_COLOR
            }
            
            try:
                insert_response = supabase.table('usuarios').insert(new_user_payload).execute()
                if not insert_response.data:
                    logger.error(f"Falha ao criar perfil para {user.id} no banco. Resposta: {insert_response}")
                    return jsonify({"error": "Falha ao criar perfil no banco de dados"}), 500
                user_data = insert_response.data[0]
                logger.info(f"Novo perfil criado para usuário {user.id} com slug {slug}.")
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

    # Populando com padrões para exibição no template
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
    user_data['card_link_text_color'] = user_data.get('card_link_text_color') or DEFAULT_CARD_LINK_TEXT_COLOR # Global
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
                
                # Adicionando padrões para font e color em card_links individuais para o template
                if key_json == 'card_links' and isinstance(user_data[key_json], list):
                    for link_item in user_data[key_json]:
                        link_item.setdefault('font', DEFAULT_FONT)
                        link_item.setdefault('color', DEFAULT_TEXT_COLOR_CARD) # Cor padrão para item individual

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
                'card_link_text_color': request.form.get('card_link_text_color', DEFAULT_CARD_LINK_TEXT_COLOR), # Global
            }

            novo_profile = update_data['profile']
            
            if not is_valid_slug(novo_profile):
                flash("❌ URL da página inválida. Use apenas letras minúsculas, números e hífens.", "error")
                current_form_data = user_data.copy() # Start with current user_data to preserve loaded JSON lists
                current_form_data.update(request.form.to_dict()) # Override with form values
                # Manter os links sociais, botões e links do cartão como foram submetidos ou estavam
                current_form_data['social_links'] = json.loads(request.form.get('social_links_json_hidden', json.dumps(user_data.get('social_links', []))))
                current_form_data['custom_buttons'] = json.loads(request.form.get('custom_buttons_json_hidden', json.dumps(user_data.get('custom_buttons', []))))
                current_form_data['card_links'] = json.loads(request.form.get('card_links_json_hidden', json.dumps(user_data.get('card_links', []))))
                # Re-processar card_links para garantir font/color para o template, mesmo em erro
                if isinstance(current_form_data['card_links'], list):
                    for link_item in current_form_data['card_links']:
                        link_item.setdefault('font', request.form.getlist('card_icon_font[]')[current_form_data['card_links'].index(link_item)] if current_form_data['card_links'].index(link_item) < len(request.form.getlist('card_icon_font[]')) else DEFAULT_FONT)
                        link_item.setdefault('color', request.form.getlist('card_icon_color[]')[current_form_data['card_links'].index(link_item)] if current_form_data['card_links'].index(link_item) < len(request.form.getlist('card_icon_color[]')) else DEFAULT_TEXT_COLOR_CARD)

                return render_template('admin.html', dados=current_form_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR, DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD, DEFAULT_FONT=DEFAULT_FONT)

            if novo_profile != username and slug_exists(novo_profile, user_id_from_session):
                flash(f"❌ A URL '{novo_profile}' já está em uso. Escolha outra.", "error")
                update_data['profile'] = username # Revert to old profile slug on error
                current_form_data = user_data.copy()
                current_form_data.update(update_data) # Apply other changes
                current_form_data['social_links'] = json.loads(request.form.get('social_links_json_hidden', json.dumps(user_data.get('social_links', []))))
                current_form_data['custom_buttons'] = json.loads(request.form.get('custom_buttons_json_hidden', json.dumps(user_data.get('custom_buttons', []))))
                current_form_data['card_links'] = json.loads(request.form.get('card_links_json_hidden', json.dumps(user_data.get('card_links', []))))
                if isinstance(current_form_data['card_links'], list):
                    for link_item in current_form_data['card_links']:
                        link_item.setdefault('font', request.form.getlist('card_icon_font[]')[current_form_data['card_links'].index(link_item)] if current_form_data['card_links'].index(link_item) < len(request.form.getlist('card_icon_font[]')) else DEFAULT_FONT)
                        link_item.setdefault('color', request.form.getlist('card_icon_color[]')[current_form_data['card_links'].index(link_item)] if current_form_data['card_links'].index(link_item) < len(request.form.getlist('card_icon_color[]')) else DEFAULT_TEXT_COLOR_CARD)
                return render_template('admin.html', dados=current_form_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR, DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD, DEFAULT_FONT=DEFAULT_FONT)


            if update_data['card_background_type'] == 'color':
                update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)
            elif update_data['card_background_type'] == 'image':
                # Mantém o valor existente se nenhum novo arquivo for enviado e nenhum pedido de remoção
                update_data['card_background_value'] = user_data.get('card_background_value', '') 

            social_links_list = []
            social_icon_names = request.form.getlist('social_icon_name[]')
            social_icon_urls = request.form.getlist('social_icon_url[]')
            for i in range(len(social_icon_names)):
                social_links_list.append({'icon': social_icon_names[i], 'url': social_icon_urls[i].strip()})
            update_data['social_links'] = json.dumps(social_links_list)

            custom_buttons_list = []
            button_texts = request.form.getlist('custom_button_text[]')
            # Iterar com base no número de textos de botão, assumindo que outras listas têm o mesmo comprimento
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
            card_icon_urls = request.form.getlist('card_icon_url[]')
            card_icon_at_texts = request.form.getlist('card_icon_at_text[]')
            card_icon_fonts = request.form.getlist('card_icon_font[]') # Lista de fontes
            card_icon_colors = request.form.getlist('card_icon_color[]') # Lista de cores

            for i in range(len(card_icon_names)):
                link_data = {
                    'icon': card_icon_names[i],
                    'url': card_icon_urls[i].strip() if i < len(card_icon_urls) else '',
                    'at_text': card_icon_at_texts[i].strip() if i < len(card_icon_at_texts) else '',
                    'font': card_icon_fonts[i] if i < len(card_icon_fonts) else DEFAULT_FONT,
                    'color': card_icon_colors[i] if i < len(card_icon_colors) else DEFAULT_TEXT_COLOR_CARD 
                }
                card_links_list.append(link_data)
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
                    if file_url: 
                        update_data['card_background_value'] = file_url
                    else: # Erro no upload, reverte para cor sólida
                        flash("❌ Erro ao fazer upload da imagem de fundo do cartão. Usando cor sólida.", "error")
                        update_data['card_background_type'] = 'color'
                        update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)
                # Se nenhum arquivo novo foi enviado, mas o tipo é imagem, mantém o valor existente (já tratado acima)
                # A menos que a remoção seja solicitada:
            
            if request.form.get('remove_card_background_image') == 'true':
                # Remove a imagem antiga do storage se existir e pertencer ao usuário
                if user_data.get('card_background_type') == 'image' and str(user_data.get('card_background_value','')).startswith(f"{SUPABASE_URL}/storage/v1/object/public/usuarios/"):
                    try:
                        old_card_bg_filename = user_data['card_background_value'].split('/')[-1]
                        supabase.storage.from_("usuarios").remove([old_card_bg_filename])
                        logger.info(f"Imagem de fundo do cartão antiga '{old_card_bg_filename}' removida do storage.")
                    except Exception as e_storage_remove:
                        logger.error(f"Erro ao remover imagem de fundo do cartão antiga do storage: {str(e_storage_remove)}")
                # Define como cor sólida
                update_data['card_background_type'] = 'color'
                update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)


            db_response = supabase.table('usuarios').update(update_data).eq('id', user_id_from_session).execute()
            
            if db_response.data:
                if 'profile' in update_data and update_data['profile'] != username:
                    session['profile'] = update_data['profile'] # Atualiza o profile na sessão
                    username = update_data['profile'] # Atualiza o username para o redirect
                flash("✅ Alterações salvas com sucesso!", "success")
                return redirect(url_for('admin_panel', username=username))
            else:
                logger.error(f"Falha ao salvar dados para {username}. Supabase response: {db_response.error if db_response.error else 'Sem dados de erro específicos.'}")
                flash("❌ Erro ao salvar os dados. Verifique os logs do servidor.", "error")
        
        except Exception as e_post: 
            logger.error(f"Erro GERAL no POST do admin_panel para {username}: {str(e_post)}", exc_info=True)
            flash(f"⚠️ Ocorreu um erro inesperado ao salvar: Verifique os logs.", "error")
            
            # Tentar recarregar o formulário com os dados que o usuário tentou enviar
            failed_update_form_data = user_data.copy() # Começa com os dados carregados
            failed_update_form_data.update(request.form.to_dict()) # Sobrescreve com o que veio do form

            # Lógica para reconstruir listas de links/botões a partir do form, se necessário
            # (idealmente, o JS manteria inputs hidden com o JSON dessas listas)
            # Exemplo simplificado:
            failed_update_form_data['social_links'] = json.loads(request.form.get('social_links_json_hidden', json.dumps(user_data.get('social_links', []))))
            failed_update_form_data['custom_buttons'] = json.loads(request.form.get('custom_buttons_json_hidden', json.dumps(user_data.get('custom_buttons', []))))
            temp_card_links = []
            card_icon_names_fail = request.form.getlist('card_icon_name[]')
            card_icon_urls_fail = request.form.getlist('card_icon_url[]')
            card_icon_at_texts_fail = request.form.getlist('card_icon_at_text[]')
            card_icon_fonts_fail = request.form.getlist('card_icon_font[]')
            card_icon_colors_fail = request.form.getlist('card_icon_color[]')

            for i in range(len(card_icon_names_fail)):
                temp_card_links.append({
                    'icon': card_icon_names_fail[i],
                    'url': card_icon_urls_fail[i] if i < len(card_icon_urls_fail) else '',
                    'at_text': card_icon_at_texts_fail[i] if i < len(card_icon_at_texts_fail) else '',
                    'font': card_icon_fonts_fail[i] if i < len(card_icon_fonts_fail) else DEFAULT_FONT,
                    'color': card_icon_colors_fail[i] if i < len(card_icon_colors_fail) else DEFAULT_TEXT_COLOR_CARD
                })
            failed_update_form_data['card_links'] = temp_card_links
            
            # Restaurar valores de fonte/cor dos campos principais
            for field_key in ['nome_font', 'nome_color', 'bio_font', 'bio_color', 
                              'card_nome_font', 'card_nome_color', 'card_titulo_font', 'card_titulo_color', 
                              'card_registro_font', 'card_registro_color', 'card_link_text_color']:
                failed_update_form_data[field_key] = request.form.get(field_key, user_data.get(field_key))


            failed_update_form_data['card_background_type'] = request.form.get('card_background_type', user_data.get('card_background_type', 'color'))
            if failed_update_form_data['card_background_type'] == 'color':
                failed_update_form_data['card_background_value'] = request.form.get('card_background_value_color', user_data.get('card_background_value', DEFAULT_CARD_BG_COLOR))
            else: # Se for imagem, mantém o valor atual salvo (JS cuida do preview de novo upload)
                failed_update_form_data['card_background_value'] = user_data.get('card_background_value')


            return render_template('admin.html', dados=failed_update_form_data, 
                                   DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR,
                                   DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD,
                                   DEFAULT_FONT=DEFAULT_FONT)

    # Para o método GET, passa as constantes de cor/fonte padrão para o template
    return render_template('admin.html', 
                           dados=user_data, 
                           DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR,
                           DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD, # Padrão para itens individuais
                           DEFAULT_FONT=DEFAULT_FONT)


@app.route('/logout')
def logout():
    try:
        if 'access_token' in session:
            sign_out_response = supabase.auth.sign_out() # noqa F841
            logger.info(f"Usuário {session.get('user_id')} deslogado do Supabase.")
    except Exception as e:
        logger.error(f"Erro ao tentar deslogar do Supabase para usuário {session.get('user_id')}: {str(e)}")
    finally:
        session.clear()
        flash("👋 Você foi desconectado.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    is_production = os.getenv('FLASK_ENV') == 'production'
    app.run(debug=not is_production, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))