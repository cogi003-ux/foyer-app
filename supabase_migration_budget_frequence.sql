-- Migration : remplacer est_recurrent par frequence (une_fois, mensuel, trimestriel)
-- À exécuter dans l'éditeur SQL Supabase si la table budget_familial existe déjà avec est_recurrent.

-- Ajouter la nouvelle colonne (avec défaut pour les lignes existantes)
ALTER TABLE budget_familial
ADD COLUMN IF NOT EXISTS frequence VARCHAR(20) NOT NULL DEFAULT 'une_fois'
CHECK (frequence IN ('une_fois', 'mensuel', 'trimestriel'));

-- Optionnel : migrer les anciennes valeurs (est_recurrent = true -> mensuel)
-- À exécuter seulement si la colonne est_recurrent existe encore :
-- UPDATE budget_familial SET frequence = 'mensuel' WHERE est_recurrent = true;

-- Supprimer l'ancienne colonne si elle existe (décommenter après vérification)
-- ALTER TABLE budget_familial DROP COLUMN IF EXISTS est_recurrent;
