import java.util.List;
import java.util.concurrent.CompletableFuture;

final class AsyncTasks {
    CompletableFuture<List<String>> load(List<String> paths) {
        return CompletableFuture.supplyAsync(() -> paths.stream()
            .filter(path -> !path.isBlank())
            .map(String::strip)
            .sorted()
            .toList());
    }
}
