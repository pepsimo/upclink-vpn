#!/bin/sh

/sbin/ldconfig
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 || :
/usr/bin/systemctl reload dbus.service >/dev/null 2>&1 || :

if /usr/bin/systemctl is-active --quiet upclink-vpn.service; then
    /usr/bin/systemctl try-restart upclink-vpn.service >/dev/null 2>&1 || :
fi

exit 0
