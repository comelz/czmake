# Macros for SIP
# ~~~~~~~~~~~~~~
# Copyright (c) 2007, Simon Edwards <simon@simonzone.com>
# Redistribution and use is allowed according to the terms of the BSD license.
# For details see the accompanying COPYING-CMAKE-SCRIPTS file.
#
# SIP website: http://www.riverbankcomputing.co.uk/sip/index.php
#
# This file defines the following macros:
#
# ADD_SIP_MODULE (MODULE_NAME MODULE_SIP [library1, libaray2, ...])
#     Specifies a SIP file to be built into a Python module and installed.
#     MODULE_NAME is the name of Python module including any path name. (e.g.
#     os.sys, Foo.bar etc). MODULE_SIP the path and filename of the .sip file
#     to process and compile. libraryN are libraries that the Python module,
#     which is typically a shared library, should be linked to. The built
#     module will also be install into Python's site-packages directory.
#
# The behaviour of the ADD_SIP_PYTHON_MODULE macro can be controlled by a
# number of variables:
#
# INCLUDES - List of directories which SIP will scan through when looking
#     for included .sip files. (Corresponds to the -I option for SIP.)
#
# TAGS - List of tags to define when running SIP. (Corresponds to the -t
#     option for SIP.)
#
# SPLIT - An integer which defines the number of parts the C++ code
#     of each module should be split into. Defaults to 8. (Corresponds to the
#     -j option for SIP.)
#
# DISABLE_FEATURES - List of feature names which should be disabled
#     running SIP. (Corresponds to the -x option for SIP.)
#
# EXTRA_OPTIONS - Extra command line options which should be passed on to
#     SIP.


FUNCTION(ADD_SIP_MODULE SIP_MODULE_FILE)
    set(options "")
    set(oneValueArgs NAME SOURCES INCLUDES LIBS TARGET_NAME SPLIT EXTRA_OPTIONS)
    set(multiValueArgs TAGS DISABLE_FEATURES)
    cmake_parse_arguments(ADD_SIP_MODULE "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    if(NOT ADD_SIP_MODULE_NAME)
        get_filename_component(ADD_SIP_MODULE_NAME ${SIP_MODULE_FILE} NAME_WE)
    endif()
    if(NOT ADD_SIP_MODULE_TARGET_NAME)
        STRING(REPLACE "." "_" _logical_name ${ADD_SIP_MODULE_NAME})
        SET(ADD_SIP_MODULE_TARGET_NAME "sip_module_${_logical_name}")
    endif()
    if(NOT ADD_SIP_MODULE_TARGET_SPLIT)
        set(ADD_SIP_MODULE_TARGET_SPLIT 8)
    endif()
    if(NOT ADD_SIP_MODULE_TARGET_INCLUDES)
        set(ADD_SIP_MODULE_TARGET_INCLUDES "")
    endif()
    if(UNIX)
        list(APPEND ADD_SIP_MODULE_TARGET_INCLUDES /usr/share/sip)
    endif()

    find_package(PythonInterp 2 REQUIRED)
    find_package(PythonLibs 2 REQUIRED)
    IF(UNIX)
        find_package(SIP REQUIRED)
        if(NOT APPLE)
            set(CMAKE_MODULE_PATH "/usr/share/apps/cmake/modules/")
        endif()
    endif()

    STRING(REPLACE "." "/" _x ${ADD_SIP_MODULE_NAME})
    GET_FILENAME_COMPONENT(_parent_module_path ${_x}  PATH)
    GET_FILENAME_COMPONENT(_child_module_name ${_x} NAME)

    GET_FILENAME_COMPONENT(FPATH ${SIP_MODULE_FILE} REALPATH)
    file(RELATIVE_PATH _module_path ${CMAKE_SOURCE_DIR} ${FPATH})
    GET_FILENAME_COMPONENT(_module_path ${_module_path} DIRECTORY)

    FILE(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/sip/${_module_path})    # Output goes in this dir.

    SET(_sip_includes)
    FOREACH (_inc ${ADD_SIP_MODULE_TARGET_INCLUDES})
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
    SET(_message "-DMESSAGE=Generating CPP code for module ${MODULE_NAME}")
    SET(_sip_output_files)
    FOREACH(CONCAT_NUM RANGE 0 ${ADD_SIP_MODULE_TARGET_SPLIT} )
        IF( ${CONCAT_NUM} LESS ${ADD_SIP_MODULE_TARGET_SPLIT} )
            list(APPEND _sip_output_files ${CMAKE_CURRENT_BINARY_DIR}/${_module_path}/sip${FNAME}part${CONCAT_NUM}.cpp)
        ENDIF( ${CONCAT_NUM} LESS ${ADD_SIP_MODULE_TARGET_SPLIT})
    ENDFOREACH(CONCAT_NUM RANGE 0 ${ADD_SIP_MODULE_TARGET_SPLIT})
    ADD_CUSTOM_COMMAND(
        OUTPUT ${_sip_output_files}
        COMMENT ${message}
        COMMAND ${SIP_EXECUTABLE} ${_sip_tags} ${_sip_x} ${ADD_SIP_MODULE_EXTRA_OPTIONS} -j ${ADD_SIP_MODULE_TARGET_SPLIT} -c ${CMAKE_CURRENT_BINARY_DIR}/${_module_path} ${_sip_includes} ${SIP_MODULE_FILE}
        DEPENDS ${SIP_MODULE_FILE} ${ADD_SIP_MODULE_SOURCES}
    )
    # not sure if type MODULE could be uses anywhere, limit to cygwin for now
    IF(CYGWIN OR APPLE)
        ADD_LIBRARY(${ADD_SIP_MODULE_TARGET_NAME} MODULE ${_sip_output_files} )
    ELSE()
        ADD_LIBRARY(${ADD_SIP_MODULE_TARGET_NAME} SHARED ${_sip_output_files})
    ENDIF()

    target_include_directories(${ADD_SIP_MODULE_TARGET_NAME} PRIVATE ${SIP_INCLUDE_DIR})
    TARGET_LINK_LIBRARIES(${ADD_SIP_MODULE_TARGET_NAME} ${ADD_SIP_MODULE_LIBS} ${PYTHON_LIBRARIES})
    IF(APPLE)
        SET_TARGET_PROPERTIES(${ADD_SIP_MODULE_TARGET_NAME} PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
    ENDIF(APPLE)
    SET_TARGET_PROPERTIES(${ADD_SIP_MODULE_TARGET_NAME} PROPERTIES PREFIX "" OUTPUT_NAME ${ADD_SIP_MODULE_NAME})

    IF(WIN32)
      SET_TARGET_PROPERTIES(${ADD_SIP_MODULE_TARGET_NAME} PROPERTIES SUFFIX ".pyd")
    ENDIF (WIN32)

    INSTALL(TARGETS ${ADD_SIP_MODULE_TARGET_NAME} DESTINATION "${PYTHON_SITE_PACKAGES_DIR}/${_parent_module_path}")

ENDFUNCTION()
