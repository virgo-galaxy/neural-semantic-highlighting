public record User(string Name, int Score)
{
    public bool IsActive => Score > 0;
}

public readonly record struct Position(double X, double Y);

public static class UserDisplay
{
    public static string Describe(User user) => user switch
    {
        { Score: >= 100, Name: var name } => $"Expert: {name}",
        { Score: > 0 } => "Active",
        _ => "Waiting"
    };
}
