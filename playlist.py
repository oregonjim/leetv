# -*- coding: utf-8 -*-
""" LeeTV playlist class module """
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
#  playlist.py
#
#  Playlist class for leetv
#  (also validates/creates configuration directory tree and files)
#
#  Last update: 2018-06-15
#
import sys
import os
import platform
import subprocess
import shutil
import random
import math
import urllib.parse
from configparser import ConfigParser

from leeutils import which


class Playlist:
    """ LeeTV playlist class """

    # list of videos to build playlist
    master_name = []
    # list of running times for each video
    master_time = []
    # list of all commercials
    cn = []
    # running times for all commercials
    ct = []
    # list of commercials already used today
    used = []
    # filename for storing used commercials
    used_filename = ''
    # total playlist running time so far (milliseconds)
    running_time_ms = 0
    # maximum time drift due to incomplete commercial fills
    drift_ms = 0
    # flag to play a different bumper video when
    # commercial pool is reset
    commercial_reset = False

    # default values
    commercials_name = 'Commercials'
    bumper_video_name = 'bumper.mp4'
    bumper_video_time = '5000'
    reset_video_name = 'reset.mp4'
    reset_video_time = '5000'
    fill_video_name = 'fill.mp4'
    fill_video_time = '1770000'
    weather_video_name = 'weather.mp4'
    weather_video_time = '25000'
    news_video_name = 'news.mp4'
    news_video_time = '25000'

    bumper_video = ''
    fill_video = ''
    reset_video = ''
    weather_video = ''
    news_video = ''
    directory = ''
    log = ''
    subdirs = ('config', 'sched', 'media', 'log')
    schedfiles = ('mon.ini', 'tue.ini', 'wed.ini', 'thu.ini',
                  'fri.ini', 'sat.ini', 'sun.ini')

    def __init__(self, logger, exclude):
        """ Tv object constructor """
        self.log = logger

        # check the config directory tree for validity
        self.directory = os.path.join(os.getenv('HOME'), '.leetv')
        self._check_prerequisites(self.directory, exclude)

        # get list of used commercials and remove them from the master commercial list
        self.used_filename = os.path.join(self.directory, 'config', 'used.lst')
        if os.path.isfile(self.used_filename):
            with open(self.used_filename, 'r') as fp:
                self.used = fp.readlines()
            for i, line in enumerate(self.used):
                self.used[i] = line.rstrip('\n')
            self.log.debug('Before commercial removal: {}'.format(len(self.cn)))

            # remove used commercials from cn, ct
            for line in self.used:
                for i, m in enumerate(self.cn):
                    if line == m:
                        self.cn.pop(i)
                        self.ct.pop(i)
                        break

            self.log.debug('Total used commercials {}'.format(len(self.used)))
            self.log.debug('After commercial removal: {}'.format(len(self.cn)))

    def _check_prerequisites(self, directory, exclude):
        """ sanity check for minimum required LeeTV configuration files """
        met = True

        # main directory
        if not os.path.exists(directory):
            met = False
            self.log.warning('Master directory does not exist!: {}'.format(directory))
            self.log.warning('Creating master directory and config files...')
            self._create_default_tree(directory)

        # subdirectories
        for i in self.subdirs:
            subdir = os.path.join(directory, i)
            if not os.path.exists(subdir):
                met = False
                self.log.warning('Missing directory! {}'.format(subdir))

        # schedule files
        for i in self.schedfiles:
            filen = os.path.join(directory, 'sched', i)
            if not os.path.isfile(filen):
                met = False
                self.log.warning('Missing file! {}'.format(filen))

        # at least one '.lst' file in the media directory
        if met:
            mediadir = os.path.join(directory, 'media')
            mediafiles = os.listdir(mediadir)
            if not mediafiles:
                met = False
                self.log.warning('No media list files found!')
            else:
                mf = False
                for filen in mediafiles:
                    if '.lst' in filen:
                        mf = True
                if not mf:
                    met = False
                    self.log.warning('No media list files found!')

            # open global settings file
            settings = ConfigParser()
            settings_file = os.path.join(directory, 'config', 'settings.ini')
            if os.path.isfile(settings_file):
                settings.read(settings_file)

            # get global default settings
            if settings.has_section('LEETV_SETTINGS'):
                self.commercials_name = settings.get('LEETV_SETTINGS', 'commercials', fallback=self.commercials_name)
                self.bumper_video_name = settings.get('LEETV_SETTINGS', 'bumpervideo', fallback=self.bumper_video_name)
                self.bumper_video_time = settings.get('LEETV_SETTINGS', 'bumpervideotime', fallback=self.bumper_video_time)
                self.reset_video_name = settings.get('LEETV_SETTINGS', 'resetvideo', fallback=self.reset_video_name)
                self.reset_video_time = settings.get('LEETV_SETTINGS', 'resetvideotime', fallback=self.reset_video_time)
                self.fill_video_name = settings.get('LEETV_SETTINGS', 'fillvideo', fallback=self.fill_video_name)
                self.fill_video_time = settings.get('LEETV_SETTINGS', 'fillvideotime', fallback=self.fill_video_time)
                self.weather_video_name = settings.get('LEETV_SETTINGS', 'weathervideo', fallback=self.weather_video_name)
                self.weather_video_time = settings.get('LEETV_SETTINGS', 'weathervideotime', fallback=self.weather_video_time)
                self.news_video_name = settings.get('LEETV_SETTINGS', 'newsvideo', fallback=self.news_video_name)
                self.news_video_time = settings.get('LEETV_SETTINGS', 'newsvideotime', fallback=self.news_video_time)

            else:
                settings.add_section('LEETV_SETTINGS')
                settings.set('LEETV_SETTINGS', 'commercials', self.commercials_name)
                settings.set('LEETV_SETTINGS', 'bumpervideo', self.bumper_video_name)
                settings.set('LEETV_SETTINGS', 'bumpervideotime', self.bumper_video_time)
                settings.set('LEETV_SETTINGS', 'resetvideo', self.reset_video_name)
                settings.set('LEETV_SETTINGS', 'resetvideotime', self.reset_video_time)
                settings.set('LEETV_SETTINGS', 'fillvideo', self.fill_video_name)
                settings.set('LEETV_SETTINGS', 'fillvideotime', self.fill_video_time)
                settings.set('LEETV_SETTINGS', 'weathervideo', self.weather_video_name)
                settings.set('LEETV_SETTINGS', 'weathervideotime', self.weather_video_time)
                settings.set('LEETV_SETTINGS', 'newsvideo', self.news_video_name)
                settings.set('LEETV_SETTINGS', 'newsvideotime', self.news_video_time)

                self.log.info('Adding defaults to settings.ini')
                with open(settings_file, 'w') as setf:
                    settings.write(setf)

        # A 'Commercials.lst' is manditory
        # (preload it here while we're checking)
        cfile = os.path.join(self.directory, 'media', self.commercials_name + '.lst')
        if not os.path.isfile(cfile):
            met = False
            self.log.warning("{} does not exist!".format(cfile))
        else:
            # preload list of commercials since we'll be using it often
            self.cn, self.ct = self.get_filelist(cfile, shuffle=True)

        if not exclude:
            # check for support videos
            vids = (self.bumper_video_name, self.reset_video_name,
                    self.weather_video_name, self.news_video_name,
                    self.fill_video_name)
            for vid in vids:
                path = os.path.join(self.directory, vid)
                if not os.path.isfile(path):
                    met = False
                    self.log.warning("{} does not exist!".format(path))

            # create playlist-ready path names
            self.bumper_video = urllib.parse.quote(os.path.join(self.directory, self.bumper_video_name))
            self.reset_video = urllib.parse.quote(os.path.join(self.directory, self.reset_video_name))
            self.weather_video = urllib.parse.quote(os.path.join(self.directory, self.weather_video_name))
            self.news_video = urllib.parse.quote(os.path.join(self.directory, self.news_video_name))
            self.fill_video = urllib.parse.quote(os.path.join(self.directory, self.fill_video_name))

        if not met:
            self.log.error('Please check the LeeTV documentation for proper setup.')

        return met

    def _create_default_tree(self, directory):
        """ create the base .leetv directory tree and default contents """

        # tuple of 1/2 hour time slots in a day - 24hr time format
        times = ('0000', '0030', '0100', '0130', '0200', '0230',
                 '0300', '0330', '0400', '0430', '0500', '0530',
                 '0600', '0630', '0700', '0730', '0800', '0830',
                 '0900', '0930', '1000', '1030', '1100', '1130',
                 '1200', '1230', '1300', '1330', '1400', '1430',
                 '1500', '1530', '1600', '1630', '1700', '1730',
                 '1800', '1830', '1900', '1930', '2000', '2030',
                 '2100', '2130', '2200', '2230', '2300', '2330')

        try:
            os.mkdir(directory)
        except FileExistsError:
            pass

        # create the required subdirectories
        for sd in self.subdirs:
            sdir = os.path.join(directory, sd)
            try:
                os.mkdir(sdir)
            except FileExistsError:
                pass

        # create the 7 daily schedule files
        for f in self.schedfiles:
            fn = os.path.join(directory, 'sched', f)
            with open(fn, 'w') as sc:
                for entry in times:
                    sc.write('[{}]\n'.format(entry))
                    sc.write('series = blank\n')
                    sc.write('seq = linear\n\n')

        # copy the LeeTV media files
        srcdir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'dist')
        files = (self.bumper_video_name,
                 self.reset_video_name,
                 self.fill_video_name,
                 self.news_video_name,
                 self.weather_video_name)
        for f in files:
            src = os.path.join(srcdir, f)
            dst = os.path.join(directory, f)
            try:
                shutil.copyfile(src, dst)
            except IOError:
                self.log.error('Unable to copy {} to {}'.format(src, dst))

        self.log.warning('Default configuration tree created.')
        self.log.error('Please see LeeTV documentation to create media list files.')

    def get_medialist(self, slot, shuffle=False):
        """ get media file list by slot object, optionally shuffled """
        filename = os.path.join(self.directory, 'media', slot['series'] + '.lst')
        return self.get_filelist(filename, shuffle=shuffle)

    def get_filelist(self, filename, shuffle=False):
        """ get media file list by filename, optionally shuffled """
        f = list()
        t = list()
        if not os.path.isfile(filename):
            self.log.error('File {} does not exist!'.format(filename))

        with open(filename, 'r') as fp:
            lst = fp.readlines()

        if not lst:
            self.log.error('File {} has zero entries!'.format(filename))

        if shuffle:
            random.shuffle(lst)
        for x in lst:
            a, b = x.split(' : ')
            f.append(a.strip())
            t.append(b.strip())
        return (f, t)

    def add_video(self, vname, vtime, logging=True, series=None):
        """ add video to master list """
        s = "{} [{}]: {} : {:.3f} minutes".format(
            self.running_time_ms_to_timestamp(self.running_time_ms),
            series,
            os.path.basename(urllib.parse.unquote(vname)),
            self.ms_to_min(int(vtime)))

        if logging:
            self.log.info(s)
        else:
            self.log.debug(s)

        self.master_name.append(vname)
        self.master_time.append(vtime)
        self.running_time_ms += int(vtime)

    def add_bumper_video(self):
        """ add bumper video to master list """
        if self.commercial_reset:
            self.add_video(self.reset_video, self.reset_video_time, logging=False)
            self.commercial_reset = False
        else:
            self.add_video(self.bumper_video, self.bumper_video_time, logging=False)

    def add_weather_video(self):
        """ add weather video to master list """
        self.add_video(self.weather_video, self.weather_video_time, logging=False)

    def add_news_video(self):
        """ add news video to master list """
        self.add_video(self.news_video, self.news_video_time, logging=False)

    def add_fill_video(self):
        """ add fill video to master list """
        self.add_video(self.fill_video, self.fill_video_time, logging=False)

    def do_commercial_fill(self, target_ms):
        """ add random commercials to master list, up to target_ms """
        # I used to use a best-fit algorithm here, but it
        # produced repeating patterns of commercials which
        # was not the desired result.  So, now we go through the
        # pool randomly several times, accumulating anything that will
        # fit, until we've gotten as close as possible to the target.
        # Any leftover time (drift) will self-correct at the next time slot.
        initial_target_ms = target_ms
        # set a realistic limit for # of retries
        limit = len(self.cn) * 10 + 1
        # try to fill remaining time to within 5 seconds
        self.log.debug('Commercial Pool: {}'.format(len(self.cn)))
        while limit and (target_ms > 5000):
            if len(self.cn) < 10:
                # we're almost out of commercials!
                self.log.warning('Commercial pool depleted! Reloading...')
                # reload master pool, reset used list
                self.cn, self.ct = self.get_filelist(os.path.join(self.directory,
                                                                  'media',
                                                                  self.commercials_name + '.lst'),
                                                     shuffle=True)
                self.used.clear()
                limit = len(self.cn) * 10 + 1
                self.commercial_reset = True

            index = random.randrange(0, len(self.cn))
            clen = int(self.ct[index])
            if clen <= target_ms:
                self.add_video(self.cn[index], self.ct[index], logging=False, series='Commercial')
                self.used.append(self.cn[index])
                target_ms -= clen
                # remove used commercial from pool
                self.cn.pop(index)
                self.ct.pop(index)
            else:
                limit -= 1

        self.log.debug("Filled: {:.3f}m Leftover: {:.3f}s".format(
            (initial_target_ms - target_ms) / 1000 / 60,
            target_ms / 1000))
        # update maximum drift
        if target_ms > self.drift_ms:
            self.drift_ms = target_ms

    def write_used(self):
        """ write commercial updates to used.lst """
        self.log.info('Updating used.lst')
        with open(self.used_filename, 'w') as usedf:
            for i in self.used:
                usedf.write(i + '\n')

    def write_playlist(self, name, fmt='m3u8'):
        """ create a playlist in one of several formats """

        self.log.info("Creating {} playlist {}".format(fmt, name))
        playlist = open(name, 'w')
        number_of_videos = len(self.master_name)

        if fmt.lower() == 'xspf':
            playlist.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            playlist.write(
                '<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">\n')
            playlist.write('\t<title>Playlist</title>\n')
            playlist.write('\t<trackList>\n')

            for i in range(number_of_videos):
                playlist.write('\t\t<track>\n')
                playlist.write('\t\t\t<location>file://{}</location>\n'.format(self.master_name[i]))
                playlist.write('\t\t\t<duration>{}</duration>\n'.format(self.master_time[i]))
                playlist.write('\t\t\t<extension application="http://www.videolan.org/vlc/playlist/0">\n')
                playlist.write('\t\t\t\t<vlc:id>{}</vlc:id>\n'.format(i))
                playlist.write('\t\t\t</extension>\n')
                playlist.write('\t\t</track>\n')

            playlist.write('\t</trackList>\n')
            playlist.write('\t<extension application="http://www.videolan.org/vlc/playlist/0">\n')

            for i in range(number_of_videos):
                playlist.write('\t\t\t<vlc:item tid="{}"/>\n'.format(i))

            playlist.write('\t</extension>\n')
            playlist.write('</playlist>\n')
            playlist.close()

        elif fmt.lower() == 'm3u8':

            playlist.write('#EXTM3U\n')
            for i in range(number_of_videos):
                name = urllib.parse.unquote(self.master_name[i])
                playlist.write('#EXTINF:{}, {}\n'.format(
                    int(self.master_time[i]) // 1000,
                    os.path.splitext(os.path.basename(name))[0]))
                playlist.write('{}\n'.format(name))
            playlist.close()

        elif fmt.lower() == 'pls':

            playlist.write('[playlist]\n')
            for i in range(number_of_videos):
                name = urllib.parse.unquote(self.master_name[i])
                title = os.path.splitext(os.path.basename(name))[0]
                length = int(self.master_time[i]) // 1000
                seq = i + 1
                playlist.write('File{}={}\n'.format(seq, name))
                playlist.write('Title{}={}\n'.format(seq, title))
                playlist.write('Length{}={}\n'.format(seq, length))

            playlist.write('NumberOfEntries={}\n'.format(number_of_videos))
            playlist.write('Version=2\n')
            playlist.close()

        else:
            self.log.error('Unknown playlist type: {}'.format(fmt))

        self.log.info("{} videos added to the playlist".format(number_of_videos))

    def start_player(self, name, playlist, offset, streaming=False):
        """ launch a media player with playlist """

        if name.lower() != 'none':
            self.log.info('Starting {}...'.format(name.lower()))

        host = platform.system()

        if name.lower() == 'mpv':
            if host == 'Linux' or host == 'Darwin':
                cmd = which('mpv')
                if not cmd:
                    self.log.error('mpv not found in path!')
            # *** these need to be checked ***
            elif host == 'Windows':
                cmd = '"C:\\Program Files\\mpv\\mpv.exe"'
            elif host.startswith('CYGWIN'):
                cmd = r'/cygdrive/c/Program\ Files/mpv/mpv.exe'
            else:
                self.log.error('Unsupported system!')

            if streaming:
                # *** need to add streaming cmds ***
                cmdline = ' '.join([cmd,
                                    '--fullscreen',
                                    '--ontop',
                                    '--no-sub-auto',
                                    '--no-sub-visibility',
                                    '--playlist=' + playlist])
            else:
                cmdline = ' '.join([cmd,
                                    '--fullscreen',
                                    '--ontop',
                                    '--no-sub-auto',
                                    '--no-sub-visibility',
                                    '--playlist=' + playlist])

            result = subprocess.Popen(cmdline,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL,
                                      # stdout=subprocess.PIPE,
                                      # stderr=subprocess.PIPE,
                                      shell=True)

        elif name.lower() == 'vlc':

            scmd = "--sout '#transcode{vcodec=mp4v,acodec=mpga,vb=800,ab=128,deinterlace}:rtp{mux=ts,dst=239.255.0.0,sdp=sap,name=LeeTV}'"
            # "--sout '#transcode{vcodec=mp4v,acodec=mpga,vb=800,ab=128}:standard{access=http,mux=ogg,dst=192.168.0.28:8080}'"
            # "--sout '#transcode{vcodec=x264{profile=baseline,level=13,crf=24},acodec=mp4a,ab=128}:rtp{mux=ts,dst=239.255.0.0,sdp=sap,name=\"LeeTV\"}'"
            # "--sout '#duplicate{dst=display,dst=\"transcode{vcodec=mp4v,acodec=mpga,vb=800,ab=128,deinterlace}:rtp{mux=ts,dst=239.255.0.0,sdp=sap,name=LeeTV}'",
            # "--sout '#duplicate{dst=display,dst=\"transcode{vcodec=x264{profile=baseline,level=13,crf=24},acodec=mp4a,ab=128}:rtp{mux=ts,dst=239.255.0.0,sdp=sap,name=LeeTV}'",

            # NOTE: 'cvlc' is the command line variant of VLC
            # that runs without a GUI interface
            if host == 'Linux':
                cmd = which('cvlc')
                if not cmd:
                    cmd = which('vlc')
                    if not cmd:
                        self.log.error('vlc not found in path!')
            elif host == 'Darwin':
                cmd = '/Applications/VLC.app/Contents/MacOS/VLC'
            elif host == 'Windows':
                cmd = '"C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"'
            elif host.startswith('CYGWIN'):
                cmd = r'/cygdrive/c/Program\ Files/VideoLAN/VLC/vlc.exe'
            else:
                self.log.error('Unsupported system!')

            if streaming:
                cmdline = ' '.join([cmd,
                                    # '--fullscreen',
                                    # '--no-video-title-show',
                                    '--play-and-exit',
                                    '--verbose 0',
                                    '--quiet-synchro',
                                    playlist,
                                    scmd])
            else:
                cmdline = ' '.join([cmd,
                                    '--fullscreen',
                                    '--no-video-title-show',
                                    '--play-and-exit',
                                    '--verbose 0',
                                    '--quiet-synchro',
                                    playlist])

            result = subprocess.Popen(cmdline,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL,
                                      # stdout=subprocess.PIPE,
                                      # stderr=subprocess.PIPE,
                                      shell=True)
        elif name.lower() == 'none':
            # allow user to select 'none' for player
            result = None

        else:
            self.log.error('Unknown player: {}'.format(name))

        return result

    def get_offset_into_playlist(self, now):
        """ return seconds since midnight """
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds = (now - midnight).seconds
        return seconds

    def ms_to_min(self, ms):
        """ convert milliseconds to minutes """
        return ms / 1000 / 60.0

    def ms_to_hr(self, ms):
        """ convert milliseconds to hours """
        return ms / 1000 / 60 / 60.0

    def min_to_ms(self, mn):
        """ convert minutes to milliseconds """
        return mn * 60 * 1000

    def running_time_ms_to_timestamp(self, running_time):
        """ convert ms since midnight to time string of form 'hh:mm:ss' """
        secs = running_time / 1000
        thishour = secs / 60 / 60
        x = int(thishour) * 60 * 60
        thismin = (secs - x) / 60
        thissec = secs % 60

        return '{:02.0f}:{:02.0f}:{:02.0f}'.format(
            math.trunc(thishour), math.trunc(thismin), math.trunc(thissec))
