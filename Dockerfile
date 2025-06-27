# Utiliser l'image Python officielle
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances système pour python-magic, OpenCV et threads
RUN apt-get update && apt-get install -y libmagic1 libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application (ignorer frontend)
COPY AppFlask/ ./AppFlask/
COPY main.py .
COPY config.py .

# Créer le dossier uploads
RUN mkdir -p uploads

# Exposer le port
EXPOSE $PORT

# Commande pour démarrer l'application
CMD ["python", "main.py"] 