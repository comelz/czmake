# Function for SIP
# ~~~~~~~~~~~~~~
#
# ADD_SIP_MODULE (MODULE_NAME MODULE_SIP [library1, libaray2, ...])
#     Specifies a SIP file to be built into a Python module and installed.
#     MODULE_NAME is the name of Python module including any path name. (e.g.
#     os.sys, Foo.bar etc). MODULE_SIP the path and filename of the .sip file
#     to process and compile. libraryN are libraries that the Python module,
#     which is typically a shared library, should be linked to. The built
#     module will also be install into Python's site-packages directory.
#
# The behaviour of the ADD_SIP_MODULE macro can be controlled by a
# number of parameters:
#
# INCLUDES - List of directories which SIP will scan through when looking
#     for included .sip files. (Corresponds to the -I option for SIP.)
#
# TAGS - List of tags to define when running SIP. (Corresponds to the -t
#     option for SIP.)
#
# DISABLE_FEATURES - List of feature names which should be disabled
#     running SIP. (Corresponds to the -x option for SIP.)
#
# EXTRA_OPTIONS - Extra command line options which should be passed on to
#     SIP.

FUNCTION(ADD_SIP_MODULE TARGET_NAME SIP_MODULE_FILE)
    set(options "")
    set(oneValueArgs "")
    set(multiValueArgs SIP_INCLUDES INCLUDES DEFS LIBS TAGS DISABLE_FEATURES EXTRA_SOURCES EXTRA_OPTIONS)
    cmake_parse_arguments(ADD_SIP_MODULE "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    if(NOT ADD_SIP_MODULE_INCLUDES)
        set(ADD_SIP_MODULE_INCLUDES "")
    endif()
    list(APPEND ADD_SIP_MODULE_SIP_INCLUDES $ENV{SIP_MODULE_INCLUDE_PATH})
    if(UNIX)
        list(APPEND ADD_SIP_MODULE_SIP_INCLUDES /usr/share/sip)
    endif()

    find_package(PythonInterp 2 REQUIRED)
    find_package(PythonLibs 2 REQUIRED)
    list(APPEND CMAKE_MODULE_PATH ${CZMAKE_ROOT_PATH})
    find_package(SIP REQUIRED)

    GET_FILENAME_COMPONENT(FPATH ${SIP_MODULE_FILE} REALPATH)
    file(RELATIVE_PATH _module_path ${CMAKE_SOURCE_DIR} ${FPATH})
    GET_FILENAME_COMPONENT(_module_path ${_module_path} DIRECTORY)

    set(SIP_BUILD_DIR ${CMAKE_BINARY_DIR}/sip/${_module_path})
    FILE(MAKE_DIRECTORY ${SIP_BUILD_DIR})

    SET(_sip_includes)
    FOREACH (_inc ${ADD_SIP_MODULE_SIP_INCLUDES})
        GET_FILENAME_COMPONENT(_abs_inc ${_inc} ABSOLUTE)
        LIST(APPEND _sip_includes -I ${_abs_inc})
    ENDFOREACH (_inc )

    SET(_sip_tags)
    FOREACH (_tag ${ADD_SIP_MODULE_TAGS})
        LIST(APPEND _sip_tags -t ${_tag})
    ENDFOREACH (_tag)

    SET(_sip_x)
    FOREACH(_x ${ADD_SIP_MODULE_DISABLE_FEATURES})
        LIST(APPEND _sip_x -x ${_x})
    ENDFOREACH()

    get_filename_component(FNAME ${SIP_MODULE_FILE} NAME_WE)
    get_property(DDEPS DIRECTORY PROPERTY CMAKE_CONFIGURE_DEPENDS )
    list(APPEND DDEPS ${SIP_MODULE_FILE} ${ADD_SIP_MODULE_EXTRA_SOURCES})
    list(REMOVE_DUPLICATES DDEPS)
    set_property(DIRECTORY PROPERTY CMAKE_CONFIGURE_DEPENDS ${DDEPS})
    SET(SIP_BUILD_FILE ${SIP_BUILD_DIR}/${FNAME}.sbf)
    execute_process(
        COMMAND ${SIP_EXECUTABLE} ${_sip_tags} ${_sip_x} ${ADD_SIP_MODULE_EXTRA_OPTIONS} ${_sip_includes} -b ${SIP_BUILD_FILE} ${SIP_MODULE_FILE}
    )
    file(STRINGS ${SIP_BUILD_FILE} LIBRARY_NAME REGEX "^ *target *= *([a-zA-Z0-9_-]+)")
    string(REGEX MATCH "^ *target *= *([a-zA-Z0-9_-]+)" LIBRARY_NAME "${LIBRARY_NAME}")
    set(LIBRARY_NAME ${CMAKE_MATCH_1})

    file(STRINGS ${SIP_BUILD_FILE} SBF REGEX "^ *sources *= *")
    string(REGEX REPLACE "^ *sources *= *" "" SBF "${SBF}")
    string(REGEX MATCHALL "[^ ]+" SBF "${SBF}")
    set(SIP_GENERATED_SOURCES)
    FOREACH(sip_generated_file ${SBF})
        list(APPEND SIP_GENERATED_SOURCES ${SIP_BUILD_DIR}/${sip_generated_file})
    ENDFOREACH()
    ADD_CUSTOM_COMMAND(
        OUTPUT ${SIP_GENERATED_SOURCES}
        COMMAND ${SIP_EXECUTABLE} ${_sip_tags} ${_sip_x} ${ADD_SIP_MODULE_EXTRA_OPTIONS} -c ${SIP_BUILD_DIR} ${_sip_includes} ${SIP_MODULE_FILE}
        DEPENDS ${SIP_MODULE_FILE} ${ADD_SIP_MODULE_EXTRA_SOURCES}
    )
    # not sure if type MODULE could be uses anywhere, limit to cygwin for now
    IF(CYGWIN OR APPLE)
        ADD_LIBRARY(${TARGET_NAME} MODULE EXCLUDE_FROM_ALL ${SIP_GENERATED_SOURCES} )
    ELSE()
        ADD_LIBRARY(${TARGET_NAME} SHARED EXCLUDE_FROM_ALL ${SIP_GENERATED_SOURCES})
    ENDIF()

    target_include_directories(${TARGET_NAME} PRIVATE ${PYTHON_INCLUDE_DIRS} ${SIP_INCLUDE_DIR} ${ADD_SIP_MODULE_INCLUDES})
    if(ADD_SIP_MODULE_DEFS)
        target_compile_definitions(${TARGET_NAME} PRIVATE ${ADD_SIP_MODULE_DEFS})
    endif()
    TARGET_LINK_LIBRARIES(${TARGET_NAME} ${ADD_SIP_MODULE_LIBS} ${PYTHON_LIBRARIES})
    IF(APPLE)
        SET_TARGET_PROPERTIES(${TARGET_NAME} PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
    ENDIF(APPLE)
    SET_TARGET_PROPERTIES(${TARGET_NAME} PROPERTIES PREFIX "" OUTPUT_NAME ${LIBRARY_NAME})

    IF(WIN32)
      SET_TARGET_PROPERTIES(${TARGET_NAME} PROPERTIES SUFFIX ".pyd")
    ENDIF (WIN32)
ENDFUNCTION()
