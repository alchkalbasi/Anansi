#!/bin/bash

set -eo pipefail

if timeout 2 bash -c 'echo > /dev/tcp/127.0.0.1/9200' >/dev/null 2>&1; then
    exit 0
else
    exit 1
fi