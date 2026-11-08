\dt public.*
\d+ accounts

SELECT id, name, created_at
FROM accounts
WHERE id = $1::integer
ORDER BY created_at DESC
LIMIT 20;

CREATE FUNCTION double_score(p_value integer)
RETURNS integer LANGUAGE sql AS $body$
    SELECT p_value * 2;
$body$;
