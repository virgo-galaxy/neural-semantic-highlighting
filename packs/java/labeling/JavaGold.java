// Offline-only JDK 22 teacher. Source is parsed, never analyzed or executed.
import com.sun.source.tree.*;
import com.sun.source.util.*;
import com.sun.tools.javac.parser.JavaTokenizer;
import com.sun.tools.javac.parser.ScannerFactory;
import com.sun.tools.javac.parser.Tokens;
import com.sun.tools.javac.util.Context;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.*;
import javax.tools.*;

public final class JavaGold {
    record Lex(int start, int end, String name, String kind, String base) {}
    record Role(String type, boolean declaration) {}
    static final class Tokenizer extends JavaTokenizer {
        final List<Lex> comments;
        Tokenizer(ScannerFactory factory, String source, List<Lex> comments) {
            super(factory, source.toCharArray(), source.length());
            this.comments = comments;
        }
        @Override protected Tokens.Comment processComment(int start, int end, Tokens.Comment.CommentStyle style) {
            comments.add(new Lex(start, end, "", "COMMENT", "comment"));
            return super.processComment(start, end, style);
        }
    }
    static final class Scanner extends com.sun.tools.javac.parser.Scanner {
        Scanner(ScannerFactory factory, Tokenizer tokenizer) { super(factory, tokenizer); }
    }
    static final Set<String> PUNCTUATION = Set.of("LPAREN", "RPAREN", "LBRACE", "RBRACE",
        "LBRACKET", "RBRACKET", "SEMI", "COMMA", "DOT", "ELLIPSIS", "MONKEYS_AT");

    final String source;
    final List<Lex> tokens = new ArrayList<>();
    final Map<Integer, Role> roles = new HashMap<>();
    final SortedSet<String> features = new TreeSet<>();
    final Deque<Map<String, String>> scopes = new ArrayDeque<>();
    final Deque<String> classes = new ArrayDeque<>();
    CompilationUnitTree unit;
    SourcePositions positions;

    JavaGold(String source) { this.source = source; }
    int start(Tree tree) { return tree == null ? -1 : (int) positions.getStartPosition(unit, tree); }
    int end(Tree tree) { return tree == null ? -1 : (int) positions.getEndPosition(unit, tree); }
    List<Lex> within(int a, int b) {
        return tokens.stream().filter(t -> t.start >= a && t.end <= b && t.base.equals("variable")).toList();
    }
    void mark(Lex token, String role, boolean declaration) {
        roles.put(token.start, new Role(role, declaration));
    }
    void name(Tree tree, String wanted, String role, boolean declaration, int limit) {
        List<Lex> candidates = within(start(tree), limit < 0 ? end(tree) : limit).stream()
            .filter(t -> t.name.equals(wanted)).toList();
        if (!candidates.isEmpty()) mark(candidates.getLast(), role, declaration);
        else throw new IllegalArgumentException("Missing original " + role + " name: " + wanted);
    }
    void keyword(Tree tree, String word) { keyword(start(tree), end(tree), word); }
    void keyword(int a, int b, String word) {
        for (Lex t : within(a, b)) if (t.name.equals(word)) mark(t, "keyword", false);
    }
    String resolve(String name) {
        for (var scope : scopes) if (scope.containsKey(name)) return scope.get(name);
        return "variable";
    }
    void bind(String name, String role) { scopes.peek().put(name, role); }
    void type(Tree tree) {
        if (tree == null) return;
        new TreeScanner<Void, Void>() {
            @Override public Void visitIdentifier(IdentifierTree n, Void p) {
                name(n, n.getName().toString(), n.getName().contentEquals("var") ? "keyword" : "type", false, -1);
                return null;
            }
            @Override public Void visitMemberSelect(MemberSelectTree n, Void p) {
                scan(n.getExpression(), p); name(n, n.getIdentifier().toString(), "type", false, -1); return null;
            }
            @Override public Void visitAnnotation(AnnotationTree n, Void p) { return null; }
        }.scan(tree, null);
    }
    void namespace(Tree tree) {
        if (tree != null) for (Lex t : within(start(tree), end(tree))) mark(t, "namespace", false);
    }

    final class Visitor extends TreePathScanner<Void, Void> {
        @Override public Void visitCompilationUnit(CompilationUnitTree n, Void p) {
            scopes.push(new HashMap<>());
            for (Tree tree : n.getTypeDecls()) if (tree instanceof ClassTree c)
                bind(c.getSimpleName().toString(), "type");
            super.visitCompilationUnit(n, p); namespace(n.getPackageName()); scopes.pop(); return null;
        }
        @Override public Void visitImport(ImportTree n, Void p) { namespace(n.getQualifiedIdentifier()); features.add("imports"); return null; }
        @Override public Void visitClass(ClassTree n, Void p) {
            String kind = n.getKind().name();
            String role = switch (kind) { case "INTERFACE", "ANNOTATION_TYPE" -> "interface"; case "ENUM" -> "enum"; default -> "class"; };
            int headerEnd = end(n);
            for (Tree member : n.getMembers()) if (start(member) >= 0) headerEnd = Math.min(headerEnd, start(member));
            if (!n.getSimpleName().isEmpty()) {
                // Neither annotations nor recursive generic bounds are the declaration.
                boolean afterKeyword = false, found = false;
                for (Lex t : tokens) {
                    if (t.start < start(n) || t.end > headerEnd) continue;
                    if (afterKeyword && t.name.equals(n.getSimpleName().toString())) {
                        mark(t, role, true); found = true; break;
                    }
                    if (Set.of("CLASS", "INTERFACE", "ENUM").contains(t.kind) || kind.equals("RECORD") && t.name.equals("record")) afterKeyword = true;
                }
                if (!found) throw new IllegalArgumentException("Missing original type declaration");
                bind(n.getSimpleName().toString(), "type");
            }
            if (kind.equals("RECORD")) { keyword(start(n), headerEnd, "record"); features.add("records"); }
            if (kind.equals("ENUM")) features.add("enums");
            keyword(start(n), headerEnd, "permits");
            classes.push(n.getSimpleName().toString()); scopes.push(new HashMap<>());
            for (Tree member : n.getMembers()) {
                if (member instanceof VariableTree v) bind(v.getName().toString(), enumConstant(v) ? "enum-member" : "property");
                if (member instanceof MethodTree m) bind(m.getName().toString(), "method");
                if (member instanceof ClassTree c) bind(c.getSimpleName().toString(), "type");
            }
            super.visitClass(n, p);
            type(n.getExtendsClause()); for (Tree t : n.getImplementsClause()) type(t);
            for (Tree t : n.getPermitsClause()) type(t);
            scopes.pop(); classes.pop(); return null;
        }
        boolean enumConstant(VariableTree n) {
            Tree parent = getCurrentPath().getLeaf();
            if (parent == n) parent = getCurrentPath().getParentPath().getLeaf();
            return parent.getKind() == Tree.Kind.ENUM && n.getInitializer() instanceof NewClassTree
                && (n.getType() == null || start(n.getType()) < 0 || start(n.getType()) == start(n));
        }
        @Override public Void visitModifiers(ModifiersTree n, Void p) {
            if (n.getFlags().contains(javax.lang.model.element.Modifier.SEALED) || n.getFlags().contains(javax.lang.model.element.Modifier.NON_SEALED)) {
                keyword(n, "sealed"); keyword(n, "non"); features.add("sealed");
            }
            return super.visitModifiers(n, p);
        }
        @Override public Void visitMethod(MethodTree n, Void p) {
            boolean constructor = n.getReturnType() == null;
            String wanted = constructor ? classes.peek() : n.getName().toString();
            int limit = n.getBody() == null ? end(n) : start(n.getBody());
            for (VariableTree parameter : n.getParameters()) if (start(parameter) >= start(n)) limit = Math.min(limit, start(parameter));
            name(n, wanted, constructor ? "constructor" : "method", true, limit);
            scopes.push(new HashMap<>());
            scan(n.getModifiers(), p); scan(n.getTypeParameters(), p); scan(n.getReturnType(), p);
            scan(n.getReceiverParameter(), p);
            for (VariableTree parameter : n.getParameters()) {
                if (start(parameter) >= start(n)) scan(parameter, p);
                else bind(parameter.getName().toString(), "parameter");
            }
            scan(n.getThrows(), p); scan(n.getBody(), p); scan(n.getDefaultValue(), p);
            type(n.getReturnType());
            for (Tree t : n.getThrows()) type(t);
            scopes.pop(); features.add("methods"); return null;
        }
        @Override public Void visitVariable(VariableTree n, Void p) {
            Tree parent = getCurrentPath().getParentPath().getLeaf();
            String role = parent instanceof ClassTree ? (enumConstant(n) ? "enum-member" : "property")
                : (parent instanceof MethodTree || parent instanceof LambdaExpressionTree || parent instanceof CatchTree) ? "parameter" : "variable";
            int limit = n.getInitializer() == null ? end(n) : start(n.getInitializer());
            // javac synthesizes the type of enum constants with non-source ranges.
            if (role.equals("enum-member")) limit = end(n);
            name(n, n.getName().toString(), role, true, limit);
            if (n.getType() == null) {
                List<Lex> header = within(start(n), limit);
                for (int i = 1; i < header.size(); i++) if (header.get(i).name.equals(n.getName().toString()) && header.get(i - 1).name.equals("var")) mark(header.get(i - 1), "keyword", false);
            }
            bind(n.getName().toString(), role);
            if (role.equals("enum-member")) {
                scan(n.getModifiers(), p);
                NewClassTree initializer = (NewClassTree) n.getInitializer();
                scan(initializer.getArguments(), p); scan(initializer.getClassBody(), p);
            } else { super.visitVariable(n, p); type(n.getType()); }
            return null;
        }
        @Override public Void visitBlock(BlockTree n, Void p) {
            scopes.push(new HashMap<>()); super.visitBlock(n, p); scopes.pop(); return null;
        }
        @Override public Void visitLambdaExpression(LambdaExpressionTree n, Void p) {
            scopes.push(new HashMap<>()); super.visitLambdaExpression(n, p); scopes.pop(); features.add("lambdas"); return null;
        }
        @Override public Void visitForLoop(ForLoopTree n, Void p) {
            scopes.push(new HashMap<>()); super.visitForLoop(n, p); scopes.pop(); return null;
        }
        @Override public Void visitEnhancedForLoop(EnhancedForLoopTree n, Void p) {
            scopes.push(new HashMap<>()); super.visitEnhancedForLoop(n, p); scopes.pop(); return null;
        }
        @Override public Void visitCatch(CatchTree n, Void p) {
            scopes.push(new HashMap<>()); super.visitCatch(n, p); scopes.pop(); return null;
        }
        @Override public Void visitIdentifier(IdentifierTree n, Void p) {
            // this/super/primitive keywords have no variable-base scanner token.
            for (Lex t : within(start(n), end(n))) mark(t, resolve(t.name), false);
            return null;
        }
        @Override public Void visitMemberSelect(MemberSelectTree n, Void p) {
            scan(n.getExpression(), p);
            for (Lex t : within(start(n), end(n))) if (t.start >= end(n.getExpression())) mark(t, "property", false);
            return null;
        }
        @Override public Void visitMethodInvocation(MethodInvocationTree n, Void p) {
            super.visitMethodInvocation(n, p);
            Tree selected = n.getMethodSelect();
            String wanted = selected instanceof IdentifierTree i ? i.getName().toString()
                : selected instanceof MemberSelectTree m ? m.getIdentifier().toString() : "";
            if (!wanted.equals("this") && !wanted.equals("super")) name(selected, wanted, "method", false, -1);
            for (Tree t : n.getTypeArguments()) type(t);
            return null;
        }
        @Override public Void visitMemberReference(MemberReferenceTree n, Void p) {
            super.visitMemberReference(n, p);
            if (n.getMode() == MemberReferenceTree.ReferenceMode.NEW) type(n.getQualifierExpression());
            else name(n, n.getName().toString(), "method", false, -1);
            features.add("method-references"); return null;
        }
        @Override public Void visitNewClass(NewClassTree n, Void p) {
            super.visitNewClass(n, p); type(n.getIdentifier());
            Tree target = n.getIdentifier();
            if (target instanceof ParameterizedTypeTree t) target = t.getType();
            String wanted = target instanceof IdentifierTree i ? i.getName().toString()
                : target instanceof MemberSelectTree m ? m.getIdentifier().toString() : "";
            if (!wanted.isEmpty() && start(target) >= 0) name(target, wanted, "constructor", false, -1);
            return null;
        }
        @Override public Void visitNewArray(NewArrayTree n, Void p) { super.visitNewArray(n, p); type(n.getType()); return null; }
        @Override public Void visitParameterizedType(ParameterizedTypeTree n, Void p) {
            super.visitParameterizedType(n, p); type(n); features.add("generics"); return null;
        }
        @Override public Void visitTypeParameter(TypeParameterTree n, Void p) {
            super.visitTypeParameter(n, p); type(n);
            Lex original = within(start(n), end(n)).stream().filter(t -> t.name.equals(n.getName().toString())).findFirst().orElseThrow();
            mark(original, "type", true);
            bind(n.getName().toString(), "type"); features.add("generics"); return null;
        }
        @Override public Void visitAnnotation(AnnotationTree n, Void p) {
            super.visitAnnotation(n, p);
            for (Lex t : within(start(n.getAnnotationType()), end(n.getAnnotationType()))) mark(t, "decorator", false);
            features.add("annotations"); return null;
        }
        @Override public Void visitTypeCast(TypeCastTree n, Void p) { super.visitTypeCast(n, p); type(n.getType()); return null; }
        @Override public Void visitInstanceOf(InstanceOfTree n, Void p) {
            super.visitInstanceOf(n, p); type(n.getType()); if (n.getPattern() != null) features.add("pattern-matching"); return null;
        }
        @Override public Void visitBindingPattern(BindingPatternTree n, Void p) {
            features.add("pattern-matching"); return super.visitBindingPattern(n, p);
        }
        @Override public Void visitDeconstructionPattern(DeconstructionPatternTree n, Void p) {
            super.visitDeconstructionPattern(n, p); type(n.getDeconstructor()); features.add("pattern-matching"); return null;
        }
        @Override public Void visitCase(CaseTree n, Void p) {
            super.visitCase(n, p);
            if (n.getGuard() != null) keyword(start(n), start(n.getGuard()), "when");
            if (n.getCaseKind() == CaseTree.CaseKind.RULE) features.add("switch-expressions"); return null;
        }
        @Override public Void visitYield(YieldTree n, Void p) {
            super.visitYield(n, p); keyword(start(n), start(n.getValue()), "yield"); features.add("switch-expressions"); return null;
        }
        @Override public Void visitModule(ModuleTree n, Void p) {
            super.visitModule(n, p); namespace(n.getName());
            int limit = n.getDirectives().isEmpty() ? end(n) : start(n.getDirectives().getFirst());
            if (n.getModuleType() == ModuleTree.ModuleKind.OPEN) keyword(0, limit, "open");
            keyword(start(n), limit, "module"); features.add("modules"); return null;
        }
        @Override public Void visitRequires(RequiresTree n, Void p) {
            namespace(n.getModuleName()); keyword(start(n), start(n.getModuleName()), "requires");
            keyword(start(n), start(n.getModuleName()), "transitive"); return null;
        }
        @Override public Void visitExports(ExportsTree n, Void p) {
            namespace(n.getPackageName()); if (n.getModuleNames() != null) n.getModuleNames().forEach(JavaGold.this::namespace);
            keyword(start(n), start(n.getPackageName()), "exports");
            if (n.getModuleNames() != null && !n.getModuleNames().isEmpty()) keyword(end(n.getPackageName()), start(n.getModuleNames().getFirst()), "to"); return null;
        }
        @Override public Void visitOpens(OpensTree n, Void p) {
            namespace(n.getPackageName()); if (n.getModuleNames() != null) n.getModuleNames().forEach(JavaGold.this::namespace);
            keyword(start(n), start(n.getPackageName()), "opens");
            if (n.getModuleNames() != null && !n.getModuleNames().isEmpty()) keyword(end(n.getPackageName()), start(n.getModuleNames().getFirst()), "to"); return null;
        }
        @Override public Void visitUses(UsesTree n, Void p) {
            type(n.getServiceName()); keyword(start(n), start(n.getServiceName()), "uses"); return null;
        }
        @Override public Void visitProvides(ProvidesTree n, Void p) {
            type(n.getServiceName()); n.getImplementationNames().forEach(JavaGold.this::type);
            keyword(start(n), start(n.getServiceName()), "provides");
            if (!n.getImplementationNames().isEmpty()) keyword(end(n.getServiceName()), start(n.getImplementationNames().getFirst()), "with"); return null;
        }
    }

    String run(JavaCompiler compiler, StandardJavaFileManager manager) throws IOException {
        var diagnostics = new DiagnosticCollector<JavaFileObject>();
        var file = new SimpleJavaFileObject(URI.create("string:///module-info.java"), JavaFileObject.Kind.SOURCE) {
            @Override public CharSequence getCharContent(boolean ignore) { return source; }
        };
        JavacTask task = (JavacTask) compiler.getTask(null, manager, diagnostics,
            List.of("-proc:none", "--source", "22", "-Xlint:none"), null, List.of(file));
        unit = task.parse().iterator().next();
        for (var diagnostic : diagnostics.getDiagnostics()) if (diagnostic.getKind() == Diagnostic.Kind.ERROR)
            throw new IllegalArgumentException("Parse error at " + diagnostic.getPosition() + ": " + diagnostic.getCode());
        positions = Trees.instance(task).getSourcePositions();
        Context context = new Context();
        ScannerFactory factory = ScannerFactory.instance(context);
        // Javac does not emit a LINE comment callback at physical EOF.
        // The sentinel terminator is outside every returned original-source range.
        Scanner scanner = new Scanner(factory, new Tokenizer(factory, source + "\n", tokens));
        while (true) {
            scanner.nextToken(); Tokens.Token token = scanner.token();
            String kind = token.kind.name();
            if (kind.equals("EOF")) break;
            if (kind.equals("ERROR") || kind.equals("STRINGFRAGMENT")) throw new IllegalArgumentException("Unsupported lexical token");
            String role = kind.equals("IDENTIFIER") ? "variable"
                : kind.equals("CHARLITERAL") || kind.equals("STRINGLITERAL") ? "string"
                : kind.endsWith("LITERAL") ? "number" : PUNCTUATION.contains(kind) ? "punctuation"
                : token.kind.name != null && Character.isJavaIdentifierStart(token.kind.name.charAt(0)) ? "keyword" : "operator";
            String name = kind.equals("IDENTIFIER") ? token.name().toString() : "";
            tokens.add(new Lex(token.pos, token.endPos, name, kind, role));
            if (kind.equals("STRINGLITERAL") && source.startsWith("\"\"\"", token.pos)) features.add("text-blocks");
        }
        tokens.sort(Comparator.comparingInt(Lex::start));
        new Visitor().scan(unit, null);
        StringBuilder json = new StringBuilder("{\"spans\":[");
        int previous = 0; boolean comma = false;
        for (Lex token : tokens) {
            if (token.start < previous || token.end <= token.start || token.end > source.length()) throw new IllegalArgumentException("Invalid original range");
            if (comma) json.append(','); comma = true;
            Role role = roles.getOrDefault(token.start, new Role(token.base, false));
            json.append("{\"start\":").append(token.start).append(",\"end\":").append(token.end)
                .append(",\"tokenType\":\"").append(role.type).append('"');
            if (role.declaration) json.append(",\"modifiers\":[\"declaration\"]");
            json.append('}'); previous = token.end;
        }
        json.append("],\"features\":["); comma = false;
        for (String feature : features) { if (comma) json.append(','); comma = true; json.append('"').append(feature).append('"'); }
        return json.append("]}").toString();
    }

    public static void main(String[] args) throws IOException {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        try (var manager = compiler.getStandardFileManager(null, Locale.ROOT, StandardCharsets.UTF_8);
             var input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.US_ASCII))) {
            for (String line; (line = input.readLine()) != null;) {
                try {
                    String source = new String(Base64.getDecoder().decode(line), StandardCharsets.UTF_8);
                    System.out.println("OK\t" + new JavaGold(source).run(compiler, manager));
                } catch (RuntimeException error) {
                    String message = error.getClass().getSimpleName() + ": " + error.getMessage();
                    System.out.println("ERROR\t" + Base64.getEncoder().encodeToString(message.getBytes(StandardCharsets.UTF_8)));
                }
                System.out.flush();
            }
        }
    }
}
