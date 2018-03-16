project(cmake_utils)

FUNCTION(SCM_CHECKOUT URI DESTINATION)
    PYFIND(VERSIONS 3 SUFFIX 3 REQUIRED)
    execute_process(COMMAND ${PYTHON_EXECUTABLE_3}
        RESULT_VARIABLE PROC_RES
        OUTPUT_VARIABLE PROC_STDOUT
        ERROR_VARIABLE  PROC_STDERR
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
    message("${PROC_STDOUT}")
    if(NOT PROC_RES EQUAL 0)
        message(FATAL_ERROR "${PROC_STDERR}")
    endif()
ENDFUNCTION()

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
    set(options REQUIRED)
    set(oneValueArgs SUFFIX)
    set(multiValueArgs VERSIONS)
    cmake_parse_arguments(PYFIND "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(PYFIND_SUFFIX)
        set(RESULT PYTHON_EXECUTABLE_${PYFIND_SUFFIX})
    else()
        set(RESULT PYTHON_EXECUTABLE)
    endif()

    if(NOT DEFINED ${RESULT})
        unset(PYTHONINTERP_FOUND CACHE)
        unset(PYTHON_EXECUTABLE CACHE)
        unset(PYTHON_VERSION_STRING CACHE)
        unset(PYTHON_VERSION_MAJOR CACHE)
        unset(PYTHON_VERSION_MINOR CACHE)
        unset(PYTHON_VERSION_PATCH CACHE)
        set(Python_ADDITIONAL_VERSIONS ${PYFIND_VERSIONS})
        find_package(PythonInterp)
        if(PYTHON_EXECUTABLE)
            set(${RESULT} ${PYTHON_EXECUTABLE} CACHE STRING "")
        endif()

        set(index 0)
        list(LENGTH PYFIND_VERSIONS limit)
        WHILE((NOT ${RESULT} OR ${RESULT} STREQUAL "PYTHON_EXECUTABLE-NOT-FOUND") AND index LESS limit)
            list(GET PYFIND_VERSIONS index version)
            find_program(${RESULT} NAMES python${version} PATHS /usr/bin NO_CMAKE_FIND_ROOT_PATH)
            MATH(EXPR index "${index}+1")
        ENDWHILE()
        if(NOT ${RESULT})
            if(PYFIND_REQUIRED)
                message(FATAL_ERROR "Python interpreter not found")
            else()
                set(PYTHONINTERP_FOUND OFF CACHE BOOL "" FORCE)
            endif()
        else()
            set(PYTHONINTERP_FOUND ON CACHE BOOL "" FORCE)
        endif()
    endif()
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
    set(B2CPP ${cmake_utils_SOURCE_DIR}/bin/b2cpp.py)
    PYFIND(VERSIONS 2 SUFFIX 2 REQUIRED)
    add_custom_command(
        OUTPUT ${OUTPUT}
        DEPENDS ${DEPS}
        COMMAND ${CMAKE_COMMAND} -E make_directory ${OUTDIR}
        COMMAND ${PYTHON_EXECUTABLE_2} ${B2CPP} ${ENCRYPT} -o ${EMBED_DESTINATION} ${EMBED_NAMESPACE} ${EMBED_BLOBS}
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
            message(STATUS "Interprocedural optimization is not supported with this compiler")
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

FUNCTION(SVN_VERSION SVN_ROOT OUTPUT)
    PYFIND(VERSIONS 3 SUFFIX 3 REQUIRED)
    set(VERSION_SCRIPT ${cmake_utils_SOURCE_DIR}/bin/version.py)
    execute_process(
        COMMAND ${PYTHON_EXECUTABLE_3} ${VERSION_SCRIPT} ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE PROC_RES
        OUTPUT_VARIABLE PROC_STDOUT
        ERROR_VARIABLE  PROC_STDERR
    )
    if(NOT PROC_RES EQUAL 0)
        message(FATAL_ERROR "${PROC_STDERR}")
    endif()
    set(${OUTPUT} ${PROC_STDOUT} PARENT_SCOPE)
ENDFUNCTION()

FUNCTION(GENERATE_VERSION)
    set(OPTIONS "")
    set(ONE_VALUE_ARGS VERSION_FILE VERSION_HEADER)
    set(MULTI_VALUE_ARGS "")
    cmake_parse_arguments(GENERATE_VERSION "${OPTIONS}" "${ONE_VALUE_ARGS}" "${MULTI_VALUE_ARGS}" ${ARGN} )

    set(VERSION_SCRIPT ${cmake_utils_SOURCE_DIR}/bin/version.py)
    PYFIND(VERSIONS 3 SUFFIX 3 REQUIRED)
    set(ARGS)
    if(GENERATE_VERSION_VERSION_FILE)
        list(APPEND ARGS -O ${GENERATE_VERSION_VERSION_HEADER})
    endif()
    if(GENERATE_VERSION_VERSION_HEADER)
        list(APPEND ARGS -o ${GENERATE_VERSION_VERSION_FILE})
        add_custom_command(OUTPUT ${GENERATE_VERSION_VERSION_HEADER}
                          COMMAND ${PYTHON_EXECUTABLE_3} ${VERSION_SCRIPT} ${CMAKE_CURRENT_SOURCE_DIR} -s ${ARGS}
                          COMMENT "Generating version.h"
                          DEPENDS ${VERSION_SCRIPT} ${CMAKE_PROJECT_DIR})
    endif()
ENDFUNCTION()
