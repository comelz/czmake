FUNCTION(CREATE_LIBRARY NAME)
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

    cmake_parse_arguments(CREATE_LIBRARY "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    set(TYPE "")
    if(CREATE_LIBRARY_STATIC)
        set(TYPE STATIC)
    elseif(CREATE_LIBRARY_SHARED)
        set(TYPE SHARED)
    endif()
    add_library(${NAME} ${TYPE} EXCLUDE_FROM_ALL ${CREATE_LIBRARY_SOURCES})
    if(CREATE_LIBRARY_PRIVATE_INCLUDES)
        target_include_directories(${NAME} PRIVATE ${CREATE_LIBRARY_PRIVATE_INCLUDES})
    endif()
    if(CREATE_LIBRARY_PUBLIC_INCLUDES)
        target_include_directories(${NAME} PUBLIC ${CREATE_LIBRARY_PUBLIC_INCLUDES})
    endif()
    if(CREATE_LIBRARY_PRIVATE_DEFS)
        target_compile_definitions(${NAME} PRIVATE ${CREATE_LIBRARY_PRIVATE_DEFS})
    endif()
    if(CREATE_LIBRARY_PUBLIC_DEFS)
        target_compile_definitions(${NAME} PUBLIC ${CREATE_LIBRARY_PUBLIC_DEFS})
    endif()
    if(CREATE_LIBRARY_PRIVATE_LIBS)
        target_link_libraries(${NAME} PRIVATE ${CREATE_LIBRARY_PRIVATE_LIBS})
    endif()
    if(CREATE_LIBRARY_PUBLIC_LIBS)
        target_link_libraries(${NAME} PUBLIC ${CREATE_LIBRARY_PUBLIC_LIBS})
    endif()
    if(CREATE_LIBRARY_PROPERTIES)
        set_target_properties(${NAME} PROPERTIES ${CREATE_LIBRARY_PROPERTIES})
    endif()
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