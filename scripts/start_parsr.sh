#!/usr/bin/env bash
set -e
set -x

# set ssh config
remote_destination=$REMOTE_WORKSTATION
remote_destination="babel"

if [ "$1" = "stop" ]; then
  ssh $remote_destination "docker stop parsr-api && docker stop parsr-ui"
  killall ssh
else
  ssh -f $remote_destination "nohup docker run --name parsr-api --rm -p 3001:3001 axarev/parsr:latest > /dev/null 2>&1 &"
  ssh -f $remote_destination "nohup docker run --name parsr-ui --rm -t -p 8080:80 axarev/parsr-ui-localhost:latest > /dev/null 2>&1 &"
  ssh -f -N -L 8080:localhost:8080 $remote_destination
  ssh -f -N -L 3001:localhost:3001 $remote_destination
fi
