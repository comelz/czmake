CZMake Buildsystem
==================

Overview
--------
A C/C++ buildsystem with modules dependency management. 
It has the following features:

* External modules have to be **Subversion** or **Git** projects at the moment (but it can be extended easily to support other    VCSs or even HTTP download of tar archives) and can be floating (always up-to-date using the last revision/commit) or freezed (always using the same revision/commit). 
* Modules dependency management: if you use module A and module B which both requires module C you don't have to tell the buildsystem you also need S, it is downloaded and added automatically to your CMake project exactly once and at the right moment (before A and B)
* CMake cache variables management: you need module ``A`` that has a CMake option to build with feature ``X``, ``A`` depends on ``B`` which has another CMake option to build with feature ``Y``, to build ``A`` with ``X`` you also need to build ``B`` with ``Y`` but if you don't need ``A`` with X you may also not need B with ``Y``. CZMake will automatically enable feature Y when you enable feature X
* Optional dependencies: you need module A that has a CMake option to build with feature X, in that case A depends on B. CZMake will download and add B only if you enable X.

Installation
------------
czmake is written in python 3, all you need is a working python3 installation with pip and run this from a terminal:

.. code:: bash

  pip install --user git+https://github.com/comelz/czmake.git

you may have to replace ``pip`` with the absolute path to your Python 3 distribution's pip executable
  

Usage
-----
Modules metadata are declared in a **JSON** file, named ``externals.json`` in the root directory of each module, the general structure of which is

.. code::

  <file> ::=  { 
    "depends" {
      "module_name": <module-object>,
      ...
    },
    "optdepends" {
      <key> : {
        "value" : <value>,
        "deps" :  {
          "module_name": <module-object>,
          ...
        }
      },
      ...
    }
  }
  
  <module_object> ::= {
    "type" : <string>,
    "uri" : <string>,
    "branch" : <string>,
    "tag" : <string>,
    "commit" : <string>,
    "options" : <options>
  }
  
  <options> ::= {
    <key> : <value>,
    ...
  }
    
``type`` is string specifying the module type, currently it can be "svn" or "git"
``uri`` is the link to the module repository (e.g ), currently only **Subversion** and **Git** are supported; if ``type`` is not specified czmake will try to deduce it from the URI's scheme (e.g. ``svn+ssh`` -> ``svn``); if ``type`` is "git" the ``branch``, ``tag`` and ``commit`` field will be also taken into consideration (``Subversion`` has a special syntax to point the URI to a single revision, branch or tag).

<options> is an object containing the key/value pairs that will be translated to CMake cache entries for that module

