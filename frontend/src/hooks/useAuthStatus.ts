import { useState, useEffect } from 'react';
import config from '../config';

const API_URL = config.API_URL;

type AuthStatus = {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: any | null;
};

export const useAuthStatus = (): AuthStatus => {
  const [status, setStatus] = useState<AuthStatus>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
  });

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Vérifier si un token existe dans le localStorage
        const token = localStorage.getItem('token');
        
        console.log("Token trouvé dans localStorage:", token ? "Oui" : "Non");
        
        if (!token) {
          console.log("Aucun token trouvé, déconnecté");
          setStatus({
            isAuthenticated: false,
            isLoading: false,
            user: null,
          });
          return;
        }

        // Essayer de récupérer les données utilisateur du localStorage
        const userStr = localStorage.getItem('user');
        let user = null;
        
        if (userStr) {
          try {
            user = JSON.parse(userStr);
            console.log("Données utilisateur trouvées dans localStorage:", user);
          } catch (e) {
            console.error("Erreur lors du parsing des données utilisateur:", e);
          }
        }

        // Vérifier si le token est valide avec une requête à l'API
        try {
          console.log("Tentative de vérification du token à l'URL:", `${API_URL}/api/auth/me`);
          const response = await fetch(`${API_URL}/api/auth/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            credentials: 'include',
          });

          console.log("Réponse de vérification:", response.status);
          
          if (response.ok) {
            const userData = await response.json();
            console.log("Vérification réussie, données utilisateur:", userData);
            setStatus({
              isAuthenticated: true,
              isLoading: false,
              user: userData,
            });
          } else {
            console.log("Vérification échouée, token invalide");
            // Si le token n'est pas valide, nettoyer le localStorage
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setStatus({
              isAuthenticated: false,
              isLoading: false,
              user: null,
            });
          }
        } catch (error) {
          console.log("Erreur lors de la vérification API, mais token présent - considéré comme authentifié");
          // En cas d'erreur de connexion à l'API, si on a un token et des données utilisateur,
          // on considère l'utilisateur comme authentifié pour éviter les problèmes de connexion
          if (token && user) {
            setStatus({
              isAuthenticated: true,
              isLoading: false,
              user: user,
            });
          } else {
            setStatus({
              isAuthenticated: false,
              isLoading: false,
              user: null,
            });
          }
        }
      } catch (error) {
        console.error('Error verifying authentication status:', error);
        setStatus({
          isAuthenticated: false,
          isLoading: false,
          user: null,
        });
      }
    };

    checkAuthStatus();
  }, []);

  return status;
}; 
