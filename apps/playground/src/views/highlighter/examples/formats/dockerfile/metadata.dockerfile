FROM nginx:alpine
LABEL org.opencontainers.image.title="Documentation preview" \
      org.opencontainers.image.description="Escaped original source"
COPY --chown=nginx:nginx ./public/ /usr/share/nginx/html/
EXPOSE 8080/tcp
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD wget -q -O - http://localhost:8080/ || exit 1
STOPSIGNAL SIGQUIT
USER nginx
CMD ["nginx", "-g", "daemon off;"]
