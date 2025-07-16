# config.py
import os

# O código lê as credenciais de "Variáveis de Ambiente" seguras no servidor.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# Caminho completo para o banco de dados no "Disco Persistente" do Render.
DATABASE_NAME = "/var/data/database.db"


# Banco de dados
DATABASE_NAME = "database.db"

# Links para a Área de Membros de cada plano
LINKS_AREA_DE_MEMBROS = {
    'trial': 'https://bit.ly/GerenciaCashDiamante', # Trial tem acesso ao melhor plano
    'bronze': 'https://bit.ly/GerenciaCashBronze',
    'prata': 'https://bit.ly/GerenciaCashPrata',
    'ouro': 'https://bit.ly/GerenciaCashOuro',
    'diamante': 'https://bit.ly/GerenciaCashDiamante'
}