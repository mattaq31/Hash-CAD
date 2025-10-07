cmake_minimum_required(VERSION 3.18)

# Root CMake to build the Python C extension eqcorr2d for CLion debugging/integration.
# Open this repo in CLion and select the default Debug profile.
# Build target: eqcorr2d
# The built module (eqcorr2d.pyd on Windows) will appear in your build directory
# (e.g., cmake-build-debug) so you can add that folder to PYTHONPATH and import eqcorr2d.

project(hash_cad_eqcorr2d C)

# Find Python and NumPy
# Prefer using the active virtualenv/conda environment if present and allow override via PYTHON_EXECUTABLE
set(Python3_FIND_VIRTUALENV FIRST)
set(Python3_FIND_IMPLEMENTATIONS CPython)
if(DEFINED ENV{CONDA_PREFIX})
    list(APPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}")
endif()
# Allow a manual override: pass -DPYTHON_EXECUTABLE:FILEPATH=... in CLion CMake options
if(DEFINED PYTHON_EXECUTABLE AND NOT Python3_EXECUTABLE)
    set(Python3_EXECUTABLE "${PYTHON_EXECUTABLE}" CACHE FILEPATH "Path to Python3 interpreter" FORCE)
endif()
find_package(Python3 COMPONENTS Interpreter Development NumPy REQUIRED)

set(EQCORR2D_SRC
    ${CMAKE_CURRENT_SOURCE_DIR}/c_sources/eqcorr2d_core.c
    ${CMAKE_CURRENT_SOURCE_DIR}/c_sources/eqcorr2d_bindings.c
    # Note: do NOT list headers here (eqcorr2d.h) — headers are included via target_include_directories
)

add_library(eqcorr2d MODULE ${EQCORR2D_SRC})

# Ensure the C sources directory is on the include path (for eqcorr2d.h)
target_include_directories(eqcorr2d PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/c_sources)

# Add a tiny C executable that embeds Python and calls the integration wrapper.
add_executable(eqcorr2d_main
    ${CMAKE_CURRENT_SOURCE_DIR}/c_sources/main.c
)
# Put the runnable exe into a subdirectory to avoid locking conflicts with AV/previous runs.
set_target_properties(eqcorr2d_main PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/runners"
)
# Link the executable with Python (same as the module) so it embeds the interpreter.
target_link_libraries(eqcorr2d_main PRIVATE Python3::Python)
# Ensure headers (Python and NumPy) are available to the executable as well
if(DEFINED Python3_INCLUDE_DIRS)
    target_include_directories(eqcorr2d_main PRIVATE ${Python3_INCLUDE_DIRS})
endif()
if(DEFINED Python3_NumPy_INCLUDE_DIRS)
    target_include_directories(eqcorr2d_main PRIVATE ${Python3_NumPy_INCLUDE_DIRS})
endif()
# Also include our C sources directory for the executable (for eqcorr2d.h)
target_include_directories(eqcorr2d_main PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/c_sources)
set_property(TARGET eqcorr2d_main PROPERTY C_STANDARD 11)
set_property(TARGET eqcorr2d_main PROPERTY C_STANDARD_REQUIRED ON)

# Match setup.py compiler flags per toolchain
if(MSVC)
    # Use debug-friendly flags for Debug config; keep optimized flags for Release-like configs
    target_compile_options(eqcorr2d PRIVATE
        $<$<CONFIG:Debug>:/Od;/Zi;/fp:precise>
        $<$<NOT:$<CONFIG:Debug>>:/O2;/GL;/fp:fast;/arch:AVX2>
    )
    target_link_options(eqcorr2d PRIVATE
        $<$<CONFIG:Debug>:/DEBUG>
    )
else()
    # Avoid -flto (Link Time Optimization) with CLion's bundled MinGW: it is built without LTO support
    # which causes: cc1.exe: error: LTO support has not been enabled in this configuration
    # Be explicit: strip any inherited -flto flags from global C flags to prevent CLion's
    # "Cannot get compiler information" due to cc1.exe error.
    foreach(var IN ITEMS CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELEASE CMAKE_C_FLAGS_RELWITHDEBINFO CMAKE_C_FLAGS_MINSIZEREL)
        if(DEFINED ${var})
            string(REPLACE "-flto" "" ${var} "${${var}}")
        endif()
    endforeach()
    set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)

    target_compile_options(eqcorr2d PRIVATE
        $<$<CONFIG:Debug>:-O0 -g>
        $<$<CONFIG:Release>:-O3 -march=native -funroll-loops -ffast-math>
        -fopenmp
    )
    target_link_options(eqcorr2d PRIVATE -fopenmp)
endif()

# Include Python and NumPy headers
# (Python include is in the Python3::Python INTERFACE; NumPy include provided by FindPython3)

# Make sure we compile as C11 for better portability
set_property(TARGET eqcorr2d PROPERTY C_STANDARD 11)
set_property(TARGET eqcorr2d PROPERTY C_STANDARD_REQUIRED ON)

# Include NumPy
if(DEFINED Python3_NumPy_INCLUDE_DIRS)
    target_include_directories(eqcorr2d PRIVATE ${Python3_NumPy_INCLUDE_DIRS})
endif()

# Link against Python
target_link_libraries(eqcorr2d PRIVATE Python3::Python)

# Extension module properties
# On Windows, make a .pyd with no "lib" prefix; on UNIX keep default .so
set_target_properties(eqcorr2d PROPERTIES
    PREFIX ""
)

if(WIN32)
    set_target_properties(eqcorr2d PROPERTIES SUFFIX ".pyd")
endif()

# Helpful message after configure
message(STATUS "Python3 executable: ${Python3_EXECUTABLE}")
message(STATUS "Python3 include dir: ${Python3_INCLUDE_DIRS}")
message(STATUS "NumPy include dir: ${Python3_NumPy_INCLUDE_DIRS}")
