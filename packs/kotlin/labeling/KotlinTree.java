// Official parse-only PSI/lexer bridge. Never analyzes, resolves, compiles or runs input.
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.lang.reflect.Method;
import java.util.*;
import org.jetbrains.kotlin.com.intellij.openapi.Disposable;
import org.jetbrains.kotlin.com.intellij.openapi.util.Disposer;
import org.jetbrains.kotlin.com.intellij.psi.*;
import org.jetbrains.kotlin.com.intellij.lang.ASTNode;
import org.jetbrains.kotlin.com.intellij.psi.tree.IElementType;
import org.jetbrains.kotlin.cli.jvm.compiler.*;
import org.jetbrains.kotlin.config.CompilerConfiguration;
import org.jetbrains.kotlin.lexer.*;
import org.jetbrains.kotlin.psi.*;

public final class KotlinTree {
    static final Map<String,String> FIELDS = new LinkedHashMap<>();
    static final Map<Class<?>,Map<String,Method>> METHODS = new HashMap<>();
    static {
        String[][] names = {{"getNameIdentifier","name"},{"getReferencedNameElement","name"},
            {"getReferenceExpression","reference"},{"getTypeReference","type"},
            {"getReceiverTypeReference","receiverType"},{"getBodyExpression","body"},
            {"getInitializer","initializer"},{"getCalleeExpression","function"},
            {"getValueArgumentList","arguments"},{"getArgumentExpression","expression"},
            {"getArgumentName","label"},{"getReceiverExpression","receiver"},
            {"getSelectorExpression","selector"},{"getOperationReference","operation"},
            {"getLoopParameter","loopParameter"},{"getLoopRange","sequence"},
            {"getSubjectVariable","subject"},{"getDestructuringDeclaration","pattern"},
            {"getDelegateExpression","delegate"},{"getConstructorKeyword","name"},
            {"getNamePlaceholder","name"},{"getTargetLabel","label"}};
        for (String[] pair : names) FIELDS.put(pair[0],pair[1]);
    }
    static String json(String text) {
        StringBuilder s = new StringBuilder("\"");
        for (int i=0;i<text.length();i++) {
            char c=text.charAt(i);
            switch (c) {
                case '"': s.append("\\\"");break;
                case '\\': s.append("\\\\");break;
                case '\n': s.append("\\n");break;
                case '\r': s.append("\\r");break;
                case '\t': s.append("\\t");break;
                default: if (c<32) s.append(String.format("\\u%04x",(int)c)); else s.append(c);
            }
        }
        return s.append('"').toString();
    }
    static Map<PsiElement,String> fields(PsiElement node) throws Exception {
        Map<String,Method> methods=METHODS.computeIfAbsent(node.getClass(), cls -> {
            Map<String,Method> result=new LinkedHashMap<>();
            for (String name : FIELDS.keySet()) {
                try { Method method=cls.getMethod(name); if (PsiElement.class.isAssignableFrom(method.getReturnType()) || ASTNode.class.isAssignableFrom(method.getReturnType())) result.put(name,method); }
                catch (NoSuchMethodException ignored) {}
            }
            return result;
        });
        Map<PsiElement,String> result=new IdentityHashMap<>();
        for (var entry:methods.entrySet()) {
            Object value=entry.getValue().invoke(node);
            if (value instanceof ASTNode ast) value=ast.getPsi();
            if (value instanceof PsiElement child && child.getParent()==node) result.put(child,FIELDS.get(entry.getKey()));
        }
        return result;
    }
    static void errors(PsiElement node, int[] offsets) {
        if (node instanceof PsiErrorElement error) throw new IllegalArgumentException(error.getErrorDescription()+" at "+offsets[error.getTextRange().getStartOffset()]);
        for (PsiElement child=node.getFirstChild();child!=null;child=child.getNextSibling()) errors(child,offsets);
    }
    static void tree(PsiElement node,String field,StringBuilder s,Set<Integer> keywords,int[] offsets) throws Exception {
        int start=offsets[node.getTextRange().getStartOffset()],end=offsets[node.getTextRange().getEndOffset()];
        s.append("{\"kind\":").append(json(node.getClass().getSimpleName())).append(",\"start\":").append(start).append(",\"end\":").append(end);
        if (field!=null) s.append(",\"field\":").append(json(field));
        if (node instanceof KtClass c && c.isEnum()) s.append(",\"enum\":true");
        if (node instanceof KtParameter p && p.hasValOrVar()) s.append(",\"propertyParameter\":true");
        if (node instanceof KtProperty p && p.hasModifier(KtTokens.CONST_KEYWORD)) s.append(",\"constant\":true");
        if (node instanceof KtFunctionLiteral f) s.append(",\"explicitParameters\":").append(f.hasParameterSpecification());
        if (node instanceof KtPropertyAccessor a) s.append(",\"accessor\":").append(json(a.isGetter()?"get":"set"));
        if (node instanceof KtTypeReference) s.append(",\"isType\":true");
        if (node.getNode()!=null) {
            IElementType type=node.getNode().getElementType();
            s.append(",\"syntaxType\":").append(json(type.toString()));
            if (KtTokens.KEYWORDS.contains(type)||KtTokens.SOFT_KEYWORDS.contains(type)) keywords.add(start);
        }
        Map<PsiElement,String> names=fields(node);s.append(",\"children\":[");boolean first=true;
        for (PsiElement child=node.getFirstChild();child!=null;child=child.getNextSibling()) {
            if (!first) s.append(',');first=false;tree(child,names.get(child),s,keywords,offsets);
        }
        s.append("]}");
    }
    static String parse(KtPsiFactory factory,String original,boolean script) throws Exception {
        StringBuilder normalized=new StringBuilder();List<Integer> positions=new ArrayList<>();
        int cursor=original.startsWith("\uFEFF")?1:0;positions.add(cursor);
        while (cursor<original.length()) {
            char c=original.charAt(cursor++);
            if (c=='\r') { if (cursor<original.length() && original.charAt(cursor)=='\n') cursor++;c='\n'; }
            normalized.append(c);positions.add(cursor);
        }
        String source=normalized.toString();int[] offsets=positions.stream().mapToInt(Integer::intValue).toArray();
        KtFile file=factory.createFile(script?"source.kts":"source.kt",source);
        if (!file.getText().equals(source)) throw new IllegalArgumentException("PSI changed original source text");
        errors(file,offsets);Set<Integer> keywords=new HashSet<>();StringBuilder s=new StringBuilder("{\"tree\":");
        tree(file,null,s,keywords,offsets);s.append(",\"tokens\":[");boolean first=true;
        KotlinLexer lexer=new KotlinLexer();lexer.start(source);
        while (lexer.getTokenType()!=null) {
            IElementType type=lexer.getTokenType();int a=offsets[lexer.getTokenStart()],b=offsets[lexer.getTokenEnd()];
            if (!first) s.append(',');first=false;
            s.append("{\"kind\":").append(json(type.toString())).append(",\"start\":").append(a).append(",\"end\":").append(b)
             .append(",\"keyword\":").append(keywords.contains(a)||KtTokens.KEYWORDS.contains(type))
             .append(",\"comment\":").append(KtTokens.COMMENTS.contains(type))
             .append(",\"operator\":").append(KtTokens.OPERATIONS.contains(type)).append('}');
            lexer.advance();
        }
        return s.append("]}").toString();
    }
    public static void main(String[] args) throws Exception {
        Disposable disposable=Disposer.newDisposable("nsh-kotlin-parse-only");
        try {
            CompilerConfiguration configuration=new CompilerConfiguration();
            org.jetbrains.kotlin.cli.FrontendConfigurationKeysKt.setExtensionsStorage(configuration,new org.jetbrains.kotlin.compiler.plugin.CompilerPluginRegistrar.ExtensionStorage());
            KotlinCoreEnvironment env=KotlinCoreEnvironment.createForProduction(disposable,configuration,EnvironmentConfigFiles.JVM_CONFIG_FILES);
            KtPsiFactory factory=new KtPsiFactory(env.getProject(),false);
            BufferedReader input=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.UTF_8));
            PrintWriter output=new PrintWriter(new OutputStreamWriter(System.out,StandardCharsets.UTF_8),true);
            for (String line;(line=input.readLine())!=null;) {
                try {
                    int tab=line.indexOf('\t');if (tab<1) throw new IllegalArgumentException("Missing profile");
                    byte[] raw=Base64.getDecoder().decode(line.substring(tab+1));
                    if (raw.length>2_000_000) throw new IllegalArgumentException("Source too large");
                    String source=new String(raw,StandardCharsets.UTF_8);boolean script=line.substring(0,tab).equals("script");
                    output.println(parse(factory,source,script));
                } catch (Exception error) { output.println("{\"error\":"+json(error.getClass().getSimpleName()+": "+String.valueOf(error.getMessage()))+"}"); }
            }
        } finally { Disposer.dispose(disposable); }
    }
}
