"""Module for independent simple helper functions."""

import os
from io import StringIO


def relative_module_path(module_file, relative_path):
    """Returns path relative to current python module."""
    dir_path = os.path.dirname(os.path.realpath(module_file))
    return os.path.join(dir_path, relative_path)


def create_open_mock(sys_file_mock):
    class OpenMock:
        def __init__(self, sys_file):
            self.file_sys = sys_file

        def __call__(self, path):
            return StringIO(self.file_sys[path])

    return OpenMock(sys_file_mock)
