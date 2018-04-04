FUNCTION(RESOLVE_DEPENDENCIES)
    set(options "")
    set(oneValueArgs REPODIR)
    set(multiValueArgs "")
    cmake_parse_arguments(RESOLVE_EXTERNALS "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    PYFIND(VERSIONS 3 SUFFIX 3 REQUIRED)
    set(EXTERNALS_SCRIPT ${CZMAKE_ROOT_PATH}/dependency_solver.py)
    if(NOT INIT_EXTERNALS_REPODIR)
        set(INIT_EXTERNALS_REPODIR lib)
    endif()
    set(ENV{PYTHONPATH} ${CZMAKE_ROOT_PATH})
    set(CACHE_FILE "${INIT_EXTERNALS_REPODIR}/tmpcache.txt")
    get_cmake_property(_variableNames CACHE_VARIABLES)
    list (SORT _variableNames)
    foreach (_variableName ${_variableNames})
        file(APPEND "${CACHE_FILE}" "${_variableName} = ${${_variableName}}\n")
    endforeach()
    execute_process(COMMAND ${PYTHON_EXECUTABLE_3} ${EXTERNALS_SCRIPT} -b ${CMAKE_BINARY_DIR} -s ${CMAKE_CURRENT_SOURCE_DIR} -r ${INIT_EXTERNALS_REPODIR} -c ${CACHE_FILE}
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

