#!/usr/bin/env bash
# Run Parsr on a remote Docker host and tunnel it to localhost:
# REMOTE_WORKSTATION=user@host scripts/remote_parsr.sh [stop]
set -euo pipefail

remote_destination=$REMOTE_WORKSTATION

parsr_version="v1.2.2"
parsr_ui_version="v1.2.2"
tunnels="ssh -f -N -L (3001|8080):localhost:(3001|8080) $remote_destination"

if [ "${1:-}" = "stop" ]; then
    ssh "$remote_destination" "docker stop parsr-api parsr-ui" || true
    pkill -f "$tunnels" || true
else
    ssh -f "$remote_destination" "nohup docker run --name parsr-api --rm --platform linux/amd64 -p 3001:3001 axarev/parsr:$parsr_version > /dev/null 2>&1 &"
    ssh -f "$remote_destination" "nohup docker run --name parsr-ui --rm --platform linux/amd64 -t -p 8080:80 axarev/parsr-ui-localhost:$parsr_ui_version > /dev/null 2>&1 &"
    ssh -f -N -L 8080:localhost:8080 "$remote_destination"
    ssh -f -N -L 3001:localhost:3001 "$remote_destination"
fi
