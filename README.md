# ESAG GED - Système de Gestion Électronique de Documents

## Description

ESAG GED est une application de Gestion Électronique de Documents (GED) moderne et complète, développée avec Flask (backend) et React (frontend). Elle permet la gestion, le stockage, et le partage sécurisé de documents au sein d'une organisation.

## Fonctionnalités principales

- 📄 Gestion complète des documents (upload, téléchargement, modification, suppression)
- 👥 Gestion des utilisateurs et des droits d'accès
- 🏢 Gestion des organisations
- 🔍 Recherche avancée de documents
- 🗑️ Système de corbeille
- 📊 Tableau de bord avec statistiques
- 📱 Interface responsive
- 🔒 Sécurité renforcée

## Prérequis

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Compte Cloudinary (pour le stockage des fichiers)
- La Base de donnees est stocker en ligne avec un mode gratuit donc il y aura un peu de lenteur dans les reponses de l'application

## Installation

### Backend (Flask)

1. Cloner le repository :

```bash
git clone [URL_DU_REPO]
cd esag-ged
```

2. Créer un environnement virtuel :

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Lancer le serveur :

```bash
python main.py
```

### Frontend (React)

1. Aller dans le dossier frontend :

```bash
cd frontend
```

2. Installer les dépendances :

```bash
npm install
```

3. Configurer les variables d'environnement (.env) :

```env
REACT_APP_API_URL=http://localhost:5000
```

4. Lancer l'application :

```bash
npm start
```

## Structure du projet

```
esag-ged/
├── AppFlask/                 # Backend Flask
│   ├── api/                  # Routes API
│   ├── routes/              # Routes web
│   ├── templates/           # Templates HTML
│   └── utils/               # Utilitaires
├── frontend/                # Frontend React
│   ├── public/
│   └── src/
│       ├── components/     # Composants React
│       ├── pages/         # Pages de l'application
│       └── services/      # Services API
├── migrations/             # Migrations de base de données
├── tests/                 # Tests
├── requirements.txt       # Dépendances Python
└── README.md
```

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.
