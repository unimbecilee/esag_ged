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

## Nouvelles fonctionnalités de gestion documentaire avancée

Nous avons implémenté plusieurs fonctionnalités avancées de gestion documentaire inspirées d'Alfresco pour enrichir notre application ESAG GED. Ces fonctionnalités permettent une gestion plus complète et professionnelle des documents.

### 1. Gestion des versions de documents

La gestion des versions permet de conserver l'historique complet des modifications apportées à un document.

**Fonctionnalités principales :**

- Création de nouvelles versions avec commentaires
- Consultation de l'historique des versions
- Téléchargement d'une version spécifique
- Restauration d'une version antérieure

**API :**

- `GET /api/versions/document/{document_id}` : Liste toutes les versions d'un document
- `POST /api/versions/document/{document_id}` : Ajoute une nouvelle version
- `GET /api/versions/{version_id}` : Récupère une version spécifique
- `POST /api/versions/document/{document_id}/restore/{version_number}` : Restaure une version antérieure
- `GET /api/versions/download/{version_id}` : Télécharge une version spécifique

### 2. Système de commentaires sur les documents

Les commentaires permettent aux utilisateurs de discuter et d'échanger des informations sur un document.

**Fonctionnalités principales :**

- Ajout de commentaires sur un document
- Organisation hiérarchique des commentaires (réponses)
- Modification et suppression de commentaires
- Notification des abonnés lors de nouveaux commentaires

**API :**

- `GET /api/comments/document/{document_id}` : Liste tous les commentaires d'un document
- `POST /api/comments/document/{document_id}` : Ajoute un nouveau commentaire
- `GET /api/comments/{comment_id}` : Récupère un commentaire spécifique
- `PUT /api/comments/{comment_id}` : Modifie un commentaire
- `DELETE /api/comments/{comment_id}` : Supprime un commentaire

### 3. Abonnements et notifications

Le système d'abonnement permet aux utilisateurs de suivre les modifications apportées aux documents qui les intéressent.

**Fonctionnalités principales :**

- Abonnement à un document
- Configuration des types de notifications (nouvelles versions, modifications des métadonnées, commentaires, workflow)
- Consultation des abonnements
- Désabonnement

**API :**

- `POST /api/subscriptions/document/{document_id}` : S'abonne à un document
- `GET /api/subscriptions/document/{document_id}` : Vérifie l'abonnement à un document
- `DELETE /api/subscriptions/document/{document_id}` : Se désabonne d'un document
- `GET /api/subscriptions/user` : Liste tous les abonnements de l'utilisateur
- `GET /api/subscriptions/document/{document_id}/subscribers` : Liste tous les abonnés à un document

### 4. Extraction/Réservation de documents (Check-out/Check-in)

Cette fonctionnalité permet d'éviter les conflits d'édition en réservant un document pour une modification exclusive.

**Fonctionnalités principales :**

- Réservation (check-out) d'un document
- Libération (check-in) d'un document
- Vérification du statut de réservation
- Libération forcée (pour les administrateurs)
- Nettoyage automatique des réservations expirées

**API :**

- `POST /api/checkout/document/{document_id}` : Réserve un document
- `POST /api/checkout/document/{document_id}/checkin` : Libère un document
- `POST /api/checkout/document/{document_id}/force-checkin` : Force la libération d'un document (admin)
- `GET /api/checkout/document/{document_id}/status` : Vérifie le statut de réservation
- `GET /api/checkout/user` : Liste tous les documents réservés par l'utilisateur
- `GET /api/checkout/document/{document_id}/history` : Historique des réservations d'un document

### Installation et configuration des nouvelles fonctionnalités

1. **Créer les nouvelles tables dans la base de données**

   Exécutez le script SQL fourni pour créer les tables nécessaires :

   ```bash
   psql -U votre_utilisateur -d votre_base -f AppFlask/sql/document_features.sql
   ```

   Pour MySQL :

   ```bash
   mysql -u votre_utilisateur -p votre_base < AppFlask/sql/document_features.sql
   ```

2. **Vérifier que les nouveaux modèles sont bien présents**

   - `AppFlask/models/document_version.py`
   - `AppFlask/models/document_comment.py`
   - `AppFlask/models/document_subscription.py`
   - `AppFlask/models/document_checkout.py`

3. **Vérifier que les routes API sont bien configurées**

   - `AppFlask/routes/document_version_routes.py`
   - `AppFlask/routes/document_comment_routes.py`
   - `AppFlask/routes/document_subscription_routes.py`
   - `AppFlask/routes/document_checkout_routes.py`

4. **Mettre à jour app.py pour enregistrer les nouveaux blueprints**
   Assurez-vous que les nouveaux blueprints sont bien importés et enregistrés dans `AppFlask/app.py`.

5. **Redémarrer l'application**

   ```bash
   python run.py
   ```

6. **Tester les nouvelles API**
   Vous pouvez utiliser un outil comme Postman ou curl pour tester les nouveaux endpoints API.

### Exemples d'utilisation

#### Ajouter une nouvelle version d'un document

```bash
curl -X POST -H "Authorization: Bearer votre_token" -F "file=@chemin/vers/fichier.pdf" -F "commentaire=Correction des erreurs" http://localhost:5000/api/versions/document/1
```

#### Commenter un document

```bash
curl -X POST -H "Authorization: Bearer votre_token" -H "Content-Type: application/json" -d '{"content":"Voici mon commentaire sur ce document"}' http://localhost:5000/api/comments/document/1
```

#### S'abonner à un document

```bash
curl -X POST -H "Authorization: Bearer votre_token" -H "Content-Type: application/json" -d '{"notify_new_version":true,"notify_comments":true}' http://localhost:5000/api/subscriptions/document/1
```

#### Réserver un document

```bash
curl -X POST -H "Authorization: Bearer votre_token" http://localhost:5000/api/checkout/document/1
```

### Prochaines étapes

- Développement de l'interface utilisateur pour ces fonctionnalités
- Implémentation d'un système de notifications en temps réel
- Ajout de fonctionnalités de recherche avancée sur les métadonnées et les versions
- Intégration avec des outils d'édition en ligne

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
