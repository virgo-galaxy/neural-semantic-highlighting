"""Shared offline SQL display grammar; no database/client execution or lookup."""
from functools import lru_cache
import re
from training.shared.offline_tools import load_lexer,provenance

PROFILES={'postgres','mysql','oracle'}
KEYWORDS=set('''SELECT FROM WHERE JOIN INNER LEFT RIGHT FULL OUTER CROSS NATURAL LATERAL ON USING AS DISTINCT ALL AND OR NOT IS NULL TRUE FALSE IN LIKE ILIKE BETWEEN EXISTS ANY SOME UNION INTERSECT EXCEPT WITH RECURSIVE GROUP BY HAVING ORDER ASC DESC NULLS FIRST LAST LIMIT OFFSET FETCH NEXT ROW ROWS ONLY OVER PARTITION RANGE UNBOUNDED PRECEDING FOLLOWING CURRENT WINDOW FILTER CREATE OR REPLACE ALTER DROP TRUNCATE TABLE VIEW MATERIALIZED INDEX UNIQUE PRIMARY KEY FOREIGN REFERENCES CHECK CONSTRAINT DEFAULT GENERATED ALWAYS IDENTITY TEMP TEMPORARY UNLOGGED IF EXISTS INSERT INTO VALUES UPDATE DELETE SET RETURNING CONFLICT DO NOTHING EXCLUDED MERGE MATCHED THEN WHEN CASE ELSE END BEGIN DECLARE RETURN RETURNS LOOP WHILE FOR EXIT CONTINUE EXCEPTION RAISE ELSIF ELSEIF FUNCTION PROCEDURE LANGUAGE IMMUTABLE STABLE VOLATILE STRICT SECURITY DEFINER INVOKER DETERMINISTIC READS MODIFIES SQL DATA NO COMMENT CHARACTER CHARSET COLLATE UNSIGNED ZEROFILL IN OUT INOUT DATABASE SCHEMA SEQUENCE SYNONYM PACKAGE BODY TRIGGER BEFORE AFTER EACH OF EXECUTE CALL PERFORM GRANT REVOKE TO PUBLIC ROLE USER IDENTIFIED QUOTA TABLESPACE ENABLE DISABLE CASCADE RESTRICT CONCURRENTLY COMMIT ROLLBACK SAVEPOINT TRANSACTION START WORK RELEASE LOCK SHARE MODE EXCLUSIVE NOWAIT SKIP LOCKED SHOW DESCRIBE EXPLAIN ANALYZE USE DELIMITER PREPARE DEALLOCATE RESET DISCARD VACUUM COPY STDIN STDOUT CSV HEADER ARRAY UNNEST SETOF IS AUTHID RESULT_CACHE PARALLEL_ENABLE EDITIONABLE NONEDITIONABLE SQLERROR WHENEVER SERVEROUTPUT VERIFY ECHO FEEDBACK DEFINE PAGESIZE LINESIZE TERMOUT TRIMSPOOL HEADING TIMING LONG TAB SQLBLANKLINES ESCAPE OFF CONNECT DISCONNECT SPOOL PROMPT ACCEPT UNDEFINE COLUMN FORMAT REMARK GO'''.split())
OBJECTS={'FROM','JOIN','INTO','UPDATE','TABLE','VIEW','SCHEMA','DATABASE','SEQUENCE','INDEX','TRIGGER','FUNCTION','PROCEDURE','PACKAGE','SYNONYM','TYPE'}
OBJECT_MODIFIERS={'IF','NOT','EXISTS','ONLY','OR','REPLACE','MATERIALIZED','TEMP','TEMPORARY','UNLOGGED','UNIQUE','CONCURRENTLY','BODY'}
CALL_EXCLUSIONS={'SELECT','FROM','WHERE','JOIN','IN','NOT','EXISTS','OVER','FILTER','PARTITION','WITH','VALUES','AS','ON','USING','WHEN','THEN','CASE','BEGIN','END','WHILE','FOR','LOOP','RETURN','RETURNS','DECLARE','EXCEPTION','RAISE','ELSE','ELSIF','ELSEIF','IF'}
KEYWORDS.update('TYPE LOAD CURRENT_DATE CURRENT_TIME CURRENT_TIMESTAMP LOCALTIME LOCALTIMESTAMP CURRENT_USER SESSION_USER SYSTEM_USER'.split())

@lru_cache(maxsize=1)
def vocabulary():
    load_lexer('sql')
    from pygments.lexers import _sql_builtins as ansi,_postgres_builtins as pg,_mysql_builtins as mysql
    types={x.upper() for x in (*ansi.DATATYPES,*pg.DATATYPES,*pg.PSEUDO_TYPES,*mysql.MYSQL_DATATYPES)}
    types.update('NUMBER VARCHAR2 NVARCHAR2 PLS_INTEGER BINARY_INTEGER BINARY_FLOAT BINARY_DOUBLE SYS_REFCURSOR CURSOR RAW UROWID XMLTYPE JSONB UUID'.split())
    functions={x.upper() for x in mysql.MYSQL_FUNCTIONS}
    functions.update('COUNT SUM AVG MIN MAX COALESCE NULLIF CAST EXTRACT TRIM SUBSTRING POSITION CURRENT_SETTING SET_CONFIG DATE_TRUNC GENERATE_SERIES JSONB_BUILD_OBJECT JSONB_ARRAY_ELEMENTS TO_CHAR TO_DATE TO_NUMBER NVL NVL2 DECODE SYSDATE SYSTIMESTAMP REGEXP_LIKE REGEXP_REPLACE'.split())
    return types,functions

@lru_cache(maxsize=3)
def lexer(profile):
    load_lexer('sql')
    from pygments.lexer import RegexLexer,bygroups
    from pygments.token import Whitespace,Keyword,String,Comment,Name,Number,Operator,Punctuation
    class DisplaySqlLexer(RegexLexer):
        flags=re.IGNORECASE|re.MULTILINE
        tokens={'root':[
            (r'^([ \t]*)(DELIMITER)([ \t]+)([^\r\n]*)(\r?\n|$)',bygroups(Whitespace,Keyword.Pseudo,Whitespace,String.Other,Whitespace)),
            (r'(\\(?:[A-Za-z]+[+]?|[?!.]))([ \t]*)([^\r\n]*)(\r?\n|$)',bygroups(Keyword.Pseudo,Whitespace,String.Other,Whitespace)),
            (r'^([ \t]*)(PROMPT|SPOOL|ACCEPT|UNDEFINE|REMARK|WHENEVER)([ \t]+)([^\r\n]*)(\r?\n|$)',bygroups(Whitespace,Keyword.Pseudo,Whitespace,String.Other,Whitespace)),
            (r'^([ \t]*)(@@?)([^\r\n]+)(\r?\n|$)',bygroups(Whitespace,Keyword.Pseudo,String.Other,Whitespace)),
            (r'[ \t\f\v]+|\r\n|\r|\n',Whitespace),
            (r'--[^\r\n]*|\#(?![>])[^\r\n]*',Comment.Single),
            (r'/\*',Comment.Multiline,'block-comment'),
            (r"q'(?:\[[\s\S]*?\]|\{[\s\S]*?\}|\([\s\S]*?\)|<[\s\S]*?>|([^\s])[\s\S]*?\1)'",String.Single),
            *([] if profile=='mysql' else [(r'(?-i:(\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$)[\s\S]*?\1)',String.Single)]),
            (r"(?:E|N|U&|X|B|_[A-Za-z0-9]+)?'(?:''|\\.|[^'\\])*'",String.Single),
            (r'(?:U&)?"(?:""|[^"])*"',String.Symbol),
            (r'`(?:``|[^`])*`',String.Symbol),
            (r'0x[0-9a-f]+|0b[01]+|(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?',Number),
            (r'::|->>|->|\#>>|\#>|\?\||\?&',Operator),
            (r"\$\d+|:(?:'[^']+'|\"[^\"]+\"|[^\W\d][\w$]*|\d+)|(?<!\w)&&?[\w]+|\?",Name.Variable.Global),
            (r'@@?[^\W\d][\w$]*(?:\.[^\W\d][\w$]*)*',Name.Variable),
            (r'\$\$|//|:=|<=|>=|<>|!=|&&|\|\||@>|<@|@@|[-+*/%=<>~!^|&@\#\\$]',Operator),
            (r'[^\W\d][\w$]*',Name),
            (r'[;:()\[\]{},.]',Punctuation),
        ],'block-comment':[
            (r'/\*',Comment.Multiline,'#push'),(r'\*/',Comment.Multiline,'#pop'),
            (r'[^/*]+|[/*]',Comment.Multiline),
        ]}
    return DisplaySqlLexer(stripnl=False,stripall=False,ensurenl=False)

def label(*,source,document_kind='sql',profile='postgres'):
    if document_kind!='sql' or profile not in PROFILES or '\0' in source:raise ValueError('Expected SQL source and a known coverage profile')
    parser=lexer(profile);types,builtins=vocabulary()
    from pygments.token import Token as T
    raw=[];cursor=0
    for a,kind,text in parser.get_tokens_unprocessed(source):
        if not text:continue
        if a!=cursor or source[a:a+len(text)]!=text:raise ValueError('SQL lexer changed original source')
        cursor=a+len(text)
        if kind in T.Error and text.strip():raise ValueError('Unsupported SQL token at '+str(a))
        if raw and kind in T.Comment.Multiline and raw[-1][2] in T.Comment.Multiline and raw[-1][1]==a:
            lo,_,_,old=raw.pop();raw.append((lo,cursor,kind,old+text))
        else:raw.append((a,cursor,kind,text))
    if cursor!=len(source):raise ValueError('Uncovered SQL source suffix')
    tokens=[]
    for a,b,kind,text in raw:
        if kind in T.String and kind not in T.String.Other:tokens.append((a,b,kind,text));continue
        lo=len(text)-len(text.lstrip());hi=len(text.rstrip())
        if lo<hi:tokens.append((a+lo,a+hi,kind,text[lo:hi]))
    words=[text.upper() for _,_,_,text in tokens];type_indices=set();definitions=set();parameters=set();variables=set();function_names=set()
    parentheses=[]
    for i,(_,_,kind,text) in enumerate(tokens):
        if text=='(':parentheses.append(words[i-1] if i else '')
        elif text==')' and parentheses:parentheses.pop()
        if kind not in T.Name or kind in T.Name.Variable:continue
        previous=words[i-1] if i else None
        cast_type=previous=='AS' and any(x in {'CAST','TRY_CAST'} for x in parentheses)
        typed_literal=i+1<len(tokens) and tokens[i+1][2] in T.String.Single and text.upper() in {'DATE','TIME','TIMESTAMP','INTERVAL'}
        if previous in {'RETURNS','::'} or text.upper() in types and (cast_type or previous=='RETURN' or typed_literal or i and tokens[i-1][2] in T.Name and words[i-1] not in KEYWORDS or i-1 in type_indices):type_indices.add(i)
    last_ddl=None
    for i,(_,_,kind,text) in enumerate(tokens):
        upper=words[i]
        if kind not in T.Name or kind in T.Name.Variable:continue
        if upper in {'CREATE','ALTER','DROP','GRANT','REVOKE'}:last_ddl=upper
        if upper in {'FUNCTION','PROCEDURE'} and last_ddl not in {'DROP','ALTER','GRANT','REVOKE'}:
            j=i+1
            while j<len(tokens) and words[j] in {'IF','NOT','EXISTS'}:j+=1
            if j>=len(tokens) or tokens[j][2] not in T.Name:continue
            while j+2<len(tokens) and words[j+1]=='.' and tokens[j+2][2] in T.Name:j+=2
            definitions.add(j);function_names.add(words[j]);j+=1
            if j<len(tokens) and words[j]=='(':
                depth=1;expect=True;j+=1
                while j<len(tokens) and depth:
                    value=words[j]
                    if value=='(':depth+=1
                    elif value==')':depth-=1
                    elif value==',' and depth==1:expect=True
                    elif depth==1 and expect and tokens[j][2] in T.Name and value not in {'IN','OUT','INOUT'}:
                        if j+1<len(tokens) and (j+1 in type_indices or words[j+1] in types):parameters.add(j)
                        elif j+1<len(tokens) and words[j+1] in {',',')'}:type_indices.add(j)
                        expect=False
                    j+=1
        if i+1 in type_indices and i and words[i-1] in {'DECLARE',';'} and upper not in KEYWORDS:variables.add(i)
    parameter_names={words[i] for i in parameters};variable_names={words[i] for i in variables}
    units=[0]
    for char in source:units.append(units[-1]+(2 if ord(char)>65535 else 1))
    output=[];features={'profile:'+profile};expect_object=None;creating=False;object_chain=False
    for i,(a,b,kind,text) in enumerate(tokens):
        upper=words[i];previous=words[i-1] if i else None;following=words[i+1] if i+1<len(tokens) else None;mods=[]
        if kind in T.Comment:role='comment';features.add('comments')
        elif kind in T.String:role='string';features.add('strings');expect_object=None;object_chain=False
        elif kind in T.Number:role='number'
        elif kind in T.Keyword.Pseudo:role='keyword';features.add('client-commands')
        elif kind in T.Name.Variable.Global:
            role='operator' if text=='?' and i and (tokens[i-1][2] in T.Name and previous not in KEYWORDS or tokens[i-1][2] in T.String or previous in {')',']'}) else 'parameter'
            if role=='parameter':features.add('parameters')
        elif kind in T.Name.Variable:role='variable';features.add('parameters')
        elif kind in T.Operator:role='operator'
        elif kind in T.Punctuation:
            role='punctuation'
            if text==';':creating=False;expect_object=None;object_chain=False
        elif kind in T.Name:
            if i in definitions:role='function';mods=['declaration'];expect_object=None;features.add('functions')
            elif i in parameters:role='parameter';mods=['declaration'];features.add('parameters')
            elif i in variables:role='variable';mods=['declaration'];features.add('parameters')
            elif expect_object and upper not in OBJECT_MODIFIERS and upper not in KEYWORDS:
                role='namespace';object_chain=following=='.'
                if creating and expect_object not in {'FROM','JOIN','INTO','UPDATE'} and not object_chain:mods=['declaration']
                expect_object=expect_object if object_chain else None
            elif upper in parameter_names:role='parameter'
            elif upper in variable_names:role='variable'
            elif following=='.':role='namespace'
            elif i in type_indices:role='type';features.add('types')
            elif following=='(' and upper not in CALL_EXCLUSIONS:
                role='function';features.add('functions')
                if upper in builtins and upper not in function_names:mods=['default-library']
            elif upper in KEYWORDS:
                role='keyword'
                if upper=='CREATE':creating=True;features.add('ddl')
                elif upper in {'ALTER','DROP','TRUNCATE'}:creating=False;features.add('ddl')
                if upper in OBJECTS:expect_object=upper
                if upper in {'WHERE','GROUP','ORDER','HAVING','LIMIT','OFFSET','SET','VALUES','RETURNING','ON'}:expect_object=None
                if upper in {'SELECT','INSERT','UPDATE','DELETE','MERGE','WITH'}:features.add('queries')
                if upper=='JOIN':features.add('joins')
            else:role='property'
        else:raise ValueError('Unmapped SQL token '+str(kind))
        span={'start':units[a],'end':units[b],'tokenType':role}
        if mods:span['modifiers']=mods
        if output and role=='comment' and output[-1]['tokenType']=='comment' and output[-1]['end']==span['start']:output[-1]['end']=span['end']
        else:output.append(span)
    if '\r\n' in source:features.add('crlf')
    if any(ord(c)>127 for c in source):features.add('unicode')
    return {'offsetEncoding':'utf-16','spans':output,'features':sorted(features)}
