#!/bin/sh

/sbin/ldconfig
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 || :
/usr/bin/systemctl reload dbus.service >/dev/null 2>&1 || :

exit 0
