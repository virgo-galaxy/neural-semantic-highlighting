SET SERVEROUTPUT ON
PROMPT Load selected account

DECLARE
    v_name VARCHAR2(80);
BEGIN
    SELECT name INTO v_name
    FROM accounts
    WHERE id = :account_id;
    DBMS_OUTPUT.PUT_LINE(v_name);
END;
/

SELECT q'[Virgo's report is ready]' AS message FROM dual;
