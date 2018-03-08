
FUNCTION(RESOLVE_EXTERNALS)
    PYFIND(INTERP VERSION 3)
    set(EXTERNALS_SCRIPT ${cmake_utils_SOURCE_DIR}/bin/external.py)
    set(REPO_SOURCE_DIR ${cmake_utils_BINARY_DIR}/.repository/source)
    set(REPO_BINARY_DIR ${cmake_utils_BINARY_DIR}/.repository/build)
    set(ENV{PYTHONPATH} ${cmake_utils_SOURCE_DIR})
    execute_process(COMMAND ${PYTHON3_EXE} ${EXTERNALS_SCRIPT} -s ${CMAKE_CURRENT_SOURCE_DIR} -r ${REPO_SOURCE_DIR}
        RESULT_VARIABLE PROC_RES
        OUTPUT_VARIABLE PROC_STDOUT
        ERROR_VARIABLE  PROC_STDERR
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    )
    message("${PROC_STDOUT}")
    if(NOT PROC_RES EQUAL 0)
        message(FATAL_ERROR "${PROC_STDERR}")
    endif()
    add_subdirectory(${REPO_SOURCE_DIR} ${REPO_BINARY_DIR})
ENDFUNCTION()

