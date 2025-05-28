from flask import Flask, render_template, request, redirect, session, url_for, abort, jsonify, flash, make_response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from uuid import uuid4
import json # Importar json
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

# Configuração otimizada do cliente Supabase
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options=ClientOptions(
        postgrest_client_timeout=10,
        headers={
            'Prefer': 'return=representation',
            'Content-Type': 'application/json'
        }
    )
)

# Configurações do app
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def migrate_existing_images():
    users = supabase.table('usuarios').select('*').execute().data
    for user in users:
        updates = {}
        if user.get('foto') and not user['foto'].startswith('http'):
            pass
        if updates:
            supabase.table('usuarios').update(updates).eq('id', user['id']).execute()

def upload_to_supabase(file, user_id, field_type):
    try:
        # Configura autenticação
        headers = {
            "Authorization": f"Bearer {session.get('access_token')}",
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        
        # Gera nome único para o arquivo
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        unique_filename = f"{user_id}_{field_type}{file_ext}"
        
        # Salva temporariamente
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(temp_path)
        
        # Faz upload via API REST diretamente
        upload_url = f"{SUPABASE_URL}/storage/v1/object/usuarios/{unique_filename}"
        with open(temp_path, 'rb') as f:
            response = requests.put(
                upload_url,
                headers=headers,
                data=f,
                params={
                    "content-type": file.content_type,
                    "x-upsert": "true"
                }
            )
        
        os.remove(temp_path)
        
        if response.status_code in [200, 201]:
            return f"{SUPABASE_URL}/storage/v1/object/public/usuarios/{unique_filename}"
        else:
            logger.error(f"Erro no upload: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"ERRO NO UPLOAD ({field_type}): {str(e)}", exc_info=True)
        return None

def arquivo_permitido(nome_arquivo):
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_slug(slug):
    return bool(re.match(r'^[a-z0-9-]+$', slug))

def get_user_by_id(user_id):
    try:
        res = supabase.table('usuarios').select('*').eq('id', user_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {str(e)}")
        return None

def create_user(user_data):
    try:
        headers = {
            "Authorization": f"Bearer {session.get('access_token')}",
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        
        res = supabase.table('usuarios').insert(user_data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return None

def slug_exists(slug):
    try:
        res = supabase.table('usuarios').select('profile').eq('profile', slug).execute()
        return len(res.data) > 0
    except Exception as e:
        logger.error(f"Erro ao verificar slug: {str(e)}")
        return True

def generate_unique_slug(base_slug):
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

@app.template_filter('style_safe')
def style_safe(color, radius):
    return f"background: {color}; border-radius: {radius}px"

@app.route('/delete_page', methods=['POST'])
def delete_page():
    if 'user_id' not in session:
        abort(401)
    
    try:
        user_id = session['user_id']
        headers = {
            "Authorization": f"Bearer {session.get('access_token')}",
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        
        api_url = f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{user_id}"
        response = requests.delete(api_url, headers=headers)
        
        if response.status_code == 204:
            session.clear()
            return redirect(url_for('index'))
        else:
            logger.error(f"Erro ao deletar usuário: {response.text}")
            flash("❌ Erro ao apagar página", "error")
            return redirect(url_for('admin_panel', username=session.get('profile')))
    
    except Exception as e:
        logger.error(f"Erro ao deletar página: {str(e)}")
        flash("⚠️ Erro ao apagar página", "warning")
        return redirect(url_for('admin_panel', username=session.get('profile')))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<profile>')
def user_page(profile):
    if profile == 'favicon.ico':
        return abort(404)
    try:
        res = supabase.table('usuarios').select('*').eq('profile', profile).execute()
        
        if not res.data:
            logger.warning(f"Perfil não encontrado: {profile}")
            abort(404)
        
        user_data = res.data[0]
        # Converter custom_buttons de JSON string para lista/dict
        if 'custom_buttons' in user_data and user_data['custom_buttons']:
            try:
                user_data['custom_buttons'] = json.loads(user_data['custom_buttons'])
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar custom_buttons para o usuário. Inicializando como vazio.")
                user_data['custom_buttons'] = []
        else:
            user_data['custom_buttons'] = []
        
        # Converter social_links de JSON string para lista/dict
        if 'social_links' in user_data and user_data['social_links']:
            try:
                user_data['social_links'] = json.loads(user_data['social_links'])
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar social_links para o usuário. Inicializando como vazio.")
                user_data['social_links'] = []
        else:
            user_data['social_links'] = []

        response = make_response(render_template('user_page.html', dados=user_data))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    except Exception as e:
        logger.error(f"Erro ao carregar perfil {profile}: {str(e)}")
        abort(500)

@app.route('/login/google')
def login_google():
    try:
        redirect_url = url_for('callback_handler', _external=True)
        auth_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to={redirect_url}"
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Erro no login Google: {str(e)}")
        return redirect(url_for('index'))

@app.route('/callback_handler')
def callback_handler():
    return render_template('callback.html')

@app.route('/callback', methods=['GET', 'POST'])
def callback():
    try:
        if request.method == 'POST':
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            access_token = request.json.get('access_token')
        else:
            access_token = request.args.get('access_token')
        
        if not access_token:
            return jsonify({"error": "Token não fornecido"}), 400
        
        supabase.postgrest.auth(access_token)
        user_resp = supabase.auth.get_user(access_token)
        if not user_resp.user:
            return jsonify({"error": "Autenticação falhou"}), 401
            
        user = user_resp.user
        user_data = get_user_by_id(user.id)
        
        if not user_data:
            slug = generate_unique_slug(user.user_metadata.get('full_name', user.email.split('@')[0]))
            new_user = {
                'id': user.id,
                'nome': user.user_metadata.get('full_name', user.email),
                'profile': slug,
                'email': user.email,
                'foto': '',
                'active': True,
                # Removendo campos fixos, eles serão tratados por social_links
                'bio': 'Olá! Esta é minha página pessoal.',
                'social_links': '[]', # Inicializa como array JSON vazio
                'custom_buttons': '[]'  # Inicializa como array JSON vazio
            }
            
            api_url = f"{SUPABASE_URL}/rest/v1/usuarios"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            
            response = requests.post(api_url, json=new_user, headers=headers)
            
            if response.status_code not in [200, 201, 204]:
                return jsonify({"error": "Falha ao criar perfil"}), 500
                
            user_data = response.json()[0] if response.status_code != 204 else new_user
        
        session['user_id'] = user.id
        session['access_token'] = access_token
        session['profile'] = user_data['profile']
        session['logado'] = True
        
        return jsonify({
            "redirect": url_for('admin_panel', username=user_data['profile']),
            "profile": user_data['profile']
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no callback: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno no servidor"}), 500

@app.route('/admin/<username>', methods=['GET', 'POST'])
def admin_panel(username):
    if 'user_id' not in session:
        return redirect(url_for('login_google')) # Redireciona para login do Google
    
    user_data = {} # Inicializa user_data para garantir que exista
    try:
        supabase.postgrest.auth(session['access_token'])
        res = supabase.table('usuarios').select('*').eq('id', session['user_id']).execute()
        
        if not res.data:
            abort(404)
            
        user_data = res.data[0]
        
        # Corrigir a conversão do social_links
        if isinstance(user_data.get('social_links'), str):
            try:
                user_data['social_links'] = json.loads(user_data['social_links'])
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar social_links para o usuário {session['user_id']}. Inicializando como vazio.")
                user_data['social_links'] = []
        elif user_data.get('social_links') is None: # Se for None, inicializa como lista vazia
            user_data['social_links'] = []
        
        # Corrigir a conversão do custom_buttons
        if isinstance(user_data.get('custom_buttons'), str):
            try:
                user_data['custom_buttons'] = json.loads(user_data['custom_buttons'])
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar custom_buttons para o usuário {session['user_id']}. Inicializando como vazio.")
                user_data['custom_buttons'] = []
        elif user_data.get('custom_buttons') is None: # Se for None, inicializa como lista vazia
            user_data['custom_buttons'] = []
        
        if request.method == 'POST':
            update_data = {
                'nome': request.form.get('nome'),
                'bio': request.form.get('bio'),
                'profile': request.form.get('profile')
            }

            # Processar ícones sociais dinâmicos
            social_links = []
            for key, value in request.form.items():
                if key.startswith('social_icon_'):
                    icon_name = key.replace('social_icon_', '')
                    if value and value.startswith(('http://', 'https://')):
                        social_links.append({
                            'icon': icon_name,
                            'url': value
                        })
                    elif value:
                        flash(f"⚠️ O link para {icon_name} deve começar com http:// ou https://", "warning")

            if len(social_links) > 10:
                flash("⚠️ Você pode adicionar no máximo 10 ícones", "warning")
                social_links = social_links[:10]

            # CONVERTER social_links PARA JSON STRING ANTES DE ENVIAR AO SUPABASE
            update_data['social_links'] = json.dumps(social_links)

            # Processar botões personalizados
            custom_buttons = []
            button_texts = request.form.getlist('custom_button_text[]')
            button_links = request.form.getlist('custom_button_link[]')
            button_colors = request.form.getlist('custom_button_color[]')
            button_radii = request.form.getlist('custom_button_radius[]')
            # NOVOS CAMPOS
            button_text_colors = request.form.getlist('custom_button_text_color[]')
            button_text_bolds = request.form.getlist('custom_button_text_bold[]')
            button_text_italics = request.form.getlist('custom_button_text_italic[]')
            button_font_sizes = request.form.getlist('custom_button_font_size[]')
            
            for i in range(len(button_texts)):
                if button_texts[i]:
                    # Garante que os valores booleanos e inteiros sejam armazenados corretamente
                    # O JavaScript envia 'true' ou 'false' como strings, convertemos para booleano
                    bold_val = button_text_bolds[i].lower() == 'true'
                    italic_val = button_text_italics[i].lower() == 'true'
                    font_size_val = int(button_font_sizes[i]) if button_font_sizes[i].isdigit() else 16 # Fallback para int
                    
                    custom_buttons.append({
                        'text': button_texts[i],
                        'link': button_links[i],
                        'color': button_colors[i],
                        'radius': button_radii[i],
                        'textColor': button_text_colors[i],
                        'bold': bold_val,
                        'italic': italic_val,
                        'fontSize': font_size_val
                    })
            
            # CONVERTER custom_buttons PARA JSON STRING ANTES DE ENVIAR AO SUPABASE
            update_data['custom_buttons'] = json.dumps(custom_buttons)

            # Processar uploads
            for field in ['foto', 'background']:
                file = request.files.get(f'{field}_upload')
                if file and arquivo_permitido(file.filename):
                    file_url = upload_to_supabase(file, session['user_id'], field)
                    if file_url:
                        update_data[field] = file_url

            # Atualizar no Supabase
            response = supabase.table('usuarios').update(update_data).eq('id', session['user_id']).execute()
            
            try:
                if response.data:
                    # Atualiza o profile na sessão se foi alterado
                    if 'profile' in update_data and update_data['profile'] != username:
                        session['profile'] = update_data['profile']
                    
                    # Redireciona para a página do usuário com cache busting
                    profile = update_data.get('profile', username)
                    flash("✅ Alterações salvas com sucesso!", "success")
                    return redirect(f"{url_for('user_page', profile=profile)}?v={uuid4().hex[:8]}")
                else:
                    flash("❌ Nenhum dado foi retornado ao salvar", "error")
            except Exception as update_error:
                logger.error(f"Erro ao atualizar dados: {str(update_error)}", exc_info=True)
                flash("❌ Erro ao salvar dados no banco de dados", "error")

        return render_template('admin.html', dados=user_data)

    except Exception as e:
        logger.error(f"ERRO: {str(e)}", exc_info=True)
        flash("⚠️ Erro durante o processamento", "warning")
        # Tenta carregar os dados do usuário novamente para evitar erro na renderização
        # caso a exceção ocorra antes de user_data ser completamente populado.
        try:
            res = supabase.table('usuarios').select('*').eq('id', session['user_id']).execute()
            user_data = res.data[0] if res.data else {}
            # Garante que social_links e custom_buttons sejam listas vazias se não existirem
            user_data['social_links'] = json.loads(user_data.get('social_links', '[]'))
            user_data['custom_buttons'] = json.loads(user_data.get('custom_buttons', '[]'))
        except Exception as inner_e:
            logger.error(f"Erro ao recuperar dados após erro inicial: {str(inner_e)}")
            user_data = {} # Garante que `dados` não seja None ou mal-formado
        return render_template('admin.html', dados=user_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)