cmake_minimum_required(VERSION 3.22)

project(
    UPClinkVPN
    VERSION 1.0.3
    LANGUAGES CXX
)

if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
    set(CMAKE_INSTALL_PREFIX "/usr" CACHE PATH "Prefijo de instalación" FORCE)
endif()

include(GNUInstallDirs)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_SKIP_RPATH TRUE)

find_package(Qt6 REQUIRED COMPONENTS
    Core
    DBus
    Qml
)

add_subdirectory(plugin)

set(
    SYSTEMD_SYSTEM_UNIT_DIR
    "lib/systemd/system"
    CACHE STRING "Directorio de unidades systemd"
)

set(
    DBUS_SYSTEM_SERVICE_DIR
    "${CMAKE_INSTALL_DATADIR}/dbus-1/system-services"
    CACHE STRING "Directorio de servicios del sistema D-Bus"
)

set(UPCLINK_GENERATED_DIR
    "${CMAKE_CURRENT_BINARY_DIR}/packaging"
)

file(MAKE_DIRECTORY "${UPCLINK_GENERATED_DIR}")

configure_file(
    packaging/systemd/upclink-vpn.service.in
    "${UPCLINK_GENERATED_DIR}/upclink-vpn.service"
    @ONLY
)

configure_file(
    packaging/dbus/org.upclink.VPN.service.in
    "${UPCLINK_GENERATED_DIR}/org.upclink.VPN.service"
    @ONLY
)

install(PROGRAMS
    backend/upclink_vpn_service.py
    DESTINATION "${CMAKE_INSTALL_LIBEXECDIR}"
    RENAME upclink-vpn-service
)

install(FILES
    backend/upclink_security.py
    DESTINATION "${CMAKE_INSTALL_LIBEXECDIR}"
)

install(FILES
    "${UPCLINK_GENERATED_DIR}/upclink-vpn.service"
    DESTINATION "${SYSTEMD_SYSTEM_UNIT_DIR}"
)

install(FILES
    "${UPCLINK_GENERATED_DIR}/org.upclink.VPN.service"
    DESTINATION "${DBUS_SYSTEM_SERVICE_DIR}"
)

install(FILES
    packaging/dbus/org.upclink.VPN.conf
    DESTINATION "${CMAKE_INSTALL_DATADIR}/dbus-1/system.d"
)

install(FILES
    packaging/polkit/org.upclink.vpn.policy
    DESTINATION "${CMAKE_INSTALL_DATADIR}/polkit-1/actions"
)

install(DIRECTORY
    plasmoid/
    DESTINATION "${CMAKE_INSTALL_DATADIR}/plasma/plasmoids/org.upclink.vpn"
)

install(FILES
    LICENSE
    DESTINATION "${CMAKE_INSTALL_DATADIR}/licenses/upclink-vpn"
)

install(FILES README.md DESTINATION "${CMAKE_INSTALL_DATADIR}/doc/packages/upclink-vpn")

set(CPACK_GENERATOR "RPM")
set(CPACK_PACKAGE_NAME "upclink-vpn")
set(CPACK_PACKAGE_VENDOR "Pep Simo")
set(CPACK_PACKAGE_CONTACT "https://www.pepsimo.eu")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY
    "UPClink VPN widget for KDE Plasma 6"
)
set(CPACK_PACKAGE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/dist")
set(CPACK_PACKAGE_CHECKSUM "SHA256")
set(CPACK_PACKAGING_INSTALL_PREFIX "/usr")
set(CPACK_PACKAGE_RELOCATABLE FALSE)
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")

set(CPACK_RPM_FILE_NAME "RPM-DEFAULT")
set(CPACK_RPM_PACKAGE_RELOCATABLE OFF)
set(CPACK_RPM_PACKAGE_RELEASE "1")
set(CPACK_RPM_PACKAGE_LICENSE "GPL-3.0-or-later")
set(CPACK_RPM_PACKAGE_GROUP "Productivity/Networking/System")
set(CPACK_RPM_PACKAGE_URL "https://www.pepsimo.eu")
set(CPACK_RPM_PACKAGE_DESCRIPTION
    "UPClink VPN connects and disconnects the Polytechnic University of Catalonia virtual private network from KDE Plasma 6. Authentication takes place in the user's web browser. Privileged operations are handled by a system service protected through D-Bus and PolicyKit."
)
set(CPACK_RPM_PACKAGE_AUTOREQPROV ON)
set(CPACK_RPM_PACKAGE_REQUIRES
   "openfortivpn, NetworkManager, polkit, dbus-1, python3-dbus-python, python3-gobject, plasma6-workspace, libplasma6-components, kf6-kirigami-imports"
)
set(CPACK_RPM_PRE_INSTALL_SCRIPT_FILE
    "${CMAKE_CURRENT_SOURCE_DIR}/packaging/rpm/pre-install.sh"
)
set(CPACK_RPM_POST_INSTALL_SCRIPT_FILE
    "${CMAKE_CURRENT_SOURCE_DIR}/packaging/rpm/post-install.sh"
)
set(CPACK_RPM_PRE_UNINSTALL_SCRIPT_FILE
    "${CMAKE_CURRENT_SOURCE_DIR}/packaging/rpm/pre-uninstall.sh"
)
set(CPACK_RPM_POST_UNINSTALL_SCRIPT_FILE
    "${CMAKE_CURRENT_SOURCE_DIR}/packaging/rpm/post-uninstall.sh"
)

set(CPACK_RPM_EXCLUDE_FROM_AUTO_FILELIST_ADDITION
    "/usr/lib/systemd"
    "/usr/lib/systemd/system"
    "/usr/lib64/qt6"
    "/usr/lib64/qt6/qml"
    "/usr/lib64/qt6/qml/org"
    "/usr/libexec"
    "/usr/share/dbus-1"
    "/usr/share/dbus-1/system-services"
    "/usr/share/dbus-1/system.d"
    "/usr/share/doc"
    "/usr/share/doc/packages"
    "/usr/share/licenses"
    "/usr/share/plasma"
    "/usr/share/plasma/plasmoids"
    "/usr/share/polkit-1"
    "/usr/share/polkit-1/actions"
)

include(CTest)

if(BUILD_TESTING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)

    add_test(
        NAME backend-security
        COMMAND
            "${Python3_EXECUTABLE}"
            -m unittest discover
            -s "${CMAKE_CURRENT_SOURCE_DIR}/tests"
            -v
    )
endif()

set(CPACK_STRIP_FILES TRUE)

include(CPack)
