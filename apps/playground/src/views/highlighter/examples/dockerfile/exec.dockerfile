FROM alpine:3
RUN ["/bin/sh", "-c", "echo original source"]
COPY ["assets/site config.json", "/etc/preview/config.json"]
VOLUME ["/var/lib/preview", "/var/cache/preview"]
SHELL ["/bin/sh", "-eu", "-c"]
RUN echo ready && test -d /etc
ENTRYPOINT ["/usr/local/bin/preview"]
CMD ["--config", "/etc/preview/config.json"]
