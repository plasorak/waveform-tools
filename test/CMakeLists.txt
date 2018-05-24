cmake_minimum_required(VERSION 3.6)

add_executable(read_samples_test read_samples_test.cxx ../cnpy.cpp)
set_property(TARGET read_samples_test PROPERTY CXX_STANDARD 14)
target_link_libraries(read_samples_test z)
