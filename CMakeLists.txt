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
        message(STATUS "${PROC_STDOUT}")
        if(NOT PROC_RES EQUAL 0)
            message(FATAL_ERROR "${PROC_STDERR}")
        endif()
    endif()
ENDFUNCTION()

FUNCTION(MINIFY TARGET)
    set(options STRIP UPX KEEP_ORIGINAL)
    set(oneValueArgs "")
    set(multiValueArgs "")

    cmake_parse_arguments(MINIFY "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    add_custom_command(OUTPUT ${TARGET}_unstripped_timestamp.txt
        COMMAND cmake -E touch ${TARGET}_unstripped_timestamp.txt
        COMMAND cmake -E copy_if_different $<TARGET_FILE:${TARGET}> $<TARGET_FILE:${TARGET}>.unstripped
        DEPENDS $<TARGET_FILE:${TARGET}>
        COMMENT "Archiving uncompressed ${TARGET}"
    )
    add_custom_command(OUTPUT ${TARGET}_stripped_timestamp.txt
        COMMAND cmake -E touch ${TARGET}_stripped_timestamp.txt
        COMMAND ${CMAKE_STRIP} -s $<TARGET_FILE:${TARGET}>
        DEPENDS $<TARGET_FILE:${TARGET}>
        COMMENT "Stripping ${TARGET}"
    )
    add_custom_command(OUTPUT ${TARGET}_compressed_timestamp.txt
        COMMAND cmake -E touch ${TARGET}_compressed_timestamp.txt
        COMMAND upx --best $<TARGET_FILE:${TARGET}>
        DEPENDS $<TARGET_FILE:${TARGET}>
        COMMENT "Compressing ${TARGET}"
        )
    set(LAST_TARGET ${TARGET})
    if(MINIFY_KEEP_ORIGINAL)
        add_custom_target(${TARGET}_unstripped ALL
            DEPENDS ${LAST_TARGET}
            SOURCES ${TARGET}_unstripped_timestamp.txt
        )
        set(LAST_TARGET ${TARGET}_unstripped)
    endif()
    if(MINIFY_STRIP)
        add_custom_target(${TARGET}_stripped ALL
            DEPENDS ${LAST_TARGET}
            SOURCES ${TARGET}_stripped_timestamp.txt
        )
        set(LAST_TARGET ${TARGET}_stripped)
    endif()
    if(MINIFY_UPX)
        add_custom_target(${TARGET}_compressed ALL
            DEPENDS ${LAST_TARGET}
            SOURCES ${TARGET}_compressed_timestamp.txt
        )
        set(LAST_TARGET ${TARGET}_compressed)
    endif()
ENDFUNCTION()
