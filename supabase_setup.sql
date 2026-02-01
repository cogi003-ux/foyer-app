-- Script SQL pour créer les tables de Foyer Magique dans Supabase
-- À exécuter dans l'éditeur SQL de Supabase

-- Table des tâches ménagères (missions)
CREATE TABLE IF NOT EXISTS taches (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    icone VARCHAR(50) NOT NULL DEFAULT 'sparkles',
    description TEXT,
    categorie VARCHAR(50) NOT NULL DEFAULT 'Ménage',
    type VARCHAR(20) NOT NULL DEFAULT 'quotidienne' CHECK (type IN ('quotidienne', 'hebdomadaire', 'ponctuelle')),
    points INTEGER NOT NULL DEFAULT 10,
    roles_autorises TEXT[] DEFAULT ARRAY['Enfant', 'Ado'],
    statut VARCHAR(20) NOT NULL DEFAULT 'a_faire' CHECK (statut IN ('a_faire', 'en_cours', 'en_attente', 'termine')),
    responsable VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_personnalisee BOOLEAN DEFAULT FALSE
);

-- Table des tâches complétées (historique)
CREATE TABLE IF NOT EXISTS taches_completees (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES taches(id) ON DELETE SET NULL,
    task_nom VARCHAR(255) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    date_completion DATE NOT NULL,
    points INTEGER NOT NULL,
    validated BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des validations en attente
CREATE TABLE IF NOT EXISTS attente_validation (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL,
    task_nom VARCHAR(255) NOT NULL,
    task_id INTEGER REFERENCES taches(id) ON DELETE SET NULL,
    points INTEGER NOT NULL,
    date_completion DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des messages (mur de messages)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    auteur VARCHAR(255) NOT NULL,
    texte TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table de configuration de la famille
CREATE TABLE IF NOT EXISTS config_famille (
    id SERIAL PRIMARY KEY,
    parents TEXT[] DEFAULT ARRAY['Papa', 'Maman'],
    ados TEXT[] DEFAULT ARRAY[]::TEXT[],
    enfants TEXT[] DEFAULT ARRAY['Enfant 1', 'Enfant 2'],
    pin_parent_hash VARCHAR(255) DEFAULT '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4',
    points_foyer INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table du classement des points
CREATE TABLE IF NOT EXISTS classement (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE NOT NULL,
    points INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des récompenses personnalisées
CREATE TABLE IF NOT EXISTS recompenses_personnalisees (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    emoji VARCHAR(10) DEFAULT '🎁',
    description TEXT,
    points INTEGER NOT NULL,
    couleur_gradient TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des récompenses achetées
CREATE TABLE IF NOT EXISTS recompenses_achetees (
    id SERIAL PRIMARY KEY,
    recompense_id INTEGER,
    recompense_nom VARCHAR(255) NOT NULL,
    points_utilises INTEGER NOT NULL,
    date_achat DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_taches_statut ON taches(statut);
CREATE INDEX IF NOT EXISTS idx_taches_type ON taches(type);
CREATE INDEX IF NOT EXISTS idx_taches_created_at ON taches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_taches_completees_date ON taches_completees(date_completion DESC);
CREATE INDEX IF NOT EXISTS idx_taches_completees_user ON taches_completees(user_name);
CREATE INDEX IF NOT EXISTS idx_attente_validation_user ON attente_validation(user_name);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_classement_points ON classement(points DESC);

-- Insérer la configuration par défaut si elle n'existe pas
INSERT INTO config_famille (id, parents, ados, enfants, points_foyer)
VALUES (1, ARRAY['Papa', 'Maman'], ARRAY[]::TEXT[], ARRAY['Enfant 1', 'Enfant 2'], 0)
ON CONFLICT DO NOTHING;
