include(GNUInstallDirs)

qt_standard_project_setup(REQUIRES 6.5)

qt_add_qml_module(upclinkplugin
    URI org.upclink.vpn
    VERSION 1.0
    OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/org/upclink/vpn"
    SOURCES
        vpncontroller.cpp
        vpncontroller.h
)

target_link_libraries(upclinkplugin PRIVATE
    Qt6::Core
    Qt6::DBus
    Qt6::Qml
)

qt_query_qml_module(upclinkplugin
    PLUGIN_TARGET qml_plugin_target
    TARGET_PATH qml_target_path
    QMLDIR qml_qmldir
    TYPEINFO qml_typeinfo
)

set(qml_install_dir
    "${CMAKE_INSTALL_LIBDIR}/qt6/qml/${qml_target_path}"
)


install(TARGETS upclinkplugin
    LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}"
)

install(TARGETS "${qml_plugin_target}"
    LIBRARY DESTINATION "${qml_install_dir}"
)

install(FILES
    "${qml_qmldir}"
    "${qml_typeinfo}"
    DESTINATION "${qml_install_dir}"
)
