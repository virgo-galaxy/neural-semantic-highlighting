using System.Linq;

public record Product(string Name, decimal Price, bool Available);

public static class Catalog
{
    public static object Search(Product[] products)
    {
        var query = from product in products
                    where product.Available && product.Price < 100m
                    orderby product.Name
                    select new { product.Name, product.Price };

        return query.ToArray();
    }
}
