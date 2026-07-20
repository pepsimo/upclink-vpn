#!/bin/sh

/sbin/ldconfig
%service_del_postun upclink-vpn.service
/usr/bin/systemctl reload dbus.service >/dev/null 2>&1 || :

exit 0
