"""Original common and dialect-specific SQL tasks, related across profiles."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

COMMON={
 'select-basic':'SELECT id, name, score FROM accounts WHERE active = TRUE ORDER BY name;\n',
 'filter-range':'SELECT id, total FROM orders WHERE total BETWEEN {n} AND 100 AND status IN (\'ready\', \'paid\');\n',
 'join-left':'SELECT a.id, a.name, o.total FROM accounts a LEFT JOIN orders o ON o.account_id = a.id WHERE o.total > {n};\n',
 'join-inner':'SELECT p.title, c.name FROM products p INNER JOIN categories c ON p.category_id = c.id WHERE p.price >= {n};\n',
 'join-aggregate':'SELECT a.name, COUNT(o.id) AS count FROM accounts a JOIN orders o ON a.id = o.account_id GROUP BY a.name HAVING COUNT(o.id) > {n};\n',
 'join-cte':'WITH totals AS (SELECT account_id, SUM(total) AS amount FROM orders GROUP BY account_id) SELECT a.name, t.amount FROM accounts a JOIN totals t ON t.account_id = a.id WHERE t.amount > {n};\n',
 'group-sum':'SELECT category_id, SUM(price) AS total, AVG(price) AS average FROM products GROUP BY category_id HAVING SUM(price) > {n};\n',
 'window-rank':'SELECT name, score, ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY score DESC) AS position FROM players WHERE score > {n};\n',
 'case-expression':'SELECT name, CASE WHEN score >= {n} THEN \'pass\' ELSE \'retry\' END AS result FROM attempts;\n',
 'cte-standard':'WITH ready AS (SELECT id, title FROM jobs WHERE score > {n}) SELECT id, title FROM ready ORDER BY id;\n',
 'subquery-exists':'SELECT a.id FROM accounts a WHERE EXISTS (SELECT 1 FROM orders o WHERE o.account_id = a.id AND o.total > {n});\n',
 'create-table':'CREATE TABLE records (id INTEGER PRIMARY KEY, name VARCHAR(80) NOT NULL, amount DECIMAL(10, 2) DEFAULT {n}, active BOOLEAN);\n',
 'alter-table':'ALTER TABLE records ADD COLUMN note VARCHAR(120);\nALTER TABLE records ADD CONSTRAINT positive_amount CHECK (amount >= {n});\n',
 'create-index':'CREATE UNIQUE INDEX record_names ON records (name);\nSELECT name FROM records WHERE amount > {n};\n',
 'create-view':'CREATE VIEW account_totals AS SELECT a.id, SUM(o.total) AS amount FROM accounts a JOIN orders o ON a.id = o.account_id GROUP BY a.id;\nSELECT * FROM account_totals WHERE amount > {n};\n',
 'insert-values':"INSERT INTO records (id, name, amount) VALUES ({n}, 'Virgo', 12.50);\nSELECT name FROM records WHERE id = {n};\n",
 'update-where':"UPDATE records SET amount = amount + {n}, note = 'updated' WHERE active = TRUE;\n",
 'delete-where':"DELETE FROM records WHERE active = FALSE AND amount < {n};\n",
 'transactions':"BEGIN;\nUPDATE accounts SET balance = balance - {n} WHERE id = 1;\nUPDATE accounts SET balance = balance + {n} WHERE id = 2;\nCOMMIT;\n",
 'union-query':'SELECT name FROM customers WHERE score > {n} UNION ALL SELECT name FROM suppliers WHERE active = TRUE;\n',
 'binding-select':'SELECT id, name FROM records WHERE id = {param};\n',
 'binding-update':"UPDATE records SET note = 'changed-{n}' WHERE id = {param};\n",
 'binding-join':'SELECT a.name, o.total FROM accounts a JOIN orders o ON o.account_id = a.id WHERE a.id = {param} AND o.total > {n};\n',
 'comment-unicode':"-- 星空 🌌 source notes\nSELECT '你好 🚀 {n}' AS message, name FROM records;\n/* original\n   block comment */\n",
}

DIALECT={
 'postgres':{
  'row-limit':'SELECT id, name FROM records ORDER BY id LIMIT {n} OFFSET 2;\n',
  'upsert':"INSERT INTO records (id, name) VALUES ({n}, 'Virgo') ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name RETURNING id;\n",
  'types-casts':"SELECT {param}::integer, CAST('2026-11-08' AS DATE), COALESCE(name, 'unknown') FROM records;\n",
  'function-declaration':'CREATE FUNCTION {fn}(p_value integer) RETURNS integer LANGUAGE sql AS $body$\nSELECT p_value + {n};\n$body$;\nSELECT {fn}({param});\n',
  'procedure-block':"DO $code$\nBEGIN\n  RAISE NOTICE 'value {n}';\nEND\n$code$;\nSELECT COUNT(*) FROM records;\n",
  'client-inspection':'\\dt public.*\n\\d+ records\nSELECT id FROM records WHERE score > {n};\n',
  'client-formatting':"\\x auto\n\\pset null '(null)'\nSELECT name FROM records WHERE id = {param};\n",
  'client-variable':'\\set threshold {n}\nSELECT name FROM records WHERE score > :threshold;\n',
  'client-output':"\\echo Report {n}\n\\o report.txt\nSELECT name, score FROM records ORDER BY score;\n\\o\n",
  'client-routine':'\\timing on\nCREATE FUNCTION {fn}(value integer) RETURNS integer AS $$ SELECT value * {n}; $$ LANGUAGE sql;\nSELECT {fn}({param});\n',
  'client-include':'\\i helpers.sql\n\\conninfo\nSELECT id, LENGTH(name) FROM records WHERE id = {param};\n',
 },
 'mysql':{
  'row-limit':'SELECT id, name FROM records ORDER BY id LIMIT {n} OFFSET 2;\n',
  'upsert':"INSERT INTO records (id, name) VALUES ({n}, 'Virgo') ON DUPLICATE KEY UPDATE name = VALUES(name);\n",
  'types-casts':"SELECT CAST(? AS SIGNED), CAST('2026-11-08' AS DATE), COALESCE(name, 'unknown') FROM records;\n",
  'function-declaration':'DELIMITER //\nCREATE FUNCTION {fn}(p_value INT) RETURNS INT DETERMINISTIC\nBEGIN\n  RETURN p_value + {n};\nEND//\nDELIMITER ;\nSELECT {fn}(?);\n',
  'procedure-block':'DELIMITER $$\nCREATE PROCEDURE {fn}(IN p_limit INT)\nBEGIN\n  SELECT id FROM records WHERE score > p_limit;\nEND$$\nDELIMITER ;\nCALL {fn}({n});\n',
  'client-inspection':'DELIMITER ;\nSHOW TABLES;\nDESCRIBE records;\nSELECT id FROM records WHERE score > {n};\n',
  'client-formatting':'DELIMITER ;\nSELECT name, score FROM records WHERE id = ?\\G\n',
  'client-variable':'DELIMITER ;\nSET @threshold = {n};\nSELECT name FROM records WHERE score > @threshold;\n',
  'client-output':"DELIMITER ;\nSELECT name, score FROM records ORDER BY score LIMIT {n};\nSHOW WARNINGS;\n",
  'client-routine':'DELIMITER //\nCREATE PROCEDURE {fn}()\nBEGIN\n  SELECT COUNT(*) FROM records WHERE score > {n};\nEND//\nDELIMITER ;\nCALL {fn}();\n',
  'client-include':'DELIMITER ;\nUSE preview;\nSELECT id, LENGTH(name) FROM records WHERE id = ?;\n',
 },
 'oracle':{
  'row-limit':'SELECT id, name FROM records ORDER BY id OFFSET 2 ROWS FETCH NEXT {n} ROWS ONLY;\n',
  'upsert':"MERGE INTO records t USING incoming s ON (t.id = s.id) WHEN MATCHED THEN UPDATE SET t.name = s.name WHEN NOT MATCHED THEN INSERT (id, name) VALUES (s.id, s.name);\n",
  'types-casts':"SELECT CAST(:value AS NUMBER), TO_DATE('2026-11-08', 'YYYY-MM-DD'), NVL(name, 'unknown') FROM records;\n",
  'function-declaration':'CREATE OR REPLACE FUNCTION {fn}(p_value NUMBER) RETURN NUMBER AS\nBEGIN\n  RETURN p_value + {n};\nEND;\n/\nSELECT {fn}(:value) FROM dual;\n',
  'procedure-block':"DECLARE\n  v_count NUMBER;\nBEGIN\n  SELECT COUNT(*) INTO v_count FROM records WHERE score > {n};\n  DBMS_OUTPUT.PUT_LINE(v_count);\nEND;\n/\n",
  'client-inspection':'PROMPT Inspect records {n}\nSELECT table_name FROM user_tables;\nSELECT id FROM records WHERE score > {n};\n',
  'client-formatting':'SET SERVEROUTPUT ON\nPROMPT Display selected record\nSELECT name FROM records WHERE id = :id;\n',
  'client-variable':'ACCEPT threshold NUMBER PROMPT \'Minimum score: \'\nSELECT name FROM records WHERE score > &threshold;\n',
  'client-output':'SPOOL report.txt\nSELECT name, score FROM records ORDER BY score FETCH FIRST {n} ROWS ONLY;\nSPOOL OFF\n',
  'client-routine':'WHENEVER SQLERROR EXIT SQL.SQLCODE\nCREATE OR REPLACE PROCEDURE {fn}(p_limit NUMBER) AS\nBEGIN\n  DBMS_OUTPUT.PUT_LINE(p_limit + {n});\nEND;\n/\n',
  'client-include':'@@helpers.sql\nPROMPT Query configured schema\nSELECT id, LENGTH(name) FROM &schema..records WHERE id = :id;\n',
 },
}

def main():
    root=PackSpec.open('sql').dataset_root/'sources/curriculum-v1';files={}
    for profile,specific in DIALECT.items():
        for family,template in {**COMMON,**specific}.items():
            for index in range(16):
                source=template.format(n=index+4,fn=['normalize_value','double_value','format_value','apply_limit'][index%4],param={'postgres':'$1','mysql':'?','oracle':':id'}[profile])
                position=(index//4)%4
                if position==1:source='-- Original SQL task\n'+source
                elif position==2:source='\n'+source
                elif position==3:source='/* Original short SQL source */\n'+source
                if index%4==3:source=source.lower()
                if index%5==2:source=source.replace('\n','\r\n')
                files[f'{profile}/{family}/{index:02}.sql']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting SQL curriculum. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous SQL source revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-sql-original-curriculum-v1','generatorHash':file_hash(Path(__file__)),'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing original SQL lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'profile-addressed original SQL tasks')

if __name__=='__main__':main()
