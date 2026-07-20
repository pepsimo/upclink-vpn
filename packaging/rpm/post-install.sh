#!/bin/sh

/sbin/ldconfig
%service_add_post upclink-vpn.service
/usr/bin/systemctl reload dbus.service >/dev/null 2>&1 || :

exit 0
