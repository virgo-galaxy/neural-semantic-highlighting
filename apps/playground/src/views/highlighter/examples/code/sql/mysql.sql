DELIMITER //
CREATE PROCEDURE account_summary(IN p_account_id INT)
BEGIN
    SELECT account_id, COUNT(*) AS count, SUM(amount) AS total
    FROM orders
    WHERE account_id = p_account_id
    GROUP BY account_id;
END//
DELIMITER ;

SET @account_id = 42;
CALL account_summary(@account_id);
