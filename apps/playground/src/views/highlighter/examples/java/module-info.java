module virgo.examples {
    requires java.net.http;
    requires transitive java.logging;

    exports virgo.examples.api;
    opens virgo.examples.internal to framework.core;

    uses virgo.examples.Service;
    provides virgo.examples.Service with virgo.examples.DefaultService;
}
