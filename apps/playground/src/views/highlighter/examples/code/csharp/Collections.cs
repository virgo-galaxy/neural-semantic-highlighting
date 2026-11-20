using System.Collections.Generic;

public static class Collections
{
    public static int[] Merge(int[] first, int[] second) => [.. first, .. second];

    public static int Head(int[] values)
    {
        if (values is [var first, ..])
            return first;

        return 0;
    }

    public static List<string> Names() => ["Virgo", "星空 🌌"];
}
