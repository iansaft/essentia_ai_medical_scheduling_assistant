BEGIN;

-- Required to combine UUID equality with range overlap checks
-- in GiST exclusion constraints used by appointment scheduling.
CREATE EXTENSION btree_gist;

COMMIT;