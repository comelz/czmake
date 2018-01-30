FUNCTION(IPO_CHECK)
    if(${CMAKE_VERSION} VERSION_GREATER "3.9" AND
            NOT DEFINED CMAKE_INTERPROCEDURAL_OPTIMIZATION
            AND (CMAKE_BUILD_TYPE STREQUAL Release OR CMAKE_BUILD_TYPE STREQUAL RelWithDebInfo))
        include(CheckIPOSupported)
        check_ipo_supported(RESULT CMAKE_INTERPROCEDURAL_OPTIMIZATION)
        if(NOT CMAKE_INTERPROCEDURAL_OPTIMIZATION)
            message(WARNING "interprocedural optimization is not supported with this compiler")
        endif()
        set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ${CMAKE_INTERPROCEDURAL_OPTIMIZATION} CACHE BOOL "Use the link time optimization feature of the compiler")
    endif()
ENDFUNCTION()

FUNCTION(CREATE_TARGET NAME)
    set(options LIB EXE WIN32 ALL STATIC SHARED INSTALL)
    set(oneValueArgs "")
    set(multiValueArgs
        PRIVATE_DEFS
        PUBLIC_DEFS
        PRIVATE_INCLUDES
        PUBLIC_INCLUDES
        PRIVATE_LIBS
        PUBLIC_LIBS
        PROPERTIES
        SOURCES
    )

    cmake_parse_arguments(CREATE_TARGET "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    IPO_CHECK()

    if(NOT CREATE_TARGET_ALL)
        set(EXCLUDE EXCLUDE_FROM_ALL)
    endif()
    set(TGTS)
    if(CREATE_TARGET_LIB)
        set(TYPES)
        if(CREATE_TARGET_STATIC)
            list(APPEND TYPES STATIC)
        endif()
        if(CREATE_TARGET_SHARED)
            list(APPEND TYPES SHARED)
        endif()
        if(NOT CREATE_TARGET_STATIC AND NOT CREATE_TARGET_SHARED)
            list(APPEND TYPES STATIC SHARED)
        endif()
        foreach(TYPE ${TYPES})
            string(TOLOWER ${TYPE} SUFFIX)
            set(LIBRARY_TARGET ${NAME}_${SUFFIX})
            add_library(${LIBRARY_TARGET} ${TYPE} ${EXCLUDE} ${CREATE_TARGET_SOURCES})
            list(APPEND TGTS ${LIBRARY_TARGET})
            if(CREATE_TARGET_PRIVATE_LIBS)
                set(LIBS)
                foreach(LIB ${CREATE_TARGET_PRIVATE_LIBS})
                    if(TARGET ${LIB}_${SUFFIX})
                        list(APPEND LIBS ${LIB}_${SUFFIX})
                    else()
                        list(APPEND LIBS ${LIB})
                    endif()
                endforeach()
                target_link_libraries(${LIBRARY_TARGET} PRIVATE ${LIBS})
            endif()
            if(CREATE_TARGET_PUBLIC_LIBS)
                set(LIBS)
                foreach(LIB ${CREATE_TARGET_PUBLIC_LIBS})
                    if(TARGET ${LIB}_${SUFFIX})
                        list(APPEND LIBS ${LIB}_${SUFFIX})
                    else()
                        list(APPEND LIBS ${LIB})
                    endif()
                endforeach()
                target_link_libraries(${LIBRARY_TARGET} PUBLIC ${LIBS})
            endif()
            if(CREATE_TARGET_INSTALL)
                export(TARGETS ${LIBRARY_TARGET} FILE ${LIBRARY_TARGET}Config.cmake)
                install(EXPORT ${LIBRARY_TARGET}Config DESTINATION share/cmake/${LIBRARY_TARGET})
                install(TARGETS ${LIBRARY_TARGET} EXPORT ${LIBRARY_TARGET}Config
                    INCLUDES DESTINATION include
                    ARCHIVE  DESTINATION lib
                    LIBRARY  DESTINATION lib
                    RUNTIME  DESTINATION bin
                    ${EXCLUDE})
            endif()
        endforeach()
        if(TYPES)
            list(GET TYPES 0 TYPE)
            string(TOLOWER ${TYPE} SUFFIX)
            add_library(${NAME} ALIAS ${NAME}_${SUFFIX})
        endif()
    elseif(CREATE_TARGET_EXE)
        if(CREATE_TARGET_WIN32)
            set(TYPE WIN32)
        endif()
        add_executable(${NAME} ${TYPE} ${EXCLUDE} ${CREATE_TARGET_SOURCES})
        list(APPEND TGTS ${NAME})
        if(CREATE_TARGET_PRIVATE_LIBS)
            target_link_libraries(${NAME} PRIVATE ${CREATE_TARGET_PRIVATE_LIBS})
        endif()
        if(CREATE_TARGET_PUBLIC_LIBS)
            target_link_libraries(${NAME} PUBLIC ${CREATE_TARGET_PUBLIC_LIBS})
        endif()
    endif()

    foreach(TGT ${TGTS})
        if(CREATE_TARGET_PRIVATE_INCLUDES)
            target_include_directories(${TGT} PRIVATE ${CREATE_TARGET_PRIVATE_INCLUDES})
        endif()
        if(CREATE_TARGET_PUBLIC_INCLUDES)
            target_include_directories(${TGT} PUBLIC ${CREATE_TARGET_PUBLIC_INCLUDES})
        endif()
        if(CREATE_TARGET_PRIVATE_DEFS)
            target_compile_definitions(${TGT} PRIVATE ${CREATE_TARGET_PRIVATE_DEFS})
        endif()
        if(CREATE_TARGET_PUBLIC_DEFS)
            target_compile_definitions(${TGT} PUBLIC ${CREATE_TARGET_PUBLIC_DEFS})
        endif()
        if(CREATE_TARGET_PROPERTIES)
            set_target_properties(${TGT} PROPERTIES ${CREATE_TARGET_PROPERTIES})
        endif()
        set_target_properties(${TGT} PROPERTIES OUTPUT_NAME ${NAME})
        if(CMAKE_INTERPROCEDURAL_OPTIMIZATION)
            set_target_properties(${TGT} PROPERTIES INTERPROCEDURAL_OPTIMIZATION ${CMAKE_INTERPROCEDURAL_OPTIMIZATION})
        endif()
    endforeach()
ENDFUNCTION()

FUNCTION(CREATE_EXECUTABLE NAME)
    CREATE_TARGET(${NAME} EXE ${ARGN})
ENDFUNCTION()

FUNCTION(CREATE_LIBRARY NAME)
    CREATE_TARGET(${NAME} LIB ${ARGN})
ENDFUNCTION()

FUNCTION(CREATE_PYLIBRARY NAME)
    set(options STATIC SHARED)
    set(oneValueArgs "")
    set(multiValueArgs
        PRIVATE_DEFS
        PUBLIC_DEFS
        PRIVATE_INCLUDES
        PUBLIC_INCLUDES
        PRIVATE_LIBS
        PUBLIC_LIBS
        PROPERTIES
        SOURCES
    )
    cmake_parse_arguments(CREATE_PYLIBRARY "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    CREATE_LIBRARY(${NAME} ${ARGN})

    set(TYPE "")
    if(CREATE_PYLIBRARY_STATIC)
        set(TYPE STATIC)
    elseif(CREATE_PYLIBRARY_SHARED)
        set(TYPE SHARED)
    endif()
    if(${TYPE} STREQUAL "STATIC")
        CREATE_LIBRARY(py_${NAME} ${ARGN})
        set_target_properties(py_${NAME} PROPERTIES POSITION_INDEPENTENT_CODE ON)
    else()
        add_library(py_${NAME} ALIAS ${NAME})
    endif()
ENDFUNCTION()
