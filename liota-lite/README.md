# Liota-Lite
Little IoT Agent-lite (liota) is the trimmed version of actual Liota, it doesn't include any example files,user-packages and additional libraries required for various DCC`s.

# Installation
Clone the Liota Repo or download the [Liota release](https://github.com/vmware/liota/releases)

Liota requires a Python 2.7.9+ environment already installed.

Copy MANIFEST.in, requirements.txt and setup.py to the main directory (one directory above) to install Liota-lite.
```bash
  $ cd liota/liota-lite
  $ cp MANIFEST.in requirements.txt setup.py ../
  $ cd ../
```

Liota-lite can be installed as per the command below:
```bash
  $ sudo python setup.py install
```

Post liota installation either you can manually copy the config files from "/usr/lib/liota/config/" to "/etc/liota" and create "/var/log/liota" directory.
Or you can use the helper script "post-install-setup.sh" to copy the config files which exist at the path "/usr/lib/liota". The script on execution by default checks if the "liota" non-root user exist if it doesn't then non-root "liota" user is required to be created manually.
If you require Liota to be installed with the different non-root user which pre-exists on the system then the script will be required to be executed in the following way:

```bash
  $ cd /usr/lib/liota
  $ LIOTA_USER="non-root user" ./post-install-setup.sh
```

It Liota is required to be installed as root user (not the preferred way) then the script should be executed in the following way:

```bash
  $ cd /usr/lib/liota
  $ LIOTA_USER="root" ./post-install-setup.sh
```
