BEGIN;

-- This application assumes ownership of the dedicated database
-- and therefore manages the extension lifecycle.
DROP EXTENSION btree_gist;

COMMIT;