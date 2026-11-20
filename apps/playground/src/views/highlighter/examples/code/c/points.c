typedef struct Point {
    double x;
    double y;
} Point;

static Point translate(Point value, double dx, double dy) {
    return (Point){ .x = value.x + dx, .y = value.y + dy };
}

double length_squared(const Point *point) {
    return point->x * point->x + point->y * point->y;
}
