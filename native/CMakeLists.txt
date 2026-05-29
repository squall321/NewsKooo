# 3.15 is the floor pybind11 supports and matches the system cmake (3.16.3) in
# dev WSL, so the extension builds without pulling a cmake wheel from PyPI.
cmake_minimum_required(VERSION 3.15)
project(newskoo_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(newskoo_native MODULE src/bindings.cpp)
target_compile_options(newskoo_native PRIVATE -O3 -funroll-loops)

# Install the extension into the wheel root so `import newskoo_native` works.
install(TARGETS newskoo_native LIBRARY DESTINATION .)
