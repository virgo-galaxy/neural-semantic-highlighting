#nullable enable
using System;

[Flags]
public enum Permission { None = 0, Read = 1, Write = 2 }

public sealed class Options
{
    public required string Name { get; init; }
    public string? Description { get; set; }
    public Permission Access { get; init; } = Permission.Read;

    public string Label() => Description?.Trim() ?? Name;
}
