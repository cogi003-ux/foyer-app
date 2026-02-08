"""
Module pour gérer la connexion à Supabase
"""
from supabase import create_client, Client
import os
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

TABLE_TACHES = 'taches'
TABLE_MESSAGES = 'messages'
TABLE_CONFIG_FAMILLE = 'config_famille'
TABLE_TACHES_COMPLETEES = 'taches_completees'
TABLE_ATTENTE_VALIDATION = 'attente_validation'
TABLE_CLASSEMENT = 'classement'
TABLE_RECOMPENSES_PERSONNALISEES = 'recompenses_personnalisees'
TABLE_RECOMPENSES_ACHETEES = 'recompenses_achetees'
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def log_debug(message: str):
    """Log uniquement si DEBUG est activé"""
    if DEBUG:
        print(f"[DEBUG] {message}")

def log_error(message: str):
    """Log les erreurs toujours"""
    print(f"[ERROR] {message}")

def get_supabase_client() -> Optional[Client]:
    """
    Crée et retourne un client Supabase
    Retourne None si les variables d'environnement ne sont pas configurées
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    log_debug("Vérification variables d'environnement")
    log_debug(f"SUPABASE_URL présent: {bool(supabase_url)}")
    if supabase_url and DEBUG:
        log_debug(f"SUPABASE_URL longueur: {len(supabase_url)} caractères")
        log_debug(f"SUPABASE_URL commence par: {supabase_url[:20]}...")
    log_debug(f"SUPABASE_KEY présent: {bool(supabase_key)}")
    if supabase_key and DEBUG:
        log_debug(f"SUPABASE_KEY longueur: {len(supabase_key)} caractères")
        log_debug(f"SUPABASE_KEY commence par: {supabase_key[:10]}...")
    
    if not supabase_url or not supabase_key:
        log_error("⚠️  SUPABASE_URL ou SUPABASE_KEY non définis dans les variables d'environnement")
        return None
    
    try:
        log_debug("Création du client Supabase...")
        client = create_client(supabase_url, supabase_key)
        log_debug("Client Supabase créé avec succès")
        return client
    except Exception as e:
        log_error(f"Erreur lors de la création du client Supabase: {type(e).__name__}: {e}")
        if DEBUG:
            import traceback
            log_error("Traceback complet:")
            traceback.print_exc()
        return None

def ensure_table_exists(table_name: str, table_sql: str) -> bool:
    """
    S'assure que la table existe, sinon affiche les instructions SQL
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table(table_name).select('id').limit(1).execute()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if 'relation' in error_msg and 'does not exist' in error_msg:
            print(f"\n⚠️  ATTENTION: La table '{table_name}' n'existe pas dans Supabase!")
            print(f"   Veuillez créer la table en exécutant ce SQL dans Supabase SQL Editor:\n")
            print(table_sql)
            print(f"\n   Ou utilisez le fichier supabase_setup.sql\n")
        return False

# ========== FONCTIONS POUR LES TÂCHES ==========

def get_all_taches() -> List[Dict]:
    """Récupère toutes les tâches depuis Supabase"""
    try:
        client = get_supabase_client()
        if not client:
            log_debug("Client Supabase non disponible")
            return []
        
        try:
            response = client.table(TABLE_TACHES).select('*').order('id', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            error_msg = str(e).lower()
            if 'relation' in error_msg and 'does not exist' in error_msg:
                log_debug(f"Table '{TABLE_TACHES}' n'existe pas encore")
                return []
            else:
                log_error(f"Erreur lors de la récupération des tâches: {e}")
                return []
    except Exception as e:
        log_error(f"Exception dans get_all_taches: {e}")
        return []

def add_tache(tache_data: Dict) -> tuple[bool, str]:
    """
    Ajoute une nouvelle tâche dans Supabase
    Retourne (success: bool, message: str)
    """
    log_debug("===== DÉBUT add_tache =====")
    log_debug(f"Données reçues: {tache_data}")
    
    client = get_supabase_client()
    if not client:
        error_msg = "Supabase non configuré: SUPABASE_URL ou SUPABASE_KEY manquants"
        log_error(error_msg)
        return False, error_msg
    
    # Vérifier que la table existe
    table_sql = f"""
    CREATE TABLE {TABLE_TACHES} (
        id SERIAL PRIMARY KEY,
        nom VARCHAR(255) NOT NULL,
        icone VARCHAR(50) NOT NULL DEFAULT 'sparkles',
        responsable VARCHAR(255),
        responsables TEXT[] DEFAULT ARRAY[]::TEXT[],
        type VARCHAR(20) NOT NULL DEFAULT 'quotidienne' CHECK (type IN ('quotidienne', 'hebdomadaire', 'ponctuelle')),
        points INTEGER NOT NULL DEFAULT 10,
        statut VARCHAR(20) NOT NULL CHECK (statut IN ('a_faire', 'en_cours', 'en_attente', 'termine')),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    log_debug(f"Vérification de l'existence de la table '{TABLE_TACHES}'...")
    if not ensure_table_exists(TABLE_TACHES, table_sql):
        error_msg = f"La table '{TABLE_TACHES}' n'existe pas dans Supabase. Veuillez l'exécuter dans SQL Editor."
        log_error(error_msg)
        return False, error_msg
    log_debug(f"Table '{TABLE_TACHES}' existe")
    
    try:
        # Gérer les responsables (peut être une liste ou une chaîne)
        responsables_list = []
        if 'responsables' in tache_data and tache_data['responsables']:
            # Si c'est une liste
            if isinstance(tache_data['responsables'], list):
                responsables_list = [str(r).strip() for r in tache_data['responsables'] if r and str(r).strip()]
            else:
                responsables_list = [str(tache_data['responsables']).strip()]
        elif 'responsable' in tache_data and tache_data['responsable']:
            # Compatibilité avec l'ancien format
            responsables_list = [str(tache_data['responsable']).strip()]
        
        # Préparer les données pour Supabase
        supabase_data = {
            'nom': str(tache_data.get('nom', '')).strip(),
            'icone': str(tache_data.get('icone', 'sparkles')).strip(),
            'type': str(tache_data.get('type', 'quotidienne')).strip(),
            'points': int(tache_data.get('points', 10)),
            'statut': str(tache_data.get('statut', 'a_faire')).strip(),
            'responsables': responsables_list
        }
        
        # Garder responsable pour compatibilité (premier de la liste)
        if responsables_list:
            supabase_data['responsable'] = responsables_list[0]
        
        log_debug("Données préparées pour Supabase:")
        for key, value in supabase_data.items():
            log_debug(f"  {key}: {repr(value)}")
        
        # Valider les champs requis
        if not supabase_data['nom']:
            error_msg = "Le nom de la tâche est requis"
            log_error(error_msg)
            return False, error_msg
        if not responsables_list:
            error_msg = "Au moins un responsable est requis"
            log_error(error_msg)
            return False, error_msg
        if supabase_data['statut'] not in ['a_faire', 'en_cours', 'en_attente', 'termine']:
            error_msg = "Le statut doit être 'a_faire', 'en_cours', 'en_attente' ou 'termine'"
            log_error(error_msg)
            return False, error_msg
        
        if supabase_data['type'] not in ['quotidienne', 'hebdomadaire', 'ponctuelle']:
            error_msg = "Le type doit être 'quotidienne', 'hebdomadaire' ou 'ponctuelle'"
            log_error(error_msg)
            return False, error_msg
        
        # Insérer dans Supabase
        log_debug(f"Tentative d'insertion dans la table '{TABLE_TACHES}'...")
        response = client.table(TABLE_TACHES).insert(supabase_data).execute()
        
        log_debug("Réponse Supabase reçue")
        log_debug(f"Response.data: {response.data}")
        
        if response.data:
            tache_id = response.data[0].get('id', 'N/A') if response.data else 'N/A'
            log_debug(f"Tâche enregistrée avec succès. ID: {tache_id}")
            return True, "Tâche enregistrée avec succès"
        else:
            error_msg = "Aucune donnée retournée par Supabase"
            log_error(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        log_error("===== ERREUR LORS DE L'AJOUT DE LA TÂCHE =====")
        log_error(f"Type d'erreur: {error_type}")
        log_error(f"Erreur Supabase: {e}")
        if DEBUG:
            import traceback
            log_error("Traceback complet:")
            traceback.print_exc()
        log_error("===========================================")
        
        if 'relation' in error_msg.lower() and 'does not exist' in error_msg.lower():
            return False, f"La table '{TABLE_TACHES}' n'existe pas. Exécutez le SQL dans Supabase SQL Editor."
        elif 'permission denied' in error_msg.lower() or 'unauthorized' in error_msg.lower():
            return False, "Erreur d'authentification Supabase. Vérifiez SUPABASE_KEY."
        else:
            return False, f"Erreur Supabase ({error_type}): {error_msg}"

def delete_tache(tache_id: int) -> bool:
    """Supprime une tâche de Supabase par son ID"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table(TABLE_TACHES).delete().eq('id', tache_id).execute()
        return True
    except Exception as e:
        print(f"Erreur lors de la suppression de la tâche: {e}")
        return False

def update_tache_db(tache_id: int, update_data: Dict) -> bool:
    """Met à jour une tâche dans Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Préparer les données de mise à jour
        supabase_update = {}
        
        if 'statut' in update_data:
            statut = str(update_data['statut']).strip()
            if statut in ['a_faire', 'en_cours', 'en_attente', 'termine']:
                supabase_update['statut'] = statut
        
        if 'type' in update_data:
            type_val = str(update_data['type']).strip()
            if type_val in ['quotidienne', 'hebdomadaire', 'ponctuelle']:
                supabase_update['type'] = type_val
        
        if 'points' in update_data:
            supabase_update['points'] = int(update_data['points'])
        
        if 'nom' in update_data:
            supabase_update['nom'] = str(update_data['nom']).strip()
        
        if 'responsable' in update_data:
            supabase_update['responsable'] = str(update_data['responsable']).strip()
        
        if 'responsables' in update_data:
            # Gérer les responsables (peut être une liste ou une chaîne)
            responsables_list = []
            if isinstance(update_data['responsables'], list):
                responsables_list = [str(r).strip() for r in update_data['responsables'] if r and str(r).strip()]
            else:
                responsables_list = [str(update_data['responsables']).strip()]
            supabase_update['responsables'] = responsables_list
        
        if 'icone' in update_data:
            supabase_update['icone'] = str(update_data['icone']).strip()
        
        if not supabase_update:
            return False
        
        client.table(TABLE_TACHES).update(supabase_update).eq('id', tache_id).execute()
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la tâche: {e}")
        return False

# ========== FONCTIONS POUR LES MESSAGES ==========

def get_all_messages() -> List[Dict]:
    """Récupère tous les messages depuis Supabase"""
    try:
        client = get_supabase_client()
        if not client:
            log_debug("Client Supabase non disponible")
            return []
        
        try:
            response = client.table(TABLE_MESSAGES).select('*').order('id', desc=True).execute()
            rows = response.data if response.data else []
            import json
            out = []
            for row in rows:
                r = dict(row)
                dest = r.get('destinataires')
                if dest is None:
                    r['destinataires'] = ['toute_la_famille']
                elif isinstance(dest, str):
                    try:
                        r['destinataires'] = json.loads(dest) if dest.strip() else ['toute_la_famille']
                    except Exception:
                        r['destinataires'] = ['toute_la_famille']
                elif not isinstance(dest, list):
                    r['destinataires'] = ['toute_la_famille']
                out.append(r)
            return out
        except Exception as e:
            error_msg = str(e).lower()
            if 'relation' in error_msg and 'does not exist' in error_msg:
                log_debug(f"Table '{TABLE_MESSAGES}' n'existe pas encore")
                return []
            else:
                log_error(f"Erreur lors de la récupération des messages: {e}")
                return []
    except Exception as e:
        log_error(f"Exception dans get_all_messages: {e}")
        return []

def add_message(message_data: Dict) -> tuple[bool, str]:
    """
    Ajoute un nouveau message dans Supabase
    Retourne (success: bool, message: str)
    """
    log_debug("===== DÉBUT add_message =====")
    log_debug(f"Données reçues: {message_data}")
    
    client = get_supabase_client()
    if not client:
        error_msg = "Supabase non configuré: SUPABASE_URL ou SUPABASE_KEY manquants"
        log_error(error_msg)
        return False, error_msg
    
    # Vérifier que la table existe
    table_sql = f"""
    CREATE TABLE {TABLE_MESSAGES} (
        id SERIAL PRIMARY KEY,
        auteur VARCHAR(255) NOT NULL,
        texte TEXT NOT NULL,
        destinataires TEXT DEFAULT '["toute_la_famille"]',
        image_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    log_debug(f"Vérification de l'existence de la table '{TABLE_MESSAGES}'...")
    if not ensure_table_exists(TABLE_MESSAGES, table_sql):
        error_msg = f"La table '{TABLE_MESSAGES}' n'existe pas dans Supabase. Veuillez l'exécuter dans SQL Editor."
        log_error(error_msg)
        return False, error_msg
    log_debug(f"Table '{TABLE_MESSAGES}' existe")
    
    try:
        import json
        dest = message_data.get('destinataires')
        if dest is not None:
            destinataires_str = json.dumps(dest) if isinstance(dest, list) else str(dest)
        else:
            destinataires_str = '["toute_la_famille"]'
        supabase_data = {
            'auteur': str(message_data.get('auteur', '')).strip(),
            'texte': str(message_data.get('texte', '')).strip(),
            'destinataires': destinataires_str
        }
        image_url = message_data.get('image_url')
        if image_url and str(image_url).strip():
            supabase_data['image_url'] = str(image_url).strip()
        
        log_debug("Données préparées pour Supabase:")
        for key, value in supabase_data.items():
            log_debug(f"  {key}: {repr(value)}")
        
        # Valider les champs requis
        if not supabase_data['auteur']:
            error_msg = "L'auteur est requis"
            log_error(error_msg)
            return False, error_msg
        if not supabase_data['texte']:
            error_msg = "Le texte du message est requis"
            log_error(error_msg)
            return False, error_msg
        
        # Insérer dans Supabase
        log_debug(f"Tentative d'insertion dans la table '{TABLE_MESSAGES}'...")
        response = client.table(TABLE_MESSAGES).insert(supabase_data).execute()
        
        log_debug("Réponse Supabase reçue")
        log_debug(f"Response.data: {response.data}")
        
        if response.data:
            message_id = response.data[0].get('id', 'N/A') if response.data else 'N/A'
            log_debug(f"Message enregistré avec succès. ID: {message_id}")
            print(f"[FOYER] Message inséré en base avec succès. ID: {message_id}")
            return True, "Message enregistré avec succès"
        else:
            error_msg = "Aucune donnée retournée par Supabase"
            log_error(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        log_error("===== ERREUR LORS DE L'AJOUT DU MESSAGE =====")
        log_error(f"Type d'erreur: {error_type}")
        log_error(f"Erreur Supabase: {e}")
        if DEBUG:
            import traceback
            log_error("Traceback complet:")
            traceback.print_exc()
        log_error("===========================================")
        
        if 'relation' in error_msg.lower() and 'does not exist' in error_msg.lower():
            return False, f"La table '{TABLE_MESSAGES}' n'existe pas. Exécutez le SQL dans Supabase SQL Editor."
        elif 'permission denied' in error_msg.lower() or 'unauthorized' in error_msg.lower():
            return False, "Erreur d'authentification Supabase. Vérifiez SUPABASE_KEY."
        else:
            return False, f"Erreur Supabase ({error_type}): {error_msg}"

def delete_message(message_id: int) -> bool:
    """Supprime un message de Supabase par son ID"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table(TABLE_MESSAGES).delete().eq('id', message_id).execute()
        return True
    except Exception as e:
        print(f"Erreur lors de la suppression du message: {e}")
        return False

# ========== FONCTIONS POUR LA CONFIGURATION FAMILLE ==========

def get_config_famille() -> Dict:
    """Récupère la configuration de la famille"""
    client = get_supabase_client()
    if not client:
        return {
            "parents": ["Papa", "Maman"],
            "ados": [],
            "enfants": ["Enfant 1", "Enfant 2"],
            "points_foyer": 0
        }
    
    try:
        response = client.table(TABLE_CONFIG_FAMILLE).select('*').limit(1).execute()
        if response.data and len(response.data) > 0:
            config = response.data[0]
            return {
                "id": config.get('id'),
                "parents": config.get('parents', []),
                "ados": config.get('ados', []),
                "enfants": config.get('enfants', []),
                "points_foyer": config.get('points_foyer', 0),
                "pin_parent_hash": config.get('pin_parent_hash')
            }
        else:
            # Créer la config par défaut
            default_config = {
                "parents": ["Papa", "Maman"],
                "ados": [],
                "enfants": ["Enfant 1", "Enfant 2"],
                "points_foyer": 0,
                "pin_parent_hash": "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"
            }
            client.table(TABLE_CONFIG_FAMILLE).insert(default_config).execute()
            return default_config
    except Exception as e:
        log_error(f"Erreur lors de la récupération de la config: {e}")
        return {
            "parents": ["Papa", "Maman"],
            "ados": [],
            "enfants": ["Enfant 1", "Enfant 2"],
            "points_foyer": 0
        }

def update_config_famille(config_data: Dict) -> bool:
    """Met à jour la configuration de la famille"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Récupérer l'ID de la config existante
        existing = client.table(TABLE_CONFIG_FAMILLE).select('id').limit(1).execute()
        if existing.data and len(existing.data) > 0:
            config_id = existing.data[0]['id']
            client.table(TABLE_CONFIG_FAMILLE).update(config_data).eq('id', config_id).execute()
        else:
            client.table(TABLE_CONFIG_FAMILLE).insert(config_data).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de la mise à jour de la config: {e}")
        return False

# ========== FONCTIONS POUR L'AUTHENTIFICATION PARENT ==========

import hashlib

def hash_password(password: str) -> str:
    """Hash un mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_parent_pin(input_pin: str) -> bool:
    """Vérifie si le PIN parent est correct"""
    config = get_config_famille()
    stored_hash = config.get('pin_parent_hash', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4')
    input_hash = hash_password(input_pin)
    return input_hash == stored_hash

# ========== FONCTIONS POUR LES TÂCHES COMPLÉTÉES ==========

def add_tache_completee(task_data: Dict) -> bool:
    """Ajoute une tâche complétée à l'historique"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        supabase_data = {
            'task_id': task_data.get('task_id'),
            'task_nom': str(task_data.get('task_nom', '')).strip(),
            'user_name': str(task_data.get('user_name', '')).strip(),
            'date_completion': str(task_data.get('date_completion', '')),
            'points': int(task_data.get('points', 0)),
            'validated': bool(task_data.get('validated', False))
        }
        client.table(TABLE_TACHES_COMPLETEES).insert(supabase_data).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de l'ajout de la tâche complétée: {e}")
        return False

def get_taches_completees(user_name: str = None, date_start: str = None, date_end: str = None) -> List[Dict]:
    """Récupère les tâches complétées avec filtres optionnels"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        query = client.table(TABLE_TACHES_COMPLETEES).select('*')
        
        if user_name:
            query = query.eq('user_name', user_name)
        if date_start:
            query = query.gte('date_completion', date_start)
        if date_end:
            query = query.lte('date_completion', date_end)
        
        response = query.order('date_completion', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        log_error(f"Erreur lors de la récupération des tâches complétées: {e}")
        return []

# ========== FONCTIONS POUR L'ATTENTE DE VALIDATION ==========

def add_attente_validation(validation_data: Dict) -> bool:
    """Ajoute une tâche en attente de validation"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        supabase_data = {
            'user_name': str(validation_data.get('user_name', '')).strip(),
            'task_nom': str(validation_data.get('task_nom', '')).strip(),
            'task_id': validation_data.get('task_id'),
            'points': int(validation_data.get('points', 0)),
            'date_completion': str(validation_data.get('date_completion', ''))
        }
        client.table(TABLE_ATTENTE_VALIDATION).insert(supabase_data).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de l'ajout en attente: {e}")
        return False

def get_attente_validation(user_name: str = None) -> List[Dict]:
    """Récupère les tâches en attente de validation"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        query = client.table(TABLE_ATTENTE_VALIDATION).select('*')
        if user_name:
            query = query.eq('user_name', user_name)
        response = query.order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        log_error(f"Erreur lors de la récupération de l'attente: {e}")
        return []

def delete_attente_validation(validation_id: int) -> bool:
    """Supprime une validation en attente"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table(TABLE_ATTENTE_VALIDATION).delete().eq('id', validation_id).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de la suppression: {e}")
        return False

# ========== FONCTIONS POUR LE CLASSEMENT ==========

def get_classement() -> List[Dict]:
    """Récupère le classement des points"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        response = client.table(TABLE_CLASSEMENT).select('*').order('points', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        log_error(f"Erreur lors de la récupération du classement: {e}")
        return []

def update_classement(user_name: str, points: int) -> bool:
    """Met à jour ou crée une entrée dans le classement.
    Les points sont attribués au Héros (user_name = exécutant de la quête),
    jamais à la personne qui valide (parent)."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Vérifier si l'utilisateur existe
        existing = client.table(TABLE_CLASSEMENT).select('*').eq('user_name', user_name).execute()
        if existing.data and len(existing.data) > 0:
            # Mettre à jour
            current_points = existing.data[0].get('points', 0)
            client.table(TABLE_CLASSEMENT).update({'points': current_points + points}).eq('user_name', user_name).execute()
        else:
            # Créer
            client.table(TABLE_CLASSEMENT).insert({'user_name': user_name, 'points': points}).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de la mise à jour du classement: {e}")
        return False

# ========== FONCTIONS POUR LES RÉCOMPENSES ==========

def get_recompenses_personnalisees() -> List[Dict]:
    """Récupère les récompenses personnalisées"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        response = client.table(TABLE_RECOMPENSES_PERSONNALISEES).select('*').order('id', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        log_error(f"Erreur lors de la récupération des récompenses: {e}")
        return []

def add_recompense_personnalisee(recompense_data: Dict) -> bool:
    """Ajoute une récompense personnalisée"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        supabase_data = {
            'nom': str(recompense_data.get('nom', '')).strip(),
            'emoji': str(recompense_data.get('emoji', '🎁')).strip(),
            'description': str(recompense_data.get('description', '')).strip(),
            'points': int(recompense_data.get('points', 0)),
            'couleur_gradient': str(recompense_data.get('couleur_gradient', ''))
        }
        client.table(TABLE_RECOMPENSES_PERSONNALISEES).insert(supabase_data).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de l'ajout de la récompense: {e}")
        return False

def get_recompenses_achetees() -> List[Dict]:
    """Récupère les récompenses achetées"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        response = client.table(TABLE_RECOMPENSES_ACHETEES).select('*').order('date_achat', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        log_error(f"Erreur lors de la récupération des récompenses achetées: {e}")
        return []

def add_recompense_achetee(recompense_data: Dict) -> bool:
    """Ajoute une récompense achetée"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        supabase_data = {
            'recompense_id': recompense_data.get('recompense_id'),
            'recompense_nom': str(recompense_data.get('recompense_nom', '')).strip(),
            'points_utilises': int(recompense_data.get('points_utilises', 0)),
            'date_achat': str(recompense_data.get('date_achat', ''))
        }
        client.table(TABLE_RECOMPENSES_ACHETEES).insert(supabase_data).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de l'ajout de la récompense achetée: {e}")
        return False
