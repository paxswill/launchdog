#! /usr/bin/env python

import plistlib
from collections import UserDict

class LaunchdPlistError(KeyError):
    pass

class Launchd(UserDict):

    def __init__(self, filename_or_handle=None):
        if filename_or_handle is not None:
            self.data = plistlib.readPlist(filename_or_handle)
            self.check_validity()

    def write(self, filename_or_handle):
        self.check_validity()
        plistlib.writePlist(self.data, filename_or_handle)

    def check_validity(self, plist=None):
        if plist is None:
            plist=self.data
        if not plist["Label"]:
            raise LaunchdPlistError("Label must be defined")
        elif not plist["Program"] and not plist["ProgramArguments"]:
            raise LaunchdPlistError(
                    "Either Program or ProgramArguments must be defined")
