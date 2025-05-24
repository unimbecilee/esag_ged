# 📄 Workflow Documentaire – ESAG GED

Ce document décrit le circuit de traitement des documents dans l’application GED (Gestion Électronique de Documents) de l’université **ESAG-NDE**. Certaines données sensibles ont été remplacées par des exemples fictifs.

---

## Acteurs impliqués

| Acteur               | Rôle principal                              | Exemple                          |
|----------------------|---------------------------------------------|----------------------------------|
| **Secrétariat**      | Saisie, numérisation et gestion des pièces  | Secrétaire pédagogique           |
| **Direction**        | Validation ou rejet des documents importants| Directeur des études             |
| **Professeurs**      | Consultation                                | Responsable de filière           |
| **Étudiants**        | Consultation                                | Étudiant inscrit                 |
| **Administrateur**   | Gestion des utilisateurs & audit            | Responsable système              |

---

## 🔄 Étapes du Workflow

| Étape | Description | Acteur concerné | Exemple |
|-------|-------------|------------------|---------|
| 1. Numérisation / Upload | Un document papier ou numérique est scanné ou téléversé dans l'application. | Secrétariat, Professeurs | Certificat de scolarité |
| 2. Attribution des métadonnées | Ajout du titre, description, type, propriétaire, etc. | Secrétariat | “Relevé S1 2024 - Étudiant X” |
| 3. Vérification / Validation | Lecture et validation (ou rejet) par la direction. | Direction | Validation d’un PV de jury |
| 4. Classement & Archivage | Le document est classé dans un dossier logique (catégorie). | Système automatisé / Secrétariat | “Notes / Semestre 1” |
| 5. Accès & Consultation | Le document est accessible selon les rôles définis. | Professeurs / Étudiants | Téléchargement par étudiant |
| 6. Historisation | Chaque action est enregistrée : qui a fait quoi, quand ? | Automatique (système) | Téléchargement le 10/04/25 |
| 7. Corbeille / Suppression | En cas d’erreur, un document peut être mis en corbeille (retraçable). | Secrétariat / Admin | Suppression d’une pièce erronée |
| 8. Recherche / OCR | Recherche textuelle dans le contenu ou les métadonnées. | Tous les rôles habilités | “PV Jury 2023” |

---

## Types de documents gérés

- Bulletins de notes
- Attestations de réussite
- PV de jury
- Dossiers d’inscription
- Pièces justificatives
- Reçus et factures
- Documents scannés (PDF, Images, Word)

---

## Sécurité & Confidentialité

| Élément | Mesures mises en place |
|--------|-------------------------|
| Accès | Restreint selon le rôle |
| Connexions | Session Flask, hash des mots de passe |
| Historique | Journalisation automatique |
| Corbeille | Suppression logique avant suppression physique |

---

## Exemple de scénario

1. **Secrétaire** scanne le **relevé de notes** de l’étudiant Jean Dupont.
2. Elle le téléverse avec le titre "Relevé S2 – Jean Dupont".
3. Le document est transmis à la **Direction** pour validation.
4. Une fois validé, le document est **archivé** dans le dossier "Notes / 2024".
5. **Jean Dupont** consulte son document depuis son espace personnel.
6. Le système trace la consultation dans l’**historique**.


---

## 📌 Remarques

- Ce modèle est **évolutif** : il pourra être complété avec d'autres cas d’usage comme la signature électronique, la notification automatique ou les alertes.

---

