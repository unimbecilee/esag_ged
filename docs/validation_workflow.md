# Workflow de Validation de Documents

## Vue d'ensemble

Le système de workflow de validation permet de soumettre des documents à un processus de validation automatique en deux étapes :

1. **Étape 1** : Validation par un chef de service
2. **Étape 2** : Validation finale par un directeur

## Architecture

### Backend

#### Service Principal

- **`ValidationWorkflowService`** : Service principal gérant toute la logique métier
- **`validation_workflow.py`** : API endpoints pour les interactions frontend

#### Endpoints API

| Endpoint                                        | Méthode | Description                          |
| ----------------------------------------------- | ------- | ------------------------------------ |
| `/api/validation-workflow/start`                | POST    | Démarre un workflow de validation    |
| `/api/validation-workflow/approve`              | POST    | Traite une approbation ou un rejet   |
| `/api/validation-workflow/pending`              | GET     | Récupère les approbations en attente |
| `/api/validation-workflow/instance/{id}`        | GET     | Détails d'une instance de workflow   |
| `/api/validation-workflow/document/{id}/status` | GET     | Statut du workflow pour un document  |
| `/api/validation-workflow/statistics`           | GET     | Statistiques des workflows (admin)   |

### Frontend

#### Composants React

- **`ValidationWorkflowButton`** : Bouton pour démarrer un workflow
- **`PendingApprovals`** : Liste des approbations en attente
- **`validationWorkflowService`** : Service pour les appels API

#### Types TypeScript

Tous les types sont définis dans `types/workflow.ts` pour une sécurité de type complète.

## Utilisation

### 1. Démarrer un workflow de validation

```typescript
import ValidationWorkflowButton from "./components/ValidationWorkflow/ValidationWorkflowButton";

<ValidationWorkflowButton
  documentId={document.id}
  documentTitle={document.titre}
  onWorkflowStarted={() => refreshDocuments()}
/>;
```

### 2. Afficher les approbations en attente

```typescript
import PendingApprovals from "./components/ValidationWorkflow/PendingApprovals";

<PendingApprovals
  userId={currentUser.id}
  onApprovalProcessed={() => refreshApprovals()}
/>;
```

### 3. Utilisation du service API

```typescript
import validationWorkflowService from "./services/validationWorkflowService";

// Démarrer un workflow
const result = await validationWorkflowService.startValidationWorkflow({
  document_id: 123,
  commentaire: "Demande de validation urgente",
});

// Traiter une approbation
const approval = await validationWorkflowService.processApproval({
  instance_id: 1,
  etape_id: 1,
  decision: "APPROUVE",
  commentaire: "Document conforme",
});

// Récupérer les approbations en attente
const pending = await validationWorkflowService.getPendingApprovals();
```

## Processus de validation

### Flux de travail

1. **Initiation** : Un utilisateur démarre un workflow pour un document
2. **Notification** : Le chef de service reçoit une notification
3. **Première validation** : Le chef de service approuve ou rejette
4. **Si approuvé** : Le directeur reçoit une notification
5. **Validation finale** : Le directeur approuve ou rejette
6. **Finalisation** : Le document est marqué comme approuvé ou rejeté

### Statuts des documents

- **`BROUILLON`** : Document en cours de rédaction
- **`EN_VALIDATION`** : Workflow de validation en cours
- **`APPROUVE`** : Document validé par toutes les étapes
- **`REJETE`** : Document rejeté à une étape

### Rôles et permissions

- **`Utilisateur`** : Peut démarrer des workflows
- **`chef_de_service`** : Peut approuver/rejeter à l'étape 1
- **`Admin`** : Peut approuver/rejeter à l'étape 2 (directeur)

## Base de données

### Tables utilisées

- **`workflow`** : Définition des workflows
- **`workflow_instance`** : Instances de workflows en cours
- **`workflow_approbation`** : Historique des approbations
- **`etapeworkflow`** : Étapes des workflows
- **`workflow_approbateur`** : Approbateurs par étape

### Exemple de données

```sql
-- Workflow de validation
INSERT INTO workflow (nom, description) VALUES
('Validation Document', 'Workflow automatique de validation en 2 étapes');

-- Étapes
INSERT INTO etapeworkflow (workflow_id, nom, ordre) VALUES
(1, 'Validation Chef de Service', 1),
(1, 'Validation Directeur', 2);

-- Approbateurs
INSERT INTO workflow_approbateur (etape_id, role_nom) VALUES
(1, 'chef_de_service'),
(2, 'Admin');
```

## Tests

### Tests unitaires

```bash
# Backend
python -m pytest AppFlask/tests/test_validation_workflow.py

# Frontend
npm test ValidationWorkflowButton.test.tsx
```

### Tests d'intégration

```bash
python test_validation_workflow_integration.py
```

## Configuration

### Variables d'environnement

Aucune configuration spéciale requise. Le système utilise la configuration existante de l'application.

### Notifications

Le système utilise le `NotificationService` existant pour envoyer des notifications aux approbateurs.

## Débogage

### Logs utiles

```python
# Activer les logs de debug
import logging
logging.getLogger('AppFlask.services.validation_workflow_service').setLevel(logging.DEBUG)
```

### Vérification de l'état

```sql
-- Vérifier les instances en cours
SELECT wi.*, d.titre, w.nom as workflow_nom
FROM workflow_instance wi
JOIN document d ON wi.document_id = d.id
JOIN workflow w ON wi.workflow_id = w.id
WHERE wi.statut = 'EN_COURS';

-- Vérifier les approbations en attente
SELECT DISTINCT wi.id, d.titre, e.nom as etape_nom
FROM workflow_instance wi
JOIN document d ON wi.document_id = d.id
JOIN etapeworkflow e ON wi.etape_courante_id = e.id
WHERE wi.statut = 'EN_COURS';
```

## Sécurité

### Authentification

Tous les endpoints nécessitent un token d'authentification valide via le décorateur `@token_required`.

### Autorisation

- Les utilisateurs ne peuvent approuver que les étapes pour lesquelles ils ont les droits
- La vérification se fait via la table `workflow_approbateur` et le rôle utilisateur

### Validation des données

- Toutes les entrées sont validées côté backend
- Les types TypeScript assurent la cohérence côté frontend

## Performance

### Optimisations

- Requêtes SQL optimisées avec des JOIN appropriés
- Cache des rôles utilisateur pour éviter les requêtes répétées
- Pagination automatique pour les listes importantes

### Monitoring

- Logs détaillés de toutes les actions
- Métriques disponibles via l'endpoint `/statistics`

## Migration et déploiement

### Prérequis

1. Tables de workflow existantes
2. Rôles utilisateur configurés (`chef_de_service`, `Admin`)
3. Service de notifications fonctionnel

### Déploiement

1. Déployer le code backend
2. Enregistrer le blueprint dans `__init__.py`
3. Déployer les composants frontend
4. Tester avec le script d'intégration

## Support et maintenance

### Problèmes courants

1. **Workflow ne démarre pas** : Vérifier les rôles et les approbateurs configurés
2. **Notifications non envoyées** : Vérifier le service de notifications
3. **Erreurs d'autorisation** : Vérifier les rôles utilisateur

### Maintenance

- Nettoyer périodiquement les anciennes instances terminées
- Monitorer les workflows bloqués (délais dépassés)
- Sauvegarder l'historique des approbations
