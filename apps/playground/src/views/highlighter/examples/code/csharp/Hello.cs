using System;
using System.Collections.Generic;

namespace Virgo.Examples;

public sealed class Greeter(string greeting)
{
    public string Greeting { get; } = greeting;

    public void Welcome(IEnumerable<string> names)
    {
        foreach (var name in names)
        {
            Console.WriteLine($"{Greeting}, {name}!");
        }
    }
}
