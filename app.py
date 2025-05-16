from flask import Flask, render_template, request, redirect, session, url_for
from config import USERNAME, PASSWORD
import json
import os

app = Flask(__name__)
app.secret_key = 'chave-super-secreta'  # Altere isso para algo mais seguro

CONFIG_FILE = 'config.json'


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
        dados['foto'] = request.form['foto']
        dados['instagram'] = request.form['instagram']
        dados['linkedin'] = request.form['linkedin']
        dados['github'] = request.form['github']
        dados['email'] = request.form['email']
        dados['whatsapp'] = request.form['whatsapp']
        dados['curriculo'] = request.form['curriculo']
        salvar_dados(dados)
        return redirect(url_for('index'))

    return render_template('admin.html', dados=dados)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
