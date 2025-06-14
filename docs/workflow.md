# Guide du système de workflow ESAG GED

Ce document explique en détail le fonctionnement du système de workflow dans l'application ESAG GED, ses composants, et comment l'utiliser efficacement pour la validation des documents.

## Introduction

Le système de workflow d'ESAG GED permet de définir et d'exécuter des processus de validation de documents structurés, avec des étapes séquentielles et des approbateurs désignés. Il est inspiré des fonctionnalités d'Alfresco tout en étant adapté aux besoins spécifiques de votre organisation.

## Concepts clés

### Workflow (Modèle)

Un workflow est un modèle de processus qui définit une séquence d'étapes à suivre pour la validation d'un document. Chaque workflow peut être réutilisé pour différents documents.

### Étape

Une étape représente une phase de validation dans le workflow avec des approbateurs désignés. Une étape peut avoir différentes règles d'approbation.

### Instance de workflow

Une instance de workflow est un processus de validation en cours, lié à un document spécifique et suivant un modèle de workflow.

### Approbateur

Un approbateur est une entité (utilisateur, rôle ou organisation) qui a la responsabilité d'approuver ou de rejeter une étape de workflow.

## Types d'approbation

Le système prend en charge trois types d'approbation pour les étapes:

1. **Simple**: L'étape est validée dès qu'un approbateur donne son accord.
2. **Multiple**: Tous les approbateurs désignés doivent approuver l'étape.
3. **Parallèle**: L'étape est validée lorsque la majorité des approbateurs ont donné leur accord.

## Création et gestion des workflows

### Créer un nouveau workflow

1. Accédez à la section "Workflow" dans le menu principal
2. Cliquez sur le bouton "Nouveau Workflow"
3. Renseignez les informations de base:
   - Nom du workflow (obligatoire)
   - Description (optionnelle)
4. Ajoutez des étapes en cliquant sur "Ajouter une étape"
5. Pour chaque étape, définissez:
   - Nom de l'étape (obligatoire)
   - Description (optionnelle)
   - Type d'approbation (Simple, Multiple, Parallèle)
   - Délai maximum (optionnel, en heures)
   - Approbateurs (utilisateurs, rôles ou organisations)
6. Réorganisez les étapes si nécessaire
7. Cliquez sur "Enregistrer" pour créer le workflow

### Modifier un workflow existant

1. Dans la liste des workflows, cliquez sur le bouton "Modifier" à côté du workflow concerné
2. Mettez à jour les informations selon vos besoins
3. Attention: la modification d'un workflow n'affecte pas les instances déjà en cours

### Supprimer un workflow

1. Dans la liste des workflows, cliquez sur le bouton "Supprimer" à côté du workflow concerné
2. Confirmez la suppression
3. Note: un workflow ne peut pas être supprimé s'il est utilisé par des instances en cours

## Utilisation des workflows

### Démarrer un workflow

1. Ouvrez le document pour lequel vous souhaitez démarrer un workflow
2. Cliquez sur le bouton "Démarrer un workflow"
3. Sélectionnez le workflow à utiliser parmi la liste
4. Ajoutez un commentaire optionnel
5. Cliquez sur "Démarrer"
6. Le document entre alors dans la première étape du workflow
7. Les approbateurs concernés sont notifiés automatiquement

### Suivre l'avancement d'un workflow

1. Dans la section "Workflow", accédez à l'onglet "Mes workflows"
2. Vous y trouverez la liste des workflows que vous avez initiés
3. Cliquez sur un workflow pour voir:
   - Son état actuel
   - L'étape en cours
   - Les approbations déjà effectuées
   - L'historique des actions

### Approuver ou rejeter une étape

1. Dans la section "Workflow", accédez à l'onglet "Mes approbations"
2. Vous y trouverez la liste des documents qui attendent votre approbation
3. Cliquez sur un document pour le consulter
4. Utilisez les boutons "Approuver" ou "Rejeter"
5. Ajoutez un commentaire si nécessaire
6. Votre décision est enregistrée et le workflow progresse en conséquence

## Statuts des workflows

Une instance de workflow peut avoir l'un des statuts suivants:

- **EN_COURS**: Le workflow est actif et en attente d'approbation pour l'étape courante
- **TERMINE**: Toutes les étapes ont été approuvées avec succès
- **REJETE**: Une étape a été rejetée par un approbateur
- **ANNULE**: Le workflow a été annulé manuellement par l'initiateur ou un administrateur

## Notifications

Le système envoie automatiquement des notifications aux utilisateurs concernés:

1. Lorsqu'un workflow démarre, les approbateurs de la première étape sont notifiés
2. Lorsqu'une étape est validée, les approbateurs de l'étape suivante sont notifiés
3. Lorsqu'un workflow est terminé ou rejeté, l'initiateur est notifié
4. Les notifications sont visibles dans l'interface utilisateur et peuvent être marquées comme lues

## Rapports et historique

Le système maintient un historique complet de toutes les actions liées aux workflows:

- Démarrage d'un workflow
- Approbations et rejets
- Progression d'étape en étape
- Complétion ou annulation

Ces informations sont accessibles via l'historique du document et les rapports d'activité dans la section Administration.

## Bonnes pratiques

1. **Définissez des workflows clairs**: Donnez des noms explicites aux workflows et aux étapes
2. **Limitez le nombre d'étapes**: Un workflow trop long peut ralentir le processus de validation
3. **Choisissez le bon type d'approbation**: Utilisez "Simple" pour les validations rapides, "Multiple" pour une validation stricte
4. **Utilisez les délais**: Définissez des délais raisonnables pour chaque étape
5. **Documentez vos workflows**: Utilisez le champ description pour expliquer l'objectif et les attentes

## Dépannage

### Un document reste bloqué dans une étape

- Vérifiez que tous les approbateurs nécessaires sont disponibles
- Un administrateur peut annuler le workflow et en démarrer un nouveau si nécessaire

### Les approbateurs ne reçoivent pas de notifications

- Vérifiez que les approbateurs sont correctement assignés à l'étape
- Si vous utilisez des rôles ou des organisations, vérifiez que les utilisateurs y sont bien rattachés

### Une étape est validée sans toutes les approbations requises

- Vérifiez le type d'approbation configuré pour l'étape
- Pour le type "Simple", une seule approbation suffit

## Conclusion

Le système de workflow d'ESAG GED offre une solution flexible et robuste pour la validation de documents. En comprenant bien son fonctionnement et en l'utilisant correctement, vous pouvez améliorer considérablement l'efficacité et la traçabilité des processus d'approbation dans votre organisation.
