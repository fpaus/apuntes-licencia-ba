# The binary is static (CGO_ENABLED=0) and embeds app/ and content/: nothing else is needed.
FROM scratch
COPY licencia /licencia
EXPOSE 8642
ENTRYPOINT ["/licencia", "-no-open", "-addr", "0.0.0.0:8642"]
