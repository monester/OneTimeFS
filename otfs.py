#!/usr/bin/python

import fuse
import stat
import errno
import yaml
import logging
import traceback

fuse.fuse_python_api = (0, 2)

config = {}


class FsStat(fuse.Stat):

    def __init__(self):
        self.st_mode = stat.S_IFDIR | 0775
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 2
        self.st_uid = config['uid']
        self.st_gid = config['gid']
        self.st_size = 4096
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


class File:
    def __init__(self, args):
        self.read_bytes = 0
        self.hits = 0
        self.persistent = 'persistent' in args and args['persistent'] or False
        self.content = 'content' in args and args['content'] or ''


def log(func):
    def wrapper(*args, **kwargs):
        logging.info("[{:12}] args: {} kwargs: {}".format(
            func.__name__,
            [arg for arg in args if not isinstance(arg, OneTimeFS)],
            kwargs)
        )
        try:
            return func(*args, **kwargs)
        except Exception, e:
            logging.info(traceback.format_exc())
            raise e
    return wrapper


class OneTimeFS(fuse.Fuse):
    """
     OneTimeFS stores file until it is read by some program

     files are stored in memory
    """
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.files = {}

    @staticmethod
    def get_filename(path):
        """get unique filename for file
            :returns filename, array of path
        """
        filename = path.split('/')[-1]
        paths = path.split('/')[1:-1]
        return filename, paths

    def get_file(self, path):
        filename, paths = self.get_filename(path)
        if filename in self.files:
            if '.control' in paths:
                return self.get_info(filename), paths
            return self.files[filename], paths
        logging.info("[{:12}] File {} not found in table".format(
            "get_file", path))
        return None, []

    def get_info(self, filename):
        """get internal file info via /control"""
        f = self.files[filename]
        buf = "persistent: {}\n" \
            "hits: {}\n" \
            "read_bytes: {}\n" \
            "length: {}\n".format(
                f.persistent,
                f.hits,
                f.read_bytes,
                len(f.content)
            )
        return File({
            'persistent': True,
            'content': buf,
        })

    @log
    def create_file(self, path):
        """init array for new file"""
        filename, paths = self.get_filename(path)
        self.files[filename] = File({})

    @log
    def getattr(self, path):
        """reads file attribute"""
        st = FsStat()
        if path == '/' or path == '/.control':
            pass
        else:
            f, paths = self.get_file(path)
            if f:
                st.st_mode = stat.S_IFREG | 0666
                st.st_nlink = 1
                st.st_size = len(f.content)
            else:
                return -errno.ENOENT
        return st

    @log
    def readdir(self, path, offset):
        """ lists each entry in directory
        :return: yield each entry
        """
        dirents = ['.', '..']
        if path == '/':
            dirents.append('.control')
        dirents.extend(self.files.keys())
        for r in dirents:
            yield fuse.Direntry(r)

    @log
    def mknod(self, path, mode, dev):
        """create new file/dir/etc"""
        f, paths = self.get_file(path)
        if not f:
            self.create_file(path=path)
        return 0

    @log
    def open(self, path, flags):
        """mark file as open"""
        f, paths = self.get_file(path)
        f.hits += 1
        if not f:
            return -errno.ENOENT
        return 0

    @log
    def read(self, path, size, offset):
        """ read from file
        :return: String with data
        """
        f, paths = self.get_file(path)
        f.read_bytes += size
        return f.content[offset:offset+size]

    @log
    def write(self, path, buf, offset):
        """ Write data to file
        :return: length of written data
        """
        f, paths = self.get_file(path)
        f.content += buf
        return len(buf)

    @log
    def release(self, path, flags):
        """mark file as closed
        and delete it if read_bytes is more than length
        """
        f, paths = self.get_file(path)
        if not f.persistent  and f.hits > 1:
            if f.read_bytes >= len(f.content):
                self.unlink(path)
        return 0

    @log
    def truncate(self, path, size):
        f, paths = self.get_file(path)
        f.content = ''
        return 0

    @log
    def unlink(self, path):
        """delete file"""
        filename, paths = self.get_filename(path)
        del self.files[filename]
        return 0

    @log
    def utime(self, path, times):
        """update date and time"""
        return 0


def main():
    """main() function of OneTimeFS"""
    global config
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    server = OneTimeFS(version="%prog " + fuse.__version__,
                       dash_s_do='setsingle')
    with open("config.yaml") as f:
        cfg = yaml.load(f)
        config = cfg['config']
    server.files = {f: File(cfg['files'][f]) for f in cfg['files']}
    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
