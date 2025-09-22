-- Migration pour ajouter les colonnes manquantes au modèle Password
-- Exécuter dans PostgreSQL

-- Ajouter les colonnes manquantes
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS email character varying(255);
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS category character varying(100);
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS tags character varying(500);
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS is_favorite boolean DEFAULT false NOT NULL;
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS priority integer DEFAULT 0;
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS password_strength integer;
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS requires_2fa boolean DEFAULT false;
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS password_changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS expires_at timestamp with time zone;
ALTER TABLE passwords ADD COLUMN IF NOT EXISTS remind_before_expiry integer DEFAULT 30;

-- Créer les index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_passwords_user_category ON passwords(user_id, category);
CREATE INDEX IF NOT EXISTS idx_passwords_user_favorite ON passwords(user_id, is_favorite);
CREATE INDEX IF NOT EXISTS idx_passwords_user_site ON passwords(user_id, site_name);
CREATE INDEX IF NOT EXISTS idx_passwords_category ON passwords(category);
CREATE INDEX IF NOT EXISTS idx_passwords_favorite ON passwords(is_favorite);
CREATE INDEX IF NOT EXISTS idx_passwords_created_at ON passwords(created_at);

-- Vérifier que toutes les colonnes ont été ajoutées
\d passwords;