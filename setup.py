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

import os
from setuptools import setup, find_packages
import pip
from pip.req import parse_requirements
requirements = [
    str(requirement.req)
    for requirement in parse_requirements('requirements.txt', session=pip.download.PipSession())
]

# Get the long description from the README file
with open('README.md') as f:
    long_description = f.read()

setup(
    name='liota',
    version='0.1.2',
    packages=find_packages(exclude=["*.json", "*.txt"]),
    description='IoT Agent',
    long_description=long_description,
    # include_package_data=True

    # The project's main homepage.
    url='https://github.com/vmware/liota',
    author='The Python Packaging Authority',
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
    data_files=[(os.path.abspath(os.sep) + '/../etc/liota/example', ['example/graphite_simulated.py',
                'example/vrops_graphite_dk300_sample.py',
                'example/vrops_graphite_DellEdge5K_sample.py',
                'example/vrops_simulated.py',
                'example/graphite_withTemp.py',
                'example/graphite_event_based.py',
                'example/sampleProp.conf']),
                (os.path.abspath(os.sep) + '/../etc/liota/conf', ['config/liota.conf', 'config/logging.json']),
                (os.path.abspath(os.sep) + '/../etc/liota', ['BSD_LICENSE.txt', 'BSD_NOTICE.txt']),
                (os.path.abspath(os.sep) + '/../var/log/liota', [])]
      )

