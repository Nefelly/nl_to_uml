#!/bin/sh
set -e

exec 2>&1
git pull
sv restart litatom