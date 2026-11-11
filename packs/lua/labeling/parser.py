"""Small ctypes binding to the pinned offline Lua parser; never used at inference."""
from __future__ import annotations
import atexit
import ctypes as C
from dataclasses import dataclass, field
from functools import lru_cache
import threading

from .tools import LIBRARY, provenance


class TSNode(C.Structure):
    _fields_ = [('context', C.c_uint32 * 4), ('id', C.c_void_p), ('tree', C.c_void_p)]


@dataclass
class Node:
    kind: str
    start: int
    end: int
    named: bool
    children: list = field(default_factory=list)
    fields: dict = field(default_factory=dict)
    parent: object = None
    raw: bytes = b''

    @property
    def text(self): return self.raw[self.start:self.end].decode('utf-8')
    def descendants(self):
        yield self
        for child in self.children: yield from child.descendants()
    def identifiers(self):
        return [n for n in self.descendants() if n.kind in {'identifier'}]


OPAQUE = {'comment', 'hash_bang_line', 'string'}


class Parser:
    def __init__(self):
        provenance()
        self.lib = C.CDLL(str(LIBRARY))
        specs = {
            'tree_sitter_lua': ([], C.c_void_p),
            'ts_parser_new': ([], C.c_void_p), 'ts_parser_delete': ([C.c_void_p], None),
            'ts_parser_set_language': ([C.c_void_p, C.c_void_p], C.c_bool),
            'ts_parser_parse_string': ([C.c_void_p, C.c_void_p, C.c_char_p, C.c_uint32], C.c_void_p),
            'ts_tree_root_node': ([C.c_void_p], TSNode), 'ts_tree_delete': ([C.c_void_p], None),
            'ts_node_type': ([TSNode], C.c_char_p), 'ts_node_start_byte': ([TSNode], C.c_uint32),
            'ts_node_end_byte': ([TSNode], C.c_uint32), 'ts_node_child_count': ([TSNode], C.c_uint32),
            'ts_node_child': ([TSNode, C.c_uint32], TSNode), 'ts_node_is_named': ([TSNode], C.c_bool),
            'ts_node_has_error': ([TSNode], C.c_bool), 'ts_node_is_missing': ([TSNode], C.c_bool),
            'ts_node_field_name_for_child': ([TSNode, C.c_uint32], C.c_char_p),
        }
        for name, (args, result) in specs.items():
            function = getattr(self.lib, name); function.argtypes = args; function.restype = result
        self.parser = self.lib.ts_parser_new()
        if not self.lib.ts_parser_set_language(self.parser, self.lib.tree_sitter_lua()):
            raise ValueError('Pinned Lua parser ABI is incompatible')
        self.lock = threading.Lock()
        atexit.register(self.close)

    def close(self):
        if self.parser: self.lib.ts_parser_delete(self.parser); self.parser = None

    def parse(self, raw):
        with self.lock:
            tree = self.lib.ts_parser_parse_string(self.parser, None, raw, len(raw))
            if not tree: raise ValueError('Offline parser did not produce a tree')
            try:
                root = self.lib.ts_tree_root_node(tree)
                if self.lib.ts_node_has_error(root):
                    raise ValueError('Lua source is outside the pinned grammar or has a syntax error')
                def extract(value, parent=None):
                    if self.lib.ts_node_is_missing(value): raise ValueError('Missing syntax token')
                    kind = self.lib.ts_node_type(value).decode('ascii')
                    node = Node(kind, self.lib.ts_node_start_byte(value), self.lib.ts_node_end_byte(value),
                                self.lib.ts_node_is_named(value), parent=parent, raw=raw)
                    if kind not in OPAQUE:
                        for index in range(self.lib.ts_node_child_count(value)):
                            child = extract(self.lib.ts_node_child(value, index), node)
                            node.children.append(child)
                            name = self.lib.ts_node_field_name_for_child(value, index)
                            if name:
                                child.field_name = name.decode('ascii')
                                node.fields.setdefault(child.field_name, child)
                    return node
                return extract(root)
            finally: self.lib.ts_tree_delete(tree)


@lru_cache(maxsize=1)
def parser(): return Parser()
