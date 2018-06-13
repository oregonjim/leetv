# -*- coding: utf-8 -*-
""" LeeTV schedule class module """
# pylint: disable=C0103,C0301,R0912,R0914,R0915,R1702
#
#######################################################################
#
# Copyright © 2018 Jim Lee <jlee54@gmail.com>
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
#
#  schedule.py
#
#  Schedule class for leetv
#
#  Last update: 2018-06-13
#
import os
import random
from datetime import date
from configparser import ConfigParser


class Schedule:
    """ LeeTV schedule class """

    # main configuration directory
    directory = ''
    # object representing settings.ini
    settings = None
    # abs path of settings.ini
    settings_file = ''
    # object representing daily schedule
    sched = None
    # global log object
    log = None
    # used for schedule comparisons (last_played)
    today = ''

    def __init__(self, log):
        self.log = log
        self.directory = os.path.join(os.getenv('HOME'), '.leetv')

        # open global settings file
        self.settings = ConfigParser()
        self.settings_file = os.path.join(self.directory, 'config', 'settings.ini')
        self.settings.read(self.settings_file)

        # get schedule for this day of the week
        self.sched = ConfigParser()
        self.sched.read(os.path.join(self.directory, 'sched', self.get_dow(date.today()) + '.ini'))

        self.today = date.strftime(date.today(), '%Y%m%d')

    def get_dow(self, today):
        """ return day of week as three-letter string """
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        day = date(today.year, today.month, today.day).weekday()
        return days[day]

    def get_next_index(self, slot, fn):
        """ get settings for this slot and pick the next episode (index) """

        if self.settings.has_section(slot['series']):
            lastdate = self.settings.get(slot['series'], 'lastdate', fallback='00000000')
            index = self.settings.getint(slot['series'], 'lastplayed', fallback=0)
            skip = self.settings.getint(slot['series'], 'skip', fallback=0)
            if (lastdate != self.today) or slot['seq'].isnumeric():
                # pick a new episode
                if slot['seq'] == 'linear':
                    if not skip:
                        index += 1
                    else:
                        index += skip
                    if index >= len(fn):
                        index = 0
                        self.log.info("Series {} rolled over".format(slot['series']))
                elif slot['seq'].isnumeric():
                    # multiple episodes in one day
                    index += int(slot['seq']) - 1
                    if index >= len(fn):
                        # end of series, start over
                        self.log.info("Series {} rolled over".format(slot['series']))
                        index -= len(fn)
                else:  # slot['seq'] is 'random'
                    index = random.randrange(0, len(fn))
                    # check to see if we've picked this index in the past
                    rndseries = ConfigParser()
                    rndseries_file = os.path.join(self.directory, 'config', slot['series'] + '.ini')
                    rndseries.read(rndseries_file)
                    name = os.path.splitext(
                        os.path.basename(fn[index]))[0]
                    if rndseries.has_section(name):
                        # already played this one
                        # keep selecting random episodes until
                        # we find an unplayed one
                        tries = len(fn) * 10 + 1
                        while tries:
                            index = random.randrange(0, len(fn))
                            name = os.path.splitext(
                                os.path.basename(fn[index]))[0]
                            if not rndseries.has_section(name):
                                # we found an unplayed episode
                                break
                            tries -= 1
                        if not tries:
                            self.log.warning("Unable to find unplayed episode for {}".format(slot['series']))
                            try:
                                dst = os.path.join(self.directory, 'config', slot['series'] + '.old')
                                os.rename(rndseries_file, dst)
                                self.log.warning("Series reset: moved {} to {}".format(rndseries_file, dst))
                            except OSError:
                                self.log.warning("Unable to create {}".format(dst))
        else:
            # no saved section, start a new one
            self.settings.add_section(slot['series'])
            if slot['seq'] == 'linear':
                index = 0
            elif slot['seq'].isnumeric():
                # this would be an error in the schedule:
                # if seq is a number, there should have been
                # a 'linear' or 'random' before it which would
                # have created the section in settings.ini
                self.log.warning('Series {} with numeric seq {} before linear/random'.format(
                    slot['series'], slot['seq']))
                index = int(slot['seq']) - 2
            else:  # slot['seq'] is 'random'
                index = random.randrange(0, len(fn))
                # check to see if we've picked this index in the past
                rndseries = ConfigParser()
                rndseries_file = os.path.join(self.directory, 'config', slot['series'] + '.ini')
                rndseries.read(rndseries_file)
                name = os.path.splitext(
                    os.path.basename(fn[index]))[0]
                if rndseries.has_section(name):
                    tries = len(fn) * 10 + 1
                    while tries:
                        index = random.randrange(0, len(fn))
                        name = os.path.splitext(
                            os.path.basename(fn[index]))[0]
                        if not rndseries.has_section(name):
                            # we found an unplayed episode
                            break
                        tries -= 1
                    if not tries:
                        self.log.info("Unable to find unplayed episode for {}".format(slot['series']))
                        try:
                            dst = os.path.join(self.directory, 'config', slot['series'] + '.old')
                            os.rename(rndseries_file, dst)
                            self.log.warning("Series reset: moved {} to {}".format(rndseries_file, dst))
                        except OSError:
                            self.log.warning("Unable to create {}".format(dst))

        return index


    def update(self, slot, fn, index):
        """ update settings after adding a video """
        if not slot['seq'].isnumeric():
            self.settings.set(slot['series'], 'lastplayed', str(index))
            self.settings.set(slot['series'], 'lastdate', self.today)
            self.settings.set(slot['series'], 'skip', '0')
            if not slot['seq'] == 'linear':
                # seq is 'random': save name so we don't play it again
                if slot['series'].lower() == 'settings':
                    self.log.warning("Please do not name a series {}!".format(slot['series']))
                    self.log.warning("Changes to {} will not be tracked".format(slot['series']))
                else:
                    rndseries = ConfigParser()
                    rndseries_file = os.path.join(self.directory, 'config', slot['series'] + '.ini')
                    rndseries.read(rndseries_file)
                    name = os.path.splitext(
                        os.path.basename(fn[index]))[0]
                    if not rndseries.has_section(name):
                        self.log.debug("Marking played episode: {}".format(name))
                        rndseries.add_section(name)
                        rndseries.set(name, 'lastdate', self.today)
                        with open(rndseries_file, 'w') as rndf:
                            rndseries.write(rndf)
        else:
            self.settings.set(slot['series'], 'skip', str(slot['seq']))


    def write(self):
        """ write updates to settings.ini """
        self.log.info('Updating settings.ini')
        with open(self.settings_file, 'w') as setf:
            self.settings.write(setf)


    def timeslot(self):
        """ generator for main scheduling loop """
        # iterates through all 48 timeslots in a day
        # returns dictionary with keys as:
        #   label  - timeslot label (0000, 0030, 0100, etc.)
        #   mins   - start of slot as minutes since midnight
        #   series - name of series scheduled for this slot
        #   seq    - type of program (linear, random, etc.)

        # tuple of 1/2 hour time slots in a day - 24hr time format
        times = ('0000', '0030', '0100', '0130', '0200', '0230',
                 '0300', '0330', '0400', '0430', '0500', '0530',
                 '0600', '0630', '0700', '0730', '0800', '0830',
                 '0900', '0930', '1000', '1030', '1100', '1130',
                 '1200', '1230', '1300', '1330', '1400', '1430',
                 '1500', '1530', '1600', '1630', '1700', '1730',
                 '1800', '1830', '1900', '1930', '2000', '2030',
                 '2100', '2130', '2200', '2230', '2300', '2330')

        for i, x in enumerate(times):

            series = self.sched.get(x, 'series', fallback='error')

            # allow several names for a 'blank' slot
            if series.lower() in ('', 'blank', 'none', 'empty'):
                series = 'blank'

            seq = self.sched.get(x, 'seq', fallback='error')

            if seq.isnumeric():
                # sanity check: if numeric, seq should never be less than '2'
                if int(seq) < 2:
                    seq = '2'

            if series == 'error' or seq == 'error':
                self.log.warning('Error getting schedule entry for slot {}'.format(x))
                series = 'blank'
                seq = 'linear'

            yield {'label': x, 'mins': i * 30, 'series': series, 'seq': seq.lower()}
