project(cmake_utils)

if(${CMAKE_VERSION} VERSION_GREATER "3.9")
    cmake_policy(VERSION 3.9)
    include(CheckIPOSupported)
    check_ipo_supported(RESULT CMAKE_INTERPROCEDURAL_OPTIMIZATION)
    if(NOT CMAKE_INTERPROCEDURAL_OPTIMIZATION)
        message(WARNING "interprocedural optimization is not supported with this compiler")
    endif()
endif()

FUNCTION(SVNCO URL DIR)
    set(options SOURCE)
    set(oneValueArgs "")
    set(multiValueArgs "")

    cmake_parse_arguments(SVNCO "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    string(FIND ${URL} "^" POSITION)
    if(POSITION EQUAL 0)
        string(SUBSTRING ${URL} 1 -1 PATH)
        set(URL "svn+ssh://svn.comelz.com/svn/${PATH}")
    endif()

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
    set(options "")
    set(oneValueArgs "")
    set(multiValueArgs VERSIONS)

    cmake_parse_arguments(PYFIND "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    unset(PYTHONINTERP_FOUND CACHE)
    unset(PYTHON_EXECUTABLE CACHE)
    unset(PYTHON_VERSION_STRING CACHE)
    unset(PYTHON_VERSION_MAJOR CACHE)
    unset(PYTHON_VERSION_MINOR CACHE)
    unset(PYTHON_VERSION_PATCH CACHE)
    set(Python_ADDITIONAL_VERSIONS ${PYFIND_VERSIONS})
    find_package(PythonInterp)

    set(index 0)
    list(LENGTH PYFIND_VERSIONS limit)
    WHILE((NOT PYTHON_EXECUTABLE OR PYTHON_EXECUTABLE STREQUAL "PYTHON_EXECUTABLE-NOT-FOUND") AND index LESS limit)
        list(GET PYFIND_VERSIONS index version)
        find_program(PYTHON_EXECUTABLE NAMES python${version} PATHS /usr/bin NO_CMAKE_FIND_ROOT_PATH)
        MATH(EXPR index "${index}+1")
    ENDWHILE()
    if(PYTHON_EXECUTABLE STREQUAL "PYTHON_EXECUTABLE-NOT-FOUND")
        set(PYTHONINTERP_FOUND OFF CACHE BOOL "" FORCE)
    else()
        set(PYTHONINTERP_FOUND ON CACHE BOOL "" FORCE)
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
