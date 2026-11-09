import java.lang.annotation.ElementType;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@interface Action {
    String value();
}

enum Status { READY, RUNNING, FINISHED }

final class Controller {
    private Status status = Status.READY;

    @Action("refresh")
    public void refresh() {
        status = Status.RUNNING;
    }
}
