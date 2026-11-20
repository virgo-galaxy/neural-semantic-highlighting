using System.Collections.Generic;

public interface IStore<T> where T : notnull
{
    T Get(string key);
}

public sealed class MemoryStore<T> : IStore<T> where T : notnull
{
    private readonly Dictionary<string, T> entries = new();

    public void Set(string key, T value) => entries[key] = value;
    public T Get(string key) => entries[key];
}
