#!/usr/bin/env bash
set -e
set -x

# had to user different versions to make it work
parsr_version="v1.0.0"
parsr_ui_version="v1.0.0"

if [ "$1" = "stop" ]; then
    docker stop parsr-api || true
    docker stop parsr-ui || true
else
    docker run --name parsr-api --rm -p 3001:3001 axarev/parsr:$parsr_version &
    docker run --name parsr-ui --rm -t -p 8080:80 axarev/parsr-ui-localhost:$parsr_ui_version
fi
