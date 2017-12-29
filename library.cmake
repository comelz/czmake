FUNCTION(CREATE_TARGET NAME)
    set(options LIB EXE WIN32 ALL STATIC SHARED)
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

    if(NOT CREATE_TARGET_ALL)
        set(EXCLUDE EXCLUDE_FROM_ALL)
    endif()
    if(CREATE_TARGET_LIB)
        set(TYPE)
        if(CREATE_TARGET_STATIC)
            set(TYPE STATIC)
        elseif(CREATE_TARGET_SHARED)
            set(TYPE SHARED)
        endif()
        add_library(${NAME} ${TYPE} ${EXCLUDE} ${CREATE_TARGET_SOURCES})
    elseif(CREATE_TARGET_EXE)
        if(CREATE_TARGET_WIN32)
            set(TYPE WIN32)
        endif()
        add_executable(${NAME} ${TYPE} ${EXCLUDE} ${CREATE_TARGET_SOURCES})
    endif()

    if(CREATE_TARGET_PRIVATE_INCLUDES)
        target_include_directories(${NAME} PRIVATE ${CREATE_TARGET_PRIVATE_INCLUDES})
    endif()
    if(CREATE_TARGET_PUBLIC_INCLUDES)
        target_include_directories(${NAME} PUBLIC ${CREATE_TARGET_PUBLIC_INCLUDES})
    endif()
    if(CREATE_TARGET_PRIVATE_DEFS)
        target_compile_definitions(${NAME} PRIVATE ${CREATE_TARGET_PRIVATE_DEFS})
    endif()
    if(CREATE_TARGET_PUBLIC_DEFS)
        target_compile_definitions(${NAME} PUBLIC ${CREATE_TARGET_PUBLIC_DEFS})
    endif()
    if(CREATE_TARGET_PRIVATE_LIBS)
        target_link_libraries(${NAME} PRIVATE ${CREATE_TARGET_PRIVATE_LIBS})
    endif()
    if(CREATE_TARGET_PUBLIC_LIBS)
        target_link_libraries(${NAME} PUBLIC ${CREATE_TARGET_PUBLIC_LIBS})
    endif()
    if(CREATE_TARGET_PROPERTIES)
        set_target_properties(${NAME} PROPERTIES ${CREATE_TARGET_PROPERTIES})
    endif()
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
