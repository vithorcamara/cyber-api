import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Obtém o caminho do arquivo JSON do Firebase
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

# Inicializa o Firebase apenas se ainda não foi inicializado
try:
    if FIREBASE_CREDENTIALS:
        FIREBASE_CREDENTIALS = json.loads(FIREBASE_CREDENTIALS)
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    raise RuntimeError(f"Erro ao conectar ao Firebase: {e}")
