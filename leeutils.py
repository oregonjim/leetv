""" general utilities module """
# -*- coding: utf-8 -*-
#
#######################################################################
#
# Copyright © 2018 Jim Lee
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

#  leeutils.py
#
#  Various utility functions
#
#  Last update: 2018-06-02
#
import os
import sys
import re
import subprocess


# Returns the directory the current script (or interpreter) is running in
def get_script_directory():
    """ return directory that the script was executed from """
    path = os.path.realpath(sys.argv[0])
    if os.path.isdir(path):
        return path
    else:
        return os.path.dirname(path)


# list.sort(key=natural_sort)
def natural_sort(x):
    """ sorts numbers correctly: (1,2,10,11) NOT (1,10,11,2) """
    return [int(y) if y.isdigit() else y for y in re.split(r'(\d+)', x)]


def makepath(*paths):
    '''
    Convenience function for creating a path
    from fragments that never begin or end
    with os.sep.
    '''
    return os.sep.join(paths)


def abswalk(path):
    '''
    Generator returning the absolute path of every file (directory or other)
    under path.
    '''
    path = os.path.abspath(path)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for dirname in dirnames:
            yield os.path.join(path, dirpath, dirname)
        for filename in filenames:
            yield os.path.join(path, dirpath, filename)


def filewalk(path):
    '''
    Generator returning the absolute path of every file under path.
    '''
    path = os.path.abspath(path)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            yield os.path.join(path, dirpath, filename)


def dirwalk(path):
    '''
    Generator returning the absolute path of every directory under path.
    '''
    path = os.path.abspath(path)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for dirname in dirnames:
            yield os.path.join(path, dirpath, dirname)


def call(args):
    '''
    Blocking process call.
    Takes a list of strings like ['ls', '-l'] and returns the 3-tuple
    (stdout, stderr, returncode).
    '''
    p = subprocess.Popen(args, stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE, close_fds=True, shell=False)
    o, e = p.communicate()
    return o.decode('utf-8'), e.decode('utf-8'), p.returncode


def rename_ini_section(cp, section_from, section_to):
    '''
    Rename a configparser .ini file section
    '''
    if section_from == section_to:
        # avoid duplicate section exception
        return

    items = cp.items(section_from)

    cp.add_section(section_to)

    for item in items:
        cp.set(section_to, item[0], item[1])

    cp.remove_section(section_from)


class Container:
    """ generic container class """
    pass


class Log:
    """ logger class capable of dual output and color """
    # COLOR CODES
    #
    # FOREGROUND
    # ------------------------------
    # 30 black     90 grey
    # 31 red       91 bright red
    # 32 green     92 bright green
    # 33 yellow    93 bright yellow
    # 34 blue      94 bright blue
    # 35 magenta   95 bright magenta
    # 36 cyan      96 bright cyan
    # 37 white     97 bright white
    #
    # BACKGROUND
    # ------------------------------
    # 40 black    100 grey
    # 41 red      101 bright red
    # 42 green    102 bright green
    # 43 yellow   103 bright yellow
    # 44 blue     104 bright blue
    # 45 magenta  105 bright magenta
    # 46 cyan     106 bright cyan
    # 47 white    107 bright white
    #
    #
    # set:              ESC[xxm
    # set both at once: ESC[fg;bgm
    # reset:            ESC[0m
    #

    levels = {'DEBUG': 0,
              'INFO': 1,
              'WARNING': 2,
              'ERROR': 3,
              'OFF': 4}

    DEBUG = '\x1b[96m'
    INFO = '\x1b[92m'
    WARNING = '\x1b[93m'
    ERROR = '\x1b[91m'

    RESET = '\x1b[0m'

    # defaults
    f = sys.stdout
    both = False
    level = levels['INFO']

    def __init__(self, level='INFO'):
        self.f = sys.stdout
        self.set_level(level)

    def __del__(self):
        self.close()

    def flush(self):
        """ flush log file """
        if self.f != sys.stdout:
            self.f.flush()

    def close(self):
        """ close log file """
        if self.f != sys.stdout:
            self.f.close()

    def _output(self, color, level, message):
        """ internal method """
        if self.f != sys.stdout:
            self.f.write(level + " {}\n".format(message))
        if (self.f == sys.stdout) or self.both:
            print(color + level + self.RESET + " {}".format(message))

    def set_output(self, filename, mode='a', dualoutput=False):
        """ assign output to log file """
        self.f = open(filename, mode)
        self.both = dualoutput

    def set_level(self, level):
        """ set logging level """
        if level in self.levels.keys():
            self.level = self.levels[level]
        else:
            print('BAD LOG LEVEL: {}'.format(level))
            sys.exit(1)

    def debug(self, message):
        """ debug log message """
        if self.level > self.levels['DEBUG']:
            return
        self._output(self.DEBUG, '[DEBUG]', message)

    def info(self, message):
        """ info log message """
        if self.level > self.levels['INFO']:
            return
        self._output(self.INFO, '[INFO]', message)

    def warning(self, message):
        """ warning log message """
        if self.level > self.levels['WARNING']:
            return
        self._output(self.WARNING, '[WARNING]', message)

    def error(self, message, retcode=1):
        """ error log message """
        if self.level > self.levels['ERROR']:
            sys.exit(retcode)
        self._output(self.ERROR, '[ERROR]', message)
        sys.exit(retcode)
