public static class Templates
{
    public static string Render(string title)
    {
        var card = $$"""
            <article class="code-card">
                <h2>{{title}}</h2>
                <!-- This stays inside the C# string. -->
            </article>
            """;

        var path = @"C:\Projects\Examples";
        return card + $"\nSource: {path}";
    }
}
