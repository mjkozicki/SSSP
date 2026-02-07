cmake_minimum_required(VERSION 3.10)
project(sssp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

add_library(sssp STATIC graph.cpp sssp.cpp)
target_include_directories(sssp PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(sssp_test test_main.cpp)
target_link_libraries(sssp_test sssp)
add_test(NAME sssp_test COMMAND sssp_test)

add_executable(benchmark benchmark_main.cpp)
target_link_libraries(benchmark sssp)
