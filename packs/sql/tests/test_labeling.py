import hashlib,json
from pathlib import Path
import unittest
from packs.sql.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode

class SqlTeacherTests(unittest.TestCase):
    def test_independent_golden(self):
        root=Path(__file__).parents[1]
        for case in json.loads((root/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source'],profile=case['profile'])
                self.assertEqual(result['spans'],gold['spans'])
                encode({'source':gold['source'],'documentKind':'sql','result':result,'contentHash':hashlib.sha256(gold['source'].encode()).hexdigest()},Schema.load(root/'schema.json'))

    def test_common_syntax_has_common_profile_labels(self):
        source='SELECT a.id, COALESCE(a.name, \'unknown\') FROM accounts a WHERE a.id = 4;\n'
        expected=label(source=source,profile='postgres')['spans']
        for profile in ['mysql','oracle']:self.assertEqual(label(source=source,profile=profile)['spans'],expected)

    def test_no_database_execution(self):
        self.assertTrue(label(source='DROP DATABASE never_execute_this;\n')['spans'])

    def test_dollar_body_has_original_coordinates(self):
        source='CREATE FUNCTION f(p_id integer) RETURNS integer AS $body$ SELECT p_id; $body$ LANGUAGE sql;\n'
        raw=source.encode('utf-16-le');strings=[raw[s['start']*2:s['end']*2].decode('utf-16-le') for s in label(source=source)['spans'] if s['tokenType']=='string']
        self.assertEqual(strings,['$body$ SELECT p_id; $body$'])

    def test_mysql_delimiter_does_not_hide_program_body(self):
        source='DELIMITER $$\nCREATE PROCEDURE f(IN p_id INT) BEGIN SELECT p_id; END$$\nDELIMITER ;\n'
        result=label(source=source,profile='mysql');raw=source.encode('utf-16-le')
        select=[s for s in result['spans'] if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='SELECT']
        self.assertEqual(select[0]['tokenType'],'keyword')

    def test_query_alias_is_not_a_type(self):
        source='SELECT display_name AS name FROM accounts;\n';raw=source.encode('utf-16-le')
        names=[s for s in label(source=source)['spans'] if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='name']
        self.assertEqual(names[0]['tokenType'],'property')

if __name__=='__main__':unittest.main()
