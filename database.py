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
TABLE_BUDGET_FAMILIAL = 'budget_familial'
TABLE_BUDGET_RECURRENCE_EXCEPTIONS = 'budget_recurrence_exceptions'
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


def update_tache_completee_validated(record_id: int) -> bool:
    """Marque une tâche complétée comme validée (validated = TRUE)."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table(TABLE_TACHES_COMPLETEES).update({'validated': True}).eq('id', record_id).execute()
        return True
    except Exception as e:
        log_error(f"Erreur lors de la mise à jour validated: {e}")
        return False


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
    """
    Récupère TOUTES les tâches en attente de validation.
    Source : table attente_validation (toutes les complétions passent par ici).
    Aucun filtre par utilisateur : toute la famille voit tout ce qui est à valider.
    """
    client = get_supabase_client()
    if not client:
        return []
    try:
        query = client.table(TABLE_ATTENTE_VALIDATION).select('*')
        response = query.order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        log_error(f"Erreur lors de la récupération de l'attente: {e}")
        return []


def validate_attente_and_mark_completee(validation_id: int) -> bool:
    """
    Quand le parent valide : supprime la ligne de attente_validation ET
    met à jour la ligne correspondante dans taches_completees (validated = TRUE).
    """
    client = get_supabase_client()
    if not client:
        return False
    try:
        row = client.table(TABLE_ATTENTE_VALIDATION).select('*').eq('id', validation_id).execute()
        if not row.data or len(row.data) == 0:
            log_error(f"validate_attente: id {validation_id} introuvable dans attente_validation")
            return False
        v = row.data[0]
        task_id = v.get('task_id')
        task_nom = str(v.get('task_nom') or '').strip()
        user_name = str(v.get('user_name') or '').strip()
        date_completion = str(v.get('date_completion') or '')
        client.table(TABLE_ATTENTE_VALIDATION).delete().eq('id', validation_id).execute()
        q = (
            client.table(TABLE_TACHES_COMPLETEES)
            .select('id, task_id, task_nom')
            .eq('user_name', user_name)
            .eq('date_completion', date_completion)
            .eq('validated', False)
        )
        resp = q.execute()
        if not resp.data:
            return True
        for r in resp.data:
            rid = r.get('id')
            if task_id is not None and r.get('task_id') == task_id:
                client.table(TABLE_TACHES_COMPLETEES).update({'validated': True}).eq('id', rid).execute()
                return True
            if (r.get('task_nom') or '').strip() == task_nom:
                client.table(TABLE_TACHES_COMPLETEES).update({'validated': True}).eq('id', rid).execute()
                return True
        return True
    except Exception as e:
        log_error(f"Erreur validate_attente_and_mark_completee: {e}")
        return False


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


# ========== FONCTIONS POUR LE BUDGET FAMILIAL ==========

BUDGET_TABLE_SQL = f"""
CREATE TABLE {TABLE_BUDGET_FAMILIAL} (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL CHECK (type IN ('revenu', 'depense')),
    nom VARCHAR(255) NOT NULL,
    montant NUMERIC(12, 2) NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'prevu' CHECK (statut IN ('prevu', 'paye')),
    date_echeance DATE,
    frequence VARCHAR(20) NOT NULL DEFAULT 'une_fois' CHECK (frequence IN ('une_fois', 'mensuel', 'trimestriel')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

# Exécuter ce SQL dans Supabase (SQL Editor) pour activer "Supprimer uniquement ce mois" sur les récurrences :
BUDGET_EXCEPTIONS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_BUDGET_RECURRENCE_EXCEPTIONS} (
    source_id INTEGER NOT NULL REFERENCES {TABLE_BUDGET_FAMILIAL}(id) ON DELETE CASCADE,
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    PRIMARY KEY (source_id, annee, mois)
);
"""

def _parse_date(d) -> Optional[tuple]:
    """Retourne (year, month, day) ou None."""
    if not d:
        return None
    try:
        if isinstance(d, str):
            parts = d.split('-')
            if len(parts) >= 3:
                return int(parts[0]), int(parts[1]), int(parts[2])
            return None
        return getattr(d, 'year', None), getattr(d, 'month', None), getattr(d, 'day', None)
    except (ValueError, TypeError):
        return None


def _synthetic_id(source_id: int, annee: int, mois: int, day: int) -> int:
    """Encode (source_id, annee, mois, day) en un id négatif unique."""
    return -((source_id * 100000000) + (annee * 10000) + (mois * 100) + min(day, 31))


def _decode_synthetic_id(synthetic_id: int) -> Optional[int]:
    """Extrait le source_id d'un id synthétique (pour mettre à jour la ligne source)."""
    if synthetic_id >= 0:
        return None
    n = -synthetic_id
    return n // 100000000


def _decode_synthetic_id_full(synthetic_id: int) -> Optional[tuple]:
    """Extrait (source_id, annee, mois, day) d'un id synthétique. Retourne None si invalide."""
    if synthetic_id >= 0:
        return None
    try:
        n = -synthetic_id
        source_id = n // 100000000
        rest = n % 100000000
        annee = rest // 10000
        rest = rest % 10000
        mois = rest // 100
        day = rest % 100
        return (source_id, annee, mois, day)
    except Exception:
        return None


def get_recurrence_exceptions(annee: int, mois: int) -> set:
    """Retourne l'ensemble des source_id à ne pas projeter pour (annee, mois)."""
    client = get_supabase_client()
    if not client:
        return set()
    try:
        r = client.table(TABLE_BUDGET_RECURRENCE_EXCEPTIONS).select('source_id').eq('annee', annee).eq('mois', mois).execute()
        if r.data:
            return {int(x['source_id']) for x in r.data}
        return set()
    except Exception as e:
        error_msg = str(e).lower()
        if 'relation' in error_msg and 'does not exist' in error_msg:
            log_debug(f"Table '{TABLE_BUDGET_RECURRENCE_EXCEPTIONS}' n'existe pas encore")
            return set()
        log_error(f"Erreur get_recurrence_exceptions: {e}")
        return set()


def add_recurrence_exception(source_id: int, annee: int, mois: int) -> bool:
    """Enregistre une exception : ne pas afficher la récurrence source_id pour ce mois."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table(TABLE_BUDGET_RECURRENCE_EXCEPTIONS).upsert(
            {'source_id': source_id, 'annee': annee, 'mois': mois},
            on_conflict='source_id,annee,mois'
        ).execute()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if 'relation' in error_msg and 'does not exist' in error_msg:
            log_debug(f"Table '{TABLE_BUDGET_RECURRENCE_EXCEPTIONS}' n'existe pas. Exécutez BUDGET_EXCEPTIONS_TABLE_SQL dans Supabase.")
            return False
        log_error(f"Erreur add_recurrence_exception: {e}")
        return False


def delete_recurrence_this_month(synthetic_id: int) -> bool:
    """Supprime uniquement l'occurrence de ce mois (la récurrence réapparaîtra le mois suivant)."""
    decoded = _decode_synthetic_id_full(synthetic_id)
    if not decoded:
        return False
    source_id, annee, mois = decoded[0], decoded[1], decoded[2]
    return add_recurrence_exception(source_id, annee, mois)


def stop_recurrence(source_id: int) -> bool:
    """Passe la dépense d'origine en frequence 'une_fois' (arrêt de la récurrence pour tous les mois futurs)."""
    return update_budget_familial(source_id, {'frequence': 'une_fois'})


def get_all_budget_familial(annee: Optional[int] = None, mois: Optional[int] = None) -> List[Dict]:
    """
    Récupère les entrées du budget familial pour le mois demandé.
    - Entrées dont date_echeance est dans ce mois.
    - Pour le mois en cours : entrées sans date (NULL).
    - Entrées récurrentes mensuelles : toutes les lignes des mois précédents avec frequence='mensuel'
      sont projetées dans le mois demandé (même jour), statut='prevu'.
    - Entrées récurrentes trimestrielles : lignes dont l'écart avec le mois demandé est 3, 6, 9... mois,
      projetées dans le mois demandé (même jour), statut='prevu'.
    Optimisation : au plus 4 requêtes SQL par appel (pas de boucle SQL par ligne, pas de N+1).
    """
    client = get_supabase_client()
    if not client:
        return []
    try:
        from calendar import monthrange
        now = datetime.now()
        if annee is not None and mois is not None:
            annee, mois = int(annee), int(mois)
            last = monthrange(annee, mois)[1]
            start = f"{annee}-{mois:02d}-01"
            end = f"{annee}-{mois:02d}-{last:02d}"
            query = client.table(TABLE_BUDGET_FAMILIAL).select('*').gte('date_echeance', start).lte('date_echeance', end)
            response = query.order('date_echeance', desc=False).order('id', desc=False).execute()
            data = list(response.data) if response.data else []
            real_keys = {(r.get('nom'), r.get('type'), r.get('date_echeance')) for r in data}

            if annee == now.year and mois == now.month:
                null_resp = client.table(TABLE_BUDGET_FAMILIAL).select('*').is_('date_echeance', 'null').execute()
                null_data = null_resp.data if null_resp.data else []
                ids_in_range = {r['id'] for r in data}
                for r in null_data:
                    if r.get('id') not in ids_in_range:
                        data.append(dict(r))
                        real_keys.add((r.get('nom'), r.get('type'), r.get('date_echeance')))

            exceptions = get_recurrence_exceptions(annee, mois)
            recur_resp = client.table(TABLE_BUDGET_FAMILIAL).select('*').in_('frequence', ['mensuel', 'trimestriel']).execute()
            recur_rows = recur_resp.data if recur_resp.data else []
            for r in recur_rows:
                if r.get('id') in exceptions:
                    continue
                parsed = _parse_date(r.get('date_echeance'))
                if not parsed:
                    continue
                ry, rm, rd = parsed
                freq = (r.get('frequence') or '').lower()
                if freq == 'mensuel':
                    if (annee, mois) < (ry, rm):
                        continue
                elif freq == 'trimestriel':
                    diff_months = (annee * 12 + mois) - (ry * 12 + rm)
                    if diff_months < 0 or diff_months % 3 != 0:
                        continue
                else:
                    continue
                last_day = monthrange(annee, mois)[1]
                day = min(rd, last_day)
                proj_date = f"{annee}-{mois:02d}-{day:02d}"
                if (r.get('nom'), r.get('type'), proj_date) in real_keys:
                    continue
                real_keys.add((r.get('nom'), r.get('type'), proj_date))
                synthetic = {
                    'id': _synthetic_id(r['id'], annee, mois, day),
                    'type': r.get('type'),
                    'nom': r.get('nom'),
                    'montant': r.get('montant'),
                    'statut': 'prevu',
                    'date_echeance': proj_date,
                    'frequence': freq,
                    'est_recurrent': True,
                }
                data.append(synthetic)
            data.sort(key=lambda x: (x.get('date_echeance') or '9999-99-99', x.get('id') or 0))
            return data
        response = client.table(TABLE_BUDGET_FAMILIAL).select('*').order('date_echeance', desc=False).order('id', desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        error_msg = str(e).lower()
        if 'relation' in error_msg and 'does not exist' in error_msg:
            log_debug(f"Table '{TABLE_BUDGET_FAMILIAL}' n'existe pas encore")
            return []
        log_error(f"Erreur lors de la récupération du budget: {e}")
        return []


def add_budget_familial(data: Dict) -> tuple[bool, str]:
    """
    Ajoute une entrée au budget familial.
    data: type (revenu/depense), nom, montant, statut (prevu/paye), date_echeance (optionnel), frequence (optionnel: une_fois, mensuel, trimestriel).
    Retourne (success, message).
    """
    client = get_supabase_client()
    if not client:
        return False, "Supabase non configuré"
    if not ensure_table_exists(TABLE_BUDGET_FAMILIAL, BUDGET_TABLE_SQL):
        return False, f"La table '{TABLE_BUDGET_FAMILIAL}' n'existe pas. Exécutez le SQL dans Supabase."
    try:
        type_val = str(data.get('type', '')).strip().lower()
        if type_val not in ('revenu', 'depense'):
            return False, "type doit être 'revenu' ou 'depense'"
        statut = str(data.get('statut', 'prevu')).strip().lower()
        if statut not in ('prevu', 'paye'):
            return False, "statut doit être 'prevu' ou 'paye'"
        nom = str(data.get('nom', '')).strip()
        if not nom:
            return False, "Le nom est requis"
        try:
            montant = float(data.get('montant', 0))
        except (TypeError, ValueError):
            return False, "montant invalide"
        date_echeance = data.get('date_echeance')
        if date_echeance is not None and date_echeance != '':
            date_echeance = str(date_echeance).strip()
        else:
            date_echeance = None
        freq = str(data.get('frequence', 'une_fois')).strip().lower()
        if freq not in ('une_fois', 'mensuel', 'trimestriel'):
            freq = 'une_fois'
        row = {
            'type': type_val,
            'nom': nom,
            'montant': round(montant, 2),
            'statut': statut,
            'date_echeance': date_echeance,
            'frequence': freq
        }
        response = client.table(TABLE_BUDGET_FAMILIAL).insert(row).execute()
        if response.data:
            return True, "Entrée ajoutée"
        return False, "Aucune donnée retournée"
    except Exception as e:
        log_error(f"Erreur add_budget_familial: {e}")
        return False, str(e)


def create_budget_from_synthetic(
    synthetic_id: int,
    statut: str = 'prevu',
    nom_override: Optional[str] = None,
    montant_override: Optional[float] = None,
    add_exception: bool = False,
) -> tuple[bool, str]:
    """
    Crée une vraie ligne en base à partir d'un id synthétique (récurrence projetée).
    - statut: paye/prevu.
    - nom_override / montant_override: si fournis, utilisés à la place de la source (copie indépendante).
    - add_exception: si True, enregistre une exception pour ce mois afin que la récurrence ne s'affiche pas (la vraie ligne prenant la place).
    """
    decoded = _decode_synthetic_id_full(synthetic_id)
    if not decoded:
        return False, "Id invalide"
    source_id, annee, mois, day = decoded
    client = get_supabase_client()
    if not client:
        return False, "Supabase non configuré"
    try:
        from calendar import monthrange
        row = client.table(TABLE_BUDGET_FAMILIAL).select('*').eq('id', source_id).execute()
        if not row.data or len(row.data) == 0:
            return False, "Entrée source introuvable"
        r = row.data[0]
        last = monthrange(annee, mois)[1]
        day = min(day, last)
        date_echeance = f"{annee}-{mois:02d}-{day:02d}"
        nom = str(nom_override).strip() if nom_override is not None and str(nom_override).strip() else r.get('nom')
        try:
            montant = round(float(montant_override), 2) if montant_override is not None else float(r.get('montant') or 0)
        except (TypeError, ValueError):
            montant = float(r.get('montant') or 0)
        new_row = {
            'type': r.get('type'),
            'nom': nom,
            'montant': montant,
            'statut': statut if statut in ('prevu', 'paye') else 'prevu',
            'date_echeance': date_echeance,
            'frequence': r.get('frequence') or 'une_fois',
        }
        client.table(TABLE_BUDGET_FAMILIAL).insert(new_row).execute()
        if add_exception or nom_override is not None or montant_override is not None:
            add_recurrence_exception(source_id, annee, mois)
        return True, "Entrée créée"
    except Exception as e:
        log_error(f"Erreur create_budget_from_synthetic: {e}")
        return False, str(e)


def update_budget_familial(item_id: int, update_data: Dict) -> bool:
    """Met à jour une entrée budget : statut (paye/prevu), montant, nom, date_echeance ou frequence (une_fois, mensuel, trimestriel)."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        payload = {}
        if 'statut' in update_data:
            s = str(update_data['statut']).strip().lower()
            if s in ('prevu', 'paye'):
                payload['statut'] = s
        if 'montant' in update_data:
            try:
                payload['montant'] = round(float(update_data['montant']), 2)
            except (TypeError, ValueError):
                pass
        if 'nom' in update_data and str(update_data['nom']).strip():
            payload['nom'] = str(update_data['nom']).strip()
        if 'date_echeance' in update_data:
            val = update_data['date_echeance']
            payload['date_echeance'] = str(val).strip() if val is not None and str(val).strip() else None
        if 'frequence' in update_data:
            f = str(update_data['frequence']).strip().lower()
            if f in ('une_fois', 'mensuel', 'trimestriel'):
                payload['frequence'] = f
        if not payload:
            return False
        client.table(TABLE_BUDGET_FAMILIAL).update(payload).eq('id', item_id).execute()
        return True
    except Exception as e:
        log_error(f"Erreur update_budget_familial: {e}")
        return False


def delete_budget_familial(item_id: int) -> bool:
    """Supprime une entrée du budget familial par id."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table(TABLE_BUDGET_FAMILIAL).delete().eq('id', item_id).execute()
        return True
    except Exception as e:
        log_error(f"Erreur delete_budget_familial: {e}")
        return False


def get_solde_restant_budget(annee: Optional[int] = None, mois: Optional[int] = None) -> float:
    """
    Solde restant = Somme Revenus - Somme Dépenses Payées - Somme Dépenses Prévues.
    Si annee et mois sont fournis, calcule sur les entrées du mois uniquement.
    """
    data = get_all_budget_familial(annee, mois)
    try:
        revenus = sum(float(r.get('montant', 0) or 0) for r in data if (r.get('type') or '').lower() == 'revenu')
        depenses_payees = sum(float(r.get('montant', 0) or 0) for r in data if (r.get('type') or '').lower() == 'depense' and (r.get('statut') or '').lower() == 'paye')
        depenses_prevues = sum(float(r.get('montant', 0) or 0) for r in data if (r.get('type') or '').lower() == 'depense' and (r.get('statut') or '').lower() == 'prevu')
        return round(revenus - depenses_payees - depenses_prevues, 2)
    except Exception as e:
        log_error(f"Erreur get_solde_restant_budget: {e}")
        return 0.0


def duplicate_budget_recurrent_mois_courant() -> tuple[int, str]:
    """
    Renouvellement des dépenses/revenus à fréquence mensuelle ou trimestrielle.
    - mensuel : duplique au mois M+1 (même jour).
    - trimestriel : duplique au mois M+3 (même jour).
    À exécuter au 1er de chaque mois (cron ou script de maintenance).
    Retourne (nombre de lignes créées, message).
    """
    client = get_supabase_client()
    if not client:
        return 0, "Supabase non configuré"
    try:
        from calendar import monthrange
        response = client.table(TABLE_BUDGET_FAMILIAL).select('*').in_('frequence', ['mensuel', 'trimestriel']).execute()
        rows = response.data if response.data else []
        if not rows:
            return 0, "Aucune entrée mensuelle ou trimestrielle à dupliquer"
        now = datetime.now()
        cur_year, cur_month = now.year, now.month
        created = 0
        for r in rows:
            freq = (r.get('frequence') or 'une_fois').lower()
            if freq not in ('mensuel', 'trimestriel'):
                continue
            add_months = 1 if freq == 'mensuel' else 3
            date_orig = r.get('date_echeance')
            if not date_orig:
                continue
            try:
                if isinstance(date_orig, str):
                    parts = date_orig.split('-')
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) >= 3 else 1
                else:
                    y, m, d = getattr(date_orig, 'year', 1), getattr(date_orig, 'month', 1), getattr(date_orig, 'day', 1)
            except (IndexError, ValueError, TypeError):
                continue
            m2 = m + add_months
            y2 = y
            while m2 > 12:
                m2 -= 12
                y2 += 1
            while m2 < 1:
                m2 += 12
                y2 -= 1
            if (y2, m2) != (cur_year, cur_month):
                continue
            last = monthrange(y2, m2)[1]
            d2 = min(d, last)
            new_date = f"{y2}-{m2:02d}-{d2:02d}"
            type_val = (r.get('type') or 'depense').lower()
            nom = str(r.get('nom') or '').strip()
            montant = float(r.get('montant') or 0)
            existing = client.table(TABLE_BUDGET_FAMILIAL).select('id').eq('nom', nom).eq('type', type_val).eq('date_echeance', new_date).execute()
            if existing.data and len(existing.data) > 0:
                continue
            new_row = {
                'type': type_val,
                'nom': nom,
                'montant': round(montant, 2),
                'statut': 'prevu',
                'date_echeance': new_date,
                'frequence': freq
            }
            client.table(TABLE_BUDGET_FAMILIAL).insert(new_row).execute()
            created += 1
        return created, f"{created} entrée(s) dupliquée(s) pour le mois en cours"
    except Exception as e:
        log_error(f"Erreur duplicate_budget_recurrent_mois_courant: {e}")
        return 0, str(e)
