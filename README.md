# ✨ Foyer Magique

Application familiale moderne pour organiser les tâches ménagères et partager des messages dans un foyer. Design glassmorphism chaleureux avec une palette de couleurs ambre, blanc cassé et bois.

## ✨ Fonctionnalités

- 📋 **Tableau des Tâches** : Gestion des tâches ménagères avec nom, icône, responsable et statut (À faire / En cours / Terminé)
- 💌 **Mur de Messages** : Partagez des mots doux et des rappels avec un style post-it
- 📊 **Tableau de bord** : Vue d'ensemble des tâches et messages
- 🎨 **Design chaleureux** : Palette de couleurs ambre, blanc cassé et bois avec effet glassmorphism
- 📱 **Interface responsive** : Accessible sur smartphone et ordinateur
- 🔄 **Onglets intuitifs** : Navigation claire entre Tableau de bord, Tâches et Messages

## 🚀 Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurer Supabase (optionnel mais recommandé) :
   - Créer un projet sur [Supabase](https://supabase.com)
   - Exécuter le script SQL dans `supabase_setup.sql` dans l'éditeur SQL de Supabase
   - Configurer les variables d'environnement :
     ```bash
     export SUPABASE_URL="votre_url_supabase"
     export SUPABASE_KEY="votre_clé_supabase"
     ```

3. Lancer l'application :
```bash
python app.py
```

4. Ouvrir dans le navigateur :
```
http://localhost:5001
```

**Note** : Le port 5001 est utilisé car le port 5000 est souvent occupé par AirPlay Receiver sur macOS.

## 📱 Accès depuis un smartphone

Pour accéder à l'application depuis votre smartphone sur le même réseau :

1. Trouver l'adresse IP de votre ordinateur :
   - Mac/Linux : `ifconfig` ou `ip addr`
   - Windows : `ipconfig`

2. Lancer l'application avec :
```bash
python app.py
```

3. Sur votre smartphone, ouvrir :
```
http://VOTRE_IP:5001
```

## 🎨 Design

L'application utilise un design **glassmorphism chaleureux** avec :
- Palette de couleurs : ambre, blanc cassé et bois
- Effets de transparence et flou (backdrop-filter)
- Animations fluides
- Dégradés de couleurs chaleureux
- Interface responsive adaptée aux petits écrans
- Icônes Lucide pour une meilleure lisibilité

## 📂 Structure du projet

```
FoyerApp2.0/
├── app.py                 # Backend Flask
├── database.py            # Gestion Supabase
├── templates/
│   └── index.html        # Interface HTML avec onglets
├── static/
│   ├── css/
│   │   └── style.css     # Styles glassmorphism chaleureux
│   └── js/
│       └── app.js        # Logique JavaScript
├── supabase_setup.sql    # Script SQL pour créer les tables
├── requirements.txt       # Dépendances Python
└── README.md             # Documentation
```

## 🔧 Technologies utilisées

- **Backend** : Flask (Python)
- **Frontend** : HTML5, CSS3 (glassmorphism), JavaScript (ES6+)
- **Base de données** : Supabase (PostgreSQL)
- **Icônes** : Lucide Icons
- **Format** : Heure en format 24h, chiffres au format belge

## 📝 Tables Supabase

L'application utilise deux tables :

1. **taches** : Stocke les tâches ménagères
   - id (SERIAL PRIMARY KEY)
   - nom (VARCHAR)
   - icone (VARCHAR)
   - responsable (VARCHAR)
   - statut (VARCHAR : 'a_faire', 'en_cours', 'termine')
   - created_at (TIMESTAMP)

2. **messages** : Stocke les messages du mur
   - id (SERIAL PRIMARY KEY)
   - auteur (VARCHAR)
   - texte (TEXT)
   - created_at (TIMESTAMP)

## 🌐 Déploiement

Pour déployer en production, vous pouvez utiliser :
- **Heroku** : Ajouter un `Procfile` avec `web: gunicorn app:app`
- **PythonAnywhere** : Uploader les fichiers et configurer l'application web
- **VPS** : Utiliser Gunicorn + Nginx

Exemple avec Gunicorn :
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📄 Licence

Projet personnel - Foyer Magique
