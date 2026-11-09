import java.util.Objects;
import java.util.function.Function;

public record Result<T>(T value, String label) {
    public Result {
        label = Objects.requireNonNull(label).strip();
    }

    public <R> Result<R> map(Function<T, R> transform) {
        return new Result<>(transform.apply(value), label);
    }
}
