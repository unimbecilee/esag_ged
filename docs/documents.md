# Guide de gestion des documents ESAG GED

Ce document explique en détail le fonctionnement du système de gestion des documents dans l'application ESAG GED, inspiré d'Alfresco, et comment l'utiliser efficacement pour gérer vos archives électroniques.

## Introduction

Le système de gestion documentaire d'ESAG GED permet de stocker, organiser, partager et suivre vos documents numériques avec un contrôle précis des versions et des accès. Cette fonctionnalité est au cœur de l'application et offre une expérience similaire à Alfresco tout en étant adaptée à vos besoins spécifiques.

## Structure et organisation

### Dossiers et hiérarchie

Les documents sont organisés dans une structure hiérarchique de dossiers:

- Un dossier peut contenir des documents et des sous-dossiers
- La navigation se fait via l'arborescence affichée dans l'interface
- Chaque dossier possède des propriétés (nom, description, permissions)
- Les dossiers peuvent être déplacés, renommés ou supprimés

### Types de documents

Le système prend en charge tous les types de fichiers courants:

- Documents bureautiques (DOC, DOCX, XLS, XLSX, PPT, PPTX, PDF)
- Images (JPG, PNG, GIF, SVG)
- Fichiers audio et vidéo (MP3, MP4, WAV, AVI)
- Fichiers d'archive (ZIP, RAR, 7Z)
- Et bien d'autres...

### Métadonnées

Chaque document est associé à des métadonnées qui facilitent sa gestion:

- Métadonnées de base: titre, description, type, taille
- Métadonnées système: dates de création/modification, créateur, version
- Métadonnées personnalisées: tags, statut, propriétés spécifiques

## Opérations sur les documents

### Créer/Téléverser un document

1. Naviguez jusqu'au dossier où vous souhaitez ajouter le document
2. Cliquez sur le bouton "Nouveau document"
3. Complétez le formulaire:
   - Titre du document (obligatoire)
   - Description (optionnelle)
   - Tags (optionnels)
4. Téléversez le fichier en le sélectionnant depuis votre ordinateur
5. Cliquez sur "Enregistrer"

### Visualiser un document

1. Cliquez sur le titre du document dans la liste
2. Le système affiche une prévisualisation si le format est pris en charge
3. Pour les formats non prévisualisables, vous pouvez télécharger le fichier

### Modifier un document

1. Ouvrez le document que vous souhaitez modifier
2. Cliquez sur le bouton "Modifier"
3. Mettez à jour les métadonnées selon vos besoins
4. Pour modifier le contenu du fichier lui-même:
   - Téléchargez-le, modifiez-le localement, puis
   - Téléversez une nouvelle version (voir section Gestion des versions)

### Déplacer/Copier un document

1. Sélectionnez le document dans la liste
2. Utilisez l'option "Déplacer" ou "Copier" dans le menu contextuel
3. Sélectionnez le dossier de destination dans l'arborescence
4. Confirmez l'opération

### Supprimer un document

1. Sélectionnez le document dans la liste
2. Cliquez sur le bouton "Supprimer" ou utilisez l'option dans le menu contextuel
3. Confirmez la suppression
4. Le document est déplacé dans la corbeille (il n'est pas supprimé définitivement)

## Gestion des versions

Le système conserve l'historique des versions de chaque document:

### Créer une nouvelle version

1. Ouvrez le document concerné
2. Cliquez sur "Télécharger une nouvelle version"
3. Sélectionnez le fichier mis à jour
4. Ajoutez un commentaire décrivant les modifications apportées
5. Cliquez sur "Téléverser"

### Consulter l'historique des versions

1. Ouvrez le document concerné
2. Accédez à l'onglet "Versions"
3. Vous verrez la liste complète des versions avec:
   - Numéro de version
   - Date de création
   - Utilisateur qui a créé la version
   - Commentaire associé

### Restaurer une version antérieure

1. Dans l'onglet "Versions", localisez la version à restaurer
2. Cliquez sur "Restaurer cette version"
3. Confirmez l'opération
4. Une nouvelle version est créée, identique à celle que vous restaurez

## Classification et recherche

### Tags et catégories

Les documents peuvent être classifiés à l'aide de tags:

1. Lors de la création ou de la modification d'un document, utilisez la section "Tags"
2. Vous pouvez sélectionner des tags existants ou en créer de nouveaux
3. Les tags facilitent le regroupement et la recherche de documents connexes

### Recherche de documents

Le système offre plusieurs méthodes pour retrouver vos documents:

1. **Recherche simple**: Utilisez la barre de recherche en haut de l'interface
2. **Recherche avancée**: Accédez à la page de recherche pour utiliser des critères multiples:
   - Texte dans le titre ou le contenu
   - Type de document
   - Plage de dates
   - Créateur
   - Tags
   - Et plus encore...
3. **Navigation**: Parcourez l'arborescence des dossiers pour trouver vos documents

## Partage et permissions

### Niveaux de permission

Le système propose plusieurs niveaux d'accès aux documents:

- **Lecture**: Permet de visualiser et télécharger le document
- **Modification**: Permet de modifier les métadonnées et d'ajouter des versions
- **Suppression**: Permet de déplacer le document vers la corbeille
- **Admin**: Permissions complètes, y compris la gestion des accès

### Partager un document

1. Ouvrez le document à partager
2. Cliquez sur "Gérer les accès"
3. Ajoutez les utilisateurs, rôles ou organisations avec qui partager
4. Pour chaque entité, définissez le niveau d'accès approprié
5. Vous pouvez également envoyer une notification par e-mail aux utilisateurs concernés

### Hériter des permissions

Par défaut, les documents héritent des permissions du dossier qui les contient:

1. Lorsque vous définissez des permissions sur un dossier, vous pouvez choisir de les appliquer à tout son contenu
2. Pour un document spécifique, vous pouvez rompre cet héritage et définir des permissions personnalisées

## Intégration avec les workflows

Les documents peuvent être soumis à des processus de validation via le système de workflow:

1. Ouvrez le document concerné
2. Cliquez sur "Démarrer un workflow"
3. Suivez les étapes décrites dans le [Guide du système de workflow](workflow.md)

## Fonctionnalités avancées

### Extraction/Réservation (Check-out/Check-in)

Pour éviter les conflits d'édition, utilisez la fonctionnalité d'extraction:

1. Ouvrez le document concerné
2. Cliquez sur "Extraire" (Check-out)
3. Le document est marqué comme "en cours d'édition" par vous
4. Autres utilisateurs ne peuvent pas modifier le document pendant ce temps
5. Une fois vos modifications terminées, cliquez sur "Libérer" (Check-in)
6. Téléversez la nouvelle version lors de la libération

### Commentaires et discussions

Vous pouvez attacher des commentaires aux documents:

1. Ouvrez le document concerné
2. Accédez à l'onglet "Commentaires"
3. Ajoutez votre commentaire dans le champ prévu
4. Les commentaires sont horodatés et associés à leur auteur
5. Vous pouvez répondre à des commentaires existants

### Abonnements et notifications

Restez informé des modifications sur les documents importants:

1. Ouvrez le document concerné
2. Cliquez sur "S'abonner"
3. Choisissez les événements qui vous intéressent:
   - Nouvelle version
   - Modification des métadonnées
   - Commentaires
   - Changement de statut workflow
4. Vous recevrez des notifications lorsque ces événements se produiront

## Corbeille et récupération

### Accéder à la corbeille

1. Cliquez sur "Corbeille" dans le menu principal
2. Vous y trouverez tous les documents et dossiers supprimés

### Restaurer des éléments

1. Dans la corbeille, sélectionnez l'élément à restaurer
2. Cliquez sur "Restaurer"
3. L'élément retrouve sa place d'origine ou, si ce n'est pas possible, est placé à la racine

### Suppression définitive

1. Dans la corbeille, sélectionnez l'élément à supprimer définitivement
2. Cliquez sur "Supprimer définitivement"
3. Confirmez l'opération (cette action est irréversible)

## Bonnes pratiques

1. **Structure cohérente**: Maintenez une arborescence de dossiers logique et cohérente
2. **Nommage clair**: Utilisez des noms explicites pour vos documents et dossiers
3. **Métadonnées complètes**: Renseignez au minimum le titre et la description
4. **Versionnement discipliné**: Créez une nouvelle version à chaque modification significative
5. **Commentaires utiles**: Décrivez précisément les changements lors de l'ajout d'une version
6. **Permissions adaptées**: N'accordez que les droits nécessaires aux utilisateurs

## Conclusion

Le système de gestion documentaire d'ESAG GED offre toutes les fonctionnalités nécessaires pour organiser, sécuriser et partager efficacement vos documents. En suivant les bonnes pratiques et en utilisant les fonctionnalités avancées, vous pouvez améliorer considérablement la gestion de l'information dans votre organisation.
