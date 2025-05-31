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

# Novos imports para geração de imagem e manipulação de bytes
from playwright.sync_api import sync_playwright
from io import BytesIO
# FileStorage já está importado de werkzeug.datastructures, mas se não estivesse:
# from werkzeug.datastructures import FileStorage


# Configurar loggers de bibliotecas antes de qualquer outra coisa
logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("werkzeug").setLevel(logging.WARNING) # Werkzeug já é gerenciado pelo Flask
logging.getLogger("playwright").setLevel(logging.WARNING) # Logger para Playwright

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

# Constantes de Estilo Padrão (já existentes)
DEFAULT_FONT = "Inter, sans-serif"
DEFAULT_TEXT_COLOR_PAGE = "#333333"
DEFAULT_BIO_COLOR_PAGE = "#555555"
DEFAULT_TEXT_COLOR_CARD = "#FFFFFF"
DEFAULT_TITLE_COLOR_CARD = "#EEEEEE"
DEFAULT_REG_COLOR_CARD = "#BBBBBB"
DEFAULT_CARD_BG_COLOR = "#4361ee"
DEFAULT_CARD_LINK_TEXT_COLOR = "#FFFFFF"

# Adicionar constantes ao app.config para fácil acesso
app.config['DEFAULT_FONT'] = DEFAULT_FONT
app.config['DEFAULT_TEXT_COLOR_CARD'] = DEFAULT_TEXT_COLOR_CARD
app.config['DEFAULT_TITLE_COLOR_CARD'] = DEFAULT_TITLE_COLOR_CARD
app.config['DEFAULT_REG_COLOR_CARD'] = DEFAULT_REG_COLOR_CARD
# ... adicione outras se forem usadas no card_render.html e precisarem ser passadas via app.config


def upload_to_supabase(file, user_id, field_type):
    try:
        # Se 'file' for bytes (da geração de imagem), filename e content_type devem ser passados de outra forma
        # A função atual espera um objeto FileStorage. A simulação cuidará disso.
        if hasattr(file, 'filename'):
            original_filename = secure_filename(file.filename)
            content_type = file.content_type
        else: # Para bytes diretos, esperamos que filename e content_type sejam definidos antes
            original_filename = f"{field_type}.png" # Default filename se não fornecido
            content_type = "image/png" # Default content_type

        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext: # Se a simulação não tiver extensão no nome
            file_ext = ".png" if "png" in content_type else ".jpg" if "jpeg" in content_type else ""

        unique_filename = f"{user_id}_{field_type}_{uuid4().hex[:8]}{file_ext}"
        
        file.seek(0) # Garante que estamos no início do stream/arquivo
        file_bytes = file.read()

        response = supabase.storage.from_("usuarios").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        public_url = supabase.storage.from_("usuarios").get_public_url(unique_filename)
        return public_url
            
    except Exception as e:
        filename_for_log = file.filename if hasattr(file, 'filename') else "generated_image"
        if "Duplicate" in str(e) or "The resource already exists" in str(e):
             logger.warning(f"Arquivo {unique_filename if 'unique_filename' in locals() else filename_for_log} já existe. Tentando obter URL pública. Erro: {str(e)}")
             try:
                # Precisamos do unique_filename para obter a URL existente
                if 'unique_filename' not in locals() and hasattr(file, 'filename'): # Tenta reconstruir se possível
                    _file_ext_temp = os.path.splitext(secure_filename(file.filename))[1].lower()
                    # Esta parte é falha se o nome não for exatamente o mesmo; idealmente upsert=true lida com isso
                    # ou não deveríamos chegar aqui se o upload original foi bem-sucedido.
                    # Para simplificar, vamos assumir que se o erro é duplicado, não precisamos obter a URL de novo aqui
                    # a menos que o upload_to_supabase seja modificado para retornar a URL existente em caso de duplicata.
                    # Por agora, se for duplicata e não tivermos unique_filename, retornamos None.
                    pass # Não podemos obter URL se não soubermos unique_filename
                public_url = supabase.storage.from_("usuarios").get_public_url(unique_filename)
                return public_url
             except Exception as e_url:
                logger.error(f"Erro ao obter URL pública de arquivo existente ({field_type}): {str(e_url)}", exc_info=True)
                return None
        logger.error(f"EXCEÇÃO NO UPLOAD ({field_type}) para o arquivo {filename_for_log} como {unique_filename if 'unique_filename' in locals() else 'desconhecido'}: {str(e)}", exc_info=True)
        return None

# --- NOVA FUNÇÃO PARA GERAR IMAGEM DO CARTÃO ---
def generate_card_image_for_og(user_card_data_dict, user_id_for_file, app_context_param):
    with app_context_param: # Necessário para render_template e url_for funcionarem corretamente
        try:
            # Garante que card_links seja uma lista
            card_links_render = user_card_data_dict.get('card_links', [])
            if isinstance(card_links_render, str):
                try:
                    card_links_render = json.loads(card_links_render)
                except json.JSONDecodeError:
                    card_links_render = []
            if not isinstance(card_links_render, list):
                card_links_render = []
            
            user_card_data_dict['card_links'] = card_links_render # Atualiza para a lista processada

            html_content = render_template('card_render.html',
                                           dados=user_card_data_dict,
                                           DEFAULT_FONT=DEFAULT_FONT,
                                           DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD,
                                           DEFAULT_TITLE_COLOR_CARD=DEFAULT_TITLE_COLOR_CARD,
                                           DEFAULT_REG_COLOR_CARD=DEFAULT_REG_COLOR_CARD,
                                           DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR
                                          )

            with sync_playwright() as p:
                browser = p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox']) # args para ambientes restritos
                page = browser.new_page()
                page.set_viewport_size({"width": 380, "height": 220})
                # Usar wait_until='networkidle' pode ser mais robusto para garantir que fontes/imagens externas carreguem
                page.set_content(html_content, wait_until='networkidle')
                
                card_element = page.query_selector('.card-container')
                if not card_element:
                    logger.error(f"Elemento .card-container não encontrado no card_render.html para user {user_id_for_file}")
                    browser.close()
                    return None

                image_bytes = card_element.screenshot(type='png') # Gera imagem PNG
                browser.close()

            # Prepara para upload
            file_ext = ".png"
            unique_filename_for_upload = f"{user_id_for_file}_card_og_img_{uuid4().hex[:8]}{file_ext}" # Nome do arquivo no storage
            
            file_stream = BytesIO(image_bytes)
            # Simula um objeto FileStorage que a função upload_to_supabase espera
            simulated_file = FileStorage(stream=file_stream, filename=unique_filename_for_upload, content_type='image/png')

            public_url = upload_to_supabase(simulated_file, user_id_for_file, 'card_og_image') # field_type para nomeação
            return public_url
        except Exception as e:
            logger.error(f"Erro CRÍTICO ao gerar/upload imagem OG do cartão para user {user_id_for_file}: {str(e)}", exc_info=True)
            return None
# --- FIM DA NOVA FUNÇÃO ---

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
        return True # Considerar como existente em caso de erro para evitar conflitos

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
    # Implemente uma sanitização mais robusta se necessário, por enquanto, simples replace
    if isinstance(value, str):
        return value.replace(';', '').replace(':', '') # Muito básico, considere uma biblioteca de sanitização CSS
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

        user_data = get_user_by_id(user_id) # Busca os dados ANTES de deletar
        if user_data:
            files_to_delete = []
            # Adiciona foto, background, e card_background_value (se for imagem)
            if user_data.get('foto') and supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['foto'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['foto'].split('/')[-1])
            if user_data.get('background') and supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['background'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['background'].split('/')[-1])
            if user_data.get('card_background_type') == 'image' and user_data.get('card_background_value') and \
               supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['card_background_value'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['card_background_value'].split('/')[-1])
            
            # Adiciona card_og_image_url para deleção
            if user_data.get('card_og_image_url') and supabase.storage.from_("usuarios").get_public_url("").startswith(user_data['card_og_image_url'].rsplit('/',1)[0]):
                files_to_delete.append(user_data['card_og_image_url'].split('/')[-1])

            if files_to_delete:
                try:
                    # Filtra para garantir que são apenas nomes de arquivos
                    valid_files_to_delete = [f.split('?')[0] for f in files_to_delete if f and '/' not in f.split('?')[0]]
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
                logger.warning("Chave de serviço SUPABASE_SERVICE_KEY não configurada. Tentando com a chave anônima, o que pode falhar.")
                supabase_admin_key = SUPABASE_KEY # Fallback para chave anônima, pode não ter permissão

            supabase_admin_client = create_client(SUPABASE_URL, supabase_admin_key) # Requer chave de serviço
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

# --- ROTA USER_PAGE MODIFICADA ---
@app.route('/<profile>')
def user_page(profile):
    if profile == 'favicon.ico': # Ignorar favicon
        return abort(404)
    try:
        res = supabase.table('usuarios').select('*').eq('profile', profile).limit(1).single().execute()
        
        if not res.data:
            logger.warning(f"Perfil público não encontrado: {profile}")
            abort(404)
        
        user_data = res.data
        
        view_type = request.args.get('view')
        card_og_image_url_to_pass = None # Para a tag og:image do cartão
        
        # Preparar título e descrição padrão para OG tags
        og_title_to_pass = user_data.get('nome', 'Perfil Pessoal')
        raw_bio = user_data.get('bio', 'Confira esta página!')
        cleaned_bio = re.sub(r'<[^>]+>', '', raw_bio) if raw_bio else 'Confira esta página!'
        og_description_to_pass = (cleaned_bio[:150] + '...') if len(cleaned_bio) > 150 else cleaned_bio

        if view_type == 'card':
            # Se view=card, ajusta o título e descrição para o cartão
            if user_data.get('card_og_image_url'):
                card_og_image_url_to_pass = user_data['card_og_image_url']
            
            card_name_for_og_title = user_data.get('card_nome', user_data.get('nome', 'Usuário'))
            og_title_to_pass = f"Cartão de Visita: {card_name_for_og_title}"
            
            card_desc_parts_og = []
            if user_data.get('card_titulo'):
                card_desc_parts_og.append(user_data['card_titulo'])
            if user_data.get('card_registro_profissional'):
                card_desc_parts_og.append(user_data['card_registro_profissional'])
            
            specific_card_desc_og = " | ".join(card_desc_parts_og) if card_desc_parts_og else f"Acesse o cartão de visita de {card_name_for_og_title}."
            og_description_to_pass = (specific_card_desc_og[:150] + '...') if len(specific_card_desc_og) > 150 else specific_card_desc_og
        
        # Populando com padrões para exibição na página (sua lógica existente)
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
        user_data['card_link_text_color'] = user_data.get('card_link_text_color') or DEFAULT_CARD_LINK_TEXT_COLOR

        # Processamento de JSON (custom_buttons, social_links, card_links)
        for key_json in ['custom_buttons', 'social_links', 'card_links']:
            if key_json in user_data and user_data[key_json]:
                try:
                    if isinstance(user_data[key_json], str):
                        user_data[key_json] = json.loads(user_data[key_json])
                    
                    # Aplicar padrões aos itens dentro das listas JSON (sua lógica existente)
                    if key_json == 'custom_buttons' and isinstance(user_data[key_json], list):
                        for button in user_data[key_json]: 
                            button.setdefault('bold', False)
                            button.setdefault('italic', False)
                            # ... (outros setdefault para custom_buttons)
                            button.setdefault('hasBorder', False)
                            button.setdefault('hasHoverEffect', False)
                            button.setdefault('fontSize', 16)
                            button.setdefault('borderWidth', 2)
                            button.setdefault('textColor', '#FFFFFF')
                            button.setdefault('borderColor', '#000000')
                            button.setdefault('shadowType', 'none')
                    
                    if key_json == 'card_links' and isinstance(user_data[key_json], list):
                        for link_item in user_data[key_json]:
                            link_item.setdefault('font', DEFAULT_FONT)
                            # A cor do link individual usa o global do cartão como fallback, se não definida no item
                            link_item.setdefault('color', user_data.get('card_link_text_color', DEFAULT_TEXT_COLOR_CARD))
                
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar {key_json} para perfil {profile}: {str(e)}")
                    user_data[key_json] = [] # Define como lista vazia em caso de erro
            else:
                user_data[key_json] = [] # Define como lista vazia se não existir ou for nulo
        
        response = make_response(render_template('user_page.html', 
                                                dados=user_data, 
                                                DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD, 
                                                DEFAULT_FONT=DEFAULT_FONT,
                                                # Passar também outras constantes se user_page.html precisar delas diretamente
                                                DEFAULT_TITLE_COLOR_CARD=DEFAULT_TITLE_COLOR_CARD,
                                                DEFAULT_REG_COLOR_CARD=DEFAULT_REG_COLOR_CARD,
                                                card_og_image_url=card_og_image_url_to_pass, # Nova variável para OG
                                                og_title=og_title_to_pass,                   # Nova variável para OG
                                                og_description=og_description_to_pass        # Nova variável para OG
                                                ))
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
# --- FIM DA ROTA USER_PAGE MODIFICADA ---

@app.route('/login/google')
def login_google():
    try:
        # redirect_url deve ser HTTPS em produção
        scheme = 'https' if not app.debug and request.host != 'localhost' and not request.host.startswith('127.0.0.1') else 'http'
        redirect_url = url_for('callback_handler', _external=True, _scheme=scheme)
        
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
        auth_code = data.get('auth_code') # Recebido do frontend

        user = None
        access_token_to_store = None
        refresh_token_to_store = None

        if auth_code: # Prioriza o auth_code se disponível (mais seguro)
            logger.info(f"Recebido auth_code para processamento.")
            try:
                # Troca o código pela sessão no backend
                exchanged_session_response = supabase.auth.exchange_code_for_session({'auth_code': auth_code})
                if exchanged_session_response and exchanged_session_response.user and exchanged_session_response.session:
                    user = exchanged_session_response.user
                    access_token_to_store = exchanged_session_response.session.access_token
                    refresh_token_to_store = exchanged_session_response.session.refresh_token
                    logger.info(f"Sessão trocada com sucesso via auth_code para user ID: {user.id}")
                else:
                    logger.error("Falha ao trocar código: resposta inválida do Supabase ao trocar código.")
                    return jsonify({"error": "Falha ao trocar código por sessão"}), 401
            except Exception as e_exchange_code:
                logger.error(f"Falha ao trocar código por sessão no Supabase: {str(e_exchange_code)}", exc_info=True)
                return jsonify({"error": "Autenticação com Supabase falhou ao trocar código"}), 401
        
        elif received_access_token: # Fallback se o frontend só enviar tokens
            logger.info(f"Recebido access_token direto para processamento.")
            try:
                # Define a sessão com os tokens recebidos (menos seguro que trocar o código)
                session_response = supabase.auth.set_session(received_access_token, received_refresh_token)
                if session_response and session_response.user: # set_session retorna a sessão, não o usuário diretamente
                     user = session_response.user
                     access_token_to_store = received_access_token # Ou session_response.session.access_token se preferir
                     refresh_token_to_store = received_refresh_token # Ou session_response.session.refresh_token
                     logger.info(f"Sessão definida com token para user ID: {user.id}")
                else:
                    # Se set_session não retornar um usuário, pode ser que o token seja inválido.
                    # Tentar get_user para confirmar.
                    get_user_resp = supabase.auth.get_user(jwt=received_access_token)
                    if get_user_resp and get_user_resp.user:
                        user = get_user_resp.user
                        access_token_to_store = received_access_token
                        refresh_token_to_store = received_refresh_token
                        logger.info(f"Sessão confirmada com get_user e token para user ID: {user.id}")
                    else:
                        logger.error("Falha ao definir/confirmar sessão com token: resposta inválida do Supabase ou token inválido.")
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
            
        user_data = get_user_by_id(user.id) # Busca na tabela 'usuarios'
        
        if not user_data: # Se não existe na tabela 'usuarios', cria o perfil
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
                'card_link_text_color': DEFAULT_CARD_LINK_TEXT_COLOR,
                'card_og_image_url': None # Novo campo
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
        
        # Define a sessão do Flask
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

# --- ROTA ADMIN_PANEL MODIFICADA ---
@app.route('/admin/<username>', methods=['GET', 'POST'])
def admin_panel(username):
    if 'user_id' not in session or not session.get('access_token'):
        flash("🔒 Sua sessão expirou ou é inválida. Por favor, faça login novamente.", "error")
        session.clear()
        return redirect(url_for('login_google'))
    
    try:
        # Tenta validar/restaurar a sessão do Supabase com os tokens da sessão Flask
        set_session_response = supabase.auth.set_session(session['access_token'], session['refresh_token'])
        if not set_session_response or not set_session_response.user: # set_session pode não retornar user diretamente, então checamos com get_user
            user_auth_check = supabase.auth.get_user() # Tenta obter o usuário com o token já setado
            if not user_auth_check or not user_auth_check.user:
                logger.warning(f"Sessão inválida (set_session/get_user falhou) para Flask session user_id {session.get('user_id')}. Deslogando.")
                session.clear()
                flash("🔑 Sua sessão expirou ou não pôde ser validada. Por favor, faça login novamente.", "error")
                return redirect(url_for('login_google'))
            # Se get_user funcionou, atualiza os tokens na sessão Flask se eles mudaram (refresh)
            if set_session_response and set_session_response.session: # Se set_session retornou uma sessão nova
                session['access_token'] = set_session_response.session.access_token
                session['refresh_token'] = set_session_response.session.refresh_token

    except Exception as e_auth: 
        logger.warning(f"Erro ao verificar/restaurar sessão para Flask session user_id {session.get('user_id')}: {str(e_auth)}. Deslogando.", exc_info=True)
        session.clear()
        flash("🔑 Ocorreu um erro com sua sessão. Por favor, faça login novamente.", "error")
        return redirect(url_for('login_google'))

    user_id_from_session = session['user_id']
    
    # Validação de permissão (se o usuário logado pode editar este perfil)
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
        return redirect(url_for('index')) # Ou para um local mais apropriado

    # Carrega os dados do usuário para o formulário
    user_data = get_user_by_id(user_id_from_session) # Este user_data será usado para pegar old_card_og_image_url
    if not user_data:
        logger.error(f"Não foi possível carregar dados para o usuário logado {user_id_from_session} no admin_panel.")
        flash("❌ Erro ao carregar seus dados. Tente fazer login novamente.", "error")
        session.clear()
        return redirect(url_for('login_google'))

    # Populando com padrões para exibição no template (GET)
    # ... (sua lógica existente de popular user_data com padrões) ...
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
        # ... (sua lógica existente de processamento de JSON para GET) ...
        if key_json in user_data and user_data[key_json]:
            try:
                if isinstance(user_data[key_json], str):
                    user_data[key_json] = json.loads(user_data[key_json])
                
                if key_json == 'custom_buttons' and isinstance(user_data[key_json], list):
                    for button in user_data[key_json]:
                        button.setdefault('bold', False)
                        # ... outros setdefault ...
                        button.setdefault('italic', False)
                        button.setdefault('hasBorder', False)
                        button.setdefault('hasHoverEffect', False)
                        button.setdefault('fontSize', 16)
                        button.setdefault('borderWidth', 2)
                        button.setdefault('textColor', '#FFFFFF')
                        button.setdefault('borderColor', '#000000')
                        button.setdefault('shadowType', 'none')

                if key_json == 'card_links' and isinstance(user_data[key_json], list):
                    for link_item in user_data[key_json]:
                        link_item.setdefault('font', DEFAULT_FONT)
                        link_item.setdefault('color', user_data.get('card_link_text_color', DEFAULT_TEXT_COLOR_CARD)) # Usa global como fallback

            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"Erro ao processar {key_json} no admin para {username} (GET): {str(e)}")
                user_data[key_json] = []
        else:
            user_data[key_json] = []


    if request.method == 'POST':
        try:
            update_data = { # Coleta dados do formulário
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
                'card_link_text_color': request.form.get('card_link_text_color', DEFAULT_CARD_LINK_TEXT_COLOR),
            }
            # ... (validação de slug e profile existente - sua lógica) ...
            novo_profile = update_data['profile']
            if not is_valid_slug(novo_profile):
                flash("❌ URL da página inválida. Use apenas letras minúsculas, números e hífens.", "error")
                # ... (lógica de recarregar form com erro)
                current_form_data = user_data.copy() 
                current_form_data.update(request.form.to_dict(flat=False)) # flat=False para listas
                # ... (reprocessar JSONs como no GET ou a partir de inputs hidden) ...
                return render_template('admin.html', dados=current_form_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR, DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD, DEFAULT_FONT=DEFAULT_FONT)

            if novo_profile != username and slug_exists(novo_profile, user_id_from_session):
                flash(f"❌ A URL '{novo_profile}' já está em uso. Escolha outra.", "error")
                # ... (lógica de recarregar form com erro)
                update_data['profile'] = username 
                current_form_data = user_data.copy()
                current_form_data.update(update_data) 
                # ... (reprocessar JSONs como no GET ou a partir de inputs hidden) ...
                return render_template('admin.html', dados=current_form_data, DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR, DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD, DEFAULT_FONT=DEFAULT_FONT)


            # Lógica de card_background_value (color vs image)
            if update_data['card_background_type'] == 'color':
                update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)
            elif update_data['card_background_type'] == 'image':
                update_data['card_background_value'] = user_data.get('card_background_value', '') # Mantém se não houver novo upload
            
            # Processamento de JSONs do form (social_links, custom_buttons, card_links)
            # ... (sua lógica existente para montar listas e fazer json.dumps) ...
            social_links_list = []
            social_icon_names = request.form.getlist('social_icon_name[]')
            # ... (resto da lógica de social_links)
            social_icon_urls = request.form.getlist('social_icon_url[]')
            for i in range(len(social_icon_names)):
                social_links_list.append({'icon': social_icon_names[i], 'url': social_icon_urls[i].strip() if i < len(social_icon_urls) else ''})
            update_data['social_links'] = json.dumps(social_links_list)
            
            custom_buttons_list = []
            button_texts = request.form.getlist('custom_button_text[]')
            # ... (resto da lógica de custom_buttons)
            for i in range(len(button_texts)):
                custom_buttons_list.append({
                    'text': button_texts[i].strip(),
                    'link': request.form.getlist('custom_button_link[]')[i].strip() if i < len(request.form.getlist('custom_button_link[]')) else '',
                    # ... (todos os campos do botão)
                    'color': request.form.getlist('custom_button_color[]')[i] if i < len(request.form.getlist('custom_button_color[]')) else '#4CAF50',
                    'radius': int(request.form.getlist('custom_button_radius[]')[i]) if i < len(request.form.getlist('custom_button_radius[]')) else 10,
                    'textColor': request.form.getlist('custom_button_text_color[]')[i] if i < len(request.form.getlist('custom_button_text_color[]')) else '#FFFFFF',
                    'bold': str(request.form.getlist('custom_button_text_bold[]')[i]).lower() == 'true' if i < len(request.form.getlist('custom_button_text_bold[]')) else False,
                    'italic': str(request.form.getlist('custom_button_text_italic[]')[i]).lower() == 'true' if i < len(request.form.getlist('custom_button_text_italic[]')) else False,
                    'fontSize': int(request.form.getlist('custom_button_font_size[]')[i]) if i < len(request.form.getlist('custom_button_font_size[]')) else 16,
                    'hasBorder': str(request.form.getlist('custom_button_has_border[]')[i]).lower() == 'true' if i < len(request.form.getlist('custom_button_has_border[]')) else False,
                    'borderColor': request.form.getlist('custom_button_border_color[]')[i] if i < len(request.form.getlist('custom_button_border_color[]')) else '#000000',
                    'borderWidth': int(request.form.getlist('custom_button_border_width[]')[i]) if i < len(request.form.getlist('custom_button_border_width[]')) else 2,
                    'hasHoverEffect': str(request.form.getlist('custom_button_has_hover[]')[i]).lower() == 'true' if i < len(request.form.getlist('custom_button_has_hover[]')) else False,
                    'shadowType': request.form.getlist('custom_button_shadow_type[]')[i] if i < len(request.form.getlist('custom_button_shadow_type[]')) else 'none'
                })
            update_data['custom_buttons'] = json.dumps(custom_buttons_list)
            
            card_links_list = []
            card_icon_names = request.form.getlist('card_icon_name[]')
            # ... (resto da lógica de card_links)
            card_icon_urls = request.form.getlist('card_icon_url[]')
            card_icon_at_texts = request.form.getlist('card_icon_at_text[]')
            card_icon_fonts = request.form.getlist('card_icon_font[]') 
            card_icon_colors = request.form.getlist('card_icon_color[]')
            for i in range(len(card_icon_names)):
                link_data = {
                    'icon': card_icon_names[i],
                    'url': card_icon_urls[i].strip() if i < len(card_icon_urls) else '',
                    'at_text': card_icon_at_texts[i].strip() if i < len(card_icon_at_texts) else '',
                    'font': card_icon_fonts[i] if i < len(card_icon_fonts) else DEFAULT_FONT,
                    'color': card_icon_colors[i] if i < len(card_icon_colors) else update_data.get('card_link_text_color', DEFAULT_TEXT_COLOR_CARD) 
                }
                card_links_list.append(link_data)
            update_data['card_links'] = json.dumps(card_links_list)


            # Upload de arquivos (foto, background, card_background)
            # ... (sua lógica de upload de arquivos existente) ...
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
                    else: 
                        flash("❌ Erro ao fazer upload da imagem de fundo do cartão. Usando cor sólida.", "error")
                        update_data['card_background_type'] = 'color'
                        update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)
            
            if request.form.get('remove_card_background_image') == 'true':
                # ... (sua lógica de remover imagem de fundo do cartão) ...
                if user_data.get('card_background_type') == 'image' and str(user_data.get('card_background_value','')).startswith(f"{SUPABASE_URL}/storage/v1/object/public/usuarios/"):
                    try:
                        old_card_bg_filename = user_data['card_background_value'].split('/')[-1].split('?')[0] # Remover query params se houver
                        supabase.storage.from_("usuarios").remove([old_card_bg_filename])
                        logger.info(f"Imagem de fundo do cartão antiga '{old_card_bg_filename}' removida do storage.")
                    except Exception as e_storage_remove:
                        logger.error(f"Erro ao remover imagem de fundo do cartão antiga do storage: {str(e_storage_remove)}")
                update_data['card_background_type'] = 'color'
                update_data['card_background_value'] = request.form.get('card_background_value_color', DEFAULT_CARD_BG_COLOR)


            # Salva os dados principais no banco
            db_response = supabase.table('usuarios').update(update_data).eq('id', user_id_from_session).execute()
            
            if db_response.data:
                logger.info(f"Dados do usuário {username} (ID: {user_id_from_session}) atualizados.")
                updated_user_data_for_card_img = db_response.data[0] # Dados recém atualizados

                # --- INÍCIO DA GERAÇÃO DA IMAGEM OG DO CARTÃO ---
                card_render_payload = {
                    'nome': updated_user_data_for_card_img.get('nome'), # Nome principal do usuário
                    'card_nome': updated_user_data_for_card_img.get('card_nome'),
                    'card_titulo': updated_user_data_for_card_img.get('card_titulo'),
                    'card_registro_profissional': updated_user_data_for_card_img.get('card_registro_profissional'),
                    'card_links': card_links_list, # Usa a lista já processada dos forms
                    'card_background_type': updated_user_data_for_card_img.get('card_background_type'),
                    'card_background_value': updated_user_data_for_card_img.get('card_background_value'),
                    'card_nome_font': updated_user_data_for_card_img.get('card_nome_font', DEFAULT_FONT),
                    'card_nome_color': updated_user_data_for_card_img.get('card_nome_color', DEFAULT_TEXT_COLOR_CARD),
                    'card_titulo_font': updated_user_data_for_card_img.get('card_titulo_font', DEFAULT_FONT),
                    'card_titulo_color': updated_user_data_for_card_img.get('card_titulo_color', DEFAULT_TITLE_COLOR_CARD),
                    'card_registro_font': updated_user_data_for_card_img.get('card_registro_font', DEFAULT_FONT),
                    'card_registro_color': updated_user_data_for_card_img.get('card_registro_color', DEFAULT_REG_COLOR_CARD),
                    'card_link_text_color': updated_user_data_for_card_img.get('card_link_text_color', DEFAULT_CARD_LINK_TEXT_COLOR),
                }
                
                # Passar app.app_context() para render_template e url_for funcionarem fora da requisição direta
                new_card_og_url = generate_card_image_for_og(card_render_payload, user_id_from_session, app.app_context())

                if new_card_og_url:
                    old_card_og_image_url = user_data.get('card_og_image_url') # Pega de user_data ANTES da atualização principal
                    if old_card_og_image_url and old_card_og_image_url.startswith(f"{SUPABASE_URL}/storage/v1/object/public/usuarios/"):
                        try:
                            old_og_filename = old_card_og_image_url.split('/')[-1].split('?')[0]
                            supabase.storage.from_("usuarios").remove([old_og_filename])
                            logger.info(f"Imagem OG do cartão antiga '{old_og_filename}' removida do storage.")
                        except Exception as e_storage_remove_og:
                            logger.error(f"Erro ao remover imagem OG do cartão antiga: {str(e_storage_remove_og)}")
                    
                    supabase.table('usuarios').update({'card_og_image_url': new_card_og_url}).eq('id', user_id_from_session).execute()
                    logger.info(f"Nova imagem OG do cartão gerada e URL salva para user {user_id_from_session}.")
                else:
                    logger.warning(f"Não foi possível gerar a imagem OG do cartão para user {user_id_from_session}.")
                # --- FIM DA GERAÇÃO DA IMAGEM OG DO CARTÃO ---

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
            flash(f"⚠️ Ocorreu um erro inesperado ao salvar. Verifique os logs.", "error")
            # Lógica de recarregar form com dados do POST em caso de erro geral
            failed_update_form_data = user_data.copy() 
            failed_update_form_data.update(request.form.to_dict(flat=False))
            # ... (sua lógica existente para re-popular listas JSON no form em caso de erro) ...
            try:
                failed_update_form_data['social_links'] = json.loads(request.form.get('social_links_json_hidden', json.dumps(user_data.get('social_links', []))))
                failed_update_form_data['custom_buttons'] = json.loads(request.form.get('custom_buttons_json_hidden', json.dumps(user_data.get('custom_buttons', []))))
                # Recriar card_links a partir do form em caso de erro
                temp_card_links_fail = []
                card_icon_names_fail_post = request.form.getlist('card_icon_name[]')
                card_icon_urls_fail_post = request.form.getlist('card_icon_url[]')
                card_icon_at_texts_fail_post = request.form.getlist('card_icon_at_text[]')
                card_icon_fonts_fail_post = request.form.getlist('card_icon_font[]')
                card_icon_colors_fail_post = request.form.getlist('card_icon_color[]')

                for i in range(len(card_icon_names_fail_post)):
                    temp_card_links_fail.append({
                        'icon': card_icon_names_fail_post[i],
                        'url': card_icon_urls_fail_post[i] if i < len(card_icon_urls_fail_post) else '',
                        'at_text': card_icon_at_texts_fail_post[i] if i < len(card_icon_at_texts_fail_post) else '',
                        'font': card_icon_fonts_fail_post[i] if i < len(card_icon_fonts_fail_post) else DEFAULT_FONT,
                        'color': card_icon_colors_fail_post[i] if i < len(card_icon_colors_fail_post) else DEFAULT_TEXT_COLOR_CARD
                    })
                failed_update_form_data['card_links'] = temp_card_links_fail
            except Exception as e_json_fail:
                logger.error(f"Erro ao processar JSON para recarregar formulário após erro: {e_json_fail}")
                # Deixar os campos como estavam em user_data se o JSON do form falhar
                failed_update_form_data['social_links'] = user_data.get('social_links', [])
                failed_update_form_data['custom_buttons'] = user_data.get('custom_buttons', [])
                failed_update_form_data['card_links'] = user_data.get('card_links', [])


            return render_template('admin.html', dados=failed_update_form_data, 
                                   DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR,
                                   DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD,
                                   DEFAULT_FONT=DEFAULT_FONT)

    # Método GET: Renderiza o painel com os dados atuais do usuário
    return render_template('admin.html', 
                           dados=user_data, 
                           DEFAULT_CARD_LINK_TEXT_COLOR=DEFAULT_CARD_LINK_TEXT_COLOR,
                           DEFAULT_TEXT_COLOR_CARD=DEFAULT_TEXT_COLOR_CARD,
                           DEFAULT_FONT=DEFAULT_FONT)
# --- FIM DA ROTA ADMIN_PANEL MODIFICADA ---

@app.route('/logout')
def logout():
    try:
        user_id_logout = session.get('user_id', 'Desconhecido')
        if 'access_token' in session:
            # A SDK do Supabase lida com a invalidação do token localmente e, se possível, no servidor.
            supabase.auth.sign_out() 
            logger.info(f"Usuário {user_id_logout} deslogado do Supabase.")
    except Exception as e:
        logger.error(f"Erro ao tentar deslogar do Supabase para usuário {session.get('user_id', 'Desconhecido')}: {str(e)}")
    finally:
        session.clear() # Limpa a sessão do Flask independentemente do resultado do Supabase
        flash("👋 Você foi desconectado.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    is_production = os.getenv('FLASK_ENV') == 'production'
    # Para produção, use um servidor WSGI como Gunicorn ou Waitress.
    # O app.run() do Flask é para desenvolvimento.
    app.run(debug=not is_production, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))