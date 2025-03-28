from flask import Flask, request, jsonify, make_response
import jwt
import hashlib
import os
from functools import wraps
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY') # Pega do .env ou usa um fallback
TOKEN_EXPIRATION = int(os.getenv('TOKEN_EXPIRATION', 300))  # Expiração padrão de 1 hora (3600s)
if not SECRET_KEY:
    raise ValueError("A SECRET_KEY não foi definida! Verifique seu .env.")


# Função para gerar hash seguro (SHA-512 + Salt)
def hash_senha(senha):
    salt = os.urandom(16).hex()
    hash_obj = hashlib.sha512((senha + salt).encode()).hexdigest()
    return f"{salt}${hash_obj}"

# Função para verificar senha
def verificar_senha(senha, hash_armazenado):
    salt, hash_correto = hash_armazenado.split("$")
    return hashlib.sha512((senha + salt).encode()).hexdigest() == hash_correto

# Função para verificar o token JWT
def token_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")  # Busca o token JWT no cookie
        if not token:
            return jsonify({"erro": "Token de autenticação ausente!"}), 401

        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS512"])
            usuario = decoded_token["usuario"]
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido!"}), 403

        return f(usuario, *args, **kwargs)
    return decorated