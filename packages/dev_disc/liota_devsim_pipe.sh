#!/bin/bash
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

liota_config="/etc/liota/conf/liota.conf"
discovery_messenger_pipe=""

if [ ! -f "$liota_config" ]; then
    echo "ERROR: Configuration file not found" >&2
    exit -1
fi

while read line # Read configurations from file
do
    if echo $line | grep -F = &>/dev/null
    then
        varname=$(echo "$line" | sed "s/^\(..*\)\s*\=\s*..*$/\1/")
        if [ $varname == "devsim_cmd_msg_pipe" ]; then
            value=$(echo "$line" | sed "s/^..*\s*\=\s*\(..*\)$/\1/")
            discovery_messenger_pipe=$value
        fi
    fi
done < $liota_config

if [ "$discovery_messenger_pipe" == "" ]; then
    echo "ERROR: Discovery pipe path not found in configuration file" >&2
    exit -2
fi

if [ ! -p "$discovery_messenger_pipe" ]; then
    echo "ERROR: Discovery Pipe path is not a named pipe" >&2
    #exit -3
fi

# Echo to named pipe
echo "Pipe file: $discovery_messenger_pipe" >&2
echo "$@" > $discovery_messenger_pipe
