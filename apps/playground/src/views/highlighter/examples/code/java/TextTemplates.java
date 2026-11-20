final class TextTemplates {
    String render(String title) {
        String template = """
            <article class="code-card">
                <h2>%s</h2>
                <!-- Preserve this as string content. -->
            </article>
            """;
        return template.formatted(title);
    }
}
