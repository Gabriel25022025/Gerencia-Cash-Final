# config.py
import os
from dotenv import load_dotenv

# Esta linha carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# O código agora lê as credenciais do .env (localmente) ou das Environment Variables (no servidor)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# O caminho do banco de dados (ajuste com seu nome de usuário para o deploy)
# Para rodar localmente, ele simplesmente criará o DB na pasta atual.
DATABASE_NAME = f"/home/GabrielRoa/Gerencia-Cash-Final/database.db"

# Links para a Área de Membros de cada plano
LINKS_AREA_DE_MEMBROS = {
    'trial': 'https://bit.ly/GerenciaCashDiamante', # Trial tem acesso ao melhor plano
    'bronze': 'https://bit.ly/GerenciaCashBronze',
    'prata': 'https://bit.ly/GerenciaCashPrata',
    'ouro': 'https://bit.ly/GerenciaCashOuro',
    'diamante': 'https://bit.ly/GerenciaCashDiamante'
}