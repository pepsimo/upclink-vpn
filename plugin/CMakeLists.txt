qt_standard_project_setup()

qt_add_library(upclinkplugin SHARED)

target_sources(upclinkplugin PRIVATE
    plugin.cpp
    vpncontroller.cpp
)

target_link_libraries(upclinkplugin PRIVATE
    Qt6::Core
    Qt6::DBus
    Qt6::Qml
)
