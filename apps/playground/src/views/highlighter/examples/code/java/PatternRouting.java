sealed interface Message permits Notice, Progress {}
record Notice(String text) implements Message {}
record Progress(int completed, int total) implements Message {}

final class Router {
    String describe(Message message) {
        return switch (message) {
            case Notice(var text) when !text.isBlank() -> text;
            case Progress(var done, var total) -> "%d / %d".formatted(done, total);
            default -> "Waiting";
        };
    }
}
