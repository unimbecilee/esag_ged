# Guide de déploiement Frontend React

## Option 1: Vercel (Recommandé)

1. Aller sur https://vercel.com
2. Se connecter avec GitHub
3. Importer le dossier `frontend/`
4. Configuration automatique détectée
5. Variables d'environnement à configurer:
   - REACT_APP_API_URL=https://votre-backend-railway.railway.app

## Option 2: Netlify

1. Aller sur https://netlify.com
2. Glisser-déposer le dossier `frontend/build/`
3. Ou connecter avec GitHub

## Commandes de build

```bash
cd frontend
npm install
npm run build
```

## Variables d'environnement Frontend

Créer un fichier `.env` dans `frontend/`:
```
REACT_APP_API_URL=https://votre-backend-url.com
```

## CORS - Important !

Assurer que le backend autorise les requêtes depuis le domaine frontend. 