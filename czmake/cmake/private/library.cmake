MACRO(SETUP_STANDARD_FLAGS)
    set(options CPP_EXT C_EXT)
    set(oneValueArgs C CPP)
    set(multiValueArgs "")

    cmake_parse_arguments(SETUP_STANDARD_FLAGS "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    set(CMAKE_CXX_EXTENSIONS OFF CACHE BOOL "")
    if(SETUP_STANDARD_FLAGS_C)
        set(CMAKE_C_STANDARD ${SETUP_STANDARD_FLAGS_C} CACHE INT "")
    else()
        set(CMAKE_C_STANDARD 99 CACHE INT "")
    endif()

    if(SETUP_STANDARD_FLAGS_CXX)
        set(CMAKE_CXX_STANDARD ${SETUP_STANDARD_FLAGS_CXX} CACHE INT "")
    else()
        set(CMAKE_CXX_STANDARD 11 CACHE INT "")
    endif()

    if(SETUP_STANDARD_FLAGS_C_EXT)
        set(CMAKE_C_EXTENSIONS ON CACHE BOOL "")
    else()
        set(CMAKE_C_EXTENSIONS OFF CACHE BOOL "")
    endif()

    if(SETUP_STANDARD_FLAGS_CXX_EXT)
        set(CMAKE_CXX_EXTENSIONS ON CACHE BOOL "")
    else()
        set(CMAKE_CXX_EXTENSIONS OFF CACHE BOOL "")
    endif()

    if(${CMAKE_VERSION} VERSION_GREATER "3.9" OR ${CMAKE_VERSION} VERSION_EQUAL "3.9")
        include(CheckIPOSupported)
        check_ipo_supported(RESULT IPO)
        if(NOT IPO)
            message(STATUS "Interprocedural optimization is not supported with this compiler")
        endif()
        option(CMAKE_INTERPROCEDURAL_OPTIMIZATION "Use the link time optimization feature of the compiler" OFF)
    endif()

    if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        option(DEBUG_STL "Enable usage of debug STL (gcc-only)" OFF)
        option(TRAP_OVERFLOW "Enable overflow trapping (gcc-only)" OFF)
        option(STATIC_BUILD "Create statically linked executables" OFF)
        set(BUILD_FLAGS -Wall -Wextra -pedantic -Wsuggest-attribute=format -Wcast-align -Wlogical-op -Wno-multichar)
      
        if(CMAKE_SIZEOF_VOID_P EQUAL 4)
            SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${GCC_COMMON_OPTIONS} -Wno-narrowing")
            SET(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3 -fomit-frame-pointer")
            SET(CMAKE_C_FLAGS_RELWITHDEBINFO "${CMAKE_C_FLAGS_RELWITHDEBINFO} -O3 -fno-omit-frame-pointer")
            SET(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -fno-omit-frame-pointer")
            
            SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wnon-virtual-dtor ${GCC_COMMON_OPTIONS}")
            SET(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -fomit-frame-pointer")
            SET(CMAKE_CXX_FLAGS_RELWITHDEBINFO "${CMAKE_CXX_FLAGS_RELWITHDEBINFO} -O3 -fno-omit-frame-pointer")
            SET(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -fno-omit-frame-pointer")
        elseif(CMAKE_SIZEOF_VOID_P EQUAL 8)
            SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${GCC_COMMON_OPTIONS} -Wno-narrowing")
            SET(CMAKE_C_FLAGS_RELWITHDEBINFO "${CMAKE_C_FLAGS_RELWITHDEBINFO} -O3")
            SET(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG}")
            
            SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wnon-virtual-dtor ${GCC_COMMON_OPTIONS}")
            SET(CMAKE_CXX_FLAGS_RELWITHDEBINFO "${CMAKE_CXX_FLAGS_RELWITHDEBINFO} -O3")
            SET(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}")
        endif()
       
        if(UNIX)
            list(APPEND BUILD_FLAGS -pthread)
            link_libraries(-pthread)
        endif()
        if(STATIC_BUILD)
            set(CMAKE_EXE_LINKER_FLAGS "-static")
        endif()
        if(WIN32)
            add_definitions(-DNOMINMAX)
        endif()

        if(DEBUG_STL)
            add_definitions(-D_GLIBCXX_DEBUG)
        endif()
        if(TRAP_OVERFLOW)
            list(APPEND BUILD_FLAGS -ftrapv)
        endif()
        if(CMAKE_INTERPROCEDURAL_OPTIMIZATION)
            list(APPEND BUILD_FLAGS -fuse-linker-plugin)
        endif()
        add_compile_options(${BUILD_FLAGS})
    endif()
ENDMACRO()

FUNCTION(CREATE_TARGET NAME)
    set(options LIB EXE WIN32 ALL STATIC INTERFACE SHARED INSTALL STRIP KEEP_UNSTRIPPED)
    set(oneValueArgs "")
    set(multiValueArgs
        PRIVATE_DEFS
        INTERFACE_DEFS
        PUBLIC_DEFS
        PRIVATE_INCLUDES
        INTERFACE_INCLUDES
        PUBLIC_INCLUDES
        PRIVATE_LIBS
        INTERFACE_LIBS
        PUBLIC_LIBS
        PRIVATE_COMPILE_OPTIONS
        INTERFACE_COMPILE_OPTIONS
        PUBLIC_COMPILE_OPTIONS
        PROPERTIES
        SOURCES
        DEPENDS
    )

    cmake_parse_arguments(CREATE_TARGET "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(NOT CREATE_TARGET_ALL)
        set(EXCLUDE EXCLUDE_FROM_ALL)
    endif()
    set(TGTS)
    if(CREATE_TARGET_LIB)
        set(TYPE)
        if(CREATE_TARGET_STATIC)
            set(TYPE STATIC)
        elseif(CREATE_TARGET_INTERFACE)
            set(TYPE INTERFACE)
        elseif(CREATE_TARGET_SHARED)
            set(TYPE SHARED)
        endif()
        if("${TYPE}" STREQUAL INTERFACE)
            add_library(${NAME} ${TYPE})
            target_sources(${LIBRARY_TARGET} ${TYPE} ${CREATE_TARGET_SOURCES})
        else()
            add_library(${NAME} ${TYPE} ${EXCLUDE} ${CREATE_TARGET_SOURCES})
            set_target_properties(${TGT} PROPERTIES OUTPUT_NAME ${NAME})
        endif()
        if(CREATE_TARGET_INSTALL)
            export(TARGETS ${NAME} FILE ${NAME}Config.cmake)
            install(EXPORT ${NAME}Config DESTINATION share/cmake/${NAME})
            install(TARGETS ${NAME} EXPORT ${NAME}Config
                INCLUDES DESTINATION include
                ARCHIVE  DESTINATION lib
                LIBRARY  DESTINATION lib
                RUNTIME  DESTINATION bin
                ${EXCLUDE})
        endif()
    elseif(CREATE_TARGET_EXE)
        if(CREATE_TARGET_WIN32)
            set(TYPE WIN32)
        endif()
        add_executable(${NAME} ${TYPE} ${EXCLUDE} ${CREATE_TARGET_SOURCES})
    endif()
    foreach(XFACE_TYPE PUBLIC PRIVATE)
        if(CREATE_TARGET_${XFACE_TYPE}_LIBS)
            target_link_libraries(${NAME} ${XFACE_TYPE} ${CREATE_TARGET_${XFACE_TYPE}_LIBS})
        endif()
        if(CREATE_TARGET_${XFACE_TYPE}_INCLUDES)
            target_include_directories(${NAME} ${XFACE_TYPE} ${CREATE_TARGET_${XFACE_TYPE}_INCLUDES})
        endif()
        if(CREATE_TARGET_${XFACE_TYPE}_DEFS)
            target_compile_definitions(${NAME} ${XFACE_TYPE} ${CREATE_TARGET_${XFACE_TYPE}_DEFS})
        endif()
        if(CREATE_TARGET_${XFACE_TYPE}_COMPILE_OPTIONS)
            target_compile_options(${NAME} ${XFACE_TYPE} ${CREATE_TARGET_${XFACE_TYPE}_COMPILE_OPTIONS})
        endif()
    endforeach()
    if(CREATE_TARGET_PROPERTIES)
        set_target_properties(${NAME} PROPERTIES ${CREATE_TARGET_PROPERTIES})
    endif()
    if(CMAKE_INTERPROCEDURAL_OPTIMIZATION)
        set_target_properties(${NAME} PROPERTIES INTERPROCEDURAL_OPTIMIZATION ${CMAKE_INTERPROCEDURAL_OPTIMIZATION})
    endif()
    if(CREATE_TARGET_STRIP)
        if(CREATE_TARGET_KEEP_UNSTRIPPED)
            set(KEEP_UNSTRIPPED_COMMAND COMMAND cmake -E copy_if_different $<TARGET_FILE:${NAME}> $<TARGET_FILE:${NAME}>.unstripped)
        endif()
        add_custom_command(TARGET ${NAME} POST_BUILD
            ${KEEP_UNSTRIPPED_COMMAND}
            COMMAND ${CMAKE_STRIP} -s $<TARGET_FILE:${NAME}>
            DEPENDS $<TARGET_FILE:${NAME}>
            COMMENT "Stripping ${NAME}"
        )
    endif()
    if(CREATE_TARGET_DEPENDS)
        add_dependencies(${NAME} ${CREATE_TARGET_DEPENDS})
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
