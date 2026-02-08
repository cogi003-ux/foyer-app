-- Migration : colonne image_url pour les messages + bucket Storage
-- À exécuter dans l'éditeur SQL de Supabase (Dashboard → SQL Editor)

-- 1. Ajouter la colonne image_url à la table messages (obligatoire pour les photos)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS image_url TEXT;

-- 2. Créer le bucket Storage pour les photos des messages (à exécuter si pas déjà fait)
-- Dans le Dashboard Supabase : Storage → New bucket → nom "message-images", Public = true
-- Ou via SQL (si votre projet le supporte) :
-- INSERT INTO storage.buckets (id, name, public) VALUES ('message-images', 'message-images', true)
-- ON CONFLICT (id) DO NOTHING;

-- 3. Politique pour permettre les uploads (anon ou service_role selon votre config)
-- Storage → message-images → Policies → New policy : Allow uploads for authenticated or anon
