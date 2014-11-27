OneTimeFS
=========

Filesystem that stores files only for single read. Based on FUSE.

Main purpose of such filesystem if you need to give some application
file and then remove the file. This fs allows you not to wait while application
read the file.

Features
--------

  * create files from YAML
  * create files via standard create_file
  * create static files which will not be removed after reading
  * remove files without reading
  * see file statistics via .control directory

Not implemented yet
-------------------

  * multilevel tree
  * set persistent option on runtime
  * config file location
  * log file location
  * set custom read limit count

Configuration
-------------

To run OneTimeFS only several configuration lines needed:

    # config.yaml
    ---
    config:
      uid: 1000
      gid: 1000

To mount OneTimeFS run the following command:

    ./otfs.py /mnt/mount_point

### Sample configuration ###

    ---
    config:
      uid: 1000
      gid: 1000
    files:
      default:
        content: |
          TIMEOUT 50
          TOTALTIMEOUT 9000
          ONTIMEOUT local
          default local

          LABEL local
                  MENU LABEL Boot local hard drive
                  LOCALBOOT 0

        persistent: True

References
----------

python-fuse http://sourceforge.net/p/fuse/wiki/Main_Page/