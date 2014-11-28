#!/usr/bin/python

import unittest
import os
from time import sleep

from proboscis import test
from proboscis.asserts import assert_false, assert_true, assert_equal, assert_is_not

base_dir = os.path.abspath(os.path.dirname(__file__))
mount_point = base_dir + "/1"

@test
def testPrepare():
    if os.path.ismount(mount_point):
        os.system("fusermount -u " + mount_point)
    assert_false(os.path.ismount(mount_point))


@test(depends_on=[testPrepare])
def testIsMount():
    os.system(base_dir + "/otfs.py 1")
    assert_true(os.path.ismount(mount_point))

filename = mount_point+"/test.txt"
basename = os.path.basename(filename)
content = "This is a test file, path = " + filename

@test(depends_on=[testIsMount])
def testCreateFile():
    with open(filename, "w") as f:
        f.write(content)
    assert_true(basename in os.listdir(mount_point))
    assert_true(basename in os.listdir(mount_point+"/.control"))

@test(depends_on=[testCreateFile])
def testReadControlFile():
    with open(mount_point + "/.control/" + basename) as f:
        assert_is_not(f.read(), '')
        f.close()

@test(depends_on=[testReadControlFile])
def testRead():
    f = open(filename)
    test_content = f.read()
    f.close()
    assert_equal(content, test_content)

@test(depends_on=[testRead])
def testRemoved():
    assert_false(filename in os.listdir(mount_point))

@test(depends_on=[testRemoved])
def testAfter():
    os.system("fusermount -u -z " + mount_point)
    os.listdir(base_dir)
    assert_false(os.path.ismount(mount_point))


def run_tests():
    from proboscis import TestProgram

    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()