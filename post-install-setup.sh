#!/bin/bash
#
# ----------------------------------------------------------------------------#
#  Copyright © 2017 VMware, Inc. All Rights Reserved.                         #
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
# Details:
#	This program is intended to be run after the software is installed
#	mainly as an install helper.  The "normal" way liota would be
#	installed is via pip, or possibly git, assuming you don't get the
#	software from your distro (which is *ALWAYS* the preferred method).
#	This will run through and setup some directories and copy some
#	config files around into the right places so that you can run this
#	and just get running.
#
# Caveats:
#	There are going to be a bunch of assumptions about how your local
#	system is setup, and these might not ultimately be correct.
#	This will modify your system, should be run as root (it's going to 
#	create directories and such in places that a normal user would not
#	have access to, and you should always be cautious in running this,
#	or any software as root, at the best of times.
#
# ----------------------------------------------------------------------------
# Things that are being done / todo list
#	- Check for the users we'll be using
#		- Check the root user
#		- Check the liota user
#		- Check the liota group
#	- Configuration files: /etc/liota
#		- If /etc/liota doesn't exist, make it
#		- Change the owner and group to what we are expecting
#		- Change the permissions on the configuration directory
#		- Check if the example config exists
#		- Copy the exapmle to the config dir
#		- Change the owner and group to what we are expecting
#		- Change the permissions on the config file
#	- Deal with setting up the logging directory
#		- mkdir
#		- change owners
#		- change perms
#
# ----------------------------------------------------------------------------
#
# Defined assumptions follow, these are all overrideable with environment 
# variables
#

# Defines where the configuration directory should be
#	Default: /etc/liota
_LIOTA_ETCDIR=${LIOTA_ETCDIR:-/etc/liota}

# Defines who the liota user is, so that appropriate
# permissions can be set
#	Default: liota
_LIOTA_USER=${LIOTA_USER:-liota}

# Defines who the 'root' user is
# It's assumed that things like /etc/liota will be owned by root but readable
# by the user.  
#	Default: root
_LIOTA_ROOTUSER=${LIOTA_ROOTUSER:-root}

# Defines that the permissions for the etc directory
#	Default: 0750
_LIOTA_ETCPERMS=${LIOTA_ETCPERMS:-0750}

# Defines where the example config file is at
#	Default: /usr/lib/liota/config/liota.conf
_LIOTA_CONFFROM=${LIOTA_CONFFROM:-/usr/lib/liota/config/liota.conf}

# Defines where the example config file is at
#	Default: /usr/lib/liota/config/logging.json
_LIOTA_JSONFROM=${LIOTA_CONFFROM:-/usr/lib/liota/config/logging.json}

# Defines where the config file should live
#	Default: /etc/liota/liota.conf
_LIOTA_CONFTO=${LIOTA_CONFTO:-/etc/liota/liota.conf}

# Defines where the config file should live
#	Default: /etc/liota/logging.json
_LIOTA_JSONTO=${LIOTA_CONFTO:-/etc/liota/logging.json}

# Defines what the permissions for the config file should be
#	Default: 0750
_LIOTA_CONFPERMS=${LIOTA_CONFPERMS:-0750}

# Defines where the log files should end up
#	Default: /var/log/liota
_LIOTA_LOGDIR=${LIOTA_LOGDIR:-/var/log/liota}

# Defines what permissions to have on the logging directory
#	Default: 0750
_LIOTA_LOGPERMS=${LIOTA_LOGPERMS:-0750}

echo "Liota: etc dir: ${_LIOTA_ETCDIR}"

# ----------------------------------------------------------------------------
#
# No User Serviceable Parts Beyond This Point
#	Qualified service personal only
#
# ----------------------------------------------------------------------------

#
# Check if the users in question all actually exist
#

which getent &> /dev/null

if [[ "$?" != "0" ]]
then
	echo "command \`which\` is not installed or available in the path. Can't perform checks. This is a fatal error."
	exit
fi

getent passwd "${_LIOTA_ROOTUSER}" &> /dev/null

if [[ "$?" != "0" ]]
then
	echo "'Root' User ${_LIOTA_ROOTUSER} is not setup, this is odd and needs to be resolved. This is a fatal error."
	exit
fi

getent passwd "${_LIOTA_USER}" &> /dev/null

if [[ "$?" != "0" ]]
then
	echo "Liota User ${_LIOTA_USER} is not setup, this is odd and needs to be resolved. This is a fatal error."
	exit
fi

getent group "${_LIOTA_USER}" &> /dev/null

if [[ "$?" != "0" ]]
then
	echo "Liota Group ${_LIOTA_USER} is not setup, this is odd and needs to be resolved. This is a fatal error."
	exit
fi


#
# Configuration directory
#

if [[ -e "${_LIOTA_ETCDIR}" ]]
then
	echo "ERROR: ${_LIOTA_ETCDIR} already exists, and assuming things are setup already or not but automatic running will not proceed. This is a fatal error."
	exit
fi

# Deal with creating the directory, if it doesn't exist
if [[ ! -d "${_LIOTA_ETCDIR}" ]]
then
	if [[ -e "${_LIOTA_ETCDIR}" ]]
	then
		echo "ERROR: ${_LIOTA_ETCDIR} already exists, but is not a directory.  This is a fatal error."
		exit
	fi

	mkdir -p "${_LIOTA_ETCDIR}"

	if [[ "$?" != "0" ]]
	then
		echo "ERROR: Couldn't create ${_LIOTA_ETCDIR}.  This is a fatal error."
		exit
	fi
fi

# Deal with directory ownership
if [[ -d "${_LIOTA_ETCDIR}" ]]
then
	# Change the ownership and group on the configuration directory
	chown "${_LIOTA_ROOTUSER}":"${_LIOTA_USER}" "${_LIOTA_ETCDIR}"

	if [[ "$?" != "0" ]]
	then
		echo "ERROR: Couldn't set the ownership and group to ${_LIOTA_ROOTUSER}:${_LIOTA_USER}.  This is a fatal error."
		exit
	fi


	# Change the permissions on the configuration directory
	chmod "${_LIOTA_ETCPERMS}" "${_LIOTA_ETCDIR}"

	if [[ "$?" != "0" ]]
	then
		echo "ERROR: Couldn't set permissions to ${_LIOTA_ETCPERMS} on ${_LIOTA_ETCDIR}.  This is a fatal error."
		exit
	fi
fi

# Deal with copying in the example config file into place
if [[ -e "${_LIOTA_CONFTO}" ]]
then
	echo "ERROR: There is a configuration file already existing at ${_LIOTA_CONFTO}, not going to overwrite. This is a fatal error."
	exit
fi

if [[ ! -e "${_LIOTA_CONFFROM}" ]]
then
	echo "ERROR: ${_LIOTA_CONFFROM} does not seem to exist, nothing to copy.  This is a fatal error."
	exit
fi

cp "${_LIOTA_CONFFROM}" "${_LIOTA_CONFTO}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't copy ${_LIOTA_CONFFROM} to ${_LIOTA_CONFTO}.  This is a fatal error."
	exit
fi

chown "${_LIOTA_ROOTUSER}:${_LIOTA_USER}" "${_LIOTA_CONFTO}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't set owner and group to ${_LIOTA_ROOTUSER}:${_LIOTA_USER} on ${_LIOTA_CONFTO}. This is a fatal error."
	exit
fi

chmod "${_LIOTA_CONFPERMS}" "${_LIOTA_CONFTO}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't set permissions to ${_LIOTA_CONFPERMS} on ${_LIOTA_CONFTO}. This is a fatal error."
	exit
fi

if [[ -e "${_LIOTA_JSONTO}" ]]
then
	echo "ERROR: There is a json file already existing at ${_LIOTA_JSONTO}, not going to overwrite. This is a fatal error."
	exit
fi

# deal with the json file too

if [[ ! -e "${_LIOTA_JSONFROM}" ]]
then
	echo "ERROR: ${_LIOTA_JSONFROM} does not seem to exist, nothing to copy.  This is a fatal error."
	exit
fi

cp "${_LIOTA_JSONFROM}" "${_LIOTA_JSONTO}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't copy ${_LIOTA_JSONFROM} to ${_LIOTA_JSONTO}.  This is a fatal error."
	exit
fi

chown "${_LIOTA_ROOTUSER}:${_LIOTA_USER}" "${_LIOTA_JSONTO}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't set owner and group to ${_LIOTA_ROOTUSER}:${_LIOTA_USER} on ${_LIOTA_JSONTO}. This is a fatal error."
	exit
fi

chmod "${_LIOTA_CONFPERMS}" "${_LIOTA_JSONTO}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't set permissions to ${_LIOTA_CONFPERMS} on ${_LIOTA_JSONTO}. This is a fatal error."
	exit
fi

#
# Log Directory stuff
#

if [[ -e "${_LIOTA_LOGDIR}" ]]
then
	echo "ERROR: Log directory ${_LIOTA_LOGDIR} already exists.  This is a fatal error."
	exit
fi

mkdir "${_LIOTA_LOGDIR}" &> /dev/null

if [[ "$?" != "0" ]]
then
	echo "ERROR: Couldn't create ${_LIOTA_LOGDIR}.  This is a fatal error."
fi

chown "${_LIOTA_USER}:${_LIOTA_USER}" "${_LIOTA_LOGDIR}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't set owner and group to ${_LIOTA_USER}:${_LIOTA_USER} on ${_LIOTA_LOGDIR}. This is a fatal error."
	exit
fi

chmod "${_LIOTA_LOGPERMS}" "${_LIOTA_LOGDIR}"

if [[ "$?" != "0" ]]
then
	echo "ERROR: couldn't set permissions to ${_LIOTA_LOGPERMS} on ${_LIOTA_LOGDIR}. This is a fatal error."
	exit
fi

echo "Setup completed successfully."
