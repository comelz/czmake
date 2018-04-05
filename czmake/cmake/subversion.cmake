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

FUNCTION(SVN_VERSION SVN_ROOT OUTPUT)
    PYFIND(VERSIONS 3 SUFFIX 3 REQUIRED)
    set(VERSION_SCRIPT ${CZMAKE_ROOT_PATH}/version.py)
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

    set(VERSION_SCRIPT ${CZMAKE_ROOT_PATH}/bin/version.py)
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