cmake_minimum_required(VERSION 3.22)

project(
    UPClinkVPN
    VERSION 1.0.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS
    Core
    DBus
    Qml
)

add_subdirectory(plugin)
