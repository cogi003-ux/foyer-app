import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURATION & SAUVEGARDE ---
PIN_PARENT = "1234" 
DB_FILE = "data_foyer.json"

def charger_donnees():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "points_foyer": 0,
        "classement": {},
        "attente_validation": [],
        "achats_en_attente": []
    }

def sauvegarder_donnees():
    donnees = {
        "points_foyer": st.session_state.points_foyer,
        "classement": st.session_state.classement,
        "attente_validation": st.session_state.attente_validation,
        "achats_en_attente": st.session_state.achats_en_attente
    }
    with open(DB_FILE, "w") as f:
        json.dump(donnees, f)

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

# --- STYLE CSS SPÉCIAL SMARTPHONE & MODE SOMBRE ---
st.markdown("""
    <style>
    /* 1. Boutons larges pour le pouce */
    .stButton>button {
        width: 100%; 
        border-radius: 12px; 
        height: 4.5em;
        background-color: #007bff; 
        color: white !important; 
        font-weight: bold;
        font-size: 1.1em;
        border: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* 2. Titres de catégories ultra-lisibles (Bleu Azur) */
    .category-header { 
        background: #1E88E5; 
        color: white !important; 
        padding: 12px; 
        border-radius: 10px; 
        margin-top: 25px; 
        margin-bottom: 15px;
        text-align: center;
        font-weight: bold;
        text-transform: uppercase;
        border: 2px solid #64B5F6;
    }
    
    /* 3. Boîtes de missions (S'adaptent au fond clair/sombre) */
    .mission-box {
        background: rgba(255, 255, 255, 0.1); 
        padding: 20px; 
        border-radius: 15px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        margin-bottom: 10px;
        border-left: 10px solid #FFD700;
    }
    
    /* 4. Points et Textes */
    .pts-label { color: #4CAF50; font-weight: bold; font-size: 1.3em; float: right; }
    .mission-title { font-weight: bold; font-size: 1.2em; display: block; }
    .description-text { color: #A0A0A0; font-size: 0.95em; line-height: 1.4; margin-top: 8px; font-style: italic; }
    
    /* Ajustement pour le texte en mode sombre de Streamlit */
    [data-testid="stMarkdownContainer"] p {
        font-size: 1.05em;
    }
    </style>
""", unsafe_allow_html=True)

def update_and_save():
    sauvegarder_donnees()
    st.rerun()

# --- NAVIGATION ---
st.sidebar.title("🏡 Menu Foyer")
mode = st.sidebar.radio("Aller vers :", ["🚀 Missions", "🏆 Classement", "🎁 Boutique", "⚙️ Espace Parents"])
st.sidebar.divider()
st.sidebar.metric("💰 Trésor Commun", f"{st.session_state.points_foyer} pts")

# --- 1. MISSIONS (TITRES FUN + SMARTPHONE FRIENDLY) ---
if mode == "🚀 Missions":
    st.title("🚀 Missions Magiques")
    all_users = st.session_state.config["parents"] + st.session_state.config["ados"] + st.session_state.config["enfants"]
    current_user = st.selectbox("Qui cherche une mission ?", all_users)
    role = "Parent" if current_user in st.session_state.config["parents"] else "Ado" if current_user in st.session_state.config["ados"] else "Enfant"

    tasks = [
        {"n": "🍳 Chef Étoilé Michelin", "p": 25, "c": "Cuisine", "r": ["Parent"], "d": "Concocter un repas digne d'un grand restaurant."},
        {"n": "🍽️ Maître du Dressage", "p": 10, "c": "Cuisine", "r": ["Enfant", "Ado"], "d": "Mettre la table avec soin (assiettes, couverts, verres)."},
        {"n": "🧼 Ninja du Débarrassage", "p": 10, "c": "Cuisine", "r": ["Enfant", "Ado"], "d": "Faire disparaître la vaisselle sale de la table."},
        {"n": "🌊 Plongeur de l'Atlantide", "p": 15, "c": "Cuisine", "r": ["Parent", "Ado"], "d": "Vider ou vider le lave-vaisselle pour une cuisine au top."},
        {"n": "🌀 Aspirateur-Man", "p": 20, "c": "Ménage", "r": ["Parent", "Ado"], "d": "Aspirer tout le rez-de-chaussée."},
        {"n": "✨ Fée de la Serpillière", "p": 20, "c": "Ménage", "r": ["Parent", "Ado"], "d": "Faire briller le sol pour qu'on puisse se voir dedans."},
        {"n": "🧸 Rangement Express", "p": 15, "c": "Ménage", "r": ["Enfant"], "d": "Ramasser tous les jouets du salon."},
        {"n": "🚀 Mission Décollage", "p": 10, "c": "Ménage", "r": ["Enfant"], "d": "Faire son lit au carré et ranger son pyjama."},
        {"n": "🚜 Dompteur de Jungle", "p": 50, "c": "Extérieur", "r": ["Parent", "Ado"], "d": "Tondre la pelouse pour un jardin parfait."},
        {"n": "🗑️ Maître des Bacs", "p": 15, "c": "Ménage", "r": ["Parent", "Ado"], "d": "Sortir les poubelles avant que le camion ne passe."},
        {"n": "👟 Gardien du Hall", "p": 5, "c": "Ménage", "r": ["Enfant", "Ado", "Parent"], "d": "Aligner toutes les chaussures dans le hall."}
    ]

    for cat in ["Cuisine", "Ménage", "Extérieur"]:
        cat_t = [t for t in tasks if t["c"] == cat and role in t["r"]]
        if cat_t:
            st.markdown(f"<div class='category-header'>{cat}</div>", unsafe_allow_html=True)
            for t in cat_t:
                st.markdown(f"""
                    <div class='mission-box'>
                        <span class='pts-label'>+{t['p']} pts</span>
                        <span class='mission-title'>{t['n']}</span>
                        <span class='description-text'>👉 {t['d']}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                label = "Vérifier & Valider ✅" if role == "Parent" else "J'ai fini ! 🚀"
                if st.button(label, key=f"btn_{t['n']}_{current_user}"):
                    if role == "Parent":
                        st.session_state.points_foyer += t['p']
                        st.session_state.classement[current_user] = st.session_state.classement.get(current_user, 0) + t['p']
                    else:
                        st.session_state.attente_validation.append({"user": current_user, "task": t['n'], "pts": t['p']})
                    update_and_save()

# --- 2. CLASSEMENT ---
elif mode == "🏆 Classement":
    st.title("🏆 Tableau d'Honneur")
    if st.session_state.classement:
        df = pd.DataFrame(list(st.session_state.classement.items()), columns=['Héros', 'Points']).sort_values(by='Points', ascending=False)
        st.table(df)
    else: st.info("Le tableau est vide, à vous de jouer !")

# --- 3. ESPACE PARENTS ---
elif mode == "⚙️ Espace Parents":
    if not st.session_state.parent_authenticated:
        pin = st.text_input("Code Parent :", type="password")
        if pin == PIN_PARENT:
            st.session_state.parent_authenticated = True
            st.rerun()
        st.stop()
    
    st.title("🛡️ Validation")
    for idx, d in enumerate(st.session_state.attente_validation):
        if st.button(f"Confirmer : {d['task']} par {d['user']} (+{d['pts']} pts)", key=f"v_{idx}"):
            st.session_state.points_foyer += d['pts']
            st.session_state.classement[d['user']] = st.session_state.classement.get(d['user'], 0) + d['pts']
            st.session_state.attente_validation.pop(idx)
            update_and_save()

# --- 4. BOUTIQUE ---
else:
    st.title("🎁 Boutique")
    st.write("Bientôt disponible...")