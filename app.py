from flask import Flask, render_template, request, redirect, session, url_for, abort, jsonify, flash, make_response, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from uuid import uuid4
import json
import os
import re
import logging
from io import BytesIO

logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or 'dev-secret-key'

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
DEFAULT_TEXT_COLOR_CARD = "#FFFFFF"
DEFAULT_TITLE_COLOR_CARD = "#EEEEEE"
DEFAULT_REG_COLOR_CARD = "#BBBBBB"
DEFAULT_CARD_BG_COLOR = "#4361ee"
DEFAULT_CARD_LINK_TEXT_COLOR = "#FFFFFF"
DEFAULT_CARD_ENDERECO_COLOR = "#FFFFFF"
DEFAULT_BUTTON_OPACITY = 1.0
DEFAULT_BUTTON_ICON_URL = ""
DEFAULT_BUTTON_ICON_TYPE = "none"
DEFAULT_BUTTON_STYLE = "default"
DEFAULT_BUTTON_ICON_ROUNDED = False
DEFAULT_BUTTON_HOVER_EFFECT_TYPE = "none"
DEFAULT_BUTTON_SHADOW_DEPTH = 4 # NOVO: Profundidade padrão para o estilo "Sombra Destacada"

DEFAULT_BACKGROUND_TYPE = "image"
DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL = 0.0
DEFAULT_BACKGROUND_COLOR_VALUE = "#000000"


app.config.update(
    DEFAULT_FONT = DEFAULT_FONT,
    DEFAULT_TEXT_COLOR_PAGE = DEFAULT_TEXT_COLOR_PAGE,
    DEFAULT_BIO_COLOR_PAGE = DEFAULT_BIO_COLOR_PAGE,
    DEFAULT_TEXT_COLOR_CARD = DEFAULT_TEXT_COLOR_CARD,
    DEFAULT_TITLE_COLOR_CARD = DEFAULT_TITLE_COLOR_CARD,
    DEFAULT_REG_COLOR_CARD = DEFAULT_REG_COLOR_CARD,
    DEFAULT_CARD_BG_COLOR = DEFAULT_CARD_BG_COLOR,
    DEFAULT_CARD_LINK_TEXT_COLOR = DEFAULT_CARD_LINK_TEXT_COLOR,
    DEFAULT_CARD_ENDERECO_COLOR = DEFAULT_CARD_ENDERECO_COLOR,
    DEFAULT_BUTTON_OPACITY = DEFAULT_BUTTON_OPACITY,
    DEFAULT_BUTTON_ICON_URL = DEFAULT_BUTTON_ICON_URL,
    DEFAULT_BUTTON_ICON_TYPE = DEFAULT_BUTTON_ICON_TYPE,
    DEFAULT_BUTTON_STYLE = DEFAULT_BUTTON_STYLE,
    DEFAULT_BUTTON_ICON_ROUNDED = DEFAULT_BUTTON_ICON_ROUNDED,
    DEFAULT_BUTTON_HOVER_EFFECT_TYPE = DEFAULT_BUTTON_HOVER_EFFECT_TYPE,
    DEFAULT_BUTTON_SHADOW_DEPTH = DEFAULT_BUTTON_SHADOW_DEPTH, # NOVO
    DEFAULT_BACKGROUND_TYPE = DEFAULT_BACKGROUND_TYPE,
    DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL = DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL,
    DEFAULT_BACKGROUND_COLOR_VALUE = DEFAULT_BACKGROUND_COLOR_VALUE
)


def upload_to_supabase(file, user_id, field_type):
    try:
        if hasattr(file, 'filename'):
            original_filename = secure_filename(file.filename)
            content_type = file.content_type
        else:
            logger.warning(f"upload_to_supabase chamado com objeto não arquivo para {field_type}")
            return None

        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext:
            file_ext = ".png" if "png" in content_type else ".jpg" if "jpeg" in content_type else ""
        if not file_ext or file_ext.replace('.', '') not in ALLOWED_EXTENSIONS:
             logger.error(f"Extensão de arquivo não permitida para upload: {file_ext} (arquivo: {original_filename})")
             return None


        unique_filename = f"{user_id}_{field_type}_{uuid4().hex[:8]}{file_ext}"
        file.seek(0)
        file_bytes = file.read()
        response = supabase.storage.from_("usuarios").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        public_url = supabase.storage.from_("usuarios").get_public_url(unique_filename)
        return public_url
    except Exception as e:
        filename_for_log = file.filename if hasattr(file, 'filename') else "objeto_sem_nome_de_arquivo"
        unique_filename_local = locals().get('unique_filename', 'desconhecido')
        if "Duplicate" in str(e) or "The resource already exists" in str(e):
             logger.warning(f"Arquivo {unique_filename_local} já existe (Supabase). Tentando obter URL pública. Erro original: {str(e)}")
             try:
                if unique_filename_local != 'desconhecido':
                    return supabase.storage.from_("usuarios").get_public_url(unique_filename_local)
                logger.error(f"Não foi possível obter URL para arquivo duplicado (nome desconhecido): {filename_for_log}")
                return None
             except Exception as e_url:
                logger.error(f"Erro ao obter URL de arquivo existente no Supabase ({field_type}, {unique_filename_local}): {str(e_url)}", exc_info=True)
                return None
        logger.error(f"EXCEÇÃO NO UPLOAD PARA SUPABASE ({field_type}) para {filename_for_log} (tentativa como {unique_filename_local}): {str(e)}", exc_info=True)
        return None

def arquivo_permitido(nome_arquivo):
    return '.' in nome_arquivo and \
           nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_slug(slug):
    return bool(re.match(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$', slug))


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
        logger.error(f"Erro ao verificar existência do slug '{slug}': {str(e)}")
        return True

def generate_unique_slug(base_slug, user_id=None):
    slug = base_slug.lower().replace(' ', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')

    if not slug:
        slug = f"user-{uuid4().hex[:6]}"
    if not is_valid_slug(slug):
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
    if isinstance(value, str):
        if re.match(r'^#(?:[0-9a-fA-F]{3,4}){1,2}$', value) or \
           re.match(r'^[a-zA-Z]+$', value) or \
           re.match(r'^(?:rgb|rgba|hsl|hsla)\([\d\s,%.a-zA-Z/-]+\)$', value, re.IGNORECASE) or \
           value == 'transparent':
            return value
        cleaned_value = re.sub(r'[^\w\s,\-\'_"%.()/]', '', value)
        cleaned_value = cleaned_value.replace(';', '').replace(':', '').replace('{', '').replace('}', '')
        if "javascript" in cleaned_value.lower():
            return ""
        return cleaned_value
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
            def get_storage_filename(url):
                if url and isinstance(url, str) and supabase.storage.from_("usuarios").get_public_url("").startswith(url.rsplit('/',1)[0]):
                    return url.split('/')[-1].split('?')[0]
                return None

            for field in ['foto', 'background']:
                filename = get_storage_filename(user_data.get(field))
                if filename: files_to_delete.append(filename)

            if user_data.get('card_background_type') == 'image':
                filename = get_storage_filename(user_data.get('card_background_value'))
                if filename: files_to_delete.append(filename)

            custom_buttons_str = user_data.get('custom_buttons', '[]')
            try:
                custom_buttons_list = json.loads(custom_buttons_str) if isinstance(custom_buttons_str, str) else custom_buttons_str
                if isinstance(custom_buttons_list, list):
                    for button in custom_buttons_list:
                        if isinstance(button, dict) and button.get('iconType') == 'image_uploaded' and button.get('iconUrl'):
                            filename = get_storage_filename(button.get('iconUrl'))
                            if filename: files_to_delete.append(filename)
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar custom_buttons para deleção de arquivos do usuário {user_id}")


            if files_to_delete:
                try:
                    valid_files_to_delete = [f for f in files_to_delete if f and '/' not in f]
                    if valid_files_to_delete:
                         supabase.storage.from_("usuarios").remove(valid_files_to_delete)
                         logger.info(f"Arquivos de storage removidos para o usuário {user_id}: {valid_files_to_delete}")
                except Exception as e_storage:
                    logger.error(f"Erro ao remover arquivos do storage para usuário {user_id}: {str(e_storage)}")

        response_db_delete = supabase.table('usuarios').delete().eq('id', user_id).execute()
        affected_rows = len(response_db_delete.data) if hasattr(response_db_delete, 'data') and response_db_delete.data is not None else 0
        logger.info(f"Usuário {user_id} deletado da tabela 'usuarios'. Registros afetados: {affected_rows}.")
        if affected_rows == 0:
            logger.warning(f"Nenhum registro encontrado na tabela 'usuarios' para deletar o ID: {user_id}")

        try:
            supabase_admin_key = os.getenv("SUPABASE_SERVICE_KEY")
            if not supabase_admin_key:
                logger.warning("Chave de serviço SUPABASE_SERVICE_KEY não configurada. Deleção do usuário Auth pulada.")
            elif supabase_admin_key == SUPABASE_KEY:
                logger.warning(f"SUPABASE_SERVICE_KEY é igual a SUPABASE_KEY (pública). Deleção de usuário Auth não permitida para {user_id}.")
            else:
                supabase_admin_client = create_client(SUPABASE_URL, supabase_admin_key)
                supabase_admin_client.auth.admin.delete_user(user_id)
                logger.info(f"Usuário {user_id} (UUID) deletado do Supabase Auth.")
        except Exception as e_auth_delete:
            logger.warning(f"Não foi possível deletar o usuário {user_id} do Supabase Auth: {str(e_auth_delete)}. Pode ser necessário remover manualmente.")

        session.clear()
        flash("✅ Sua página e conta foram apagadas com sucesso.", "success")
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Erro CRÍTICO ao deletar página e conta para o usuário {user_id_to_delete}: {str(e)}", exc_info=True)
        flash("⚠️ Erro ao apagar sua página e conta. Tente novamente ou contate o suporte.", "error")
        return redirect(url_for('admin_panel', username=profile_to_redirect_to_admin) if profile_to_redirect_to_admin else url_for('index') )


@app.route('/')
def index():
    if 'user_id' in session and 'profile' in session:
        pass
    return render_template('index.html')


@app.route('/<profile>')
def user_page(profile):
    if profile == 'favicon.ico' or profile == 'robots.txt' or profile == 'sitemap.xml':
        return abort(404)
    try:
        res = supabase.table('usuarios').select('*').eq('profile', profile).limit(1).single().execute()

        if not res.data:
            logger.warning(f"Perfil público não encontrado: {profile}")
            abort(404)

        user_data = res.data
        view_type = request.args.get('view')

        og_image_to_pass = user_data.get('foto')
        og_title_to_pass = user_data.get('nome', 'Perfil Pessoal')
        raw_bio = user_data.get('bio', 'Confira esta página!')
        cleaned_bio = re.sub(r'<[^>]+>', '', raw_bio) if raw_bio else 'Confira esta página!'
        og_description_to_pass = (cleaned_bio[:150] + '...') if len(cleaned_bio) > 150 else cleaned_bio

        if view_type == 'card':
            card_name_for_og_title = user_data.get('card_nome', user_data.get('nome', 'Usuário'))
            og_title_to_pass = f"Cartão de Visita: {card_name_for_og_title}"
            card_desc_parts_og = []
            if user_data.get('card_titulo'): card_desc_parts_og.append(user_data['card_titulo'])
            if user_data.get('card_registro_profissional'): card_desc_parts_og.append(user_data['card_registro_profissional'])
            if user_data.get('card_endereco'): card_desc_parts_og.append(user_data['card_endereco'])
            specific_card_desc_og = " | ".join(card_desc_parts_og) if card_desc_parts_og else f"Acesse o cartão de visita de {card_name_for_og_title}."
            og_description_to_pass = (specific_card_desc_og[:150] + '...') if len(specific_card_desc_og) > 150 else specific_card_desc_og

        user_data.setdefault('nome_font', app.config['DEFAULT_FONT'])
        user_data.setdefault('nome_color', app.config['DEFAULT_TEXT_COLOR_PAGE'])
        user_data.setdefault('bio_font', app.config['DEFAULT_FONT'])
        user_data.setdefault('bio_color', app.config['DEFAULT_BIO_COLOR_PAGE'])
        user_data.setdefault('card_nome_font', app.config['DEFAULT_FONT'])
        user_data.setdefault('card_nome_color', app.config['DEFAULT_TEXT_COLOR_CARD'])
        user_data.setdefault('card_titulo_font', app.config['DEFAULT_FONT'])
        user_data.setdefault('card_titulo_color', app.config['DEFAULT_TITLE_COLOR_CARD'])
        user_data.setdefault('card_registro_font', app.config['DEFAULT_FONT'])
        user_data.setdefault('card_registro_color', app.config['DEFAULT_REG_COLOR_CARD'])
        user_data.setdefault('card_link_text_color', app.config['DEFAULT_CARD_LINK_TEXT_COLOR'])
        user_data.setdefault('card_endereco', '')
        user_data.setdefault('card_endereco_font', app.config['DEFAULT_FONT'])
        user_data.setdefault('card_endereco_color', app.config['DEFAULT_CARD_ENDERECO_COLOR'])
        user_data.setdefault('card_background_type', 'color')
        user_data.setdefault('card_background_value', app.config['DEFAULT_CARD_BG_COLOR'])
        if user_data['card_background_type'] == 'color' and not re.match(r'^#(?:[0-9a-fA-F]{3,4}){1,2}$', str(user_data.get('card_background_value',''))):
            user_data['card_background_value'] = app.config['DEFAULT_CARD_BG_COLOR']

        user_data.setdefault('background_type', app.config['DEFAULT_BACKGROUND_TYPE'])
        user_data.setdefault('background_image_darken_level', app.config['DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL'])
        user_data.setdefault('background_color_value', app.config['DEFAULT_BACKGROUND_COLOR_VALUE'])
        if not user_data.get('background'):
            user_data['background'] = ''


        for key_json in ['custom_buttons', 'social_links', 'card_links']:
            current_value = user_data.get(key_json)
            if current_value:
                try:
                    if isinstance(current_value, str):
                        parsed_value = json.loads(current_value)
                    elif isinstance(current_value, list):
                        parsed_value = current_value
                    else:
                        parsed_value = []
                    user_data[key_json] = parsed_value

                    if key_json == 'custom_buttons' and isinstance(user_data[key_json], list):
                        for button in user_data[key_json]:
                            if isinstance(button, dict):
                                button.setdefault('bold', False); button.setdefault('italic', False); button.setdefault('hasBorder', False)
                                if 'hoverEffectType' not in button:
                                    if button.get('hasHoverEffect') is True:
                                        button['hoverEffectType'] = 'elevate'
                                    else:
                                        button['hoverEffectType'] = app.config['DEFAULT_BUTTON_HOVER_EFFECT_TYPE']
                                button.pop('hasHoverEffect', None)

                                button.setdefault('fontSize', 16); button.setdefault('borderWidth', 2)
                                button.setdefault('textColor', '#FFFFFF'); button.setdefault('borderColor', '#000000'); button.setdefault('shadowType', 'none')
                                button.setdefault('opacity', app.config['DEFAULT_BUTTON_OPACITY'])
                                button.setdefault('iconUrl', app.config['DEFAULT_BUTTON_ICON_URL'])
                                button.setdefault('iconType', app.config['DEFAULT_BUTTON_ICON_TYPE'])
                                button.setdefault('iconRounded', app.config['DEFAULT_BUTTON_ICON_ROUNDED'])
                                button.setdefault('buttonStyle', app.config['DEFAULT_BUTTON_STYLE'])
                                button.setdefault('shadowDepth', app.config['DEFAULT_BUTTON_SHADOW_DEPTH']) # NOVO: Garantir que existe

                    if key_json == 'card_links' and isinstance(user_data[key_json], list):
                        for link_item in user_data[key_json]:
                             if isinstance(link_item, dict):
                                link_item.setdefault('font', app.config['DEFAULT_FONT'])
                                link_item.setdefault('color', user_data.get('card_link_text_color', app.config['DEFAULT_TEXT_COLOR_CARD']))
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar JSON para '{key_json}' no perfil {profile}: {str(e)}. Usando lista vazia.")
                    user_data[key_json] = []
            else:
                user_data[key_json] = []

        response = make_response(render_template('user_page.html',
                                                dados=user_data,
                                                DEFAULT_FONT=app.config['DEFAULT_FONT'],
                                                DEFAULT_TEXT_COLOR_PAGE=app.config['DEFAULT_TEXT_COLOR_PAGE'],
                                                DEFAULT_BIO_COLOR_PAGE=app.config['DEFAULT_BIO_COLOR_PAGE'],
                                                DEFAULT_TEXT_COLOR_CARD=app.config['DEFAULT_TEXT_COLOR_CARD'],
                                                DEFAULT_TITLE_COLOR_CARD=app.config['DEFAULT_TITLE_COLOR_CARD'],
                                                DEFAULT_REG_COLOR_CARD=app.config['DEFAULT_REG_COLOR_CARD'],
                                                DEFAULT_CARD_LINK_TEXT_COLOR=app.config['DEFAULT_CARD_LINK_TEXT_COLOR'],
                                                DEFAULT_CARD_ENDERECO_COLOR=app.config['DEFAULT_CARD_ENDERECO_COLOR'],
                                                DEFAULT_BACKGROUND_TYPE=app.config['DEFAULT_BACKGROUND_TYPE'],
                                                DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL=app.config['DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL'],
                                                DEFAULT_BACKGROUND_COLOR_VALUE=app.config['DEFAULT_BACKGROUND_COLOR_VALUE'],
                                                DEFAULT_BUTTON_SHADOW_DEPTH=app.config['DEFAULT_BUTTON_SHADOW_DEPTH'], # NOVO: Passar para o template
                                                og_image=og_image_to_pass,
                                                og_title=og_title_to_pass,
                                                og_description=og_description_to_pass))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        if hasattr(e, 'message') and "PGRST116" in e.message:
            logger.warning(f"Perfil público não encontrado (PGRST116 Supabase): {profile}")
            abort(404)
        logger.error(f"Erro ao carregar perfil público {profile}: {str(e)}", exc_info=True)
        abort(500)


@app.route('/login/google')
def login_google():
    try:
        scheme = 'http'
        if request.headers.get('X-Forwarded-Proto') == 'https' or request.url.startswith('https'):
            scheme = 'https'
        elif not app.debug and request.host not in ['localhost', '127.0.0.1']:
             scheme = 'https'

        redirect_uri = url_for('callback_handler', _external=True, _scheme=scheme)
        logger.info(f"Login Google: redirect_uri gerado: {redirect_uri}")

        auth_response = supabase.auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {
                'redirect_to': redirect_uri
            }
        })
        return redirect(auth_response.url)
    except Exception as e:
        logger.error(f"Erro no início do login com Google: {str(e)}", exc_info=True)
        flash("❌ Ocorreu um erro inesperado durante o processo de login com o Google. Por favor, tente novamente mais tarde.", "error")
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

        user_supabase, access_token_to_store, refresh_token_to_store = None, None, None

        if auth_code:
            logger.info("Callback: Recebido código de autorização. Tentando trocar por sessão.")
            try:
                exchanged_session_response = supabase.auth.exchange_code_for_session({'auth_code': auth_code})
                if exchanged_session_response and exchanged_session_response.user and exchanged_session_response.session:
                    user_supabase = exchanged_session_response.user
                    access_token_to_store = exchanged_session_response.session.access_token
                    refresh_token_to_store = exchanged_session_response.session.refresh_token
                    logger.info(f"Callback: Código trocado com sucesso para usuário ID: {user_supabase.id}")
                else:
                    logger.error("Callback: Falha ao trocar código de autorização por sessão (resposta inválida do Supabase).")
                    return jsonify({"error": "Falha ao trocar código de autorização."}), 401
            except Exception as e:
                logger.error(f"Callback: Exceção ao trocar código de autorização: {str(e)}", exc_info=True)
                return jsonify({"error": "Autenticação falhou durante a troca de código."}), 401

        elif received_access_token:
            logger.info("Callback: Recebido access_token (fluxo implícito/hash). Tentando definir/verificar sessão.")
            try:
                session_response = supabase.auth.set_session(received_access_token, received_refresh_token)
                if session_response and session_response.user:
                     user_supabase = session_response.user
                else:
                    get_user_resp = supabase.auth.get_user(jwt=received_access_token)
                    if get_user_resp and get_user_resp.user:
                        user_supabase = get_user_resp.user
                    else:
                        logger.error("Callback: Falha ao definir sessão ou obter usuário com tokens recebidos.")
                        return jsonify({"error": "Falha ao validar sessão com tokens."}), 401

                access_token_to_store = received_access_token
                refresh_token_to_store = received_refresh_token
                logger.info(f"Callback: Sessão definida/verificada com tokens para usuário ID: {user_supabase.id}")

            except Exception as e:
                logger.error(f"Callback: Exceção ao definir/verificar sessão com tokens: {str(e)}", exc_info=True)
                return jsonify({"error": "Autenticação falhou durante a validação da sessão."}), 401
        else:
            logger.error("Callback: Nenhum token de acesso ou código de autorização fornecido.")
            return jsonify({"error": "Token de acesso ou código de autorização não fornecido."}), 400


        if not user_supabase or not user_supabase.id:
            logger.error("Callback: Falha na autenticação - usuário Supabase não obtido ou ID ausente.")
            return jsonify({"error": "Falha na autenticação do usuário."}), 401

        user_data_db = get_user_by_id(user_supabase.id)

        if not user_data_db:
            logger.info(f"Callback: Novo usuário detectado com ID Supabase: {user_supabase.id}. Criando perfil...")
            base_for_slug = user_supabase.user_metadata.get('full_name', user_supabase.email.split('@')[0] if user_supabase.email else 'usuario')
            profile_slug = generate_unique_slug(base_for_slug)

            new_user_payload = {
                'id': user_supabase.id,
                'nome': user_supabase.user_metadata.get('full_name', user_supabase.email or 'Usuário Anônimo'),
                'profile': profile_slug,
                'email': user_supabase.email,
                'foto': user_supabase.user_metadata.get('avatar_url', ''),
                'active': True,
                'bio': 'Olá! Bem-vindo(a) à minha página pessoal. Edite-me no painel de administração!',
                'social_links': json.dumps([]),
                'custom_buttons': json.dumps([]),
                'card_nome': user_supabase.user_metadata.get('full_name', user_supabase.email or 'Usuário Anônimo'),
                'card_titulo': '', 'card_registro_profissional': '', 'card_links': json.dumps([]),
                'card_background_type': 'color', 'card_background_value': app.config['DEFAULT_CARD_BG_COLOR'],
                'nome_font': app.config['DEFAULT_FONT'], 'nome_color': app.config['DEFAULT_TEXT_COLOR_PAGE'],
                'bio_font': app.config['DEFAULT_FONT'], 'bio_color': app.config['DEFAULT_BIO_COLOR_PAGE'],
                'card_nome_font': app.config['DEFAULT_FONT'], 'card_nome_color': app.config['DEFAULT_TEXT_COLOR_CARD'],
                'card_titulo_font': app.config['DEFAULT_FONT'], 'card_titulo_color': app.config['DEFAULT_TITLE_COLOR_CARD'],
                'card_registro_font': app.config['DEFAULT_FONT'], 'card_registro_color': app.config['DEFAULT_REG_COLOR_CARD'],
                'card_link_text_color': app.config['DEFAULT_CARD_LINK_TEXT_COLOR'],
                'card_endereco': '', 'card_endereco_font': app.config['DEFAULT_FONT'], 'card_endereco_color': app.config['DEFAULT_CARD_ENDERECO_COLOR'],
                'background_type': app.config['DEFAULT_BACKGROUND_TYPE'],
                'background_image_darken_level': app.config['DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL'],
                'background_color_value': app.config['DEFAULT_BACKGROUND_COLOR_VALUE'],
                'background': '',
            }
            try:
                insert_response = supabase.table('usuarios').insert(new_user_payload).execute()
                if not insert_response.data or len(insert_response.data) == 0:
                    logger.error(f"Callback: Falha ao inserir novo usuário no banco de dados 'usuarios'. Resposta Supabase: {insert_response}")
                    return jsonify({"error": "Falha ao criar perfil do usuário no banco de dados."}), 500
                user_data_db = insert_response.data[0]
                logger.info(f"Callback: Novo usuário ID {user_data_db['id']} criado com perfil '{user_data_db['profile']}'.")
            except Exception as e_insert:
                logger.error(f"Callback: Exceção ao inserir novo usuário no banco de dados 'usuarios': {str(e_insert)}", exc_info=True)
                return jsonify({"error": "Erro interno do servidor ao criar perfil."}), 500
        else:
            logger.info(f"Callback: Usuário existente ID {user_data_db['id']} com perfil '{user_data_db['profile']}' logado.")

        session['user_id'] = user_supabase.id
        session['access_token'] = access_token_to_store
        session['refresh_token'] = refresh_token_to_store
        session['profile'] = user_data_db['profile']
        session['logado'] = True

        logger.info(f"Callback: Login bem-sucedido para usuário {user_supabase.id}. Redirecionando para admin/{user_data_db['profile']}.")
        return jsonify({
            "message": "Login bem-sucedido!",
            "redirect": url_for('admin_panel', username=user_data_db['profile']),
            "profile": user_data_db['profile']
        }), 200

    except Exception as e_crit:
        logger.error(f"Erro CRÍTICO não esperado no endpoint /callback: {str(e_crit)}", exc_info=True)
        return jsonify({"error": "Erro interno do servidor durante o callback."}), 500


@app.route('/admin/upload_button_temp_image', methods=['POST'])
def upload_button_temp_image():
    if 'user_id' not in session or not session.get('access_token'):
        return jsonify({"error": "Não autorizado: Sessão inválida."}), 401

    try:
        set_session_response = supabase.auth.set_session(session['access_token'], session.get('refresh_token'))
        current_supabase_user = supabase.auth.get_user().user
        if not current_supabase_user or current_supabase_user.id != session.get('user_id'):
            session.clear()
            return jsonify({"error": "Não autorizado: Sessão Supabase inválida ou expirada."}), 401
        if set_session_response and set_session_response.session and set_session_response.session.access_token != session.get('access_token'):
            session['access_token'] = set_session_response.session.access_token
            if set_session_response.session.refresh_token:
                 session['refresh_token'] = set_session_response.session.refresh_token

    except Exception as e_auth_upload:
        logger.error(f"Erro de autenticação ao tentar fazer upload de imagem de botão: {str(e_auth_upload)}")
        session.clear()
        return jsonify({"error": "Erro de autenticação."}), 401

    user_id_from_session = session['user_id']

    if 'button_image' not in request.files:
        return jsonify({"error": "Nenhum arquivo de imagem encontrado na requisição."}), 400

    file = request.files['button_image']

    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    if file and arquivo_permitido(file.filename):
        try:
            public_url = upload_to_supabase(file, user_id_from_session, 'button_icon')
            if public_url:
                return jsonify({"success": True, "url": public_url}), 200
            else:
                return jsonify({"error": "Falha ao fazer upload da imagem para o Supabase."}), 500
        except Exception as e:
            logger.error(f"Erro durante o upload da imagem do botão para {user_id_from_session}: {str(e)}", exc_info=True)
            return jsonify({"error": f"Erro interno do servidor durante o upload: {str(e)}"}), 500
    else:
        return jsonify({"error": "Tipo de arquivo não permitido."}), 400


@app.route('/admin/<username>', methods=['GET', 'POST'])
def admin_panel(username):
    if 'user_id' not in session or not session.get('access_token'):
        flash("🔒 Sessão inválida ou expirada. Por favor, faça login novamente.", "error")
        session.clear()
        return redirect(url_for('login_google'))

    try:
        set_session_response = supabase.auth.set_session(session['access_token'], session.get('refresh_token'))
        current_supabase_user = supabase.auth.get_user().user

        if not current_supabase_user:
            logger.warning(f"Admin: Sessão Supabase inválida para user_id Flask {session.get('user_id')}. Redirecionando para login.")
            session.clear()
            flash("🔑 Sua sessão expirou. Por favor, faça login novamente.", "error")
            return redirect(url_for('login_google'))

        if set_session_response and set_session_response.session and set_session_response.session.access_token != session.get('access_token'):
            session['access_token'] = set_session_response.session.access_token
            if set_session_response.session.refresh_token:
                 session['refresh_token'] = set_session_response.session.refresh_token
            logger.info(f"Admin: Sessão Supabase refrescada para user_id {current_supabase_user.id}.")

        if current_supabase_user.id != session.get('user_id'):
            logger.error(f"Admin: Discrepância de ID! Flask session ID: {session.get('user_id')}, Supabase Auth ID: {current_supabase_user.id}. Forçando logout.")
            session.clear()
            flash("🚫 Erro de segurança na sessão. Por favor, faça login novamente.", "error")
            return redirect(url_for('login_google'))

    except Exception as e_auth_admin:
        logger.error(f"Admin: Erro ao validar/refrescar sessão Supabase: {str(e_auth_admin)}", exc_info=True)
        session.clear()
        flash(f"🔑 Ocorreu um erro com sua sessão. Por favor, faça login novamente.", "error")
        return redirect(url_for('login_google'))

    user_id_from_session = session['user_id']

    try:
        target_user_res = supabase.table('usuarios').select('id, profile').eq('profile', username).limit(1).single().execute()
        if not target_user_res.data:
            logger.warning(f"Admin: Tentativa de acesso a perfil '{username}' que não existe.")
            abort(404)

        if target_user_res.data['id'] != user_id_from_session:
            logger.warning(f"Admin: Acesso negado. Usuário {user_id_from_session} tentou acessar admin de '{username}' (ID: {target_user_res.data['id']}).")
            flash("🚫 Você não tem permissão para acessar este painel.", "error")
            return redirect(url_for('admin_panel', username=session.get('profile', '')) if session.get('profile') else url_for('login_google'))
    except Exception as e_fetch_target_admin:
        logger.error(f"Admin: Erro ao verificar permissões para o perfil '{username}': {str(e_fetch_target_admin)}", exc_info=True)
        flash("⚠️ Erro ao verificar permissões de acesso.", "warning")
        return redirect(url_for('index'))

    user_data_db = get_user_by_id(user_id_from_session)
    if not user_data_db:
        logger.error(f"Admin: Dados do usuário {user_id_from_session} não encontrados no banco, apesar de autenticado.")
        flash("❌ Erro crítico ao carregar seus dados. Por favor, tente logar novamente.", "error")
        session.clear()
        return redirect(url_for('login_google'))

    user_data_db.setdefault('nome_font', app.config['DEFAULT_FONT'])
    user_data_db.setdefault('nome_color', app.config['DEFAULT_TEXT_COLOR_PAGE'])
    user_data_db.setdefault('bio_font', app.config['DEFAULT_FONT'])
    user_data_db.setdefault('bio_color', app.config['DEFAULT_BIO_COLOR_PAGE'])
    user_data_db.setdefault('card_nome_font', app.config['DEFAULT_FONT'])
    user_data_db.setdefault('card_nome_color', app.config['DEFAULT_TEXT_COLOR_CARD'])
    user_data_db.setdefault('card_titulo_font', app.config['DEFAULT_FONT'])
    user_data_db.setdefault('card_titulo_color', app.config['DEFAULT_TITLE_COLOR_CARD'])
    user_data_db.setdefault('card_registro_font', app.config['DEFAULT_FONT'])
    user_data_db.setdefault('card_registro_color', app.config['DEFAULT_REG_COLOR_CARD'])
    user_data_db.setdefault('card_link_text_color', app.config['DEFAULT_CARD_LINK_TEXT_COLOR'])
    user_data_db.setdefault('card_endereco', '')
    user_data_db.setdefault('card_endereco_font', app.config['DEFAULT_FONT'])
    user_data_db.setdefault('card_endereco_color', app.config['DEFAULT_CARD_ENDERECO_COLOR'])
    user_data_db.setdefault('card_background_type', 'color')
    user_data_db.setdefault('card_background_value', app.config['DEFAULT_CARD_BG_COLOR'])
    if user_data_db['card_background_type'] == 'color' and not re.match(r'^#(?:[0-9a-fA-F]{3,4}){1,2}$', str(user_data_db.get('card_background_value',''))):
        user_data_db['card_background_value'] = app.config['DEFAULT_CARD_BG_COLOR']

    user_data_db.setdefault('background_type', app.config['DEFAULT_BACKGROUND_TYPE'])
    user_data_db.setdefault('background_image_darken_level', app.config['DEFAULT_BACKGROUND_IMAGE_DARKEN_LEVEL'])
    user_data_db.setdefault('background_color_value', app.config['DEFAULT_BACKGROUND_COLOR_VALUE'])
    if not user_data_db.get('background'):
            user_data_db['background'] = ''


    for key_json in ['custom_buttons', 'social_links', 'card_links']:
        current_value_admin = user_data_db.get(key_json)
        if current_value_admin:
            try:
                if isinstance(current_value_admin, str):
                    user_data_db[key_json] = json.loads(current_value_admin)
                elif not isinstance(current_value_admin, list):
                    user_data_db[key_json] = []

                if isinstance(user_data_db[key_json], list):
                    if key_json == 'custom_buttons':
                        for button in user_data_db[key_json]:
                            if isinstance(button, dict):
                                button.setdefault('bold', False); button.setdefault('italic', False); button.setdefault('hasBorder', False)

                                if 'hoverEffectType' not in button:
                                    if button.get('hasHoverEffect') is True:
                                        button['hoverEffectType'] = 'elevate'
                                    else:
                                        button['hoverEffectType'] = app.config['DEFAULT_BUTTON_HOVER_EFFECT_TYPE']
                                button.pop('hasHoverEffect', None)

                                button.setdefault('fontSize', 16); button.setdefault('borderWidth', 2)
                                button.setdefault('textColor', '#FFFFFF'); button.setdefault('borderColor', '#000000'); button.setdefault('shadowType', 'none')
                                button.setdefault('opacity', app.config['DEFAULT_BUTTON_OPACITY'])
                                button.setdefault('iconUrl', app.config['DEFAULT_BUTTON_ICON_URL'])
                                button.setdefault('iconType', app.config['DEFAULT_BUTTON_ICON_TYPE'])
                                button.setdefault('iconRounded', app.config['DEFAULT_BUTTON_ICON_ROUNDED'])
                                button.setdefault('buttonStyle', app.config['DEFAULT_BUTTON_STYLE'])
                                button.setdefault('shadowDepth', app.config['DEFAULT_BUTTON_SHADOW_DEPTH']) # NOVO: Garantir que existe ao carregar
                    elif key_json == 'card_links':
                        for link_item in user_data_db[key_json]:
                            if isinstance(link_item, dict):
                                link_item.setdefault('font', app.config['DEFAULT_FONT'])
                                link_item.setdefault('color', user_data_db.get('card_link_text_color', app.config['DEFAULT_TEXT_COLOR_CARD']))
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                user_data_db[key_json] = []
        else:
            user_data_db[key_json] = []


    if request.method == 'POST':
        try:
            update_data = {
                'nome': request.form.get('nome', user_data_db.get('nome')),
                'bio': request.form.get('bio', user_data_db.get('bio')),
                'profile': request.form.get('profile', user_data_db.get('profile')).strip().lower(),
                'card_nome': request.form.get('card_nome', user_data_db.get('card_nome')),
                'card_titulo': request.form.get('card_titulo', user_data_db.get('card_titulo')),
                'card_registro_profissional': request.form.get('card_registro_profissional', user_data_db.get('card_registro_profissional')),
                'card_background_type': request.form.get('card_background_type', user_data_db.get('card_background_type')),
                'nome_font': request.form.get('nome_font', user_data_db.get('nome_font')),
                'nome_color': request.form.get('nome_color', user_data_db.get('nome_color')),
                'bio_font': request.form.get('bio_font', user_data_db.get('bio_font')),
                'bio_color': request.form.get('bio_color', user_data_db.get('bio_color')),
                'card_nome_font': request.form.get('card_nome_font', user_data_db.get('card_nome_font')),
                'card_nome_color': request.form.get('card_nome_color', user_data_db.get('card_nome_color')),
                'card_titulo_font': request.form.get('card_titulo_font', user_data_db.get('card_titulo_font')),
                'card_titulo_color': request.form.get('card_titulo_color', user_data_db.get('card_titulo_color')),
                'card_registro_font': request.form.get('card_registro_font', user_data_db.get('card_registro_font')),
                'card_registro_color': request.form.get('card_registro_color', user_data_db.get('card_registro_color')),
                'card_link_text_color': request.form.get('card_link_text_color', user_data_db.get('card_link_text_color')),
                'card_endereco': request.form.get('card_endereco', user_data_db.get('card_endereco')),
                'card_endereco_font': request.form.get('card_endereco_font', user_data_db.get('card_endereco_font')),
                'card_endereco_color': request.form.get('card_endereco_color', user_data_db.get('card_endereco_color')),
                'background_type': request.form.get('background_type_page', user_data_db.get('background_type')),
                'background_image_darken_level': float(request.form.get('background_image_darken_level_page', user_data_db.get('background_image_darken_level', 0.0))),
                'background_color_value': request.form.get('background_color_value_page', user_data_db.get('background_color_value')),
            }

            novo_profile = update_data['profile']
            if not novo_profile or not is_valid_slug(novo_profile):
                flash("❌ URL de perfil inválida. Use apenas letras minúsculas (sem acentos), números e hífens. Não pode começar ou terminar com hífen.", "error")
                form_data_for_repopulation = user_data_db.copy()
                form_data_for_repopulation.update(request.form.to_dict(flat=True))
                for key_json_repop in ['social_links', 'custom_buttons', 'card_links']:
                     form_data_for_repopulation[key_json_repop] = json.loads(user_data_db.get(key_json_repop, '[]'))
                return render_template('admin.html', dados=form_data_for_repopulation, **app.config)


            if novo_profile != username and slug_exists(novo_profile, user_id_from_session):
                flash(f"❌ A URL de perfil '{novo_profile}' já está em uso. Por favor, escolha outra.", "error")
                update_data['profile'] = username
                form_data_for_repopulation_slug_error = user_data_db.copy()
                form_data_for_repopulation_slug_error.update(update_data)
                for key_json_repop_slug in ['social_links', 'custom_buttons', 'card_links']:
                     form_data_for_repopulation_slug_error[key_json_repop_slug] = json.loads(user_data_db.get(key_json_repop_slug, '[]'))
                return render_template('admin.html', dados=form_data_for_repopulation_slug_error, **app.config)

            if update_data['card_background_type'] == 'color':
                update_data['card_background_value'] = request.form.get('card_background_value_color', app.config['DEFAULT_CARD_BG_COLOR'])
            elif update_data['card_background_type'] == 'image':
                update_data['card_background_value'] = user_data_db.get('card_background_value', '')

            background_file = request.files.get('background_upload')
            if background_file and background_file.filename != '' and arquivo_permitido(background_file.filename):
                file_url = upload_to_supabase(background_file, user_id_from_session, 'background')
                if file_url:
                    update_data['background'] = file_url
                else:
                    flash("❌ Erro no upload da imagem de fundo da página.", "error")
                    update_data['background'] = user_data_db.get('background', '')
            elif not user_data_db.get('background') and not background_file:
                 update_data['background'] = ''
            else:
                update_data['background'] = user_data_db.get('background', '')


            if update_data['background_type'] == 'color':
                if not update_data['background_color_value']:
                    update_data['background_color_value'] = app.config['DEFAULT_BACKGROUND_COLOR_VALUE']
                if not background_file or background_file.filename == '':
                    update_data['background'] = ''
            elif update_data['background_type'] == 'image':
                if not update_data.get('background') and not user_data_db.get('background'):
                     update_data['background_color_value'] = user_data_db.get('background_color_value', app.config['DEFAULT_BACKGROUND_COLOR_VALUE'])
                else:
                    update_data['background_color_value'] = user_data_db.get('background_color_value', app.config['DEFAULT_BACKGROUND_COLOR_VALUE'])


            social_links_list = []
            sc_names = request.form.getlist('social_icon_name[]')
            sc_urls = request.form.getlist('social_icon_url[]')
            for i in range(len(sc_names)):
                social_links_list.append({'icon': sc_names[i], 'url': sc_urls[i].strip() if i < len(sc_urls) else ''})
            update_data['social_links'] = json.dumps(social_links_list)

            custom_buttons_list = []
            btn_texts = request.form.getlist('custom_button_text[]')
            btn_links = request.form.getlist('custom_button_link[]')
            btn_colors = request.form.getlist('custom_button_color[]')
            btn_radii = request.form.getlist('custom_button_radius[]')
            btn_text_colors = request.form.getlist('custom_button_text_color[]')
            btn_bolds = request.form.getlist('custom_button_text_bold[]')
            btn_italics = request.form.getlist('custom_button_text_italic[]')
            btn_font_sizes = request.form.getlist('custom_button_font_size[]')
            btn_has_borders = request.form.getlist('custom_button_has_border[]')
            btn_border_colors = request.form.getlist('custom_button_border_color[]')
            btn_border_widths = request.form.getlist('custom_button_border_width[]')
            btn_hover_effect_types = request.form.getlist('custom_button_hover_effect_type[]')
            btn_shadow_types = request.form.getlist('custom_button_shadow_type[]')
            btn_opacities = request.form.getlist('custom_button_opacity[]')
            btn_icon_urls = request.form.getlist('custom_button_icon_url[]')
            btn_icon_types = request.form.getlist('custom_button_icon_type[]')
            btn_icon_roundeds = request.form.getlist('custom_button_icon_rounded[]')
            btn_styles = request.form.getlist('custom_button_style[]')
            btn_shadow_depths = request.form.getlist('custom_button_shadow_depth[]') # NOVO: Obter profundidades

            for i in range(len(btn_texts)):
                custom_buttons_list.append({
                    'text': btn_texts[i].strip(),
                    'link': btn_links[i].strip() if i < len(btn_links) else '',
                    'color': btn_colors[i] if i < len(btn_colors) else '#4CAF50',
                    'radius': int(btn_radii[i] or 10) if i < len(btn_radii) and btn_radii[i] else 10,
                    'textColor': btn_text_colors[i] or '#FFFFFF' if i < len(btn_text_colors) else '#FFFFFF',
                    'bold': str(btn_bolds[i] or 'false').lower() == 'true' if i < len(btn_bolds) else False,
                    'italic': str(btn_italics[i] or 'false').lower() == 'true' if i < len(btn_italics) else False,
                    'fontSize': int(btn_font_sizes[i] or 16) if i < len(btn_font_sizes) and btn_font_sizes[i] else 16,
                    'hasBorder': str(btn_has_borders[i] or 'false').lower() == 'true' if i < len(btn_has_borders) else False,
                    'borderColor': btn_border_colors[i] or '#000000' if i < len(btn_border_colors) else '#000000',
                    'borderWidth': int(btn_border_widths[i] or 2) if i < len(btn_border_widths) and btn_border_widths[i] else 2,
                    'hoverEffectType': btn_hover_effect_types[i] if i < len(btn_hover_effect_types) else app.config['DEFAULT_BUTTON_HOVER_EFFECT_TYPE'],
                    'shadowType': btn_shadow_types[i] or 'none' if i < len(btn_shadow_types) else 'none',
                    'opacity': float(btn_opacities[i] or app.config['DEFAULT_BUTTON_OPACITY']) if i < len(btn_opacities) and btn_opacities[i] else app.config['DEFAULT_BUTTON_OPACITY'],
                    'iconUrl': btn_icon_urls[i].strip() if i < len(btn_icon_urls) else app.config['DEFAULT_BUTTON_ICON_URL'],
                    'iconType': btn_icon_types[i] if i < len(btn_icon_types) else app.config['DEFAULT_BUTTON_ICON_TYPE'],
                    'iconRounded': str(btn_icon_roundeds[i] or 'false').lower() == 'true' if i < len(btn_icon_roundeds) else app.config['DEFAULT_BUTTON_ICON_ROUNDED'],
                    'buttonStyle': btn_styles[i] if i < len(btn_styles) else app.config['DEFAULT_BUTTON_STYLE'],
                    'shadowDepth': int(btn_shadow_depths[i] or app.config['DEFAULT_BUTTON_SHADOW_DEPTH']) if i < len(btn_shadow_depths) and btn_shadow_depths[i] else app.config['DEFAULT_BUTTON_SHADOW_DEPTH'] # NOVO: Salvar profundidade
                })
            update_data['custom_buttons'] = json.dumps(custom_buttons_list)

            card_links_list = []
            cl_names = request.form.getlist('card_icon_name[]')
            cl_urls = request.form.getlist('card_icon_url[]')
            cl_ats = request.form.getlist('card_icon_at_text[]')
            cl_fonts = request.form.getlist('card_icon_font[]')
            cl_colors = request.form.getlist('card_icon_color[]')
            for i in range(len(cl_names)):
                card_links_list.append({
                    'icon': cl_names[i],
                    'url': cl_urls[i].strip() if i < len(cl_urls) else '',
                    'at_text': cl_ats[i].strip() if i < len(cl_ats) else '',
                    'font': cl_fonts[i] if i < len(cl_fonts) else app.config['DEFAULT_FONT'],
                    'color': cl_colors[i] if i < len(cl_colors) else update_data.get('card_link_text_color', app.config['DEFAULT_TEXT_COLOR_CARD'])
                })
            update_data['card_links'] = json.dumps(card_links_list)

            foto_file = request.files.get('foto_upload')
            if foto_file and foto_file.filename != '' and arquivo_permitido(foto_file.filename):
                file_url = upload_to_supabase(foto_file, user_id_from_session, 'foto')
                if file_url: update_data['foto'] = file_url
                else: flash("❌ Erro no upload da foto de perfil.", "error")

            if update_data['card_background_type'] == 'image':
                card_bg_file = request.files.get('card_background_upload')
                if card_bg_file and card_bg_file.filename != '' and arquivo_permitido(card_bg_file.filename):
                    file_url = upload_to_supabase(card_bg_file, user_id_from_session, 'card_background')
                    if file_url:
                        update_data['card_background_value'] = file_url
                    else:
                        flash("❌ Erro no upload da imagem de fundo do cartão. Revertendo para cor.", "error")
                        update_data['card_background_type'] = 'color'
                        update_data['card_background_value'] = request.form.get('card_background_value_color', app.config['DEFAULT_CARD_BG_COLOR'])
                if request.form.get('remove_card_background_image') == 'true':
                    if user_data_db.get('card_background_type') == 'image' and str(user_data_db.get('card_background_value','')).startswith(f"{SUPABASE_URL}/storage/v1/object/public/usuarios/"):
                        try:
                            filename_to_remove = user_data_db['card_background_value'].split('/')[-1].split('?')[0]
                            supabase.storage.from_("usuarios").remove([filename_to_remove])
                            logger.info(f"Imagem de fundo do cartão '{filename_to_remove}' removida do storage.")
                        except Exception as e_remove_storage:
                            logger.error(f"Erro ao remover imagem de fundo do cartão do storage: {str(e_remove_storage)}")
                    update_data['card_background_type'] = 'color'
                    update_data['card_background_value'] = request.form.get('card_background_value_color', app.config['DEFAULT_CARD_BG_COLOR'])


            db_response = supabase.table('usuarios').update(update_data).eq('id', user_id_from_session).execute()

            if db_response.data:
                logger.info(f"Dados do usuário '{username}' (ID: {user_id_from_session}) atualizados com sucesso.")
                if 'profile' in update_data and update_data['profile'] != username:
                    session['profile'] = update_data['profile']
                    username = update_data['profile']
                flash("✅ Alterações salvas com sucesso!", "success")
                return redirect(url_for('admin_panel', username=username))
            else:
                error_message_supabase = "Erro desconhecido do Supabase."
                if hasattr(db_response, 'error') and db_response.error and hasattr(db_response.error, 'message'):
                    error_message_supabase = db_response.error.message
                logger.error(f"Falha ao salvar dados para '{username}' no Supabase: {error_message_supabase}")
                flash(f"❌ Erro ao salvar os dados no banco de dados: {error_message_supabase}", "error")
                failed_form_data = user_data_db.copy()
                failed_form_data.update(update_data)
                for key_json_fail in ['social_links', 'custom_buttons', 'card_links']:
                    if isinstance(failed_form_data.get(key_json_fail), str):
                        try:
                            failed_form_data[key_json_fail] = json.loads(failed_form_data[key_json_fail])
                        except: failed_form_data[key_json_fail] = []
                    elif not isinstance(failed_form_data.get(key_json_fail), list):
                         failed_form_data[key_json_fail] = []


                return render_template('admin.html', dados=failed_form_data, **app.config)

        except Exception as e_post_general:
            logger.error(f"Erro GERAL durante o POST do admin_panel para '{username}': {str(e_post_general)}", exc_info=True)
            flash(f"⚠️ Ocorreu um erro inesperado ao tentar salvar as alterações: {str(e_post_general)}", "error")
            failed_form_data_general_error = user_data_db.copy()
            for key_form, value_form in request.form.items():
                 if key_form.endswith('[]'):
                    failed_form_data_general_error[key_form.replace('[]','')] = request.form.getlist(key_form)
                 else:
                    failed_form_data_general_error[key_form] = value_form
            for key_json_error in ['social_links', 'custom_buttons', 'card_links']:
                if not isinstance(failed_form_data_general_error.get(key_json_error), list):
                    try:
                        loaded_json = json.loads(user_data_db.get(key_json_error, '[]'))
                        failed_form_data_general_error[key_json_error] = loaded_json if isinstance(loaded_json, list) else []
                    except:
                         failed_form_data_general_error[key_json_error] = []

            return render_template('admin.html', dados=failed_form_data_general_error, **app.config)

    return render_template('admin.html', dados=user_data_db, **app.config)


@app.route('/logout')
def logout():
    user_id_logout = session.get('user_id', 'Desconhecido')
    try:
        if 'access_token' in session:
            supabase.auth.sign_out()
        logger.info(f"Usuário {user_id_logout} deslogado com sucesso do Supabase Auth.")
    except Exception as e_supabase_logout:
        logger.error(f"Erro durante o sign_out do Supabase para o usuário {user_id_logout}: {str(e_supabase_logout)}")
    finally:
        session.clear()
        flash("👋 Você foi desconectado com segurança.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    is_production = os.getenv('FLASK_ENV') == 'production' or bool(os.getenv('PORT'))
    app.run(
        debug=not is_production,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )