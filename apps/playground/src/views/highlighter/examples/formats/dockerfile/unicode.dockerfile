# 原文、引号与换行都保留 🌌
FROM alpine:3
ENV TITLE="你好 🌌"
COPY <<'NOTE' /tmp/note.txt
原文包含 <script>source only</script>。
这里不会执行，也不会渲染 HTML。
NOTE
CMD ["cat", "/tmp/note.txt"]
