FUNCTION(RESOLVE_DEPENDENCIES)
    set(options "")
    set(oneValueArgs REPODIR)
    set(multiValueArgs "")
    cmake_parse_arguments(RESOLVE_EXTERNALS "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    PYFIND(VERSIONS 3 SUFFIX 3 REQUIRED)
    if(NOT CZMAKE_REPODIR)
        set(CZMAKE_REPODIR ${CMAKE_BINARY_DIR}/czmake)
    endif()
    set(CACHE_FILE "${CZMAKE_REPODIR}/tmpcache.txt")
    get_cmake_property(cache_keys CACHE_VARIABLES)
    list (SORT cache_keys)
    file(WRITE "${CACHE_FILE}" "")
    foreach (cache_key ${cache_keys})
        file(APPEND "${CACHE_FILE}" "${cache_key} = ${${cache_key}}\n")
    endforeach()
    execute_process(COMMAND ${PYTHON_EXECUTABLE_3} -m czmake.dependency_solver -b ${CMAKE_BINARY_DIR} -s ${CMAKE_CURRENT_SOURCE_DIR} -r ${CZMAKE_REPODIR} -c ${CACHE_FILE}
        RESULT_VARIABLE PROC_RES
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
    message("${PROC_STDOUT}")
    if(NOT PROC_RES EQUAL 0)
        message(FATAL_ERROR "Error resolving project dependencies")
    endif()
    include(${CZMAKE_REPODIR}/dependency_list.cmake)
ENDFUNCTION()

