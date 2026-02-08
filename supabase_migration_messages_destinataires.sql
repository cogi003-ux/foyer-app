-- ============================================================
-- Migration : Erreur PGRST204 — colonne "destinataires" manquante
-- À exécuter dans l'éditeur SQL de Supabase (Dashboard → SQL Editor)
-- ============================================================
-- Si la table messages existe déjà SANS la colonne destinataires,
-- exécutez uniquement la ligne suivante :
-- ============================================================

ALTER TABLE messages ADD COLUMN IF NOT EXISTS destinataires TEXT DEFAULT '["toute_la_famille"]';

-- Mettre à jour les lignes existantes qui auraient NULL
UPDATE messages SET destinataires = '["toute_la_famille"]' WHERE destinataires IS NULL;

-- ============================================================
-- Alternative : recréer la table messages (si vous préférez repartir de zéro)
-- ATTENTION : cela supprime toutes les données de la table messages !
-- Décommentez et exécutez uniquement si nécessaire.
-- ============================================================
/*
DROP TABLE IF EXISTS messages CASCADE;
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    auteur VARCHAR(255) NOT NULL,
    texte TEXT NOT NULL,
    destinataires TEXT DEFAULT '["toute_la_famille"]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
*/
