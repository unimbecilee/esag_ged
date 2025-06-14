import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre_cle_secrete_ici'
    UPLOAD_FOLDER = os.path.join(basedir, '../uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16MB

# Configuration Email ESAG GED - Gmail
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = "mainuser1006@gmail.com"
MAIL_PASSWORD = "dzizhixzevtlwgle"
MAIL_DEFAULT_SENDER = "mainuser1006@gmail.com"

# Configuration SMTP alternative
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "mainuser1006@gmail.com"
SMTP_PASSWORD = "dzizhixzevtlwgle"
SMTP_USE_TLS = True
EMAIL_FROM = "mainuser1006@gmail.com"
EMAIL_FROM_NAME = "ESAG GED"

# Définir les variables d'environnement pour que le service email les trouve
os.environ['MAIL_SERVER'] = MAIL_SERVER
os.environ['MAIL_PORT'] = str(MAIL_PORT)
os.environ['MAIL_USE_TLS'] = str(MAIL_USE_TLS)
os.environ['MAIL_USE_SSL'] = str(MAIL_USE_SSL)
os.environ['MAIL_USERNAME'] = MAIL_USERNAME
os.environ['MAIL_PASSWORD'] = MAIL_PASSWORD
os.environ['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
