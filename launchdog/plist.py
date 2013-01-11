#! /usr/bin/env python3

import plistlib
import sys
from collections import UserDict
from xml.parsers import expat

try:
    type(basestring)
except NameError:
    basestring=str

class LaunchdPlistError(KeyError):
    pass

def read(filename_or_handle):
    try:
        return Launchd(plistlib.readPlist(filename_or_handle))
    except expat.ExpatError:
        sys.stderr.write("{} is not an XML plist\n".format(filename_or_handle))

class Launchd(UserDict):

    def write(self, filename_or_handle):
        self.check_validity()
        plistlib.writePlist(self.data, filename_or_handle)

    def check_validity(self, plist=None):
        if plist is None:
            plist=self.data
        # Check for the two required elements
        if "Label" not in plist:
            raise LaunchdPlistError("Label must be defined")
        elif "Program" not in plist and "ProgramArguments" not in plist:
            raise LaunchdPlistError(
                    "Either Program or ProgramArguments must be defined")
        # Check the types of each element

        def check_bool(key, value):
            if not isinstance(value, bool):
                raise LaunchdPlistError("{} is not a boolean value".format(
                    key))
        def check_str(key, value):
            if not isinstance(value, basestring):
                raise LaunchdPlistError("{} is not a string ".format(key))
        def check_int(key, value):
            if not isinstance(value, int):
                raise LaunchdPlistError("{} is not an integer".format(key))

        def warn_deprecated(key):
            sys.stderr.write("{} has been deprecated\n".format(key))
        def warn_private(key):
            sys.stderr.write("{} is an undocumented, private key\n".format(key))

        for key, value in plist.items():
            if key in ("Disabled", "EnableGlobbing", "OnDemand", "RunAtLoad",
                    "InitGroups", "StartOnMount", "Debug", "WaitForDebugger",
                    "AbandonProcessGroup", "LowPriorityIO", "LaunchOnlyOnce",
                    "EnableTransactions", "ServiceIPC", "SessionCreate"):
                # SessionCreate is mentioned in passing int TN #2083
                check_bool(key, value)
            elif key in ("UserName", "GroupName", "Label", "Program",
                    "RootDirectory", "WorkingDirectory", "StandardInPath",
                    "StandardOutPath", "StandardErrorPath"):
                check_str(key, value)
            elif key in ("LimitLoadToHosts", "LimitLoadFromHosts",
                    "ProgramArguments", "WatchPaths", "QueueDirectories"):
                for v in value:
                    if not isinstance(v, basestring):
                        raise LaunchdPlistError("'{}' in '{}' is not a string".
                                format(v, key))
            elif key in ("Umask", "TimeOut", "ExitTimeOut", "ThrottleInterval",
                    "StartInterval"):
                check_int(key, value)
            # Complex entries below
            elif key == "inetdCompatibility":
                if not isinstance(value, dict):
                    raise LaunchdPlistError("{} is not a dictionary".format(
                        key))
                if len(value) < 1:
                    raise LaunchdPlistError("{} needs to define 'Wait'".format(
                            key))
                elif "Wait" not in value or len(value) > 1:
                    raise LaunchdPlistError("{} can only contain 'Wait'".format
                            (key))
                else:
                    check_bool("Wait", value["Wait"])
            elif key == "KeepAlive":
                if isinstance(value, dict):
                    for k, v in value.items():
                        if k in ("SuccessfulExit", "NetworkState"):
                            check_bool(k, v)
                        elif k in ("PathState", "OtherJobEnabled"):
                            for i in v.values():
                                if not isinstance(i, bool):
                                    raise LaunchdPlistError(
                                            "There is a non-boolean value in {}"
                                            .format(k))
                        else:
                            raise LaunchdPlistError("Invalid key '{}' in {}"
                                    .format(k, key))
                elif not isinstance(value, bool):
                    raise LaunchdPlistError(
                            "{} must either be a boolean or dictionary"
                            .format(value))
            elif key == "EnvironmentVariables":
                for i in value.values():
                    if not isinstance(i, basestring):
                        raise LaunchdPlistError(
                                "{} contains someting other than strings"
                                .format(key))
            elif key == "StartCalendarInterval":
                def check_calendar(calendar):
                    for k, v in calendar.items():
                        if k in ("Minute", "Hour", "Day", "Weekday", "Month"):
                            check_int(k, v)
                        else:
                            raise LaunchdPlistError(
                                    "{} is an invalid key in {}"
                                    .format(k, key))
                if isinstance(value, dict):
                    check_calendar(value)
                elif isinstance(value, (list, tuple)):
                    for v in value:
                        check_calendar(v)
            elif key in ("SoftResourceLimits", "HardResourceLimits"):
                for k, v in value.items():
                    if k not in ("Core", "CPU", "Data", "FileSize",
                            "MemoryLock", "NumberOfFiles", "NumberOfProcesses",
                            "ResidentSetSize", "Stack"):
                        raise LaunchdPlistError(
                                "'{}' is not supported as a key of '{}'"
                                .format(k, key))
                    else:
                        check_int(k, v)
            elif key == "Nice":
                check_int(key, value)
                if value < -20 or value > 20:
                    raise LaunchdPlistError("{} must be in the range [-20,20]".
                            format(key))
            elif key == "MachServices":
                for service in value.values():
                    if isinstance(service, dict):
                        for k, v in service.items():
                            if k in ("ResetAtClose", "HideUntilCheckIn"):
                                check_bool(k, v)
                            elif k == "HostSpecialPort":
                                check_int(k, v)
                                warn_private(k)
                            else:
                                raise LaunchdPlistError(
                                        "'{}' is not a supported key for '{}'"
                                        .format(k, key))
                    elif not isinstance(service, bool):
                        raise LaunchdPlistError(
                                "The value for the Mach services must be dictionaries or booleans")
            elif key == "Sockets":
                # Madness here...
                # TODO: Unravel the man page for this section
                if not isinstance(value, dict):
                    raise LaunchdPlistError("{} needs to be a dictionary.".
                            format(key))
            elif key == "BinaryOrderPreference":
                check_int(key, value)
                warn_private(key)
            elif key in ("MultipleInstances", "NSSupportsSuddenTermination",
                    "HopefullyExitsLast", "BeginTransactionAtShutdown"):
                check_bool(key, value)
                warn_private(key)
            elif key == "SHAuthorizationRight":
                check_str(key, value)
                warn_private(key)
            elif key == "LimitLoadToSessionType":
                # Contrary to the man page, LimitLoadToSessionType can be an
                # array according to Apple Technote #2083
                if isinstance(value, (tuple, list)):
                    for session in value:
                        if session not in ("Aqua", "StandardIO", "Background",
                                "LoginWindow"):
                            raise LaunchdPlistError("'{}' is an invalid session type for '{}'"
                                    .format(session, key))
                elif not isinstance(value, basestring):
                    raise LaunchdPlistError("{} needs to either be an arry or a string"
                            .format(key))
            elif key == "LaunchEvents":
                # This key is documented in the xpc_set_event_stream_handler(3)
                # manpage. As far as I can tell, this is a dict of dicts of
                # dicts.
                if not isinstance(value, dict):
                    raise LaunchdPlistError("{} requires a dictionary value"
                            .format(key))
                else:
                    for stream in value.values():
                        if not isinstance(stream, dict):
                            raise LaunchdPlistError(
                                "Event streams for {} are supposed to be dictionaries of events"
                                .format(key))
                        else:
                            for event in stream.values():
                                if not isinstance(stream, dict):
                                    raise LaunchdPlistError(
                                            "Events for {} are defined by dictionaries"
                                            .format(key))
            elif key == "POSIXSpawnType":
                check_str(key, value)
                if value not in ("Interactive", "Adaptive", "TALApp", "Widget",
                        "Widget", "iOSApp", "Background"):
                    raise LaunchdPlistError("Invlaid value {} for key {}"
                            .format(value, key))
                    warn_private(key)
            else:
                raise LaunchdPlistError(
                        "'{}' is an invalid key for a launchd property list"
                        .format(key))
            # Warn for deprecated keys
            if key in ("ServiceIPC", "OnDemand", "HopefullyExitsLast"):
                warn_deprecated(key)
