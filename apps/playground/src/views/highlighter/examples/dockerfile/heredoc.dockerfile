# syntax=docker/dockerfile:1
FROM alpine:3
RUN <<SETUP
set -eu
mkdir -p /etc/preview

printf '%s\n' "Setup complete"
SETUP

COPY <<'SETTINGS' /etc/preview/settings.conf
name=source-preview

# FROM and RUN below are file contents.
command=RUN unchanged
SETTINGS

CMD ["cat", "/etc/preview/settings.conf"]
