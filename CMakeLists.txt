project(cmake_utils)

FUNCTION(SVNCO URL DIR)
    set(options SOURCE)
    set(oneValueArgs "")
    set(multiValueArgs "")

    cmake_parse_arguments(SVNCO "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(SVNCO_SOURCE)
        set(DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/${DIR})
    else()
        set(DESTINATION ${DIR})
    endif()

    if(NOT EXISTS ${DIR})
        execute_process(COMMAND svn co ${URL} ${DESTINATION}
            RESULT_VARIABLE PROC_RES
            OUTPUT_VARIABLE PROC_STDOUT
            ERROR_VARIABLE  PROC_STDERR
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        )
        message("${PROC_STDOUT}")
        if(NOT PROC_RES EQUAL 0)
            message(FATAL_ERROR "${PROC_STDERR}")
        endif()
    endif()
ENDFUNCTION()

FUNCTION(MINIFY TARGET)
    set(options STRIP UPX ALL KEEP_ORIGINAL)
    set(oneValueArgs "")
    set(multiValueArgs "")

    cmake_parse_arguments(MINIFY "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    set(LAST_TARGET ${TARGET})
    if(MINIFY_ALL)
        set(MINIFY_ALL ALL)
    else()
        set(MINIFY_ALL "")
    endif()
    if(MINIFY_KEEP_ORIGINAL)
        add_custom_command(OUTPUT ${TARGET}_unstripped_timestamp.txt
            DEPENDS ${LAST_TARGET}
            COMMAND cmake -E touch ${TARGET}_unstripped_timestamp.txt
            COMMAND cmake -E copy_if_different $<TARGET_FILE:${TARGET}> $<TARGET_FILE:${TARGET}>.unstripped
            DEPENDS $<TARGET_FILE:${TARGET}>
            COMMENT "Archiving unstripped ${TARGET}"
        )
        add_custom_target(${TARGET}_unstripped ${MINIFY_ALL} SOURCES ${TARGET}_unstripped_timestamp.txt)
        set(LAST_TARGET ${TARGET}_unstripped)
    endif()
    if(MINIFY_STRIP)
        add_custom_command(OUTPUT ${TARGET}_stripped_timestamp.txt
            DEPENDS ${LAST_TARGET}
            COMMAND cmake -E touch ${TARGET}_stripped_timestamp.txt
            COMMAND ${CMAKE_STRIP} -s $<TARGET_FILE:${TARGET}>
            DEPENDS $<TARGET_FILE:${TARGET}>
            COMMENT "Stripping ${TARGET}"
        )
        add_custom_target(${TARGET}_stripped ${MINIFY_ALL} SOURCES ${TARGET}_stripped_timestamp.txt)
        set(LAST_TARGET ${TARGET}_stripped)
    endif()
    if(MINIFY_UPX)
        add_custom_command(OUTPUT ${TARGET}_compressed_timestamp.txt
            DEPENDS ${LAST_TARGET}
            COMMAND cmake -E touch ${TARGET}_compressed_timestamp.txt
            COMMAND upx $<TARGET_FILE:${TARGET}>
            DEPENDS $<TARGET_FILE:${TARGET}>
            COMMENT "Compressing ${TARGET}"
        )
        add_custom_target(${TARGET}_compressed ${MINIFY_ALL} SOURCES ${TARGET}_compressed_timestamp.txt)
        set(LAST_TARGET ${TARGET}_compressed)
    endif()
ENDFUNCTION()

FUNCTION(PYFIND)
    set(options INTERP LIBS REQUIRED)
    set(oneValueArgs VERSION)
    set(multiValueArgs "")

    cmake_parse_arguments(PYFIND "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    unset(PYTHON_INCLUDE_PATH CACHE)
    unset(PYTHONLIBS_FOUND CACHE)
    unset(PYTHON_LIBRARY CACHE)
    unset(PYTHON_LIBRARIES CACHE)
    unset(PYTHON_INCLUDE_DIR CACHE)
    unset(PYTHON_INCLUDE_DIRS CACHE)
    unset(PYTHON_DEBUG_LIBRARIES CACHE)
    unset(PYTHONLIBS_VERSION_STRING CACHE)

    unset(PYTHONINTERP_FOUND CACHE)
    unset(PYTHON_EXECUTABLE CACHE)
    unset(PYTHON_VERSION_STRING CACHE)
    unset(PYTHON_VERSION_MAJOR CACHE)
    unset(PYTHON_VERSION_MINOR CACHE)
    unset(PYTHON_VERSION_PATCH CACHE)
    set(Python_ADDITIONAL_VERSIONS ${PYFIND_VERSION})
    if(NOT PYFIND_INTERP AND NOT PYFIND_LIBS)
        set(PYFIND_INTERP ON)
        set(PYFIND_LIBS ON)
    endif()
    if(PYFIND_INTERP)
        find_package(PythonInterp ${PYFIND_VERSION})
    endif()
    if(PYFIND_LIBS)
        find_package(PythonLibs ${PYFIND_VERSION})
    endif()
    if(PYFIND_REQUIRED)
        if(PYFIND_INTERP AND NOT PythonInterp_FOUND)
            message(FATAL "Python interpreter not found")
        endif()
        if(PYFIND_LIBS AND NOT PythonLibs_FOUND)
            message(FATAL "Python library not found")
        endif()
    endif()
    set(PYTHON${PYFIND_VERSION}_EXE ${PYTHON_EXECUTABLE} CACHE STRING "")
    set(PYTHON${PYFIND_VERSION}_INCLUDE ${PYTHON_INCLUDE_DIRS} CACHE STRING "")
    set(PYTHON${PYFIND_VERSION}_LIB ${PYTHON_LIBRARIES} CACHE STRING "")
ENDFUNCTION()



FUNCTION(EMBED)
    set(OPTIONS ENCRYPT)
    set(ONE_VALUE_ARGS ID NAMESPACE DESTINATION)
    set(MULTI_VALUE_ARGS BLOBS)
    cmake_parse_arguments(EMBED "${OPTIONS}" "${ONE_VALUE_ARGS}" "${MULTI_VALUE_ARGS}" ${ARGN} )
    get_filename_component(OUTDIR ${EMBED_DESTINATION} DIRECTORY)
    set(${ID}_HEADER  ${EMBED_DESTINATION}.h PARENT_SCOPE)
    if(EMBED_NAMESPACE)
        set(EMBED_NAMESPACE "-n ${EMBED_NAMESPACE}")
        set(OUTPUT ${EMBED_DESTINATION}.cpp)
    else()
        set(OUTPUT ${EMBED_DESTINATION}.c)
    endif()
    if(EMBED_ENCRYPT)
        set(ENCRYPT "-e")
    endif()
    set(${EMBED_ID}_OUTPUT ${OUTPUT} PARENT_SCOPE)
    set(DEPS)
    FOREACH(BLOBPAIR ${EMBED_BLOBS})
        STRING(REGEX MATCH "(=|^)([^=]+$)" RESULT ${BLOBPAIR})
        list(APPEND DEPS ${CMAKE_MATCH_2})
    ENDFOREACH()
    add_custom_command(
        OUTPUT ${OUTPUT}
        DEPENDS ${DEPS}
        COMMAND ${CMAKE_COMMAND} -E make_directory ${OUTDIR}
        COMMAND ${PYTHON_EXECUTABLE} ${B2CPP} ${ENCRYPT} -o ${EMBED_DESTINATION} ${EMBED_NAMESPACE} ${EMBED_BLOBS}
        COMMENT "Generating ${OUTPUT}"
        )
ENDFUNCTION()

include(${CMAKE_CURRENT_SOURCE_DIR}/library.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/sip.cmake)

set(CMAKE_UTILS_MODULE_MANAGER_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/bin/module_manager.py)
include(${CMAKE_CURRENT_SOURCE_DIR}/external.cmake)

MACRO(SETUP_STANDARD_FLAGS)
    set(options CPP_EXT C_EXT)
    set(oneValueArgs C CPP)
    set(multiValueArgs "")

    cmake_parse_arguments(SETUP_STANDARD_FLAGS "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    set(CMAKE_CXX_EXTENSIONS OFF CACHE BOOL "")
    if(SETUP_STANDARD_FLAGS_C)
        set(CMAKE_C_STANDARD ${SETUP_STANDARD_FLAGS_C} CACHE INT "")
    else()
        set(CMAKE_C_STANDARD 99 CACHE INT "")
    endif()

    if(SETUP_STANDARD_FLAGS_CXX)
        set(CMAKE_CXX_STANDARD ${SETUP_STANDARD_FLAGS_CXX} CACHE INT "")
    else()
        set(CMAKE_CXX_STANDARD 11 CACHE INT "")
    endif()

    if(SETUP_STANDARD_FLAGS_C_EXT)
        set(CMAKE_C_EXTENSIONS ON CACHE BOOL "")
    else()
        set(CMAKE_C_EXTENSIONS OFF CACHE BOOL "")
    endif()

    if(SETUP_STANDARD_FLAGS_CXX_EXT)
        set(CMAKE_CXX_EXTENSIONS ON CACHE BOOL "")
    else()
        set(CMAKE_CXX_EXTENSIONS OFF CACHE BOOL "")
    endif()

    if(${CMAKE_VERSION} VERSION_GREATER "3.9" OR ${CMAKE_VERSION} VERSION_EQUAL "3.9")
        include(CheckIPOSupported)
        check_ipo_supported(RESULT IPO)
        if(NOT IPO)
            message(INFO "interprocedural optimization is not supported with this compiler")
        endif()
        option(CMAKE_INTERPROCEDURAL_OPTIMIZATION "Use the link time optimization feature of the compiler" OFF)
    endif()

    if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        option(DEBUG_STL "Enable usage of debug STL (gcc-only)" OFF)
        option(TRAP_OVERFLOW "Enable overflow trapping (gcc-only)" OFF)
        option(STATIC_BUILD "Create statically linked executables" OFF)
        set(BUILD_FLAGS -Wall -Wextra -pedantic)
        if(UNIX)
            list(APPEND BUILD_FLAGS -pthread)
            link_libraries(-pthread)
        endif()
        if(STATIC_BUILD)
            set(CMAKE_EXE_LINKER_FLAGS "-static")
        endif()
        if(WIN32)
            add_definitions(-DNOMINMAX)
        endif()

        if(DEBUG_STL)
            add_definitions(-D_GLIBCXX_DEBUG)
        endif()
        if(TRAP_OVERFLOW)
            list(APPEND BUILD_FLAGS -ftrapv)
        endif()
        if(CMAKE_INTERPROCEDURAL_OPTIMIZATION)
            list(APPEND BUILD_FLAGS -fuse-linker-plugin)
        endif()
        add_compile_options(${BUILD_FLAGS})
    endif()
ENDMACRO()
