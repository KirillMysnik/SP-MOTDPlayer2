from path import Path


def parse_packages(dir_):
    packages = []
    for path in Path(dir_).dirs():
        name = path.name
        if name.startswith('__') and name.endswith('__'):
            continue

        packages.append(name)

    return packages


def parse_modules(dir_):
    modules = []
    for path in Path(dir_).files():
        if path.ext != '.py':
            continue

        if path.name.startswith('__') and path.namebase.endswith('__'):
            continue

        modules.append(path.namebase)

    return modules


__all__ = (parse_modules(Path(__file__).parent) +
           parse_packages(Path(__file__).parent))

from . import *
