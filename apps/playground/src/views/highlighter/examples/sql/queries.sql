WITH account_totals AS (
    SELECT account_id, SUM(amount) AS total
    FROM orders
    WHERE status = 'paid'
    GROUP BY account_id
)
SELECT a.id, a.name, COALESCE(t.total, 0) AS total
FROM accounts a
LEFT JOIN account_totals t ON t.account_id = a.id
WHERE a.active = TRUE
ORDER BY total DESC;
