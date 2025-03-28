from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import jwt
import datetime
import os
from dotenv import load_dotenv
from auth.auth import hash_senha, verificar_senha, token_obrigatorio
from db.connection import db
from auth.mfa import enviar_email, gerar_mfa

# Carrega variáveis do .env
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')  # Chave secreta
TOKEN_EXPIRATION = int(os.getenv('TOKEN_EXPIRATION', 3600))  # Expiração padrão de 1 hora
if not SECRET_KEY:
    raise ValueError("A SECRET_KEY não foi definida! Verifique seu .env.")

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = SECRET_KEY

# Simula um banco de dados temporário (exemplo: Redis ou cache)
mfa_cache = {}

# Rota de registro
@app.route('/registrar', methods=['POST'])
def registrar():
    dados = request.json
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    email = dados.get('email')
    nome = dados.get('nome')
    
    if not usuario or not senha or not email or not nome:
        return jsonify({'erro': 'Usuário, senha, e-mail e nome são obrigatórios'}), 400
    
    users_ref = db.collection('usuarios')
    if users_ref.document(usuario).get().exists:
        return jsonify({'erro': 'Usuário já existe'}), 400
    
    senha_hash = hash_senha(senha)
    users_ref.document(usuario).set({'senha': senha_hash, 'email': email, 'nome': nome})
    
    return jsonify({'mensagem': 'Usuário registrado com sucesso'}), 201

# Rota de login (gera código MFA)
@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    
    user_doc = db.collection('usuarios').document(usuario).get()
    if not user_doc.exists:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    user_data = user_doc.to_dict()
    if not verificar_senha(senha, user_data['senha']):
        return jsonify({'erro': 'Senha incorreta'}), 401
    
    # Gera o código MFA e armazena temporariamente
    codigo_mfa = gerar_mfa()
    mfa_cache[usuario] = codigo_mfa  # 🔒 Idealmente, usar Redis com expiração de 30s

    # Envia o código MFA por e-mail
    enviar_email(user_data['email'], codigo_mfa)

    return jsonify({'mensagem': 'Login bem-sucedido. Código MFA enviado para o e-mail.'})

# Rota para verificar o código MFA e liberar o token
@app.route('/verificarmfa', methods=['POST'])
def verificar_mfa():
    dados = request.json
    usuario = dados.get('usuario')
    codigo_mfa = mfa_cache[usuario]

    if not usuario or not codigo_mfa:
        return jsonify({'erro': 'Usuário e código MFA são obrigatórios'}), 400
    
    codigo_salvo = mfa_cache.get(usuario)
    if not codigo_salvo or codigo_mfa != codigo_salvo:
        return jsonify({'erro': 'Código MFA inválido ou expirado'}), 401
    
    # Remove o código MFA após validação
    del mfa_cache[usuario]
    
    # Gera o token JWT
    token = jwt.encode({'usuario': usuario, 'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_EXPIRATION)}, SECRET_KEY, algorithm='HS512')
    
    resposta = make_response(jsonify({'mensagem': 'MFA verificado com sucesso!'}))
    resposta.set_cookie('token', token, httponly=True, secure=True, samesite='None')
    
    return resposta

# Rota protegida para buscar perfil do usuário autenticado
@app.route('/perfil', methods=['GET'])
@token_obrigatorio
def perfil(usuario):
    user_doc = db.collection('usuarios').document(usuario).get()
    
    if not user_doc.exists:
        return jsonify({"erro": "Usuário não encontrado!"}), 404

    usuario_info = user_doc.to_dict()
    usuario_info.pop("senha", None)
    usuario_info['usuario'] = usuario

    print(usuario_info)

    return jsonify({"mensagem": "Acesso autorizado!", "usuario": usuario_info})


@app.route('/logout', methods=['GET'])
def logout():
    resposta = make_response(jsonify({"mensagem": "Logout realizado com sucesso!"}))
    resposta.set_cookie('token', '', expires=0, httponly=True, secure=False, samesite='Lax')  # Remove o cookie
    return resposta