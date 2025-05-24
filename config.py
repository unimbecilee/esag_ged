import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre_cle_secrete_ici'
    UPLOAD_FOLDER = os.path.join(basedir, '../uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16MB
