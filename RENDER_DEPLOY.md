# 🚀 Guide de déploiement sur Render

Ce guide vous explique comment déployer **Foyer Magique 2.0** sur Render et le lier à votre dépôt GitHub.

## 📋 Prérequis

- Un compte GitHub avec votre projet FoyerApp2.0
- Un compte Render (gratuit disponible sur [render.com](https://render.com))
- Vos clés Supabase (`SUPABASE_URL` et `SUPABASE_KEY`)

## 🔗 Étape 1 : Préparer votre dépôt GitHub

1. **Vérifiez que tous les fichiers sont commités** :
   ```bash
   git status
   git add .
   git commit -m "Préparation pour déploiement Render"
   ```

2. **Poussez vers GitHub** :
   ```bash
   git push origin main
   ```

## 🌐 Étape 2 : Créer un nouveau service sur Render

1. **Connectez-vous à Render** :
   - Allez sur [dashboard.render.com](https://dashboard.render.com)
   - Connectez-vous avec votre compte GitHub

2. **Créez un nouveau service** :
   - Cliquez sur **"New +"** en haut à droite
   - Sélectionnez **"Web Service"**

3. **Liez votre dépôt GitHub** :
   - Cliquez sur **"Connect account"** si ce n'est pas déjà fait
   - Autorisez Render à accéder à vos dépôts GitHub
   - Sélectionnez le dépôt **FoyerApp2.0**

## ⚙️ Étape 3 : Configurer le service

### Informations de base :
- **Name** : `foyer-magique` (ou le nom de votre choix)
- **Region** : Choisissez la région la plus proche (ex: `Frankfurt` pour l'Europe)
- **Branch** : `main` (ou `master` selon votre dépôt)
- **Root Directory** : Laissez vide (racine du projet)
- **Runtime** : `Python 3`
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `gunicorn app:app`

### Variables d'environnement :

Cliquez sur **"Advanced"** puis **"Add Environment Variable"** et ajoutez :

| Clé | Valeur | Description |
|-----|--------|-------------|
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | Votre URL Supabase |
| `SUPABASE_KEY` | `eyJhbGc...` | Votre clé API Supabase |
| `DEBUG` | `False` | Mode debug (False en production) |

⚠️ **Important** : Ne partagez jamais vos clés Supabase publiquement !

## 🎨 Étape 4 : Créer les icônes PWA (optionnel mais recommandé)

Pour que l'application s'installe correctement sur smartphone, vous devez créer des icônes :

1. **Créez un dossier pour les icônes** :
   ```bash
   mkdir -p static/icons
   ```

2. **Générez les icônes** :
   - Utilisez un outil comme [PWA Asset Generator](https://github.com/onderceylan/pwa-asset-generator)
   - Ou créez une icône 512x512px et utilisez un convertisseur en ligne
   - Placez les fichiers dans `static/icons/` avec les noms :
     - `icon-72x72.png`
     - `icon-96x96.png`
     - `icon-128x128.png`
     - `icon-144x144.png`
     - `icon-152x152.png`
     - `icon-192x192.png`
     - `icon-384x384.png`
     - `icon-512x512.png`

3. **Commitez et poussez** :
   ```bash
   git add static/icons/
   git commit -m "Ajout des icônes PWA"
   git push origin main
   ```

## 🚀 Étape 5 : Déployer

1. **Lancez le déploiement** :
   - Cliquez sur **"Create Web Service"**
   - Render va automatiquement :
     - Cloner votre dépôt
     - Installer les dépendances (`pip install -r requirements.txt`)
     - Démarrer l'application avec Gunicorn

2. **Surveillez les logs** :
   - Dans l'onglet **"Logs"**, vous devriez voir :
     ```
     ✅ Supabase connecté : https://xxxxx.supabase...
     [INFO] Starting gunicorn 21.2.0
     [INFO] Listening at: http://0.0.0.0:10000
     ```

3. **Vérifiez l'URL** :
   - Render vous donne une URL du type : `https://foyer-magique.onrender.com`
   - Ouvrez cette URL dans votre navigateur
   - L'application devrait fonctionner !

## 🔄 Déploiements automatiques

Par défaut, Render déploie automatiquement à chaque push sur la branche `main`.

Pour désactiver les déploiements automatiques :
- Allez dans **Settings** → **Auto-Deploy**
- Désactivez **"Auto-Deploy"**

## 📱 Installation sur smartphone

Une fois déployé, les utilisateurs peuvent installer l'application :

### Sur Android (Chrome) :
1. Ouvrez l'URL de l'application
2. Cliquez sur le menu (⋮)
3. Sélectionnez **"Ajouter à l'écran d'accueil"**

### Sur iOS (Safari) :
1. Ouvrez l'URL de l'application
2. Cliquez sur le bouton de partage (□↑)
3. Sélectionnez **"Sur l'écran d'accueil"**

## 🛠️ Dépannage

### L'application ne démarre pas :
- Vérifiez les logs dans Render
- Assurez-vous que `SUPABASE_URL` et `SUPABASE_KEY` sont bien définies
- Vérifiez que le `Start Command` est : `gunicorn app:app`

### Erreur "Module not found" :
- Vérifiez que `requirements.txt` contient toutes les dépendances
- Les logs de build montreront les erreurs d'installation

### Erreur de connexion Supabase :
- Vérifiez que les variables d'environnement sont correctement définies
- Assurez-vous que votre clé Supabase est valide
- Vérifiez que votre projet Supabase est actif

### Le Service Worker ne fonctionne pas :
- Vérifiez que l'application est servie en HTTPS (obligatoire pour les PWA)
- Ouvrez la console du navigateur pour voir les erreurs
- Vérifiez que `sw.js` est accessible à l'URL `/static/sw.js`

## 📝 Notes importantes

- **Gratuit mais avec limitations** : Le plan gratuit de Render met l'application en veille après 15 minutes d'inactivité. Le premier démarrage peut prendre 30-60 secondes.
- **HTTPS automatique** : Render fournit automatiquement un certificat SSL, nécessaire pour les PWA.
- **Variables d'environnement** : Ne jamais commiter le fichier `.env` dans Git. Utilisez toujours les variables d'environnement de Render.

## 🎉 C'est tout !

Votre application est maintenant en ligne et peut être installée sur smartphone comme une application native !
