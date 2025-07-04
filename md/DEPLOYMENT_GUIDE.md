# 🚀 GUIDE DE DÉPLOIEMENT ESAG GED

## 📋 PRÉPARATION

### ✅ Fichiers créés automatiquement :
- `Procfile` - Configuration du serveur
- `railway.json` - Configuration Railway
- `main.py` - Modifié pour le déploiement
- `environment_variables.txt` - Variables d'environnement

## 🎯 ÉTAPE 1 : DÉPLOYER LE BACKEND (Railway)

### 1.1 Créer un compte Railway
1. Aller sur https://railway.app
2. S'inscrire avec GitHub
3. Confirmer l'email

### 1.2 Créer un nouveau projet
1. Cliquer "New Project"
2. Choisir "Deploy from GitHub repo"
3. Sélectionner le repo ESAG GED
4. Railway détecte automatiquement Python

### 1.3 Configurer les variables d'environnement
Dans Railway Dashboard > Variables :

```
SECRET_KEY=generate_une_cle_secrete_longue_et_aleatoire
FLASK_ENV=production
DATABASE_URL=postgresql://thefau:Passecale2002@@postgresql-thefau.alwaysdata.net:5432/thefau_archive
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=mainuser1006@gmail.com
MAIL_PASSWORD=dzizhixzevtlwgle
MAIL_DEFAULT_SENDER=mainuser1006@gmail.com
```

### 1.4 Déployer
1. Railway build automatiquement
2. Attendre le déploiement (5-10 minutes)
3. Récupérer l'URL du backend : `https://votre-app.railway.app`

## 🎯 ÉTAPE 2 : DÉPLOYER LE FRONTEND (Vercel)

### 2.1 Préparer le frontend
```bash
cd frontend
npm install
npm run build
```

### 2.2 Configurer l'API URL
Créer `frontend/.env` :
```
REACT_APP_API_URL=https://votre-app.railway.app
```

### 2.3 Déployer sur Vercel
1. Aller sur https://vercel.com
2. S'inscrire avec GitHub
3. "New Project" > Importer le repo
4. Configurer :
   - Framework: Create React App
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`

### 2.4 Variables d'environnement Vercel
Dans Vercel Dashboard > Settings > Environment Variables :
```
REACT_APP_API_URL=https://votre-app.railway.app
```

## 🎯 ÉTAPE 3 : CONFIGURATION CORS

Modifier `AppFlask/__init__.py` pour autoriser le frontend :

```python
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Configuration CORS pour le déploiement
    CORS(app, origins=[
        "http://localhost:3000",  # Développement
        "https://votre-frontend.vercel.app"  # Production
    ])
```

## 🎯 ÉTAPE 4 : VÉRIFICATION

### 4.1 Tests à effectuer :
- [ ] Backend accessible : `https://votre-app.railway.app`
- [ ] Frontend accessible : `https://votre-frontend.vercel.app`
- [ ] Connexion à la base de données
- [ ] Upload de fichiers
- [ ] Envoi d'emails
- [ ] Authentification

### 4.2 Logs et débogage
- Railway : Dashboard > Deployments > View Logs
- Vercel : Dashboard > Functions > View Logs

## 🎯 ÉTAPE 5 : CONFIGURATION AVANCÉE

### 5.1 Domaine personnalisé (Optionnel)
- Railway : Settings > Domains
- Vercel : Settings > Domains

### 5.2 Monitoring et alertes
- Railway : Métriques intégrées
- Vercel : Analytics intégrées

## 🆘 DÉPANNAGE

### Erreurs courantes :

**1. Erreur de connexion DB :**
- Vérifier `DATABASE_URL` dans Railway
- Vérifier la connexion réseau

**2. Erreur CORS :**
- Ajouter le domaine frontend dans CORS
- Vérifier `REACT_APP_API_URL`

**3. Build échoue :**
- Vérifier `requirements.txt`
- Vérifier les logs Railway

**4. Frontend ne charge pas :**
- Vérifier `REACT_APP_API_URL`
- Vérifier le build React

## 💡 OPTIMISATIONS

### Performance :
- Activer le cache Railway
- Utiliser Vercel Edge Functions
- Optimiser les images

### Sécurité :
- Variables d'environnement sécurisées
- HTTPS obligatoire
- Rate limiting

## 📞 SUPPORT

- Railway : https://docs.railway.app
- Vercel : https://vercel.com/docs
- GitHub Issues pour questions spécifiques

---

🎉 **Votre application ESAG GED sera en ligne !** 