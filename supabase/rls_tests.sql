-- ========================================================================
-- NUTRI-103 RLS Tests — Output via SELECT (tab Results)
-- ========================================================================

DROP TABLE IF EXISTS _test_results;

CREATE TEMP TABLE _test_results (
    test_id TEXT,
    description TEXT,
    result TEXT
);

GRANT INSERT, SELECT ON _test_results TO authenticated;
GRANT INSERT, SELECT ON _test_results TO anon;

-- ========================================================================
-- SET ROLE: authenticated sebagai User A
-- ========================================================================
SET request.jwt.claims = '{"sub": "16e73c75-6764-4ec9-bbfd-f82151a905ee", "role": "authenticated"}';
SET ROLE authenticated;

-- ========================================================================
-- TC-103-1: User A cuma lihat profile sendiri
-- ========================================================================
DO $$
DECLARE
    row_count INT;
    own_count INT;
BEGIN
    SELECT COUNT(*) INTO row_count FROM profiles;
    SELECT COUNT(*) INTO own_count FROM profiles
    WHERE id = '16e73c75-6764-4ec9-bbfd-f82151a905ee'::uuid;

    INSERT INTO _test_results VALUES (
        'TC-103-1',
        'User A only sees own profile',
        CASE WHEN row_count = 1 AND own_count = 1 THEN 'PASS' ELSE 'FAIL (visible=' || row_count || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-2: User A update profile User B → deny
-- ========================================================================
DO $$
DECLARE
    affected INT;
BEGIN
    UPDATE profiles SET age_years = 99
    WHERE id = '8f11cb7d-4e20-48fd-a3e0-7957b2b580ae'::uuid;
    GET DIAGNOSTICS affected = ROW_COUNT;

    INSERT INTO _test_results VALUES (
        'TC-103-2',
        'User A cannot update User B profile',
        CASE WHEN affected = 0 THEN 'PASS' ELSE 'FAIL (affected=' || affected || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-3: User A delete profile User B → deny
-- ========================================================================
DO $$
DECLARE
    affected INT;
BEGIN
    DELETE FROM profiles
    WHERE id = '8f11cb7d-4e20-48fd-a3e0-7957b2b580ae'::uuid;
    GET DIAGNOSTICS affected = ROW_COUNT;

    INSERT INTO _test_results VALUES (
        'TC-103-3',
        'User A cannot delete User B profile',
        CASE WHEN affected = 0 THEN 'PASS' ELSE 'FAIL (affected=' || affected || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-8: User A update disclaimer sendiri → sukses
-- ========================================================================
DO $$
DECLARE
    affected INT;
BEGIN
    UPDATE profiles
    SET disclaimer_accepted_at = NOW(), disclaimer_version = 'v1.0'
    WHERE id = '16e73c75-6764-4ec9-bbfd-f82151a905ee'::uuid;
    GET DIAGNOSTICS affected = ROW_COUNT;

    INSERT INTO _test_results VALUES (
        'TC-103-8',
        'User A can update own disclaimer',
        CASE WHEN affected = 1 THEN 'PASS' ELSE 'FAIL (affected=' || affected || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-5: User A select daily_intake_logs User B → kosong
-- ========================================================================
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM daily_intake_logs
    WHERE user_id = '8f11cb7d-4e20-48fd-a3e0-7957b2b580ae'::uuid;

    INSERT INTO _test_results VALUES (
        'TC-103-5',
        'User A sees empty logs for User B',
        CASE WHEN cnt = 0 THEN 'PASS' ELSE 'FAIL (visible=' || cnt || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-34: User A read daily_limits User B → kosong
-- ========================================================================
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM daily_limits
    WHERE user_id = '8f11cb7d-4e20-48fd-a3e0-7957b2b580ae'::uuid;

    INSERT INTO _test_results VALUES (
        'TC-103-34',
        'User A sees empty daily_limits for User B',
        CASE WHEN cnt = 0 THEN 'PASS' ELSE 'FAIL (visible=' || cnt || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-28: Authenticated read portion_references → sukses
-- ========================================================================
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM portion_references;

    INSERT INTO _test_results VALUES (
        'TC-103-28',
        'Authenticated can read portion_references',
        CASE WHEN cnt > 0 THEN 'PASS' ELSE 'FAIL (visible=' || cnt || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-29: Authenticated write portion_references → ditolak
-- ========================================================================
DO $$
DECLARE
    denied BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO portion_references (name, measurement_type, amount_gram)
        VALUES ('Hacker Food', 'WEIGHT', 999);
    EXCEPTION
        WHEN insufficient_privilege THEN
            denied := TRUE;
    END;

    INSERT INTO _test_results VALUES (
        'TC-103-29',
        'Authenticated cannot write portion_references',
        CASE WHEN denied THEN 'PASS' ELSE 'FAIL (insert sukses!)' END
    );
END $$;

-- ========================================================================
-- TC-103-38: User A read scanned_products private User B → kosong
-- ========================================================================
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM scanned_products
    WHERE created_by = '8f11cb7d-4e20-48fd-a3e0-7957b2b580ae'::uuid AND is_public = false;

    INSERT INTO _test_results VALUES (
        'TC-103-38',
        'User A cannot see User B private products',
        CASE WHEN cnt = 0 THEN 'PASS' ELSE 'FAIL (visible=' || cnt || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-39: User A read scanned_products public → sukses
-- ========================================================================
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM scanned_products
    WHERE is_public = true;

    INSERT INTO _test_results VALUES (
        'TC-103-39',
        'User A can see public products',
        CASE WHEN cnt > 0 THEN 'PASS' ELSE 'FAIL (visible=' || cnt || ')' END
    );
END $$;

-- ========================================================================
-- TC-103-6: Anon akses profiles → ditolak
-- ========================================================================
RESET ROLE;
SET ROLE anon;
SET request.jwt.claims = '{"role": "anon"}';

DO $$
DECLARE
    denied BOOLEAN := FALSE;
BEGIN
    BEGIN
        PERFORM COUNT(*) FROM profiles;
    EXCEPTION
        WHEN insufficient_privilege THEN
            denied := TRUE;
    END;

    INSERT INTO _test_results VALUES (
        'TC-103-6',
        'Anon cannot access profiles',
        CASE WHEN denied THEN 'PASS' ELSE 'FAIL (anon bisa akses!)' END
    );
END $$;

-- ========================================================================
-- RESET ROLE
-- ========================================================================
RESET ROLE;
RESET request.jwt.claims;

-- ========================================================================
-- OUTPUT
-- ========================================================================
SELECT test_id, description, result
FROM _test_results
ORDER BY test_id;

SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE result = 'PASS') AS pass,
    COUNT(*) FILTER (WHERE result = 'FAIL' OR result LIKE 'FAIL%') AS fail
FROM _test_results;

DROP TABLE IF EXISTS _test_results;