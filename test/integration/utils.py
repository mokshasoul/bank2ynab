import configparser
from os import path

PRODPATH = "bank2ynab.conf"
TESTCONFPATH = path.join("test-data", "test.conf")


def get_test_confparser():
    cp = configparser.RawConfigParser()
    # convert our paths into absolutes

    project_dir = get_project_dir()
    prodpath = path.join(project_dir, PRODPATH)
    testconfpath = path.join(project_dir, TESTCONFPATH)

    # first read prod to get all defaults
    cp.read([prodpath])
    for section in cp.sections():
        cp.remove_section(section)
    # then read any test-specific config
    cp.read([testconfpath])

    return cp


def get_project_dir():
    ppath = path.realpath(__file__)
    return path.dirname(path.dirname(ppath))
