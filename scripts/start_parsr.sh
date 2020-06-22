#!/usr/bin/env bash
set -e
set -x

# set ssh config
remote_destination=$REMOTE_WORKSTATION

# had to user different versions to make it work
parsr_version="v0.12"
parsr_ui_version="v0.12.2"

if [ "$1" = "stop" ]; then
  ssh $remote_destination "docker stop parsr-api; docker stop parsr-ui" || true
  killall ssh
else
  ssh -f $remote_destination "nohup docker run --name parsr-api --rm -p 3001:3001 axarev/parsr:$parsr_version > /dev/null 2>&1 &"
  ssh -f $remote_destination "nohup docker run --name parsr-ui --rm -t -p 8080:80 axarev/parsr-ui-localhost:$parsr_ui_version > /dev/null 2>&1 &"
  ssh -f -N -L 8080:localhost:8080 $remote_destination
  ssh -f -N -L 3001:localhost:3001 $remote_destination
fi
