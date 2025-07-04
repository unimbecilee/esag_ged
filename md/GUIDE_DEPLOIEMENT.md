# 🚀 GUIDE DE DÉPLOIEMENT ESAG GED

## 📋 PRÉPARATION TERMINÉE

J'ai préparé ton application pour le déploiement :
- ✅ `Procfile` créé
- ✅ `railway.json` configuré  
- ✅ `main.py` adapté pour le déploiement
- ✅ Variables d'environnement listées

## 🎯 PLAN DE DÉPLOIEMENT RECOMMANDÉ

**Backend Flask** → Railway.app (GRATUIT)
**Frontend React** → Vercel.com (GRATUIT)
**Base de données** → Déjà hébergée (AlwaysData)

## 📝 ÉTAPES À SUIVRE

### ÉTAPE 1 : DÉPLOYER LE BACKEND

1. **Créer un compte Railway :**
   - Aller sur https://railway.app
   - S'inscrire avec GitHub
   - Confirmer l'email

2. **Nouveau projet :**
   - Cliquer "New Project"
   - Choisir "Deploy from GitHub repo"
   - Sélectionner ton repo ESAG GED

3. **Variables d'environnement dans Railway :**
   ```
   SECRET_KEY=cle_secrete_longue_et_aleatoire_ici
   FLASK_ENV=production
   DATABASE_URL=postgresql://thefau:Passecale2002@@postgresql-thefau.alwaysdata.net:5432/thefau_archive
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=mainuser1006@gmail.com
   MAIL_PASSWORD=dzizhixzevtlwgle
   MAIL_DEFAULT_SENDER=mainuser1006@gmail.com
   ```

4. **Déployer :**
   - Railway build automatiquement
   - Attendre 5-10 minutes
   - Récupérer l'URL : `https://ton-app.railway.app`

### ÉTAPE 2 : DÉPLOYER LE FRONTEND

1. **Préparer le frontend :**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Créer compte Vercel :**
   - Aller sur https://vercel.com
   - S'inscrire avec GitHub

3. **Nouveau projet Vercel :**
   - "New Project" > Importer le repo
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`

4. **Variable d'environnement Vercel :**
   ```
   REACT_APP_API_URL=https://ton-app.railway.app
   ```

### ÉTAPE 3 : CONFIGURATION CORS

Modifier le fichier `AppFlask/__init__.py` :

```python
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Autoriser le frontend
    CORS(app, origins=[
        "http://localhost:3000",  # Développement
        "https://ton-frontend.vercel.app"  # Production
    ])
```

## ✅ VÉRIFICATIONS

- [ ] Backend accessible
- [ ] Frontend accessible  
- [ ] Connexion base de données OK
- [ ] Upload fichiers OK
- [ ] Emails fonctionnent
- [ ] Login/logout OK

## 🆘 EN CAS DE PROBLÈME

**Erreur Database :**
- Vérifier DATABASE_URL dans Railway

**Erreur CORS :**
- Ajouter ton domaine Vercel dans CORS

**Build échoue :**
- Vérifier les logs Railway

## 💰 COÛTS

- **Railway :** GRATUIT (500h/mois)
- **Vercel :** GRATUIT (100GB bande passante)
- **Total :** GRATUIT ! 🎉

## 🚀 PRÊT À DÉPLOYER ?

Dis-moi quand tu veux commencer et on fait ça ensemble étape par étape ! 