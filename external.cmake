
FUNCTION(INIT_EXTERNALS)
    set(options "")
    set(oneValueArgs REPODIR)
    set(multiValueArgs "")
    cmake_parse_arguments(RESOLVE_EXTERNALS "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    PYFIND(INTERP VERSION 3)
    set(EXTERNALS_SCRIPT ${cmake_utils_SOURCE_DIR}/bin/external.py)
    if(NOT INIT_EXTERNALS_REPODIR)
        set(INIT_EXTERNALS_REPODIR lib)
    endif()
    set(ENV{PYTHONPATH} ${cmake_utils_SOURCE_DIR})
    execute_process(COMMAND ${PYTHON3_EXE} ${EXTERNALS_SCRIPT} -s ${CMAKE_CURRENT_SOURCE_DIR} -r ${INIT_EXTERNALS_REPODIR}
        RESULT_VARIABLE PROC_RES
        OUTPUT_VARIABLE PROC_STDOUT
        ERROR_VARIABLE  PROC_STDERR
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
    message("${PROC_STDOUT}")
    if(NOT PROC_RES EQUAL 0)
        message(FATAL_ERROR "${PROC_STDERR}")
    endif()
    add_subdirectory(${INIT_EXTERNALS_REPODIR})
ENDFUNCTION()

