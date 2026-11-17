# Defaults remain source; no host environment is read.
ARG BASE_IMAGE=alpine:3
FROM ${BASE_IMAGE}
ARG APP_VERSION=stable
ENV APP_HOME=/opt/preview \
    APP_MODE="production" \
    APP_TITLE="Original # source"
WORKDIR ${APP_HOME}
LABEL org.opencontainers.image.title="Source preview" \
      org.opencontainers.image.version=$APP_VERSION
COPY ./app/ ./
RUN printf '%s\n' "$APP_MODE"
