"""
FashionAI - Gestionnaire de base de données
Système complet avec SQLite pour la persistance des données
"""

import sqlite3
import hashlib
import datetime
import json
import os

class Database:
    """Gestionnaire de base de données pour FashionAI"""
    
    def __init__(self, db_path="fashionai.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données avec toutes les tables nécessaires"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Table du panier d'achat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des commandes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount REAL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                shipping_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des interactions utilisateur (pour l'IA)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                interaction_type TEXT,
                search_query TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table de l'historique de navigation (pour recommandations personnalisées)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                product_id INTEGER,
                action_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash le mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, email, password, full_name, phone="", address=""):
        """Crée un nouveau utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, phone, address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, phone, address))
            
            user_id = cursor.lastrowid
            conn.commit()
            return {"success": True, "user_id": user_id}
        
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return {"success": False, "error": "Ce nom d'utilisateur est déjà pris"}
            elif "email" in str(e):
                return {"success": False, "error": "Cette adresse email est déjà utilisée"}
            else:
                return {"success": False, "error": "Erreur lors de la création du compte"}
        except Exception as e:
            return {"success": False, "error": f"Erreur inattendue: {str(e)}"}
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        """Authentifie un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                SELECT id, username, email, full_name, phone, address FROM users 
                WHERE username = ? AND password_hash = ? AND is_active = 1
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                # Mettre à jour la dernière connexion
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user[0],))
                conn.commit()
                
                return {
                    "success": True,
                    "user": {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "full_name": user[3],
                        "phone": user[4],
                        "address": user[5]
                    }
                }
            else:
                return {"success": False, "error": "Nom d'utilisateur ou mot de passe incorrect"}
        
        except Exception as e:
            return {"success": False, "error": f"Erreur d'authentification: {str(e)}"}
        finally:
            conn.close()
    
    def add_to_cart(self, user_id, product_id, quantity=1):
        """Ajoute un produit au panier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            ''', (user_id, product_id, quantity))
            
            conn.commit()
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def log_interaction(self, user_id, product_id=None, interaction_type="view", search_query=None):
        """Enregistre une interaction utilisateur pour l'IA"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_interactions (user_id, product_id, interaction_type, search_query)
                VALUES (?, ?, ?, ?)
            ''', (user_id, product_id, interaction_type, search_query))
            
            conn.commit()
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def add_user_history(self, user_id, category, product_id=None, action_type="view"):
        """Enregistre l'historique de navigation utilisateur pour recommandations personnalisées"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_history (user_id, category, product_id, action_type)
                VALUES (?, ?, ?, ?)
            ''', (user_id, category, product_id, action_type))
            
            conn.commit()
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def get_user_preferred_categories(self, user_id, limit=10):
        """Récupère les catégories préférées de l'utilisateur basées sur l'historique récent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Récupérer les dernières interactions (limit dernières)
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM user_history
                WHERE user_id = ?
                GROUP BY category
                ORDER BY MAX(created_at) DESC, count DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            
            # Retourner les catégories triées par fréquence
            preferred_categories = [row[0] for row in results if row[0]]
            return preferred_categories
        
        except Exception as e:
            return []
        finally:
            conn.close()