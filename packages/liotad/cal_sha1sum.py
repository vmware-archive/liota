import os 
import sys
import hashlib

def sha1sum(path_file):
    """
    This method calculates SHA-1 checksum of file.
    :param path_file: the relative or absolute path of a file
    :return: the SHA-1 checksum of the file
    """
    if not os.path.isfile(path_file):
        return None
    sha1 = hashlib.sha1()
    with open(path_file, "rb") as fp:
        while True:
            data = fp.read(65536)  # buffer size
            if not data:
                break
            sha1.update(data)
    return sha1

# main
param_1= sys.argv[1] 
print 'Params=', param_1
filen = param_1
print "File: ", filen
sum = sha1sum(filen)
print "Checksum=", sum.hexdigest()