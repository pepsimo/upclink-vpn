#!/bin/sh

if [ "$1" -eq 0 ]; then
    /usr/bin/systemctl stop upclink-vpn.service >/dev/null 2>&1 || :
fi

exit 0
