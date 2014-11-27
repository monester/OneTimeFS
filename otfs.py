#!/usr/bin/python

import fuse
import stat
import errno
import logging

fuse.fuse_python_api = (0, 2)


class FsStat(fuse.Stat):

    def __init__(self):
        self.st_mode = stat.S_IFDIR | 0755
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 2
        self.st_uid = 1000
        self.st_gid = 1000
        self.st_size = 4096
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


def log(func):
    def wrapper(*args, **kwargs):
        logging.info("[{:12}] args: {} kwargs: {}".format(
            func.__name__,
            [arg for arg in args if not isinstance(arg, OneTimeFS)],
            kwargs)
        )
        return func(*args, **kwargs)
    return wrapper


class OneTimeFS(fuse.Fuse):
    """
     OneTimeFS stores file until it is read by some program

     files are stored in memory
    """
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.files = {
            'test_persistent': {
                'persistent': True,
                'read_bytes': 0,
                'hits': 0,
                'content': 'This file can be deleted only by rm command',
            },
            'test_file': {
                'persistent': True,
                'read_bytes': 0,
                'hits': 0,
                'content': 'This is a persistent file\n',
            },
            'test_file_auto': {
                'persistent': False,
                'read_bytes': 0,
                'hits': 0,
                'content': 'This is a one time read file\n',
            }
        }

    def get_filename(self, path, create=False):
        """get unique filename for file
            :returns filename, array of path
        """
        filename = path.split('/')[-1]
        paths = path.split('/')[1:-1]
        if filename in self.files or create:
            return filename, paths
        logging.info("[{:12}] File {} not found in table".format(
            "get_filename", path))
        return '', []

    def get_info(self, filename):
        """get internal file info via /control"""
        f = self.files[filename]
        buf = """persistent: {}
        hits: {}
        read_bytes: {}
        length: {}
        """.format(
            f['persistent'],
            f['hits'],
            f['read_bytes'],
            len(f['content'])
        )
        return buf

    def create_file(self, filename):
        """init array for new file"""
        self.files[filename] = {
            'type': '',
            'persistent': False,
            'read_bytes': 0,
            'content': '',
        }

    @log
    def getattr(self, path):
        """reads file attribute"""
        filename, paths = self.get_filename(path)
        st = FsStat()
        if path == '/' or path == '/.control':
            pass
        elif filename:
            st.st_mode = stat.S_IFREG | 0666
            st.st_nlink = 1
            st.st_size = len(self.files[filename]['content'])
        else:
            return -errno.ENOENT
        return st

    @log
    def readdir(self, path, offset):
        """ lists each entry in directory
        :return: yield each entry
        """
        dirents = ['.', '..', '.control']
        dirents.extend(self.files.keys())
        for r in dirents:
            yield fuse.Direntry(r)

    @log
    def mknod(self, path, mode, dev):
        """create new file/dir/etc"""
        filename, paths = self.get_filename(path, create=True)
        if filename not in self.files:
            self.create_file(filename)
        return 0

    @log
    def open(self, path, flags):
        """mark file as open"""
        filename, paths = self.get_filename(path)
        if not filename:
            return -errno.ENOENT
        return 0

    @log
    def read(self, path, size, offset):
        """ read from file
        :return: String with data
        """
        filename, paths = self.get_filename(path)
        self.files[filename]['read_bytes'] += size
        buff = self.files[filename]['content']
        return buff[offset:offset+size]

    @log
    def write(self, path, buf, offset):
        """ Write data to file
        :return: length of written data
        """
        filename, paths = self.get_filename(path)
        self.files[filename]['content'] += buf
        return len(buf)

    @log
    def release(self, path, flags):
        """mark file as closed
        and delete it if read_bytes is more than length
        """
        filename, paths = self.get_filename(path)
        f = self.files[filename]
        if not f['persistent']  and f['hits'] > 1:
            if f['read_bytes'] >= len(f['content']):
                self.unlink(path)
        return 0

    @log
    def unlink(self, path):
        """delete file"""
        filename = self.get_filename(path)
        del(self.files[filename])
        return 0

    @log
    def utime(self, path, times):
        """update date and time"""
        return 0


def main():
    """main() function of OneTimeFS"""
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    # logging.INFO("TEST INIT")
    server = OneTimeFS(version="%prog " + fuse.__version__,
                       dash_s_do='setsingle')
    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
