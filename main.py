import streamlit as st
import pandas as pd
import json
import os
import time
import hashlib
from datetime import datetime, timedelta

# --- CONFIGURATION & SAUVEGARDE ---
PIN_PARENT = "1234" 
DB_FILE = "data_foyer.json"

# --- FONCTIONS D'AUTHENTIFICATION ---
def hash_password(password):
    """Hash un mot de passe pour sécurisation."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(input_password, stored_hash=None):
    """Vérifie si le mot de passe entré correspond au PIN parent."""
    if stored_hash is None:
        # Hash du PIN par défaut
        default_hash = "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"  # hash de "1234"
        input_hash = hash_password(input_password)
        return input_hash == default_hash
    else:
        input_hash = hash_password(input_password)
        return input_hash == stored_hash

def require_parent_auth(show_form=True):
    """
    Vérifie si l'utilisateur est authentifié en tant que parent.
    Si show_form=True, affiche un formulaire d'authentification si non authentifié.
    Retourne True si authentifié, False sinon.
    """
    if st.session_state.get('parent_authenticated', False):
        return True
    
    if show_form:
        st.title("🔐 Authentification Parents")
        st.info("Cette section est réservée aux parents. Veuillez entrer le code d'accès.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            code_input = st.text_input("Code Parent :", type="password", key="auth_code_input")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Se connecter", use_container_width=True, key="auth_btn_connect"):
                    if verify_password(code_input):
                        st.session_state.parent_authenticated = True
                        st.success("✅ Authentification réussie !")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Code incorrect. Accès refusé.")
            with col_btn2:
                if st.button("🔙 Retour", use_container_width=True, key="auth_btn_back"):
                    st.session_state.parent_authenticated = False
                    st.rerun()
    
    return False

def logout_parent():
    """Déconnecte le parent et réinitialise la session."""
    st.session_state.parent_authenticated = False
    st.rerun()

def charger_donnees():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"points_foyer": 0, "classement": {}, "attente_validation": [], "taches_completees": [], "taches_personnalisees": [], "config": None, "recompenses_achetees": [], "recompenses_personnalisees": []}

def sauvegarder_donnees():
    donnees = {
        "points_foyer": st.session_state.points_foyer,
        "classement": st.session_state.classement,
        "attente_validation": st.session_state.attente_validation,
        "taches_completees": st.session_state.get("taches_completees", []),
        "taches_personnalisees": st.session_state.get("taches_personnalisees", []),
        "config": st.session_state.get("config", None),
        "recompenses_achetees": st.session_state.get("recompenses_achetees", []),
        "recompenses_personnalisees": st.session_state.get("recompenses_personnalisees", [])
    }
    with open(DB_FILE, "w") as f:
        json.dump(donnees, f)

# --- FONCTIONS DE GESTION DES FRÉQUENCES ---
def get_today_str():
    """Retourne la date d'aujourd'hui au format YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

def get_week_start(date_str=None):
    """Retourne le début de la semaine (lundi) pour une date donnée."""
    if date_str is None:
        date_str = get_today_str()
    date = datetime.strptime(date_str, "%Y-%m-%d")
    # Retourner le lundi de la semaine
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    return monday.strftime("%Y-%m-%d")

def get_next_due_date(task_name, user, frequency):
    """
    Calcule la prochaine date à laquelle une tâche doit être réalisée selon sa fréquence.
    Retourne (date_str, date_display, can_do_today)
    """
    if 'taches_completees' not in st.session_state:
        st.session_state.taches_completees = []
    
    taches_user = [t for t in st.session_state.taches_completees 
                   if t['user'] == user and t['task'] == task_name]
    
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    if frequency == "Quotidien":
        # Vérifier si déjà faite aujourd'hui
        today_tasks = [t for t in taches_user if t['date'] == today_str]
        if today_tasks:
            # Prochaine date = demain
            tomorrow = today + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d"), tomorrow.strftime("le %d/%m/%Y"), False
        else:
            # Peut être faite aujourd'hui
            return today_str, "aujourd'hui", True
    
    elif frequency == "Hebdomadaire":
        week_start = get_week_start()
        week_tasks = [t for t in taches_user if t['date'] >= week_start]
        
        # Déterminer le maximum par semaine
        max_per_week = 1
        if "Aspirateur-Man" in task_name:
            max_per_week = 2
        elif "Maître des Bacs" in task_name:
            # Poubelles : peut être faite selon ramassage
            return today_str, "selon les jours de ramassage", True
        
        if len(week_tasks) >= max_per_week:
            # Déjà faite cette semaine, prochaine date = début semaine prochaine
            next_monday = today + timedelta(days=(7 - today.weekday()))
            return next_monday.strftime("%Y-%m-%d"), next_monday.strftime("le %d/%m/%Y"), False
        else:
            # Peut être faite cette semaine
            if len(week_tasks) == 0:
                return today_str, "aujourd'hui", True
            else:
                # Peut encore être faite cette semaine (pour 2x/semaine)
                return today_str, "encore cette semaine", True
    
    elif frequency == "Ponctuel":
        # Tâches ponctuelles : peut être refaite à tout moment
        return today_str, "à tout moment", True
    
    return today_str, "maintenant", True

def can_validate_task(task_name, user, frequency):
    """
    Vérifie si une tâche peut être validée selon sa fréquence.
    Retourne (True/False, message_info)
    """
    if 'taches_completees' not in st.session_state:
        st.session_state.taches_completees = []
    
    taches_user = [t for t in st.session_state.taches_completees 
                   if t['user'] == user and t['task'] == task_name]
    
    today = get_today_str()
    
    if frequency == "Quotidien":
        # Vérifier si la tâche a déjà été faite aujourd'hui
        today_tasks = [t for t in taches_user if t['date'] == today]
        if today_tasks:
            return False, f"✅ Déjà complétée aujourd'hui ({len(today_tasks)} fois)"
        return True, "📅 Peut être complétée chaque jour"
    
    elif frequency == "Hebdomadaire":
        week_start = get_week_start()
        week_tasks = [t for t in taches_user if t['date'] >= week_start]
        
        # Déterminer le maximum par semaine selon la tâche
        max_per_week = 1  # Par défaut 1x par semaine
        if "Aspirateur-Man" in task_name:
            max_per_week = 2  # 2x par semaine
        elif "Maître des Bacs" in task_name:
            # Poubelles : on vérifie juste cette semaine
            return True, "📅 Peut être complétée selon les jours de ramassage"
        
        if len(week_tasks) >= max_per_week:
            return False, f"⚠️ Déjà complétée {len(week_tasks)} fois cette semaine (max: {max_per_week})"
        return True, f"📅 Peut être complétée {max_per_week}x par semaine ({len(week_tasks)}/{max_per_week} cette semaine)"
    
    elif frequency == "Ponctuel":
        # Les tâches ponctuelles peuvent être refaites
        return True, "📅 Tâche ponctuelle - Peut être refaite"
    
    return True, ""

def add_completed_task(task_name, user, points):
    """Ajoute une tâche complétée à l'historique."""
    if 'taches_completees' not in st.session_state:
        st.session_state.taches_completees = []
    
    st.session_state.taches_completees.append({
        "task": task_name,
        "user": user,
        "date": get_today_str(),
        "points": points,
        "timestamp": datetime.now().isoformat()
    })

# --- INITIALISATION ---
st.set_page_config(page_title="Foyer Magique 🏡", page_icon="✨", layout="wide")
saved_data = charger_donnees()
for key, value in saved_data.items():
    if key not in st.session_state:
        st.session_state[key] = value

if 'config' not in st.session_state:
    st.session_state.config = {"parents": ["Papa", "Maman"], "ados": ["Ado 1"], "enfants": ["Enfant 1", "Enfant 2"]}
if 'parent_authenticated' not in st.session_state:
    st.session_state.parent_authenticated = False
if 'taches_completees' not in st.session_state:
    st.session_state.taches_completees = []
if 'taches_personnalisees' not in st.session_state:
    st.session_state.taches_personnalisees = []
if 'recompenses_achetees' not in st.session_state:
    st.session_state.recompenses_achetees = []
if 'recompenses_personnalisees' not in st.session_state:
    st.session_state.recompenses_personnalisees = []

# --- STYLE CSS (Smartphone, Mode Sombre & Animations) ---
st.markdown("""
    <style>
    /* Variables CSS pour mode sombre */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f0f2f6;
        --text-primary: #262730;
        --text-secondary: #808495;
        --border-color: rgba(128, 128, 128, 0.3);
        --shadow: rgba(0, 0, 0, 0.1);
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #0e1117;
            --bg-secondary: #1e1e1e;
            --text-primary: #fafafa;
            --text-secondary: #a0a0a0;
            --border-color: rgba(255, 255, 255, 0.2);
            --shadow: rgba(0, 0, 0, 0.5);
        }
    }
    
    /* Responsive design pour smartphone */
    @media (max-width: 768px) {
        .stButton>button { height: 3.5em; font-size: 0.9em; }
        .category-header { padding: 10px; font-size: 0.95em; }
        .mission-box { padding: 12px; }
        .reward-card { min-width: 100% !important; }
    }
    
    /* Styles de base */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 4em; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; 
        font-weight: bold; 
        border: none; 
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6); }
    
    .category-header { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; 
        padding: 12px; 
        border-radius: 10px; 
        margin-top: 25px; 
        text-align: center; 
        font-weight: bold; 
        border: none;
        box-shadow: 0 4px 10px var(--shadow);
    }
    
    .mission-box { 
        background: var(--bg-secondary); 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid var(--border-color); 
        margin-bottom: 5px; 
        border-left: 8px solid #FFD700;
        box-shadow: 0 2px 8px var(--shadow);
    }
    
    .description-text { 
        color: var(--text-secondary); 
        font-size: 0.9em; 
        font-style: italic; 
    }
    
    .pts-badge { 
        color: #4CAF50; 
        font-weight: bold; 
        float: right; 
        font-size: 1.1em; 
    }
    
    /* Code couleur pour les fréquences */
    .mission-box-quotidien { border-left: 8px solid #4CAF50 !important; background: rgba(76, 175, 80, 0.15) !important; }
    .mission-box-hebdomadaire { border-left: 8px solid #2196F3 !important; background: rgba(33, 150, 243, 0.15) !important; }
    .mission-box-ponctuel { border-left: 8px solid #FF9800 !important; background: rgba(255, 152, 0, 0.15) !important; }
    
    /* Animation du sablier */
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    .waiting-msg { color: #FFA000; font-weight: bold; text-align: center; padding: 10px; animation: blink 1.5s infinite; font-size: 1.1em; }
    
    /* Badge de fréquence */
    .freq-badge-quotidien { color: #4CAF50; font-weight: bold; }
    .freq-badge-hebdomadaire { color: #2196F3; font-weight: bold; }
    .freq-badge-ponctuel { color: #FF9800; font-weight: bold; }
    
    /* Styles pour les récompenses */
    .reward-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 50%, #4facfe 100%);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 20px var(--shadow);
        border: 3px solid transparent;
        transition: transform 0.3s, box-shadow 0.3s;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        color: white;
    }
    
    .reward-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px var(--shadow);
    }
    
    .reward-card.achetee {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        opacity: 0.8;
        border: 3px solid #4CAF50;
    }
    
    .reward-title {
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .reward-description {
        font-size: 1em;
        opacity: 0.95;
        margin: 10px 0;
    }
    
    .reward-price {
        font-size: 1.8em;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        background: rgba(255,255,255,0.2);
        border-radius: 10px;
        margin-top: 15px;
    }
    
    .reward-badge-achete {
        background: #4CAF50;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: bold;
        text-align: center;
        margin-top: 10px;
    }
    
    .reward-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin-top: 20px;
    }
    
    @media (max-width: 768px) {
        .reward-grid {
            grid-template-columns: 1fr;
        }
        .reward-card {
            min-height: 160px;
            padding: 20px;
        }
    }
    </style>
""", unsafe_allow_html=True)

def animate_hourglass_submission():
    """Animation sablier lors de la soumission d'une tâche en attente."""
    hourglass_frames = ["⏳", "⏳", "⌛", "⌛"]
    placeholder = st.empty()
    for frame in hourglass_frames:
        placeholder.markdown(f"""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='font-size: 64px; margin: 0;'>{frame}</h1>
            <p style='font-size: 1.2em; color: #FFA000; font-weight: bold;'>Mission envoyée !</p>
            <p style='color: var(--text-secondary);'>En attente de validation...</p>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.3)
    placeholder.empty()

def update_and_save():
    sauvegarder_donnees()
    st.rerun()

# --- NAVIGATION ---
st.sidebar.title("🏡 Menu Foyer")
mode = st.sidebar.radio("Navigation", ["🚀 Missions", "🎁 Récompenses", "📅 Calendrier", "🏆 Classement", "⚙️ Espace Parents"])
st.sidebar.metric("💰 Trésor Commun", f"{st.session_state.points_foyer} pts")

# --- 1. MISSIONS (VERSION COMPLÈTE & SÉCURISÉE) ---
if mode == "🚀 Missions":
    st.title("🚀 Missions Magiques")
    
    # Légende du code couleur
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='background: rgba(76, 175, 80, 0.1); padding: 8px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
            <strong>🔄 Quotidien</strong><br>
            <small>Tâches journalières</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='background: rgba(33, 150, 243, 0.1); padding: 8px; border-radius: 8px; border-left: 4px solid #2196F3;'>
            <strong>📅 Hebdomadaire</strong><br>
            <small>Tâches hebdomadaires</small>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style='background: rgba(255, 152, 0, 0.1); padding: 8px; border-radius: 8px; border-left: 4px solid #FF9800;'>
            <strong>⭐ Ponctuel</strong><br>
            <small>Tâches ponctuelles</small>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    
    all_users = st.session_state.config["parents"] + st.session_state.config["ados"] + st.session_state.config["enfants"]
    current_user = st.selectbox("Qui es-tu ?", all_users)
    role = "Parent" if current_user in st.session_state.config["parents"] else "Ado" if current_user in st.session_state.config["ados"] else "Enfant"

    # Authentification obligatoire pour les profils parents
    parent_authenticated_for_missions = True
    if role == "Parent":
        if not require_parent_auth(show_form=True):
            parent_authenticated_for_missions = False
            # Arrêter l'affichage des missions si le parent n'est pas authentifié
            st.stop()
        else:
            # Afficher le bouton de déconnexion si authentifié
            st.success("✅ Authentifié en tant que parent - Vous pouvez valider les missions")
            if st.button("🔒 Se déconnecter (Profil Parent)", use_container_width=False):
                logout_parent()

    # Tâches par défaut
    tasks_default = [
        # TÂCHES QUOTIDIENNES
        {"n": "🍽️ Maître du Dressage", "p": 10, "c": "Cuisine", "r": ["Enfant", "Ado"], "d": "Mettre la table matin, midi et soir.", "f": "Quotidien"},
        {"n": "🧼 Ninja du Débarrassage", "p": 10, "c": "Cuisine", "r": ["Enfant", "Ado"], "d": "Débarrasser après chaque repas.", "f": "Quotidien"},
        {"n": "🚀 Mission Décollage", "p": 10, "c": "Ménage", "r": ["Enfant"], "d": "Faire son lit et ranger son pyjama le matin.", "f": "Quotidien"},
        {"n": "🦷 Sourire Éclatant", "p": 5, "c": "Hygiène", "r": ["Enfant"], "d": "Brossage de dents (Matin/Soir).", "f": "Quotidien"},
        
        # TÂCHES HEBDOMADAIRES
        {"n": "🚜 Dompteur de Jungle", "p": 50, "c": "Extérieur", "r": ["Parent", "Ado"], "d": "Tondre la pelouse (1x par semaine).", "f": "Hebdomadaire"},
        {"n": "🌀 Aspirateur-Man", "p": 20, "c": "Ménage", "r": ["Parent", "Ado"], "d": "Passer l'aspirateur (2x par semaine).", "f": "Hebdomadaire"},
        {"n": "🗑️ Maître des Bacs", "p": 15, "c": "Déchets", "r": ["Parent", "Ado"], "d": "Sortir les poubelles (selon les jours de ramassage).", "f": "Hebdomadaire"},
        {"n": "✨ Fée de la Serpillière", "p": 20, "c": "Ménage", "r": ["Parent", "Ado"], "d": "Nettoyer les sols (1x par semaine).", "f": "Hebdomadaire"},
        
        # TÂCHES PONCTUELLES
        {"n": "🍳 Chef Étoilé Michelin", "p": 25, "c": "Cuisine", "r": ["Parent"], "d": "Préparer un repas complet.", "f": "Ponctuel"},
        {"n": "🧺 Expert Origami (Linge)", "p": 15, "c": "Ménage", "r": ["Parent", "Ado"], "d": "Plier et ranger une manne de linge.", "f": "Ponctuel"},
        
        # AUTRES TÂCHES (sans fréquence spécifiée - reste comme avant)
        {"n": "🌊 Plongeur de l'Atlantide", "p": 15, "c": "Cuisine", "r": ["Parent", "Ado"], "d": "Vider ou remplir le lave-vaisselle.", "f": None},
        {"n": "🧸 Rangement Express", "p": 15, "c": "Ménage", "r": ["Enfant"], "d": "Ramasser les jouets du salon.", "f": None},
        {"n": "👟 Gardien du Hall", "p": 5, "c": "Ménage", "r": ["Enfant", "Ado", "Parent"], "d": "Aligner les chaussures.", "f": None}
    ]
    
    # Fusionner avec les tâches personnalisées
    tasks = tasks_default + st.session_state.get("taches_personnalisees", [])

    # Vérifier si l'utilisateur a déjà des missions en attente pour afficher le sablier global
    en_attente_user = [m for m in st.session_state.attente_validation if m['user'] == current_user]
    if en_attente_user:
        st.markdown(f"<div class='waiting-msg'>⏳ Sablier magique activé... Papa ou Maman vérifient tes {len(en_attente_user)} mission(s) !</div>", unsafe_allow_html=True)

    # Ne pas afficher les missions si le parent n'est pas authentifié
    if role == "Parent" and not parent_authenticated_for_missions:
        st.stop()

    for cat in ["Cuisine", "Ménage", "Hygiène", "Déchets", "Extérieur"]:
        cat_t = [t for t in tasks if t["c"] == cat and role in t["r"]]
        if cat_t:
            st.markdown(f"<div class='category-header'>{cat}</div>", unsafe_allow_html=True)
            for t in cat_t:
                # Vérifier la fréquence
                frequency = t.get("f")
                freq_badge = ""
                status_info = ""
                can_validate = True
                
                # Calculer la prochaine date et vérifier si elle peut être validée
                next_date_str = ""
                next_date_display = ""
                can_do_today = True
                
                if frequency:
                    can_validate, status_info = can_validate_task(t['n'], current_user, frequency)
                    next_date_str, next_date_display, can_do_today = get_next_due_date(t['n'], current_user, frequency)
                    
                    if frequency == "Quotidien":
                        freq_badge = " 🔄"
                    elif frequency == "Hebdomadaire":
                        freq_badge = " 📅"
                    elif frequency == "Ponctuel":
                        freq_badge = " ⭐"
                else:
                    can_validate = True
                    status_info = ""
                
                # Déterminer la classe CSS selon la fréquence
                box_class = "mission-box"
                freq_class = ""
                if frequency == "Quotidien":
                    box_class = "mission-box-quotidien"
                    freq_class = "freq-badge-quotidien"
                elif frequency == "Hebdomadaire":
                    box_class = "mission-box-hebdomadaire"
                    freq_class = "freq-badge-hebdomadaire"
                elif frequency == "Ponctuel":
                    box_class = "mission-box-ponctuel"
                    freq_class = "freq-badge-ponctuel"
                
                freq_label = f" ({frequency})" if frequency else ""
                freq_badge_html = f"<span class='{freq_class}'>{freq_badge}</span>" if freq_class else freq_badge
                
                # Ajouter la date dans la description
                date_info = ""
                if frequency:
                    if can_do_today and can_validate:
                        date_info = f" | <strong style='color: #4CAF50;'>📅 À faire {next_date_display}</strong>"
                    elif not can_validate:
                        date_info = f" | <strong style='color: #FF9800;'>📅 Prochaine fois {next_date_display}</strong>"
                    else:
                        date_info = f" | <strong style='color: #2196F3;'>📅 À faire {next_date_display}</strong>"
                
                st.markdown(f"<div class='{box_class}'><span class='pts-badge'>+{t['p']} pts{freq_badge_html}</span><b>{t['n']}{freq_label}</b><br><span class='description-text'>👉 {t['d']}{date_info}</span></div>", unsafe_allow_html=True)
                
                if status_info:
                    st.caption(f"ℹ️ {status_info}")
                
                # Désactiver le bouton si le parent n'est pas authentifié OU si la fréquence ne permet pas
                button_disabled = (role == "Parent" and not parent_authenticated_for_missions) or not can_validate
                if st.button(f"Terminé ! 🚀", key=f"btn_{t['n']}_{current_user}", disabled=button_disabled):
                    if role == "Parent":
                        if parent_authenticated_for_missions:
                            if can_validate:
                                st.session_state.points_foyer += t['p']
                                st.session_state.classement[current_user] = st.session_state.classement.get(current_user, 0) + t['p']
                                add_completed_task(t['n'], current_user, t['p'])
                                st.balloons()
                            else:
                                st.error("⚠️ Cette tâche a déjà été complétée selon sa fréquence aujourd'hui/cette semaine.")
                        else:
                            st.error("🔒 Authentification requise pour valider les missions en tant que parent.")
                    else:
                        if can_validate:
                            st.session_state.attente_validation.append({"user": current_user, "task": t['n'], "pts": t['p']})
                            add_completed_task(t['n'], current_user, t['p'])  # Enregistrer même en attente
                            # Animation sablier
                            animate_hourglass_submission()
                            st.toast(f"Mission envoyée ! ⏳", icon="⌛")
                        else:
                            st.error("⚠️ Cette tâche a déjà été complétée selon sa fréquence aujourd'hui/cette semaine.")
                    update_and_save()

# --- 2. RÉCOMPENSES ---
elif mode == "🎁 Récompenses":
    st.title("🎁 Boutique des Récompenses")
    
    # Initialiser les récompenses si nécessaire
    if 'recompenses_achetees' not in st.session_state:
        st.session_state.recompenses_achetees = []
    
    # Définition des récompenses par défaut
    recompenses_default = [
        {
            "id": 1,
            "nom": "🎮 Soirée Jeux Vidéo",
            "description": "1h30 de jeux vidéo en famille ou seul",
            "points": 50,
            "emoji": "🎮",
            "couleur": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        },
        {
            "id": 2,
            "nom": "🍿 Film en Famille",
            "description": "Choisir un film à regarder tous ensemble",
            "points": 75,
            "emoji": "🍿",
            "couleur": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
        },
        {
            "id": 3,
            "nom": "🍦 Dessert Spécial",
            "description": "Dessert de ton choix après le repas",
            "points": 30,
            "emoji": "🍦",
            "couleur": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
        },
        {
            "id": 4,
            "nom": "🎁 Petit Cadeau",
            "description": "Cadeau surprise de 10€ maximum",
            "points": 100,
            "emoji": "🎁",
            "couleur": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
        },
        {
            "id": 5,
            "nom": "🎯 Choix du Repas",
            "description": "Choisir le menu du soir pour toute la famille",
            "points": 40,
            "emoji": "🎯",
            "couleur": "linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
        }
    ]
    
    # Fusionner avec les récompenses personnalisées
    recompenses = recompenses_default + st.session_state.get("recompenses_personnalisees", [])
    
    # Affichage du solde
    col_balance1, col_balance2, col_balance3 = st.columns([1, 2, 1])
    with col_balance2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; 
                    border-radius: 15px; 
                    text-align: center; 
                    color: white; 
                    margin: 20px 0;
                    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);'>
            <h2 style='margin: 0; font-size: 2em;'>💰 {st.session_state.points_foyer} pts</h2>
            <p style='margin: 5px 0 0 0; opacity: 0.9;'>Trésor disponible</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("✨ Récompenses disponibles")
    
    # Affichage des récompenses en colonnes responsive
    for i in range(0, len(recompenses), 2):
        cols = st.columns(2)
        for j, recompense in enumerate(recompenses[i:i+2]):
            with cols[j] if j < len(cols) else st.container():
                est_achetee = any(r.get('id') == recompense['id'] for r in st.session_state.recompenses_achetees)
                peut_acheter = st.session_state.points_foyer >= recompense['points'] and not est_achetee
                
                classe_css = "reward-card"
                if est_achetee:
                    classe_css += " achetee"
                
                st.markdown(f"""
                <div class="{classe_css}" style="background: {recompense['couleur']};">
                    <div class="reward-title">{recompense['emoji']} {recompense['nom']}</div>
                    <div class="reward-description">{recompense['description']}</div>
                    <div class="reward-price">{recompense['points']} 💰 pts</div>
                    {"<div class='reward-badge-achete'>✅ Déjà obtenue !</div>" if est_achetee else ""}
                </div>
                """, unsafe_allow_html=True)
                
                if est_achetee:
                    st.info(f"✅ Déjà obtenue !")
                elif peut_acheter:
                    if st.button(f"✨ Obtenir cette récompense", key=f"buy_{recompense['id']}", use_container_width=True):
                        st.session_state.points_foyer -= recompense['points']
                        st.session_state.recompenses_achetees.append({
                            "id": recompense['id'],
                            "nom": recompense['nom'],
                            "date": get_today_str(),
                            "points_utilises": recompense['points']
                        })
                        st.success(f"🎉 Félicitations ! Vous avez obtenu : {recompense['nom']}")
                        st.balloons()
                        update_and_save()
                else:
                    manque = recompense['points'] - st.session_state.points_foyer
                    st.warning(f"💡 Il manque {manque} pts")
    
    # Afficher les récompenses obtenues
    if st.session_state.recompenses_achetees:
        st.markdown("---")
        st.subheader("🏆 Mes Récompenses Obtenues")
        
        recompenses_obtenues = [r for r in st.session_state.recompenses_achetees]
        for rec in recompenses_obtenues:
            rec_info = next((r for r in recompenses if r['id'] == rec['id']), None)
            if rec_info:
                date_obj = datetime.strptime(rec['date'], "%Y-%m-%d")
                date_display = date_obj.strftime("%d/%m/%Y")
                st.markdown(f"""
                <div style='background: var(--bg-secondary); 
                            padding: 15px; 
                            border-radius: 10px; 
                            margin: 10px 0;
                            border-left: 4px solid #4CAF50;'>
                    <strong>{rec_info['emoji']} {rec['nom']}</strong><br>
                    <small>Obtenue le {date_display} • {rec['points_utilises']} points utilisés</small>
                </div>
                """, unsafe_allow_html=True)

# --- 3. CALENDRIER ---
elif mode == "📅 Calendrier":
    st.title("📅 Calendrier des Missions")
    
    if 'taches_completees' not in st.session_state:
        st.session_state.taches_completees = []
    
    # Sélection de la période
    view_mode = st.radio("Vue", ["Aujourd'hui", "Cette semaine", "Ce mois"], horizontal=True)
    
    today = datetime.now()
    
    if view_mode == "Aujourd'hui":
        selected_date = today.strftime("%Y-%m-%d")
        date_label = today.strftime("%A %d %B %Y")
        date_tasks = [t for t in st.session_state.taches_completees if t['date'] == selected_date]
        
    elif view_mode == "Cette semaine":
        week_start = get_week_start()
        week_end = (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
        date_label = f"Semaine du {datetime.strptime(week_start, '%Y-%m-%d').strftime('%d/%m')} au {datetime.strptime(week_end, '%Y-%m-%d').strftime('%d/%m/%Y')}"
        date_tasks = [t for t in st.session_state.taches_completees if week_start <= t['date'] <= week_end]
        
    else:  # Ce mois
        month_start = today.replace(day=1).strftime("%Y-%m-%d")
        date_label = today.strftime("%B %Y")
        date_tasks = [t for t in st.session_state.taches_completees if t['date'] >= month_start and t['date'][:7] == today.strftime("%Y-%m")]
    
    st.subheader(f"📅 {date_label}")
    
    if not date_tasks:
        st.info("Aucune tâche complétée pour cette période.")
    else:
        # Grouper par date
        tasks_by_date = {}
        for task in date_tasks:
            date = task['date']
            if date not in tasks_by_date:
                tasks_by_date[date] = []
            tasks_by_date[date].append(task)
        
        # Afficher par date
        for date in sorted(tasks_by_date.keys(), reverse=True):
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            if view_mode == "Aujourd'hui":
                date_display = "Aujourd'hui"
            elif view_mode == "Cette semaine":
                date_display = date_obj.strftime("%A %d/%m")
            else:
                date_display = date_obj.strftime("%A %d %B")
            
            st.markdown(f"### 📆 {date_display}")
            
            # Grouper par utilisateur
            tasks_by_user = {}
            for task in tasks_by_date[date]:
                user = task['user']
                if user not in tasks_by_user:
                    tasks_by_user[user] = []
                tasks_by_user[user].append(task)
            
            for user, user_tasks in tasks_by_user.items():
                total_points = sum(t['points'] for t in user_tasks)
                st.markdown(f"**{user}** ({total_points} pts)")
                for task in user_tasks:
                    status = "✅" if task.get('validated', True) else "⏳"
                    st.write(f"  {status} {task['task']} (+{task['points']} pts)")
                st.markdown("---")
        
        # Statistiques
        total_points_period = sum(t['points'] for t in date_tasks)
        st.metric("Total points sur la période", f"{total_points_period} pts")

# --- 4. ESPACE PARENTS (SÉCURISÉ) ---
elif mode == "⚙️ Espace Parents":
    if not require_parent_auth(show_form=True):
        st.stop()
    
    st.title("🛡️ Zone de Validation")
    
    # Bouton de déconnexion
    if st.button("🔒 Se déconnecter", use_container_width=True):
        logout_parent()

    # Onglets dans l'espace parents
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Validations", "👨‍👩‍👧‍👦 Gestion Famille", "➕ Créer une Tâche", "🎁 Gérer Récompenses"])
    
    with tab1:
        st.subheader("✅ Missions à confirmer")
        if not st.session_state.attente_validation:
            st.info("Tout est à jour !")
        else:
            for idx, d in enumerate(st.session_state.attente_validation):
                col_txt, col_v, col_x = st.columns([2, 1, 1])
                col_txt.write(f"**{d['user']}** : {d['task']} (+{d['pts']})")
                if col_v.button("Valider", key=f"v_{idx}"):
                    st.session_state.points_foyer += d['pts']
                    st.session_state.classement[d['user']] = st.session_state.classement.get(d['user'], 0) + d['pts']
                    # Marquer la tâche comme validée dans l'historique
                    today = get_today_str()
                    for task in st.session_state.get('taches_completees', []):
                        if task['task'] == d['task'] and task['user'] == d['user'] and task['date'] == today:
                            task['validated'] = True
                    st.session_state.attente_validation.pop(idx)
                    update_and_save()
                if col_x.button("Refuser", key=f"x_{idx}"):
                    st.session_state.attente_validation.pop(idx)
                    update_and_save()
    
    with tab2:
        st.subheader("👨‍👩‍👧‍👦 Gestion de la Famille")
        
        # Gestion des enfants
        st.markdown("### 👶 Gestion des Enfants")
        if st.session_state.config["enfants"]:
            for idx, enfant in enumerate(st.session_state.config["enfants"]):
                col_name, col_role, col_del = st.columns([3, 2, 1])
                
                with col_name:
                    new_name = st.text_input(f"Nom", value=enfant, key=f"enfant_name_{idx}")
                    if new_name != enfant:
                        st.session_state.config["enfants"][idx] = new_name
                        # Mettre à jour dans le classement si existant
                        if enfant in st.session_state.classement:
                            st.session_state.classement[new_name] = st.session_state.classement.pop(enfant)
                        # Mettre à jour dans attente_validation
                        for item in st.session_state.attente_validation:
                            if item['user'] == enfant:
                                item['user'] = new_name
                        # Mettre à jour dans taches_completees
                        for task in st.session_state.get('taches_completees', []):
                            if task['user'] == enfant:
                                task['user'] = new_name
                        update_and_save()
                
                with col_role:
                    if st.button(f"➡️ Devenir Ado", key=f"enfant_to_ado_{idx}"):
                        # Ajouter à la liste des ados
                        st.session_state.config["ados"].append(enfant)
                        # Retirer de la liste des enfants
                        st.session_state.config["enfants"].pop(idx)
                        update_and_save()
                
                with col_del:
                    if st.button("🗑️", key=f"del_enfant_{idx}"):
                        st.session_state.config["enfants"].pop(idx)
                        # Retirer du classement si présent
                        if enfant in st.session_state.classement:
                            del st.session_state.classement[enfant]
                        update_and_save()
        else:
            st.info("Aucun enfant enregistré.")
        
        # Bouton pour ajouter un nouvel enfant
        if st.button("➕ Ajouter un Enfant"):
            nouveau = f"Enfant {len(st.session_state.config['enfants']) + 1}"
            st.session_state.config["enfants"].append(nouveau)
            update_and_save()
        
        st.markdown("---")
        
        # Gestion des ados
        st.markdown("### 🧑 Gestion des Ados")
        if st.session_state.config["ados"]:
            for idx, ado in enumerate(st.session_state.config["ados"]):
                col_name, col_del = st.columns([4, 1])
                
                with col_name:
                    new_name = st.text_input(f"Nom", value=ado, key=f"ado_name_{idx}")
                    if new_name != ado:
                        st.session_state.config["ados"][idx] = new_name
                        # Mettre à jour dans le classement si existant
                        if ado in st.session_state.classement:
                            st.session_state.classement[new_name] = st.session_state.classement.pop(ado)
                        # Mettre à jour dans attente_validation
                        for item in st.session_state.attente_validation:
                            if item['user'] == ado:
                                item['user'] = new_name
                        # Mettre à jour dans taches_completees
                        for task in st.session_state.get('taches_completees', []):
                            if task['user'] == ado:
                                task['user'] = new_name
                        update_and_save()
                
                with col_del:
                    if st.button("🗑️", key=f"del_ado_{idx}"):
                        st.session_state.config["ados"].pop(idx)
                        # Retirer du classement si présent
                        if ado in st.session_state.classement:
                            del st.session_state.classement[ado]
                        update_and_save()
        else:
            st.info("Aucun ado enregistré.")
        
        # Bouton pour ajouter un nouvel ado
        if st.button("➕ Ajouter un Ado"):
            nouveau = f"Ado {len(st.session_state.config['ados']) + 1}"
            st.session_state.config["ados"].append(nouveau)
            update_and_save()
    
    with tab3:
        st.subheader("➕ Créer une Nouvelle Tâche")
        
        with st.form("nouvelle_tache", clear_on_submit=True):
            nom_tache = st.text_input("Nom de la tâche (avec emoji)", placeholder="🧹 Exemple : Nettoyer la salle de bain")
            description = st.text_area("Description", placeholder="Description détaillée de la tâche")
            
            col_points, col_cat = st.columns(2)
            with col_points:
                points = st.number_input("Points", min_value=1, max_value=100, value=10)
            with col_cat:
                categorie = st.selectbox("Catégorie", ["Cuisine", "Ménage", "Hygiène", "Déchets", "Extérieur", "Autre"])
            
            roles = st.multiselect("Rôles autorisés", ["Parent", "Ado", "Enfant"], default=["Enfant", "Ado"])
            
            frequence = st.selectbox("Fréquence", ["Aucune", "Quotidien", "Hebdomadaire", "Ponctuel"])
            
            if st.form_submit_button("✅ Créer la Tâche"):
                if nom_tache and description:
                    nouvelle_tache = {
                        "n": nom_tache,
                        "p": int(points),
                        "c": categorie,
                        "r": roles,
                        "d": description,
                        "f": frequence if frequence != "Aucune" else None
                    }
                    
                    if 'taches_personnalisees' not in st.session_state:
                        st.session_state.taches_personnalisees = []
                    
                    st.session_state.taches_personnalisees.append(nouvelle_tache)
                    st.success(f"✅ Tâche '{nom_tache}' créée avec succès !")
                    update_and_save()
                else:
                    st.error("⚠️ Veuillez remplir le nom et la description de la tâche.")
        
        # Afficher les tâches personnalisées existantes
        if st.session_state.get("taches_personnalisees"):
            st.markdown("---")
            st.subheader("📋 Tâches Personnalisées")
            for idx, tache in enumerate(st.session_state.taches_personnalisees):
                with st.expander(f"{tache['n']} (+{tache['p']} pts)"):
                    col_info, col_del = st.columns([4, 1])
                    with col_info:
                        st.write(f"**Description:** {tache['d']}")
                        st.write(f"**Catégorie:** {tache['c']} | **Rôles:** {', '.join(tache['r'])} | **Fréquence:** {tache.get('f', 'Aucune')}")
                    with col_del:
                        if st.button("🗑️ Supprimer", key=f"del_tache_{idx}"):
                            st.session_state.taches_personnalisees.pop(idx)
                            update_and_save()
    
    with tab4:
        st.subheader("🎁 Gestion des Récompenses")
        
        # Formulaire pour créer/modifier une récompense
        st.markdown("### ➕ Créer ou Modifier une Récompense")
        
        # Sélectionner une récompense existante à modifier ou créer nouvelle
        if 'recompenses_personnalisees' not in st.session_state:
            st.session_state.recompenses_personnalisees = []
        
        # Trouver le prochain ID disponible
        next_id = 6  # Commence après les 5 récompenses par défaut
        if st.session_state.recompenses_personnalisees:
            max_id = max(r.get('id', 0) for r in st.session_state.recompenses_personnalisees)
            next_id = max_id + 1
        
        recompense_to_edit = st.selectbox(
            "Modifier une récompense existante ou créer une nouvelle",
            ["➕ Créer une nouvelle récompense"] + [f"{r['emoji']} {r['nom']}" for r in st.session_state.recompenses_personnalisees],
            key="select_recompense_edit"
        )
        
        # Récupérer les données de la récompense à modifier
        recompense_data = None
        if recompense_to_edit != "➕ Créer une nouvelle récompense":
            idx_edit = [f"{r['emoji']} {r['nom']}" for r in st.session_state.recompenses_personnalisees].index(recompense_to_edit)
            recompense_data = st.session_state.recompenses_personnalisees[idx_edit]
        
        with st.form("form_recompense", clear_on_submit=False):
            emoji = st.text_input("Emoji", value=recompense_data['emoji'] if recompense_data else "🎁", max_chars=2)
            nom = st.text_input("Nom de la récompense", value=recompense_data['nom'].replace(recompense_data['emoji'], '').strip() if recompense_data else "", placeholder="Exemple : Soirée Cinéma")
            description = st.text_area("Description", value=recompense_data['description'] if recompense_data else "", placeholder="Description détaillée de la récompense")
            points = st.number_input("Points requis", min_value=1, max_value=500, value=recompense_data['points'] if recompense_data else 50)
            
            # Sélection de la couleur
            couleurs_predefinies = [
                "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
                "linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
                "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
                "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)"
            ]
            couleur_idx = couleurs_predefinies.index(recompense_data['couleur']) if recompense_data and recompense_data['couleur'] in couleurs_predefinies else 0
            couleur_selectionnee = st.selectbox("Couleur du dégradé", couleurs_predefinies, index=couleur_idx, format_func=lambda x: "Dégradé " + str(couleurs_predefinies.index(x) + 1))
            
            col_submit, col_delete = st.columns([3, 1])
            
            with col_submit:
                if recompense_data:
                    submit_text = "💾 Modifier la Récompense"
                else:
                    submit_text = "✅ Créer la Récompense"
                
                submitted = st.form_submit_button(submit_text, use_container_width=True)
            
            with col_delete:
                if recompense_data:
                    delete_clicked = st.form_submit_button("🗑️ Supprimer", use_container_width=True)
                else:
                    delete_clicked = False
            
            if submitted:
                if nom and description and emoji:
                    nouvelle_recompense = {
                        "id": recompense_data['id'] if recompense_data else next_id,
                        "nom": f"{emoji} {nom}",
                        "description": description,
                        "points": int(points),
                        "emoji": emoji,
                        "couleur": couleur_selectionnee
                    }
                    
                    if recompense_data:
                        # Modifier la récompense existante
                        idx_to_update = st.session_state.recompenses_personnalisees.index(recompense_data)
                        st.session_state.recompenses_personnalisees[idx_to_update] = nouvelle_recompense
                        st.success(f"✅ Récompense '{nouvelle_recompense['nom']}' modifiée avec succès !")
                    else:
                        # Créer une nouvelle récompense
                        st.session_state.recompenses_personnalisees.append(nouvelle_recompense)
                        st.success(f"✅ Récompense '{nouvelle_recompense['nom']}' créée avec succès !")
                    
                    update_and_save()
                else:
                    st.error("⚠️ Veuillez remplir tous les champs.")
            
            if delete_clicked and recompense_data:
                st.session_state.recompenses_personnalisees.remove(recompense_data)
                st.success(f"✅ Récompense '{recompense_data['nom']}' supprimée !")
                update_and_save()
        
        # Afficher les récompenses personnalisées existantes
        if st.session_state.recompenses_personnalisees:
            st.markdown("---")
            st.subheader("📋 Récompenses Personnalisées")
            for idx, rec in enumerate(st.session_state.recompenses_personnalisees):
                with st.expander(f"{rec['emoji']} {rec['nom']} ({rec['points']} pts)"):
                    st.write(f"**Description:** {rec['description']}")
                    st.write(f"**Points:** {rec['points']} pts")
                    st.markdown(f"<div style='background: {rec['couleur']}; height: 30px; border-radius: 5px;'></div>", unsafe_allow_html=True)

# --- 5. CLASSEMENT ---
elif mode == "🏆 Classement":
    st.title("🏆 Tableau d'Honneur")
    
    # Animation sablier
    def animate_hourglass():
        hourglass_frames = [
            "⏳",
            "⏳",
            "⌛",
            "⌛",
            "⏳"
        ]
        placeholder = st.empty()
        for frame in hourglass_frames:
            placeholder.markdown(f"<h1 style='font-size: 72px; text-align:center;'>{frame}</h1>", unsafe_allow_html=True)
            time.sleep(0.2)
        placeholder.empty()

    # Sécurité pour accès au classement
    if not require_parent_auth(show_form=True):
        st.stop()
    
    # Bouton de déconnexion
    if st.button("🔒 Se déconnecter", use_container_width=True):
        logout_parent()
    
    # Affichage du classement
    if st.session_state.classement:
        st.success("🔓 Accès sécurisé activé !")
        animate_hourglass()
        df = pd.DataFrame(list(st.session_state.classement.items()), columns=['Héros', 'Points']).sort_values(by='Points', ascending=False)
        st.table(df)
    else:
        st.info("Aucun point enregistré pour le moment.")