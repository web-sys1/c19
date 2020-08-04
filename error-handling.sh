#!/usr/bin/env bash

. ./error-handling.conf
# The .conf file needs to have these variables:
#MAIL_SERVER="smtp://some.email.server:25"
#MAIL_FROM="source@address.com"
#MAIL_TO="destination@address.com"


# apt-get install s-nail
cat *.log | s-nail \
  -s "c19 rebuild error" \
  -r "${MAIL_FROM}" \
  -S smtp="${MAIL_SERVER}" \
  "${MAIL_TO}"
