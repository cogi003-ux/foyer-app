-- Migration : ajouter la colonne est_recurrent à budget_familial
-- À exécuter dans l'éditeur SQL Supabase si la table existe déjà.

ALTER TABLE budget_familial
ADD COLUMN IF NOT EXISTS est_recurrent BOOLEAN NOT NULL DEFAULT FALSE;
