#!/usr/bin/env python3
"""Script pour analyser le problème des workflows"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_workflow_issue():
    """Analyse le problème des workflows en attente"""
    print("=== ANALYSE DU PROBLÈME DES WORKFLOWS EN ATTENTE ===")
    
    print("\n1. PROBLÈMES IDENTIFIÉS :")
    print("   - Connexion à la base de données échoue avec le mot de passe")
    print("   - Les validations en attente ne s'affichent pas")
    print("   - Le rôle 'chef_de_service' ne récupère pas les validations")
    
    print("\n2. POINTS À VÉRIFIER :")
    print("   a) Configuration des rôles dans la base de données")
    print("   b) Mapping des rôles dans le service de validation")
    print("   c) Requête SQL pour récupérer les validations")
    print("   d) Authentification et envoi du token")
    
    print("\n3. SOLUTIONS POSSIBLES :")
    print("   a) Vérifier que le workflow de validation existe")
    print("   b) Vérifier que les étapes sont correctement configurées")
    print("   c) Vérifier que les approbateurs sont assignés aux bonnes étapes")
    print("   d) Vérifier que les instances de workflow sont créées")
    
    print("\n4. VÉRIFICATIONS FRONTEND :")
    print("   - Le token d'authentification est-il envoyé ?")
    print("   - L'API /api/validation-workflow/pending est-elle appelée ?")
    print("   - Y a-t-il des erreurs dans la console du navigateur ?")
    
    print("\n5. VÉRIFICATIONS BACKEND :")
    print("   - L'endpoint /api/validation-workflow/pending fonctionne-t-il ?")
    print("   - La méthode get_pending_approvals retourne-t-elle des données ?")
    print("   - Y a-t-il des erreurs dans les logs du serveur ?")
    
    print("\n6. RECOMMANDATIONS IMMÉDIATES :")
    print("   1. Vérifier les logs du serveur Flask lors de l'appel à l'API")
    print("   2. Tester l'API directement avec curl ou Postman")
    print("   3. Ajouter des logs dans le frontend pour voir les réponses")
    print("   4. Vérifier que l'utilisateur connecté a bien le rôle 'chef_de_service'")
    
    print("\n7. POINTS CRITIQUES À VÉRIFIER :")
    print("   - Le rôle dans la base de données correspond-il exactement à 'chef_de_service' ?")
    print("   - Y a-t-il des instances de workflow avec le statut 'EN_COURS' ?")
    print("   - Les workflow_approbateur sont-ils correctement configurés ?")
    
    print("\n8. ÉTAPES DE DÉBOGAGE :")
    print("   1. Démarrer le serveur Flask en mode debug")
    print("   2. Ouvrir la console du navigateur")
    print("   3. Aller sur la page des workflows")
    print("   4. Vérifier les requêtes réseau dans l'onglet Network")
    print("   5. Vérifier les logs du serveur")
    
    print("\n=== SCRIPT DE TEST POUR L'API ===")
    print("curl -X GET http://localhost:5000/api/validation-workflow/pending \\")
    print("  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \\")
    print("  -H 'Content-Type: application/json'")
    
    print("\n=== COMMANDES POUR DÉMARRER LE SERVEUR ===")
    print("python main.py")
    print("# Puis dans un autre terminal :")
    print("curl -X GET http://localhost:5000/api/validation-workflow/pending -H 'Authorization: Bearer TOKEN'")

if __name__ == '__main__':
    analyze_workflow_issue() 