"""Offline CPython token/AST teacher. Never import this module from inference."""
from __future__ import annotations

import ast
from bisect import bisect_left
import builtins
import io
import keyword
import sys
import token
import tokenize
import unicodedata


def normalized(name): return unicodedata.normalize("NFKC", name)


class Scope:
    def __init__(self, parent=None, kind="module"):
        self.parent, self.kind = parent, kind
        self.names, self.globals, self.nonlocals = {}, set(), set()

    def resolve(self, name):
        scope = self
        if name in self.globals:
            while scope.parent: scope = scope.parent
            return scope.names.get(name)
        if name in self.nonlocals: scope = scope.parent
        first = True
        while scope:
            if (first or scope.kind != "class") and name in scope.names:
                return scope.names[name]
            first, scope = False, scope.parent
        return None


def label(*, source: str, document_kind="python", profile="python3") -> dict:
    if document_kind != "python" or profile != "python3" or "\0" in source:
        raise ValueError("Expected original Python 3 source")
    tree = ast.parse(source, filename="source.py", type_comments=True)
    lines = source.split("\n")
    line_starts, total = [], 0
    for line in lines:
        line_starts.append(total); total += len(line) + 1
    units = [0]
    for character in source: units.append(units[-1] + (2 if ord(character) > 0xFFFF else 1))

    def coordinate(position):
        row, col = position
        if row == len(lines) + 1 and col == 0: return len(source)
        if not 1 <= row <= len(lines) or not 0 <= col <= len(lines[row-1]):
            raise ValueError("Tokenizer location outside original source")
        return line_starts[row-1] + col

    def ast_coordinate(row, byte_col):
        line = lines[row-1]
        prefix = line.encode("utf-8")[:byte_col].decode("utf-8")
        return line_starts[row-1] + len(prefix)

    def node_range(node):
        return ast_coordinate(node.lineno,node.col_offset), ast_coordinate(node.end_lineno,node.end_col_offset)

    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    located = [(coordinate(item.start),coordinate(item.end),item) for item in tokens
               if item.type not in {token.ENCODING,token.ENDMARKER,token.NEWLINE,token.NL,token.INDENT,token.DEDENT}]
    starts = [a for a,_,_ in located]
    formats, depth, start_format = [], 0, None
    features = set()
    for a,b,item in located:
        name = token.tok_name[item.type]
        if name in {"FSTRING_START","TSTRING_START"}:
            if depth == 0: start_format = a
            depth += 1; features.add("t-strings" if name.startswith("T") else "f-strings")
        elif name in {"FSTRING_END","TSTRING_END"}:
            depth -= 1
            if depth < 0: raise ValueError("Unbalanced formatted string")
            if depth == 0: formats.append((start_format,b))
    if depth: raise ValueError("Unclosed formatted string")
    roles, decorator_ats = {}, set()

    def within(node):
        a,b = node_range(node)
        return [(lo,hi,t) for lo,hi,t in located[bisect_left(starts,a):bisect_left(starts,b)] if hi <= b]

    def mark(a,b,role,modifiers=()):
        if not 0 <= a < b <= len(source): raise ValueError("Invalid AST source range")
        roles[(a,b)] = (role,tuple(modifiers))

    def mark_name(node, role, modifiers=()):
        if isinstance(node,ast.Name): mark(*node_range(node),role,modifiers); return
        name = getattr(node,"name",None) or getattr(node,"arg",None)
        matches = [(a,b) for a,b,t in within(node) if t.type == token.NAME and normalized(t.string) == name]
        if not matches: raise ValueError("AST identifier has no original token")
        mark(*matches[0],role,modifiers)

    def declaration(node, role, modifiers=()):
        matches = within(node)
        wanted = "class" if isinstance(node,ast.ClassDef) else "def"
        seen = False
        for a,b,item in matches:
            if item.string == wanted: seen=True; continue
            if seen and item.type == token.NAME:
                mark(a,b,role,("declaration",*modifiers)); return
        raise ValueError("Missing declaration token")

    def collect(node, scope):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            scope.names[node.name] = "method" if scope.kind == "class" else "function"; return
        if isinstance(node,ast.ClassDef): scope.names[node.name]="class"; return
        if isinstance(node,(ast.Lambda,ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp)): return
        if isinstance(node,ast.Global): scope.globals.update(node.names)
        elif isinstance(node,ast.Nonlocal): scope.nonlocals.update(node.names)
        elif isinstance(node,ast.Name) and isinstance(node.ctx,ast.Store): scope.names.setdefault(node.id,"variable")
        elif isinstance(node,ast.MatchAs) and node.name: scope.names.setdefault(node.name,"variable")
        elif isinstance(node,ast.MatchStar) and node.name: scope.names.setdefault(node.name,"variable")
        elif isinstance(node,ast.Import):
            for alias in node.names: scope.names[alias.asname or alias.name.split(".")[0]]="namespace"
        elif isinstance(node,ast.ImportFrom):
            for alias in node.names: scope.names[alias.asname or alias.name]="variable"
        elif isinstance(node,getattr(ast,"TypeAlias",())) and isinstance(node.name,ast.Name): scope.names[node.name.id]="type"
        for child in ast.iter_child_nodes(node): collect(child,scope)

    builtin_types = {name for name,value in vars(builtins).items() if isinstance(value,type)}
    builtin_functions = {name for name,value in vars(builtins).items() if callable(value)} - builtin_types

    def name_role(name,scope,annotation=False,call=False):
        binding = scope.resolve(name)
        if annotation: return "type", (() if binding else ("default-library",) if name in builtin_types else ())
        if binding: return binding, ()
        if name in builtin_types: return "type", ("default-library",)
        if name in builtin_functions: return "function", ("default-library",)
        return ("function" if call else "variable"), ()

    def visit(node,scope,annotation=False):
        if isinstance(node,(ast.JoinedStr,getattr(ast,"TemplateStr",ast.JoinedStr))): return
        if isinstance(node,ast.Name):
            role,mods = name_role(node.id,scope,annotation)
            mark(*node_range(node),role,(("declaration",)+mods if isinstance(node.ctx,ast.Store) else mods)); return
        if isinstance(node,ast.Attribute):
            visit(node.value,scope,annotation)
            names = [(a,b) for a,b,t in within(node) if t.type==token.NAME and normalized(t.string)==node.attr]
            if not names: raise ValueError("Missing attribute token")
            mark(*names[-1],"type" if annotation else "property"); return
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            features.add("functions")
            modifiers=[]
            if isinstance(node,ast.AsyncFunctionDef): modifiers.append("async");features.add("async")
            def yields(value):
                if isinstance(value,(ast.Yield,ast.YieldFrom)):return True
                if isinstance(value,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Lambda)):return False
                return any(yields(child) for child in ast.iter_child_nodes(value))
            if any(yields(statement) for statement in node.body):modifiers.append("generator");features.add("generators")
            declaration(node,"method" if scope.kind=="class" else "function",modifiers)
            for decorator in node.decorator_list: visit_decorator(decorator,scope)
            for default in [*node.args.defaults,*node.args.kw_defaults]:
                if default:visit(default,scope)
            if node.returns:visit(node.returns,scope,True);features.add("annotations")
            child=Scope(scope,"function")
            arguments=[*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs]
            arguments += [arg for arg in (node.args.vararg,node.args.kwarg) if arg]
            for arg in arguments:
                child.names[arg.arg]="parameter";mark_name(arg,"parameter",("declaration",))
                if arg.annotation:visit(arg.annotation,scope,True);features.add("annotations")
            for parameter in getattr(node,"type_params",[]):visit_type_parameter(parameter,child)
            for statement in node.body:collect(statement,child)
            for name in child.globals | child.nonlocals:child.names.pop(name,None)
            for statement in node.body:visit(statement,child)
            return
        if isinstance(node,ast.ClassDef):
            features.add("classes");declaration(node,"class")
            for decorator in node.decorator_list:visit_decorator(decorator,scope)
            for base in node.bases:visit(base,scope,True)
            for item in node.keywords:visit(item,scope)
            child=Scope(scope,"class")
            for parameter in getattr(node,"type_params",[]):visit_type_parameter(parameter,child)
            for statement in node.body:collect(statement,child)
            for statement in node.body:visit(statement,child)
            return
        if isinstance(node,ast.Lambda):
            child=Scope(scope,"function")
            args=[*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs]
            args += [arg for arg in (node.args.vararg,node.args.kwarg) if arg]
            for arg in args:child.names[arg.arg]="parameter";mark_name(arg,"parameter",("declaration",))
            for default in [*node.args.defaults,*node.args.kw_defaults]:
                if default:visit(default,scope)
            visit(node.body,child);return
        if isinstance(node,(ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp)):
            features.add("comprehensions");child=Scope(scope,"function")
            for index,generator in enumerate(node.generators):
                visit(generator.iter,scope if index==0 else child);collect(generator.target,child);visit(generator.target,child)
                for condition in generator.ifs:visit(condition,child)
            if isinstance(node,ast.DictComp):visit(node.key,child);visit(node.value,child)
            else:visit(node.elt,child)
            return
        if isinstance(node,ast.Call):
            visit(node.func,scope,annotation)
            if isinstance(node.func,ast.Name):
                role,mods=name_role(node.func.id,scope,annotation,True);mark(*node_range(node.func),role,mods)
            elif isinstance(node.func,ast.Attribute) and not annotation:
                a,b,_=next((entry for entry in reversed(within(node.func)) if entry[2].type==token.NAME))
                mark(a,b,"method")
            for arg in node.args:visit(arg,scope,annotation)
            for item in node.keywords:visit(item,scope,annotation)
            return
        if isinstance(node,ast.keyword):
            if node.arg:
                a,b,item=next(entry for entry in within(node) if entry[2].type==token.NAME)
                mark(a,b,"parameter")
            visit(node.value,scope,annotation);return
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            features.add("imports")
            for a,b,item in within(node):
                if item.type==token.NAME and not keyword.iskeyword(item.string):
                    role="namespace" if isinstance(node,ast.Import) else "variable"
                    if isinstance(node,ast.ImportFrom):
                        import_at=next(lo for lo,_,t in within(node) if t.string=="import")
                        if a < import_at:role="namespace"
                    mark(a,b,role)
            return
        if isinstance(node,ast.AnnAssign):
            visit(node.target,scope);visit(node.annotation,scope,True);features.add("annotations")
            if node.value:visit(node.value,scope)
            return
        if isinstance(node,getattr(ast,"TypeAlias",())):
            features.add("type-parameters")
            for a,b,item in within(node):
                if item.string=="type":mark(a,b,"keyword");break
            mark(*node_range(node.name),"type",("declaration",))
            child=Scope(scope,"function")
            for parameter in getattr(node,"type_params",[]):visit_type_parameter(parameter,child)
            visit(node.value,child,True);return
        if isinstance(node,ast.Match):
            features.add("pattern-matching")
            for a,b,item in within(node):
                if item.string=="match":mark(a,b,"keyword");break
            visit(node.subject,scope)
            for case in node.cases:
                at=node_range(case.pattern)[0]
                prior=[(a,b) for a,b,t in located[:bisect_left(starts,at)] if t.type==token.NAME and t.string=="case"]
                if not prior:raise ValueError("Missing case soft keyword")
                mark(*prior[-1],"keyword");visit(case.pattern,scope)
                if case.guard:visit(case.guard,scope)
                for statement in case.body:visit(statement,scope)
            return
        if isinstance(node,(ast.MatchAs,ast.MatchStar)):
            if getattr(node,"pattern",None):visit(node.pattern,scope)
            if node.name:mark_name(node,"variable",("declaration",))
            elif isinstance(node,ast.MatchAs) and not node.pattern:mark(*node_range(node),"keyword")
            return
        if isinstance(node,ast.MatchMapping):
            for key in node.keys:visit(key,scope)
            for pattern in node.patterns:visit(pattern,scope)
            if node.rest:
                a,b,_=next(entry for entry in reversed(within(node)) if entry[2].type==token.NAME and normalized(entry[2].string)==node.rest)
                mark(a,b,"variable",("declaration",))
            return
        for child in ast.iter_child_nodes(node):visit(child,scope,annotation)

    def visit_type_parameter(node,scope):
        scope.names[node.name]="type";mark_name(node,"type",("declaration",));features.add("type-parameters")
        for child in ast.iter_child_nodes(node):visit(child,scope,True)

    def visit_decorator(node,scope):
        features.add("decorators");visit(node,scope)
        target=node.func if isinstance(node,ast.Call) else node
        candidates=[(a,b) for a,b,t in within(target) if t.type==token.NAME]
        if candidates:mark(*candidates[-1],"decorator")
        at=node_range(node)[0]
        prior=[a for a,_,t in located[:bisect_left(starts,at)] if t.string=="@"]
        if prior:decorator_ats.add(prior[-1])

    scope=Scope()
    for statement in tree.body:collect(statement,scope)
    for statement in tree.body:visit(statement,scope)
    output=[]
    format_by_start=dict(formats)
    covered_until=-1
    for a,b,item in located:
        if a < covered_until:continue
        if a in format_by_start:
            b=format_by_start[a];role,mods="string",();covered_until=b
        elif item.type==token.COMMENT:role,mods="comment",()
        elif item.type==token.STRING:role,mods="string",()
        elif item.type==token.NUMBER:role,mods="number",()
        elif item.type==token.NAME:
            role,mods=("keyword",()) if keyword.iskeyword(item.string) else roles.get((a,b),("variable",()))
        elif item.type==token.OP:
            role,mods=("punctuation" if item.string in {"(",")","[","]","{","}",",",":",".",";"} or a in decorator_ats else "operator"),()
        elif item.type==token.ERRORTOKEN and not item.string.strip():continue
        else:raise ValueError("Unsupported lexical token: "+token.tok_name[item.type])
        if b<=a:continue
        if role=="string" and len(source[a:b].encode())>512:features.add("long-strings")
        output.append({"start":units[a],"end":units[b],"tokenType":role,**({"modifiers":list(mods)} if mods else {})})
    # Tokenize omits explicit physical-line joins. Recognize only this compiler-
    # validated punctuation in uncovered source, never arbitrary guessed tokens.
    unit_to_char={unit:index for index,unit in enumerate(units)}
    char_spans=[(unit_to_char[s['start']],unit_to_char[s['end']]) for s in output]
    previous=0
    for a,b in [*char_spans,(len(source),len(source))]:
        for index in range(previous,a):
            if source[index].isspace():continue
            if source[index]=="\\" and (source.startswith("\n",index+1) or source.startswith("\r\n",index+1)):
                output.append({"start":units[index],"end":units[index+1],"tokenType":"punctuation"});features.add("line-continuations")
            else:raise ValueError("Uncovered Python source at "+str(index))
        previous=b
    output.sort(key=lambda span:span['start'])
    if "\r\n" in source:features.add("crlf")
    if any(ord(c)>127 for c in source):features.add("unicode")
    return {"offsetEncoding":"utf-16","spans":output,"features":sorted(features)}


def main():
    import json
    for line in sys.stdin:
        if not line.strip():continue
        request_id=None
        try:
            request=json.loads(line);request_id=request.get('id')
            result=label(source=request['source'],document_kind=request.get('documentKind','python'),profile=request.get('profile','python3'))
            response={'id':request_id,'result':result}
        except Exception as error:response={'id':request_id,'error':{'message':str(error)}}
        print(json.dumps(response,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
