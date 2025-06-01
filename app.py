from flask import Flask, render_template, request, redirect, session, url_for, abort, jsonify, flash, make_response, send_file
from werkzeug.utils import secure_filename
# from werkzeug.datastructures import FileStorage # Não é mais necessário para card_og_image
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from uuid import uuid4
import json
import os
import re
import logging
from io import BytesIO # Ainda pode ser útil para send_file se você tiver outros downloads

# Removidas importações de Playwright e WeasyPrint

logging.getLogger("httpx").setLevel(logging.WARNING)
# Removido logging de Playwright

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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # Para foto de perfil, fundo da página, fundo do cartão
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

app.config['DEFAULT_FONT'] = DEFAULT_FONT
app.config['DEFAULT_TEXT_COLOR_PAGE'] = DEFAULT_TEXT_COLOR_PAGE
app.config['DEFAULT_BIO_COLOR_PAGE'] = DEFAULT_BIO_COLOR_PAGE
app.config['DEFAULT_TEXT_COLOR_CARD'] = DEFAULT_TEXT_COLOR_CARD
app.config['DEFAULT_TITLE_COLOR_CARD'] = DEFAULT_TITLE_COLOR_CARD
app.config['DEFAULT_REG_COLOR_CARD'] = DEFAULT_REG_COLOR_CARD
app.config['DEFAULT_CARD_BG_COLOR'] = DEFAULT_CARD_BG_COLOR
app.config['DEFAULT_CARD_LINK_TEXT_COLOR'] = DEFAULT_CARD_LINK_TEXT_COLOR
app.config['DEFAULT_CARD_ENDERECO_COLOR'] = DEFAULT_CARD_ENDERECO_COLOR


def upload_to_supabase(file, user_id, field_type):
    try:
        if hasattr(file, 'filename'):
            original_filename = secure_filename(file.filename)
            content_type = file.content_type
        else:
            logger.warning(f"upload_to_supabase chamado com objeto não arquivo para {field_type}")
            return None

        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext: # Fallback
            file_ext = ".png" if "png" in content_type else ".jpg" if "jpeg" in content_type else ""


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
             logger.warning(f"Arquivo {unique_filename_local} já existe. Tentando obter URL. Erro: {str(e)}")
             try:
                if unique_filename_local != 'desconhecido':
                    return supabase.storage.from_("usuarios").get_public_url(unique_filename_local)
                logger.error(f"Não foi possível obter URL para duplicado: {filename_for_log}")
                return None
             except Exception as e_url:
                logger.error(f"Erro ao obter URL de arquivo existente ({field_type}): {str(e_url)}", exc_info=True)
                return None
        logger.error(f"EXCEÇÃO UPLOAD ({field_type}) para {filename_for_log} como {unique_filename_local}: {str(e)}", exc_info=True)
        return None

# Funções get_card_image_bytes (ou get_card_pdf_bytes) e generate_card_image_for_og foram REMOVIDAS.
# A rota /<profile>/download_card_image (ou /<profile>/download_card_pdf) também foi REMOVIDA.

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
    if isinstance(value, str):
        if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value) or \
           re.match(r'^[a-zA-Z]+$', value) or \
           re.match(r'^(?:rgb|rgba|hsl|hsla)\([\d\s,%.]+\)$', value, re.IGNORECASE):
            return value
        cleaned_value = re.sub(r'[^\w\s,\-\'_"]', '', value)
        cleaned_value = cleaned_value.replace(';', '').replace(':', '').replace('(', '').replace(')', '').replace('{', '').replace('}', '')
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
            if user_data.get('foto') and supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['foto'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['foto'].split('/')[-1].split('?')[0])
            if user_data.get('background') and supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['background'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['background'].split('/')[-1].split('?')[0])
            if user_data.get('card_background_type') == 'image' and user_data.get('card_background_value') and \
               supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['card_background_value'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['card_background_value'].split('/')[-1].split('?')[0])
            
            # O campo card_og_image_url não é mais usado para armazenar imagens geradas,
            # então a lógica de apagar do storage foi removida. Se você o usava para algo mais,
            # pode precisar revisar aqui.

            if files_to_delete:
                try:
                    valid_files_to_delete = [f for f in files_to_delete if f and '/' not in f] # Simples verificação
                    if valid_files_to_delete:
                         supabase.storage.from_("usuarios").remove(valid_files_to_delete)
                         logger.info(f"Arquivos de storage removidos para o usuário {user_id}: {valid_files_to_delete}")
                except Exception as e_storage:
                    logger.error(f"Erro ao remover arquivos do storage para usuário {user_id}: {str(e_storage)}")

        response_db_delete = supabase.table('usuarios').delete().eq('id', user_id).execute()
        affected_rows = len(response_db_delete.data) if hasattr(response_db_delete, 'data') and response_db_delete.data is not None else 0
        logger.info(f"Usuário {user_id} deletado da tabela 'usuarios'. Registros afetados: {affected_rows}.")

        try:
            supabase_admin_key = os.getenv("SUPABASE_SERVICE_KEY")
            if not supabase_admin_key:
                logger.warning("Chave de serviço SUPABASE_SERVICE_KEY não configurada.")
                supabase_admin_key = SUPABASE_KEY

            supabase_admin_client = create_client(SUPABASE_URL, supabase_admin_key)
            supabase_admin_client.auth.admin.delete_user(user_id)
            logger.info(f"Usuário {user_id} (UUID) deletado do Supabase Auth.")
        except Exception as e_auth_delete:
            logger.warning(f"Não foi possível deletar o usuário {user_id} do Supabase Auth: {str(e_auth_delete)}")

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
        view_type = request.args.get('view')
        
        # A imagem OG principal será a foto do perfil ou uma imagem padrão do site.
        og_image_to_pass = user_data.get('foto')
        # Exemplo de fallback para uma imagem OG padrão do site:
        # if not og_image_to_pass and os.path.exists(os.path.join(app.static_folder, 'default_og.png')):
        #    og_image_to_pass = url_for('static', filename='default_og.png', _external=True)


        og_title_to_pass = user_data.get('nome', 'Perfil Pessoal')
        raw_bio = user_data.get('bio', 'Confira esta página!')
        cleaned_bio = re.sub(r'<[^>]+>', '', raw_bio) if raw_bio else 'Confira esta página!'
        og_description_to_pass = (cleaned_bio[:150] + '...') if len(cleaned_bio) > 150 else cleaned_bio

        if view_type == 'card':
            # Não há mais uma imagem OG específica do cartão gerada dinamicamente.
            # A og_image_to_pass (foto de perfil ou padrão) será usada.
            card_name_for_og_title = user_data.get('card_nome', user_data.get('nome', 'Usuário'))
            og_title_to_pass = f"Cartão de Visita: {card_name_for_og_title}"

            card_desc_parts_og = []
            if user_data.get('card_titulo'): card_desc_parts_og.append(user_data['card_titulo'])
            if user_data.get('card_registro_profissional'): card_desc_parts_og.append(user_data['card_registro_profissional'])
            if user_data.get('card_endereco'): card_desc_parts_og.append(user_data['card_endereco'])
            specific_card_desc_og = " | ".join(card_desc_parts_og) if card_desc_parts_og else f"Acesse o cartão de visita de {card_name_for_og_title}."
            og_description_to_pass = (specific_card_desc_og[:150] + '...') if len(specific_card_desc_og) > 150 else specific_card_desc_og

        # Preenchimento de defaults para user_data
        user_data['nome_font'] = user_data.get('nome_font') or app.config['DEFAULT_FONT']
        user_data['nome_color'] = user_data.get('nome_color') or app.config['DEFAULT_TEXT_COLOR_PAGE']
        user_data['bio_font'] = user_data.get('bio_font') or app.config['DEFAULT_FONT']
        user_data['bio_color'] = user_data.get('bio_color') or app.config['DEFAULT_BIO_COLOR_PAGE']
        user_data['card_nome_font'] = user_data.get('card_nome_font') or app.config['DEFAULT_FONT']
        user_data['card_nome_color'] = user_data.get('card_nome_color') or app.config['DEFAULT_TEXT_COLOR_CARD']
        user_data['card_titulo_font'] = user_data.get('card_titulo_font') or app.config['DEFAULT_FONT']
        user_data['card_titulo_color'] = user_data.get('card_titulo_color') or app.config['DEFAULT_TITLE_COLOR_CARD']
        user_data['card_registro_font'] = user_data.get('card_registro_font') or app.config['DEFAULT_FONT']
        user_data['card_registro_color'] = user_data.get('card_registro_color') or app.config['DEFAULT_REG_COLOR_CARD']
        user_data['card_link_text_color'] = user_data.get('card_link_text_color') or app.config['DEFAULT_CARD_LINK_TEXT_COLOR']
        user_data['card_endereco'] = user_data.get('card_endereco', '')
        user_data['card_endereco_font'] = user_data.get('card_endereco_font') or app.config['DEFAULT_FONT']
        user_data['card_endereco_color'] = user_data.get('card_endereco_color') or app.config['DEFAULT_CARD_ENDERECO_COLOR']


        for key_json in ['custom_buttons', 'social_links', 'card_links']:
            if key_json in user_data and user_data[key_json]:
                try:
                    if isinstance(user_data[key_json], str):
                        user_data[key_json] = json.loads(user_data[key_json])
                    if key_json == 'custom_buttons' and isinstance(user_data[key_json], list):
                        for button in user_data[key_json]:
                            button.setdefault('bold', False); button.setdefault('italic', False); button.setdefault('hasBorder', False)
                            button.setdefault('hasHoverEffect', False); button.setdefault('fontSize', 16); button.setdefault('borderWidth', 2)
                            button.setdefault('textColor', '#FFFFFF'); button.setdefault('borderColor', '#000000'); button.setdefault('shadowType', 'none')
                    if key_json == 'card_links' and isinstance(user_data[key_json], list):
                        for link_item in user_data[key_json]:
                            link_item.setdefault('font', app.config['DEFAULT_FONT'])
                            link_item.setdefault('color', user_data.get('card_link_text_color', app.config['DEFAULT_TEXT_COLOR_CARD']))
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar {key_json} para perfil {profile}: {str(e)}"); user_data[key_json] = []
            else: user_data[key_json] = []

        response = make_response(render_template('user_page.html',
                                                dados=user_data,
                                                DEFAULT_TEXT_COLOR_CARD=app.config['DEFAULT_TEXT_COLOR_CARD'],
                                                DEFAULT_FONT=app.config['DEFAULT_FONT'],
                                                DEFAULT_TITLE_COLOR_CARD=app.config['DEFAULT_TITLE_COLOR_CARD'],
                                                DEFAULT_REG_COLOR_CARD=app.config['DEFAULT_REG_COLOR_CARD'],
                                                DEFAULT_CARD_LINK_TEXT_COLOR=app.config['DEFAULT_CARD_LINK_TEXT_COLOR'],
                                                DEFAULT_CARD_ENDERECO_COLOR=app.config['DEFAULT_CARD_ENDERECO_COLOR'],
                                                og_image=og_image_to_pass, # Passa a URL da imagem OG principal
                                                og_title=og_title_to_pass,
                                                og_description=og_description_to_pass))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'; response.headers['Pragma'] = 'no-cache'; response.headers['Expires'] = '0'
        return response
    except Exception as e:
        if "PGRST116" in str(e): logger.warning(f"Perfil público não encontrado (PGRST116): {profile}"); abort(404)
        logger.error(f"Erro ao carregar perfil público {profile}: {str(e)}", exc_info=True); abort(500)

@app.route('/login/google')
def login_google():
    # ... (código inalterado) ...
    try:
        scheme = 'https' if not app.debug and request.host != 'localhost' and not request.host.startswith('127.0.0.1') else 'http'
        redirect_url = url_for('callback_handler', _external=True, _scheme=scheme)
        auth_response = supabase.auth.sign_in_with_oauth({'provider': 'google', 'options': {'redirect_to': redirect_url}})
        return redirect(auth_response.url)
    except Exception as e:
        logger.error(f"Erro no login Google: {str(e)}", exc_info=True)
        flash("❌ Ocorreu um erro inesperado durante o login. Tente mais tarde.", "error")
        return redirect(url_for('index'))


@app.route('/callback_handler')
def callback_handler():
    # ... (código inalterado) ...
    return render_template('callback.html')


@app.route('/callback', methods=['POST'])
def callback():
    # ... (código inalterado, mas new_user_payload não terá card_og_image_url preenchido dinamicamente) ...
    try:
        if not request.is_json: return jsonify({"error": "Content-Type deve ser application/json"}), 415
        data = request.get_json(); received_access_token, received_refresh_token, auth_code = data.get('access_token'), data.get('refresh_token'), data.get('auth_code')
        user, access_token_to_store, refresh_token_to_store = None, None, None

        if auth_code:
            try:
                exchanged_session_response = supabase.auth.exchange_code_for_session({'auth_code': auth_code})
                if exchanged_session_response and exchanged_session_response.user and exchanged_session_response.session:
                    user, access_token_to_store, refresh_token_to_store = exchanged_session_response.user, exchanged_session_response.session.access_token, exchanged_session_response.session.refresh_token
                else: return jsonify({"error": "Falha ao trocar código"}), 401
            except Exception as e: logger.error(f"Falha ao trocar código: {str(e)}"); return jsonify({"error": "Autenticação falhou"}), 401
        elif received_access_token:
            try:
                session_response = supabase.auth.set_session(received_access_token, received_refresh_token)
                if session_response and session_response.user:
                     user, access_token_to_store, refresh_token_to_store = session_response.user, received_access_token, received_refresh_token
                else:
                    get_user_resp = supabase.auth.get_user(jwt=received_access_token)
                    if get_user_resp and get_user_resp.user: user, access_token_to_store, refresh_token_to_store = get_user_resp.user, received_access_token, received_refresh_token
                    else: return jsonify({"error": "Falha ao definir sessão"}), 401
            except Exception as e: logger.error(f"Falha ao definir sessão: {str(e)}"); return jsonify({"error": "Autenticação falhou"}), 401
        else: return jsonify({"error": "Token ou código não fornecido"}), 400

        if not user: return jsonify({"error": "Falha na autenticação"}), 401
            
        user_data = get_user_by_id(user.id)
        if not user_data:
            slug = generate_unique_slug(user.user_metadata.get('full_name', user.email.split('@')[0] if user.email else 'usuario'))
            new_user_payload = {
                'id': user.id, 'nome': user.user_metadata.get('full_name', user.email or 'Usuário Anônimo'),
                'profile': slug, 'email': user.email, 'foto': user.user_metadata.get('avatar_url', ''), 'active': True,
                'bio': 'Olá! Bem-vindo(a) à minha página pessoal.', 'social_links': json.dumps([]), 'custom_buttons': json.dumps([]),
                'card_nome': user.user_metadata.get('full_name', user.email or 'Usuário Anônimo'), 'card_titulo': '',
                'card_registro_profissional': '', 'card_links': json.dumps([]), 'card_background_type': 'color',
                'card_background_value': app.config['DEFAULT_CARD_BG_COLOR'], 'nome_font': app.config['DEFAULT_FONT'],
                'nome_color': app.config['DEFAULT_TEXT_COLOR_PAGE'], 'bio_font': app.config['DEFAULT_FONT'],
                'bio_color': app.config['DEFAULT_BIO_COLOR_PAGE'], 'card_nome_font': app.config['DEFAULT_FONT'],
                'card_nome_color': app.config['DEFAULT_TEXT_COLOR_CARD'], 'card_titulo_font': app.config['DEFAULT_FONT'],
                'card_titulo_color': app.config['DEFAULT_TITLE_COLOR_CARD'], 'card_registro_font': app.config['DEFAULT_FONT'],
                'card_registro_color': app.config['DEFAULT_REG_COLOR_CARD'], 'card_link_text_color': app.config['DEFAULT_CARD_LINK_TEXT_COLOR'],
                'card_endereco': '', 'card_endereco_font': app.config['DEFAULT_FONT'], 'card_endereco_color': app.config['DEFAULT_CARD_ENDERECO_COLOR'],
                'card_og_image_url': None # Campo não será mais preenchido dinamicamente pelo sistema
            }
            try:
                insert_response = supabase.table('usuarios').insert(new_user_payload).execute()
                if not insert_response.data: return jsonify({"error": "Falha ao criar perfil no banco"}), 500
                user_data = insert_response.data[0]
            except Exception as e: logger.error(f"Erro ao inserir novo usuário: {str(e)}"); return jsonify({"error": "Erro interno"}), 500
        
        session.update(user_id=user.id, access_token=access_token_to_store, refresh_token=refresh_token_to_store, profile=user_data['profile'], logado=True)
        return jsonify({"message": "Login bem-sucedido!", "redirect": url_for('admin_panel', username=user_data['profile']), "profile": user_data['profile']}), 200
    except Exception as e: logger.error(f"Erro CRÍTICO callback: {str(e)}", exc_info=True); return jsonify({"error": "Erro interno servidor"}), 500


@app.route('/admin/<username>', methods=['GET', 'POST'])
def admin_panel(username):
    # ... (lógica de verificação de sessão e usuário inalterada) ...
    if 'user_id' not in session or not session.get('access_token'):
        flash("🔒 Sessão inválida. Faça login.", "error"); session.clear(); return redirect(url_for('login_google'))
    try:
        set_session_response = supabase.auth.set_session(session['access_token'], session['refresh_token'])
        if not set_session_response or not set_session_response.user: 
            user_auth_check = supabase.auth.get_user() 
            if not user_auth_check or not user_auth_check.user:
                session.clear(); flash("🔑 Sessão expirou. Faça login.", "error"); return redirect(url_for('login_google'))
            if set_session_response and set_session_response.session: 
                session['access_token'] = set_session_response.session.access_token; session['refresh_token'] = set_session_response.session.refresh_token
    except Exception as e_auth: 
        session.clear(); flash("🔑 Erro sessão. Faça login.", "error"); return redirect(url_for('login_google'))

    user_id_from_session = session['user_id']
    try:
        target_user_res = supabase.table('usuarios').select('id, profile').eq('profile', username).limit(1).single().execute()
        if not target_user_res.data: abort(404)
        if target_user_res.data['id'] != user_id_from_session:
            flash("🚫 Acesso negado.", "error"); return redirect(url_for('admin_panel', username=session.get('profile', '')) if session.get('profile') else url_for('login_google'))
    except Exception as e_fetch_target: flash("⚠️ Erro permissões.", "warning"); return redirect(url_for('index')) 

    user_data = get_user_by_id(user_id_from_session) 
    if not user_data:
        flash("❌ Erro carregar dados. Login.", "error"); session.clear(); return redirect(url_for('login_google'))

    # Preenchimento de defaults para user_data (GET)
    user_data['nome_font'] = user_data.get('nome_font') or app.config['DEFAULT_FONT']
    user_data['nome_color'] = user_data.get('nome_color') or app.config['DEFAULT_TEXT_COLOR_PAGE']
    user_data['bio_font'] = user_data.get('bio_font') or app.config['DEFAULT_FONT']
    user_data['bio_color'] = user_data.get('bio_color') or app.config['DEFAULT_BIO_COLOR_PAGE']
    user_data['card_nome_font'] = user_data.get('card_nome_font') or app.config['DEFAULT_FONT']
    user_data['card_nome_color'] = user_data.get('card_nome_color') or app.config['DEFAULT_TEXT_COLOR_CARD']
    user_data['card_titulo_font'] = user_data.get('card_titulo_font') or app.config['DEFAULT_FONT']
    user_data['card_titulo_color'] = user_data.get('card_titulo_color') or app.config['DEFAULT_TITLE_COLOR_CARD']
    user_data['card_registro_font'] = user_data.get('card_registro_font') or app.config['DEFAULT_FONT']
    user_data['card_registro_color'] = user_data.get('card_registro_color') or app.config['DEFAULT_REG_COLOR_CARD']
    user_data['card_link_text_color'] = user_data.get('card_link_text_color') or app.config['DEFAULT_CARD_LINK_TEXT_COLOR']
    user_data['card_background_type'] = user_data.get('card_background_type') or 'color'
    user_data['card_background_value'] = user_data.get('card_background_value') or app.config['DEFAULT_CARD_BG_COLOR']
    user_data['card_endereco'] = user_data.get('card_endereco', '')
    user_data['card_endereco_font'] = user_data.get('card_endereco_font') or app.config['DEFAULT_FONT']
    user_data['card_endereco_color'] = user_data.get('card_endereco_color') or app.config['DEFAULT_CARD_ENDERECO_COLOR']
    if user_data['card_background_type'] == 'color' and not re.match(r'^#[0-9a-fA-F]{6}$', str(user_data.get('card_background_value',''))):
        user_data['card_background_value'] = app.config['DEFAULT_CARD_BG_COLOR']

    for key_json in ['custom_buttons', 'social_links', 'card_links']: # Processamento JSON para GET
        if key_json in user_data and user_data[key_json]:
            try:
                if isinstance(user_data[key_json], str): user_data[key_json] = json.loads(user_data[key_json])
                if key_json == 'custom_buttons' and isinstance(user_data[key_json], list):
                    for button in user_data[key_json]:
                        button.setdefault('bold', False); button.setdefault('italic', False); button.setdefault('hasBorder', False)
                        button.setdefault('hasHoverEffect', False); button.setdefault('fontSize', 16); button.setdefault('borderWidth', 2)
                        button.setdefault('textColor', '#FFFFFF'); button.setdefault('borderColor', '#000000'); button.setdefault('shadowType', 'none')
                if key_json == 'card_links' and isinstance(user_data[key_json], list):
                    for link_item in user_data[key_json]:
                        link_item.setdefault('font', app.config['DEFAULT_FONT']); link_item.setdefault('color', user_data.get('card_link_text_color', app.config['DEFAULT_TEXT_COLOR_CARD']))
            except (json.JSONDecodeError, ValueError, TypeError) as e: user_data[key_json] = []
        else: user_data[key_json] = []

    if request.method == 'POST':
        try:
            update_data = {
                'nome': request.form.get('nome'), 'bio': request.form.get('bio'), 
                'profile': request.form.get('profile', '').strip().lower(),
                'card_nome': request.form.get('card_nome'), 'card_titulo': request.form.get('card_titulo'),
                'card_registro_profissional': request.form.get('card_registro_profissional'),
                'card_background_type': request.form.get('card_background_type'),
                'nome_font': request.form.get('nome_font', app.config['DEFAULT_FONT']),
                'nome_color': request.form.get('nome_color', app.config['DEFAULT_TEXT_COLOR_PAGE']),
                'bio_font': request.form.get('bio_font', app.config['DEFAULT_FONT']),
                'bio_color': request.form.get('bio_color', app.config['DEFAULT_BIO_COLOR_PAGE']),
                'card_nome_font': request.form.get('card_nome_font', app.config['DEFAULT_FONT']),
                'card_nome_color': request.form.get('card_nome_color', app.config['DEFAULT_TEXT_COLOR_CARD']),
                'card_titulo_font': request.form.get('card_titulo_font', app.config['DEFAULT_FONT']),
                'card_titulo_color': request.form.get('card_titulo_color', app.config['DEFAULT_TITLE_COLOR_CARD']),
                'card_registro_font': request.form.get('card_registro_font', app.config['DEFAULT_FONT']),
                'card_registro_color': request.form.get('card_registro_color', app.config['DEFAULT_REG_COLOR_CARD']),
                'card_link_text_color': request.form.get('card_link_text_color', app.config['DEFAULT_CARD_LINK_TEXT_COLOR']),
                'card_endereco': request.form.get('card_endereco', ''),
                'card_endereco_font': request.form.get('card_endereco_font', app.config['DEFAULT_FONT']),
                'card_endereco_color': request.form.get('card_endereco_color', app.config['DEFAULT_CARD_ENDERECO_COLOR']),
                # card_og_image_url não é mais atualizado aqui
            }
            novo_profile = update_data['profile']
            # ... (validações de slug e recarregamento do formulário em caso de erro, como na sua versão original) ...
            if not is_valid_slug(novo_profile):
                flash("❌ URL inválida.", "error")
                current_form_data = user_data.copy(); current_form_data.update(request.form.to_dict(flat=True))
                for key_json_form in ['social_links', 'custom_buttons', 'card_links']:
                    form_val = request.form.get(f'{key_json_form}_json_hidden', json.dumps(user_data.get(key_json_form, [])))
                    try: current_form_data[key_json_form] = json.loads(form_val)
                    except: current_form_data[key_json_form] = user_data.get(key_json_form, [])
                return render_template('admin.html', dados=current_form_data, DEFAULT_FONT=app.config['DEFAULT_FONT'], DEFAULT_TEXT_COLOR_CARD=app.config['DEFAULT_TEXT_COLOR_CARD'], DEFAULT_TITLE_COLOR_CARD=app.config['DEFAULT_TITLE_COLOR_CARD'], DEFAULT_REG_COLOR_CARD=app.config['DEFAULT_REG_COLOR_CARD'], DEFAULT_CARD_LINK_TEXT_COLOR=app.config['DEFAULT_CARD_LINK_TEXT_COLOR'], DEFAULT_CARD_ENDERECO_COLOR=app.config['DEFAULT_CARD_ENDERECO_COLOR'])

            if novo_profile != username and slug_exists(novo_profile, user_id_from_session):
                flash(f"❌ URL '{novo_profile}' em uso.", "error")
                update_data['profile'] = username 
                current_form_data = user_data.copy(); current_form_data.update(update_data)
                for key_json_form in ['social_links', 'custom_buttons', 'card_links']:
                    form_val = request.form.get(f'{key_json_form}_json_hidden', json.dumps(user_data.get(key_json_form, [])))
                    try: current_form_data[key_json_form] = json.loads(form_val)
                    except: current_form_data[key_json_form] = user_data.get(key_json_form, [])
                return render_template('admin.html', dados=current_form_data, DEFAULT_FONT=app.config['DEFAULT_FONT'], DEFAULT_TEXT_COLOR_CARD=app.config['DEFAULT_TEXT_COLOR_CARD'], DEFAULT_TITLE_COLOR_CARD=app.config['DEFAULT_TITLE_COLOR_CARD'], DEFAULT_REG_COLOR_CARD=app.config['DEFAULT_REG_COLOR_CARD'], DEFAULT_CARD_LINK_TEXT_COLOR=app.config['DEFAULT_CARD_LINK_TEXT_COLOR'], DEFAULT_CARD_ENDERECO_COLOR=app.config['DEFAULT_CARD_ENDERECO_COLOR'])


            # ... (lógica de card_background_type, processamento de JSONs e uploads de arquivos inalterada) ...
            if update_data['card_background_type'] == 'color': update_data['card_background_value'] = request.form.get('card_background_value_color', app.config['DEFAULT_CARD_BG_COLOR'])
            elif update_data['card_background_type'] == 'image': update_data['card_background_value'] = user_data.get('card_background_value', '') # Mantém o antigo se não houver novo upload

            social_links_list = []; sc_names = request.form.getlist('social_icon_name[]'); sc_urls = request.form.getlist('social_icon_url[]')
            for i in range(len(sc_names)): social_links_list.append({'icon': sc_names[i], 'url': sc_urls[i].strip() if i < len(sc_urls) else ''})
            update_data['social_links'] = json.dumps(social_links_list)

            custom_buttons_list = []; btn_texts = request.form.getlist('custom_button_text[]')
            for i in range(len(btn_texts)): custom_buttons_list.append({
                'text': btn_texts[i].strip(), 'link': request.form.getlist('custom_button_link[]')[i].strip() if i < len(request.form.getlist('custom_button_link[]')) else '',
                'color': request.form.getlist('custom_button_color[]')[i] if i < len(request.form.getlist('custom_button_color[]')) else '#4CAF50',
                'radius': int(request.form.getlist('custom_button_radius[]')[i] or 10), 'textColor': request.form.getlist('custom_button_text_color[]')[i] or '#FFFFFF',
                'bold': str(request.form.getlist('custom_button_text_bold[]')[i] or 'false').lower() == 'true', 'italic': str(request.form.getlist('custom_button_text_italic[]')[i] or 'false').lower() == 'true',
                'fontSize': int(request.form.getlist('custom_button_font_size[]')[i] or 16), 'hasBorder': str(request.form.getlist('custom_button_has_border[]')[i] or 'false').lower() == 'true',
                'borderColor': request.form.getlist('custom_button_border_color[]')[i] or '#000000', 'borderWidth': int(request.form.getlist('custom_button_border_width[]')[i] or 2),
                'hasHoverEffect': str(request.form.getlist('custom_button_has_hover[]')[i] or 'false').lower() == 'true', 'shadowType': request.form.getlist('custom_button_shadow_type[]')[i] or 'none' })
            update_data['custom_buttons'] = json.dumps(custom_buttons_list)
            
            card_links_list = []; cl_names = request.form.getlist('card_icon_name[]'); cl_urls = request.form.getlist('card_icon_url[]'); cl_ats = request.form.getlist('card_icon_at_text[]')
            cl_fonts = request.form.getlist('card_icon_font[]'); cl_colors = request.form.getlist('card_icon_color[]')
            for i in range(len(cl_names)): card_links_list.append({
                'icon': cl_names[i], 'url': cl_urls[i].strip() if i < len(cl_urls) else '', 'at_text': cl_ats[i].strip() if i < len(cl_ats) else '',
                'font': cl_fonts[i] if i < len(cl_fonts) else app.config['DEFAULT_FONT'], 'color': cl_colors[i] if i < len(cl_colors) else update_data.get('card_link_text_color', app.config['DEFAULT_TEXT_COLOR_CARD']) })
            update_data['card_links'] = json.dumps(card_links_list)

            foto_file = request.files.get('foto_upload')
            if foto_file and foto_file.filename != '' and arquivo_permitido(foto_file.filename):
                file_url = upload_to_supabase(foto_file, user_id_from_session, 'foto')
                if file_url: update_data['foto'] = file_url
                else: flash("❌ Erro upload foto.", "error")
            
            background_file = request.files.get('background_upload')
            if background_file and background_file.filename != '' and arquivo_permitido(background_file.filename):
                file_url = upload_to_supabase(background_file, user_id_from_session, 'background')
                if file_url: update_data['background'] = file_url
                else: flash("❌ Erro upload fundo.", "error")
            
            if update_data['card_background_type'] == 'image':
                card_bg_file = request.files.get('card_background_upload')
                if card_bg_file and card_bg_file.filename != '' and arquivo_permitido(card_bg_file.filename):
                    file_url = upload_to_supabase(card_bg_file, user_id_from_session, 'card_background')
                    if file_url: update_data['card_background_value'] = file_url
                    else: flash("❌ Erro upload fundo cartão.", "error"); update_data['card_background_type'] = 'color'; update_data['card_background_value'] = request.form.get('card_background_value_color', app.config['DEFAULT_CARD_BG_COLOR'])
            
            if request.form.get('remove_card_background_image') == 'true': 
                if user_data.get('card_background_type') == 'image' and str(user_data.get('card_background_value','')).startswith(f"{SUPABASE_URL}/storage/v1/object/public/usuarios/"):
                    try: supabase.storage.from_("usuarios").remove([user_data['card_background_value'].split('/')[-1].split('?')[0]])
                    except Exception as e: logger.error(f"Erro remover fundo cartão storage: {str(e)}")
                update_data['card_background_type'] = 'color'; update_data['card_background_value'] = request.form.get('card_background_value_color', app.config['DEFAULT_CARD_BG_COLOR'])


            db_response = supabase.table('usuarios').update(update_data).eq('id', user_id_from_session).execute()

            if db_response.data:
                logger.info(f"Dados do usuário {username} (ID: {user_id_from_session}) atualizados.")
                if 'profile' in update_data and update_data['profile'] != username:
                    session['profile'] = update_data['profile']
                    username = update_data['profile']
                flash("✅ Alterações salvas com sucesso!", "success")
                return redirect(url_for('admin_panel', username=username))
            else:
                logger.error(f"Falha ao salvar dados para {username}: {db_response.error or 'Erro desconhecido'}")
                flash("❌ Erro ao salvar os dados.", "error")
        
        except Exception as e_post: 
            logger.error(f"Erro GERAL no POST do admin_panel para {username}: {str(e_post)}", exc_info=True)
            flash(f"⚠️ Ocorreu um erro inesperado ao salvar.", "error")
            failed_update_form_data = user_data.copy(); failed_update_form_data.update(request.form.to_dict(flat=True))
            for key_json_form in ['social_links', 'custom_buttons', 'card_links']:
                form_val = request.form.get(f'{key_json_form}_json_hidden', json.dumps(user_data.get(key_json_form, [])))
                try: failed_update_form_data[key_json_form] = json.loads(form_val)
                except: failed_update_form_data[key_json_form] = user_data.get(key_json_form, [])
            return render_template('admin.html', dados=failed_update_form_data, DEFAULT_FONT=app.config['DEFAULT_FONT'], DEFAULT_TEXT_COLOR_CARD=app.config['DEFAULT_TEXT_COLOR_CARD'], DEFAULT_TITLE_COLOR_CARD=app.config['DEFAULT_TITLE_COLOR_CARD'], DEFAULT_REG_COLOR_CARD=app.config['DEFAULT_REG_COLOR_CARD'], DEFAULT_CARD_LINK_TEXT_COLOR=app.config['DEFAULT_CARD_LINK_TEXT_COLOR'], DEFAULT_CARD_ENDERECO_COLOR=app.config['DEFAULT_CARD_ENDERECO_COLOR'])

    return render_template('admin.html', dados=user_data, DEFAULT_FONT=app.config['DEFAULT_FONT'], DEFAULT_TEXT_COLOR_CARD=app.config['DEFAULT_TEXT_COLOR_CARD'], DEFAULT_TITLE_COLOR_CARD=app.config['DEFAULT_TITLE_COLOR_CARD'], DEFAULT_REG_COLOR_CARD=app.config['DEFAULT_REG_COLOR_CARD'], DEFAULT_CARD_LINK_TEXT_COLOR=app.config['DEFAULT_CARD_LINK_TEXT_COLOR'], DEFAULT_CARD_ENDERECO_COLOR=app.config['DEFAULT_CARD_ENDERECO_COLOR'])


@app.route('/logout')
def logout():
    # ... (código inalterado) ...
    try:
        if 'access_token' in session: supabase.auth.sign_out()
        logger.info(f"Usuário {session.get('user_id', 'Desconhecido')} deslogado.")
    except Exception as e: logger.error(f"Erro Supabase logout user {session.get('user_id', 'Desconhecido')}: {str(e)}")
    finally: session.clear(); flash("👋 Você foi desconectado.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    is_production = os.getenv('FLASK_ENV') == 'production'
    app.run(debug=not is_production, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))