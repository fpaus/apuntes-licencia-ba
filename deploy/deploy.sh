#!/usr/bin/env bash
# Build the arm64 binary and (re)start the container on server.pi.
# Plain docker, not docker-compose: compose 1.29 on server.pi fails to recreate containers (KeyError 'ContainerConfig').
set -euo pipefail
cd "$(dirname "$0")/.."
CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o dist/licencia-arm64 .
ssh server.pi 'mkdir -p ~/Projects/licencia_dinamica && rm -f ~/Projects/licencia_dinamica/docker-compose.yml'
scp -q deploy/Dockerfile server.pi:Projects/licencia_dinamica/
scp -q dist/licencia-arm64 server.pi:Projects/licencia_dinamica/licencia
ssh server.pi 'cd ~/Projects/licencia_dinamica && docker build -q -t licencia-dinamica . >/dev/null &&
  docker ps -aq --filter name=licencia | xargs -r docker rm -f >/dev/null &&
  docker run -d --name licencia --restart unless-stopped -p 8642:8642 licencia-dinamica >/dev/null &&
  docker image prune -f >/dev/null && docker ps --filter name=licencia --format "{{.Names}} {{.Status}}"'
