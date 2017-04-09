import os


def parse_packages(dir_):
    packages = []
    for name in os.listdir(dir_):
        if name.startswith('__') and name.endswith('__'):
            continue

        if os.path.isdir(os.path.join(dir_, name)):
            packages.append(name)

    return packages


current_dir = os.path.dirname(__file__)
__all__ = parse_packages(current_dir)

from . import *
