# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2016 VMware, Inc. All Rights Reserved.                    #
#                                                                             #
#  Licensed under the BSD 2-Clause License (the “License”); you may not use   #
#  this file except in compliance with the License.                           #
#                                                                             #
#  The BSD 2-Clause License                                                   #
#                                                                             #
#  Redistribution and use in source and binary forms, with or without         #
#  modification, are permitted provided that the following conditions are met:#
#                                                                             #
#  - Redistributions of source code must retain the above copyright notice,   #
#      this list of conditions and the following disclaimer.                  #
#                                                                             #
#  - Redistributions in binary form must reproduce the above copyright        #
#      notice, this list of conditions and the following disclaimer in the    #
#      documentation and/or other materials provided with the distribution.   #
#                                                                             #
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"#
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE  #
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE #
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE  #
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR        #
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF       #
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS   #
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN    #
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)    #
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF     #
#  THE POSSIBILITY OF SUCH DAMAGE.                                            #
# ----------------------------------------------------------------------------#

#
# Includes
#

import os
import pip
import sys
from pip.req import parse_requirements
from setuptools import setup, find_packages

#
# Useful Variables
#

PACKAGE_NAME = "liota"
PACKAGE_VERSION = "0.4.1"

#
# Functions
#


def get_tree_walk(path):
    """
    Get the file names list present in directory or its sub-directories
    :param path: Directory Path
    :return: File name list
    """
    filename_list = []
    for dirpath, dirname, filenames in os.walk(path):
        # We need to remove the leading directory
        # as the os.walk adds it in, and it's not super
        # useful to us in this case as we know it
        dirpath_split = (dirpath.split(os.path.sep)[1:])

        if( len( dirpath_split) > 0 ):
            dirpath_trunk = os.path.join(*(dirpath_split))
        else:
            dirpath_trunk = ""

        # If the filenames isn't empty, add the filenames
        if( len( filenames ) > 0):
            filename_list.append((dirpath, filenames))
    return filename_list


def get_data_files():
    """
    Get data files name list required to be bundled with Liota
    :return: Data Files list
    """
    # Setup an empty return
    data_files = []

    #
    # The following 4 lines would be useful if we were doing cross
    # platform installation.  It's currently unclear if this is
    # supported so this is being left here in the off chance it
    # becomes relevant
    #
    # if sys.platform == "win32":
    #     datadir = os.path.join("doc", PACKAGE_NAME)
    # else:
    #    datadir = os.path.join("share", "doc", PACKAGE_NAME)

    datadir = os.path.join(
        os.path.abspath(os.sep),
        "usr",
        "lib",
        PACKAGE_NAME
        )

    data_files = [
        (datadir, ['BSD_LICENSE.txt', 'BSD_NOTICE.txt', 'post-install-setup.sh']),
        ]
    for docs in ['examples', 'packages', 'config', ]:
        file_list = get_tree_walk(docs)
        if len(file_list):
            for dirpath,files in file_list:
                thesefiles = []
                for sfile in files:
                    thesefiles.append(os.path.join(dirpath, sfile))
                data_files.append((os.path.join(datadir, dirpath), thesefiles))

    return data_files

#
# Python setup.py definitions
#
requirements = [str(requirement.req) for requirement in parse_requirements(
    'requirements.txt', session=pip.download.PipSession())]

# Python Version check
if not sys.version_info[0] == 2:
    sys.exit('Python 3 is not supported')

# Python 2.7.9 sub-version check
if sys.version_info[1] < 7 or \
        sys.version_info[1] == 7 and sys.version_info[2] < 9:
    sys.exit('Python versions lower than 2.7.9 are not supported')

# Get the long description from the README file
with open('README.md') as f:
    long_description = f.read()

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    packages=find_packages(exclude=["*.json", "*.txt",]),
    description='Little IoT Agent (liota)',
    long_description=long_description,
    # include_package_data=True

    # The project's main homepage.
    url='https://github.com/vmware/liota',
    author='Kohli Vaibhav (VMware)',
    author_email='vkohli@vmware.com',

    # License
    license='BSD',
    platforms=['Linux'],

    # Classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        # TO DO: Check for other python versions
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
    ],

    keywords='iot liota agent',

    # Installation requirement
    install_requires=requirements,

    # 'data_file'(conf_files) at custom location
    data_files=get_data_files()
)
