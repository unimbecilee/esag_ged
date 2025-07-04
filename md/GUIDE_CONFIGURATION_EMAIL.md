# 📧 Guide de Configuration du Système d'Email - ESAG GED

## 🎯 Vue d'ensemble

Votre système ESAG GED dispose maintenant des fonctionnalités email suivantes :

✅ **Email de bienvenue automatique** lors de la création d'utilisateurs  
✅ **Réinitialisation de mot de passe** par email  
✅ **Notifications de documents** (ajout, partage)  
✅ **Notifications de workflows** (assignation de tâches)  
✅ **Interface d'administration** pour configurer les emails  
✅ **Logs complets** de tous les emails envoyés  

---

## 🚀 Configuration Rapide (Recommandée : Gmail)

### Étape 1 : Préparer votre compte Gmail

1. **Activer l'authentification à 2 facteurs** sur votre compte Google
2. **Générer un mot de passe d'application** :
   - Allez sur https://myaccount.google.com/security
   - Cliquez sur "Authentification à 2 facteurs"
   - En bas, cliquez sur "Mots de passe d'application"
   - Sélectionnez "Mail" comme application
   - **Copiez le mot de passe généré** (format : xxxx xxxx xxxx xxxx)

### Étape 2 : Configurer via l'interface web

1. **Connectez-vous** à ESAG GED en tant qu'administrateur
2. **Allez dans Paramètres** → **Configuration Email**
3. **Remplissez les informations** :
   ```
   Serveur SMTP : smtp.gmail.com
   Port : 587
   Nom d'utilisateur : votre-email@gmail.com
   Mot de passe : le mot de passe d'application Gmail (16 caractères)
   TLS : ✅ Activé
   Email expéditeur : votre-email@gmail.com
   Nom expéditeur : ESAG GED
   ```
4. **Testez la configuration** avec le bouton "Test"
5. **Activez le système** si le test réussit

---

## 🔧 Configuration Alternative (Variables d'environnement)

Créez un fichier `.env` à la racine du projet :

```env
# Configuration Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-application
SMTP_USE_TLS=true
EMAIL_FROM=votre-email@gmail.com
EMAIL_FROM_NAME=ESAG GED

# URL de base pour les liens dans les emails
BASE_URL=http://localhost:3000
```

---

## 📱 Autres Fournisseurs d'Email

### Outlook/Hotmail
```
Serveur SMTP : smtp-mail.outlook.com
Port : 587
TLS : Activé
Utilisateur : votre-email@outlook.com
Mot de passe : votre mot de passe Outlook
```

### Yahoo Mail
```
Serveur SMTP : smtp.mail.yahoo.com
Port : 587
TLS : Activé
Utilisateur : votre-email@yahoo.com
Mot de passe : mot de passe d'application Yahoo
```

### Serveur SMTP personnalisé
```
Serveur SMTP : mail.votre-domaine.com
Port : 587 ou 465
TLS/SSL : Selon votre configuration
Utilisateur : votre-email@votre-domaine.com
Mot de passe : votre mot de passe
```

---

## ✅ Test du Système

### 1. Test de configuration
- Utilisez le bouton "Test" dans l'interface d'administration
- Vous devriez recevoir un email de test

### 2. Test des fonctionnalités

**Email de bienvenue :**
- Créez un nouvel utilisateur depuis l'interface admin
- L'utilisateur devrait recevoir un email avec son mot de passe

**Réinitialisation de mot de passe :**
- Allez sur la page de connexion
- Cliquez sur "Mot de passe oublié ?"
- Entrez un email d'utilisateur existant

**Notifications de documents :**
- Ajoutez un nouveau document
- Les administrateurs et utilisateurs concernés recevront une notification

---

## 🔧 Dépannage

### Problème : "Authentification échouée"
- **Gmail** : Vérifiez que vous utilisez un mot de passe d'application, pas votre mot de passe principal
- **Outlook** : Activez l'authentification à 2 facteurs et utilisez un mot de passe d'application
- **Vérifiez** : nom d'utilisateur et mot de passe corrects

### Problème : "Connexion refusée"
- **Vérifiez** : serveur SMTP et port corrects
- **Gmail** : smtp.gmail.com:587
- **Outlook** : smtp-mail.outlook.com:587

### Problème : "Emails non reçus"
- **Vérifiez** : dossier spam/courrier indésirable
- **Testez** : envoi vers différentes adresses email
- **Logs** : consultez les logs d'email dans l'interface admin

### Problème : "TLS/SSL"
- **Gmail/Outlook** : utilisez toujours TLS (port 587)
- **Serveur personnel** : vérifiez si SSL (port 465) ou TLS (port 587)

---

## 📋 Fonctionnalités Détaillées

### 🎉 Email de Bienvenue
- **Déclencheur** : Création d'un utilisateur par un admin
- **Contenu** : Nom, email, mot de passe temporaire, rôle
- **Action** : Lien direct vers la page de connexion

### 🔒 Réinitialisation de Mot de Passe
- **Accès public** : Page `/reset-password`
- **Accès admin** : Bouton dans la gestion des utilisateurs
- **Sécurité** : Nouveau mot de passe sécurisé généré automatiquement

### 📄 Notifications de Documents
- **Ajout de document** : Notifie les admins et utilisateurs avec accès
- **Partage de document** : Notifie l'utilisateur concerné
- **Personnalisation** : Chaque utilisateur peut désactiver les notifications

### ⚡ Notifications de Workflows
- **Assignation de tâche** : Notifie l'utilisateur assigné
- **Informations** : Titre du workflow, qui a assigné, date limite
- **Lien direct** : Vers la tâche dans l'application

---

## 🛡️ Sécurité et Bonnes Pratiques

### Mots de Passe d'Application
- **Jamais** votre mot de passe principal
- **Toujours** un mot de passe d'application dédié
- **Révocation** possible à tout moment

### Chiffrement
- **TLS activé** pour toutes les connexions SMTP
- **Mots de passe** chiffrés dans la base de données
- **Logs** ne contiennent jamais les mots de passe

### Gestion des Erreurs
- **Logs détaillés** pour le débogage
- **Pas d'interruption** si l'email échoue
- **Retry automatique** pour certaines erreurs

---

## 📊 Monitoring et Logs

### Interface Admin
- **Logs d'emails** : Tous les emails envoyés/échoués
- **Statistiques** : Taux de succès, types d'emails
- **Configuration** : Status du service email

### Logs Techniques
```bash
# Voir les logs de l'application
tail -f logs/email.log

# Logs en temps réel
python main.py  # Les logs s'affichent dans la console
```

---

## 🎯 Prochaines Étapes

Après configuration :

1. **Testez** toutes les fonctionnalités
2. **Formez** vos utilisateurs sur les nouvelles fonctionnalités
3. **Personnalisez** les templates d'email si besoin
4. **Configurez** les préférences utilisateur par défaut
5. **Surveillez** les logs pour détecter d'éventuels problèmes

---

## 🆘 Support

Si vous rencontrez des problèmes :

1. **Vérifiez** ce guide étape par étape
2. **Consultez** les logs d'email dans l'interface admin
3. **Testez** avec un service email simple (Gmail)
4. **Contactez** le support technique avec les messages d'erreur exacts

---

**✨ Votre système d'email est maintenant prêt ! ✨** 