-- ============================================================
-- Script SQL complet pour Foyer Magique 2.0
-- À exécuter dans l'éditeur SQL de Supabase
-- ============================================================

-- ============================================================
-- NETTOYAGE : Suppression de toutes les tables existantes
-- ============================================================
DROP TABLE IF EXISTS taches, messages, config_famille, taches_completees, attente_validation, classement, recompenses_personnalisees, recompenses_achetees CASCADE;

-- ============================================================
-- 1. TABLE TACHES
-- ============================================================
CREATE TABLE IF NOT EXISTS taches (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    icone VARCHAR(50) NOT NULL DEFAULT 'sparkles',
    responsable VARCHAR(255),
    responsables TEXT[] DEFAULT ARRAY[]::TEXT[],
    type VARCHAR(20) NOT NULL DEFAULT 'quotidienne' 
        CHECK (type IN ('quotidienne', 'hebdomadaire', 'ponctuelle')),
    points INTEGER NOT NULL DEFAULT 10,
    statut VARCHAR(20) NOT NULL DEFAULT 'a_faire' 
        CHECK (statut IN ('a_faire', 'en_cours', 'en_attente', 'termine')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 2. TABLE MESSAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    auteur VARCHAR(255) NOT NULL,
    texte TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 3. TABLE CONFIG_FAMILLE
-- ============================================================
CREATE TABLE IF NOT EXISTS config_famille (
    id SERIAL PRIMARY KEY,
    parents TEXT[] DEFAULT ARRAY['Papa', 'Maman'],
    ados TEXT[] DEFAULT ARRAY[]::TEXT[],
    enfants TEXT[] DEFAULT ARRAY['Enfant 1', 'Enfant 2'],
    pin_parent_hash VARCHAR(255) DEFAULT '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4',
    points_foyer INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 4. TABLE TACHES_COMPLETEES
-- ============================================================
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

-- ============================================================
-- 5. TABLE ATTENTE_VALIDATION
-- ============================================================
CREATE TABLE IF NOT EXISTS attente_validation (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL,
    task_nom VARCHAR(255) NOT NULL,
    task_id INTEGER REFERENCES taches(id) ON DELETE SET NULL,
    points INTEGER NOT NULL,
    date_completion DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 6. TABLE CLASSEMENT
-- ============================================================
CREATE TABLE IF NOT EXISTS classement (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE NOT NULL,
    points INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 7. TABLE RECOMPENSES_PERSONNALISEES
-- ============================================================
CREATE TABLE IF NOT EXISTS recompenses_personnalisees (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    emoji VARCHAR(10) DEFAULT '🎁',
    description TEXT,
    points INTEGER NOT NULL,
    couleur_gradient TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 8. TABLE RECOMPENSES_ACHETEES
-- ============================================================
CREATE TABLE IF NOT EXISTS recompenses_achetees (
    id SERIAL PRIMARY KEY,
    recompense_id INTEGER,
    recompense_nom VARCHAR(255) NOT NULL,
    points_utilises INTEGER NOT NULL,
    date_achat DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- INDEX POUR AMÉLIORER LES PERFORMANCES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_taches_statut ON taches(statut);
CREATE INDEX IF NOT EXISTS idx_taches_type ON taches(type);
CREATE INDEX IF NOT EXISTS idx_taches_created_at ON taches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_taches_responsables ON taches USING GIN(responsables);
CREATE INDEX IF NOT EXISTS idx_taches_completees_date ON taches_completees(date_completion DESC);
CREATE INDEX IF NOT EXISTS idx_taches_completees_user ON taches_completees(user_name);
CREATE INDEX IF NOT EXISTS idx_taches_completees_task_id ON taches_completees(task_id);
CREATE INDEX IF NOT EXISTS idx_attente_validation_user ON attente_validation(user_name);
CREATE INDEX IF NOT EXISTS idx_attente_validation_task_id ON attente_validation(task_id);
CREATE INDEX IF NOT EXISTS idx_attente_validation_created_at ON attente_validation(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_classement_points ON classement(points DESC);
CREATE INDEX IF NOT EXISTS idx_classement_user_name ON classement(user_name);
CREATE INDEX IF NOT EXISTS idx_recompenses_achetees_date ON recompenses_achetees(date_achat DESC);

-- ============================================================
-- DONNÉES PAR DÉFAUT
-- ============================================================

-- Insérer la configuration par défaut si elle n'existe pas
-- Note: Si la table est vide, on insère. Sinon, on ne fait rien.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM config_famille LIMIT 1) THEN
        INSERT INTO config_famille (parents, ados, enfants, points_foyer, pin_parent_hash)
        VALUES (
            ARRAY['Papa', 'Maman'], 
            ARRAY[]::TEXT[], 
            ARRAY['Enfant 1', 'Enfant 2'], 
            0,
            '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4'
        );
    END IF;
END $$;

-- ============================================================
-- VÉRIFICATION
-- ============================================================
-- Pour vérifier que toutes les tables ont été créées, exécutez :
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('taches', 'messages', 'config_famille', 'taches_completees', 
--                    'attente_validation', 'classement', 'recompenses_personnalisees', 
--                    'recompenses_achetees')
-- ORDER BY table_name;
