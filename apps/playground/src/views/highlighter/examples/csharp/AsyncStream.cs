using System.Collections.Generic;
using System.Threading.Tasks;

public static class Streams
{
    public static async IAsyncEnumerable<int> CountAsync(int limit)
    {
        for (var index = 0; index < limit; index++)
        {
            await Task.Delay(10);
            yield return index;
        }
    }
}
