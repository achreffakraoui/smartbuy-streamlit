"""
SmartBuy - Gestionnaire d'authentification
Système complet avec base de données et sécurité
"""

import streamlit as st
import hashlib
import datetime
import re

class AuthManager:
    """Gestionnaire d'authentification sécurisé"""
    
    def __init__(self, db):
        self.db = db
    
    def hash_password(self, password):
        """Hash le mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email):
        """Valide le format de l'email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Valide la force du mot de passe"""
        if len(password) < 6:
            return False, "Le mot de passe doit contenir au moins 6 caractères"
        if not re.search(r'[A-Za-z]', password):
            return False, "Le mot de passe doit contenir au moins une lettre"
        if not re.search(r'[0-9]', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        return True, "Mot de passe valide"
    
    def render(self):
        """Affiche l'interface d'authentification"""
        st.markdown("""
        <div style='background: linear-gradient(135deg, #6c757d 0%, #495057 100%); 
                    padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;'>
            <h1 style='color: white; font-size: 2.2rem; margin: 0;'>🛒 SmartBuy</h1>
            <p style='color: white; font-size: 1rem; margin-top: 0.8rem;'>
                Achetez malin, vivez mieux
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Onglets de connexion/inscription
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        with tab1:
            self.show_login_form()
        
        with tab2:
            self.show_register_form()
    
    def show_login_form(self):
        """Affiche le formulaire de connexion"""
        st.markdown("### 🔐 Connexion à votre compte")
        
        with st.form("login_form"):
            username = st.text_input("👤 Nom d'utilisateur", placeholder="Votre nom d'utilisateur")
            password = st.text_input("🔒 Mot de passe", type="password", placeholder="Votre mot de passe")
            
            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button("🚀 Se connecter", type="primary", use_container_width=True)
            with col2:
                forgot_button = st.form_submit_button("🔑 Mot de passe oublié ?", use_container_width=True)
            
            if login_button and username and password:
                result = self.authenticate_user(username, password)
                if result["success"]:
                    st.session_state.user = result["user"]
                    st.session_state.authenticated = True
                    st.success(f"Bienvenue {result['user']['full_name']} ! 🎉")
                    st.session_state.page = 'home'
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
            
            if forgot_button:
                self.show_forgot_password()
    
    def show_register_form(self):
        """Affiche le formulaire d'inscription"""
        st.markdown("### 📝 Créer un nouveau compte")
        
        # Vérifier si un compte vient d'être créé
        if 'account_created_success' in st.session_state and st.session_state.account_created_success:
            # Afficher seulement le message de succès
            st.success("🎉 Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
            st.balloons()
            st.info("👉 Cliquez sur l'onglet **Connexion** ci-dessus pour vous connecter avec votre nouveau compte.")
            
            # Bouton pour créer un autre compte
            if st.button("➕ Créer un autre compte", use_container_width=True, type="primary"):
                del st.session_state.account_created_success
                st.rerun()
            
            return
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("👤 Nom complet *", placeholder="Jean Dupont")
                username = st.text_input("🏷️ Nom d'utilisateur *", placeholder="jeandupont")
                email = st.text_input("📧 Email *", placeholder="jean@example.com")
            
            with col2:
                phone = st.text_input("📱 Téléphone", placeholder="+33 6 12 34 56 78")
                password = st.text_input("🔒 Mot de passe *", type="password", placeholder="Minimum 6 caractères")
                confirm_password = st.text_input("🔒 Confirmer *", type="password", placeholder="Confirmer le mot de passe")
            
            address = st.text_area("🏠 Adresse", placeholder="123 Rue de la Mode, 75001 Paris")
            
            # Conditions d'utilisation
            accept_terms = st.checkbox("J'accepte les conditions d'utilisation et la politique de confidentialité *")
            newsletter = st.checkbox("Je souhaite recevoir la newsletter SmartBuy")
            
            register_button = st.form_submit_button("✨ Créer mon compte", type="primary", use_container_width=True)
            
            if register_button:
                # Validation des champs
                if not all([full_name, username, email, password, confirm_password]):
                    st.error("❌ Veuillez remplir tous les champs obligatoires (*)")
                elif not accept_terms:
                    st.error("❌ Vous devez accepter les conditions d'utilisation")
                elif password != confirm_password:
                    st.error("❌ Les mots de passe ne correspondent pas")
                elif not self.validate_email(email):
                    st.error("❌ Format d'email invalide")
                else:
                    # Validation du mot de passe
                    is_valid, message = self.validate_password(password)
                    if not is_valid:
                        st.error(f"❌ {message}")
                    else:
                        # Créer le compte
                        result = self.create_user(username, email, password, full_name, phone, address)
                        if result["success"]:
                            # Marquer le compte comme créé
                            st.session_state.account_created_success = True
                            st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")
    
    def show_forgot_password(self):
        """Affiche l'interface de récupération de mot de passe"""
        st.markdown("### 🔑 Récupération de mot de passe")
        
        with st.form("forgot_password_form"):
            email = st.text_input("📧 Votre email", placeholder="Entrez votre adresse email")
            
            if st.form_submit_button("📤 Envoyer le lien de récupération", type="primary"):
                if email and self.validate_email(email):
                    # Simuler l'envoi d'email
                    st.success("📧 Un lien de récupération a été envoyé à votre adresse email !")
                    st.info("Vérifiez votre boîte de réception et vos spams.")
                else:
                    st.error("❌ Veuillez entrer une adresse email valide")
    
    def authenticate_user(self, username, password):
        """Authentifie un utilisateur via la base de données"""
        return self.db.authenticate_user(username, password)
    
    def create_user(self, username, email, password, full_name, phone="", address=""):
        """Crée un nouveau utilisateur via la base de données"""
        return self.db.create_user(username, email, password, full_name, phone, address)
    
    def logout(self):
        """Déconnecte l'utilisateur"""
        # Nettoyer les variables de session
        keys_to_remove = ['user', 'authenticated', 'cart', 'order_confirmed']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        # Rediriger vers la page de connexion
        st.session_state.page = 'login'
        st.success("👋 Vous avez été déconnecté avec succès")
    
    def is_authenticated(self):
        """Vérifie si l'utilisateur est connecté"""
        return st.session_state.get('user') is not None
    
    def get_current_user(self):
        """Récupère l'utilisateur actuel"""
        return st.session_state.get('user', None)
    
    def require_auth(self):
        """Décorateur pour les pages nécessitant une authentification"""
        if not self.is_authenticated():
            st.warning("🔐 Vous devez être connecté pour accéder à cette page")
            st.session_state.page = 'login'
            st.rerun()
            return False
        return True