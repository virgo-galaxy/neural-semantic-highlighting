$offset = 10;
$values = [1, 2, 3];
$mapped = array_map(fn(int $value): int => $value + $offset, $values);

$sum = 0;
array_walk($mapped, function (int $value) use (&$sum): void {
    $sum += $value;
});
