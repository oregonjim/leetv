# leetv
## A personal television station :tv: designed for 24/7 unattended operation.
- - -

  Do you have a large collection of TV shows stored on a hard drive somewhere?
Have you spent weeks (or months) ripping all your TV and movie DVDs to media files?
Have you ever wanted a program that could take your entire collection and just
play it according to a daily schedule, all day long, every day (like a real TV station does),
without requiring you to do anything beyond the initial schedule programming?
Do you wish you could choose your OWN commercials to play between shows (perhaps
some memorable favorites from your childhood, or maybe a few of those SuperBowl halftime legends)
rather than watch the drivel that plagues today's television?  Want to get rid of Cable
because you realized that you're paying for 1000 channels worth of stuff that doesn't interest you?

That's what LeeTV is for.  It's a set-it-and-forget-it application that turns
an unused computer into an always on, always playing personal TV station - one
that plays the content YOU want.

My own setup has been running continuously for months now.  It requires
nothing of me.  I will occasionally ssh into my LeeTV box to change a
schedule, or to add a few more commercials that I found on YouTube, but that's it.
I don't even have to stop or restart anything.  It works so well that I added
a wireless HDMI transmitter so that the signal is available on any TV in the house!
- - -

LeeTV works with any operating system that supports Python 3.x and VLC or mpv.

  LeeTV and its utilities are written in Python 3.x.  I have tested it heavily
under Linux, almost as heavily under MacOS X, and lightly under Windows.  While
Windows 'works', it's not really suitable for use with anything labeled '24/7'.
- - -

Two usage scenarios are possible:

1. Automated - A dedicated computer, connected to a TV, is set up to run leetv once
a day as a cron job (Linux), LaunchAgent (MacOS X), or Task Scheduler task
(Windows).  Your scheduled shows are broadcast all day long, every day,
just like a real network TV station.  The computer need not be particularly
powerful - all it needs to do is be able to run VLC or mpv smoothly.  I have
even run it sucessfully on a Raspberry Pi 3 (though I had to build a custom
version of VLC with GPU hw acceleration in order to prevent overheating).  Any
PC made in the last 10 or so years will do fine.  Internet connectivity
is not required unless you want to have the (optional) hourly news and weather
updates.
2. On demand - you can run leetv on demand from your own PC.  It will behave
as though you have just 'turned on' the TV and will start playing whatever
is scheduled for 'now'.  You can optionally specify a start time and leetv will
pretend that it is running at that time in the schedule (in case you missed
your favorite show).
- - -
## REQUIREMENTS

### Hardware

Any computer and OS capable of running mpv (or VLC) smoothly, and
compatible with your TV's video/audio input (e.g. HDMI).


Internet connectivity only needed if weather/news updates are enabled.

Local network connectivity is desirable for remote control via ssh,
but not necessary.

Tested:
```
    Linux (various PCs, Fedora Linux)
    MacOS (2009 Mac Mini, MacOS Snow Leopard 10.6)
    MacOS (Macbook Pro, Core2Duo, MacOS El Capitan 10.11)
    Windows (Dell Core2Duo, Windows 7)
    Windows (MSI Stealth Pro i7, Windows 10)
    Raspbian (Raspberry Pi 3, VLC built w/HW acceleration)
```
- - -
### Software

Note:  package names and install commands are for Fedora/Redhat Linux.
Other distributions (e.g. Debian, Ubuntu) may have slightly
different package names.  Substitute ```apt-get``` for ```dnf```.
You typically need to prefix all commands with ```sudo```.

#### Manditory:

Python 3.x (likely already present)

mpv or VLC:
```dnf install mpv```
or
```dnf install vlc```

ffprobe (part of the ffmpeg package):
```dnf install ffmpeg```

#### Optional:

If you want to see memory usage: ```dnf install python3-psutil```

If you want to normalize audio on a bunch of videos (e.g. commercials): ```pip3 install ffmpeg-normalize```

Fonts used by various utilities: ```dnf install bitstream-vera*```

##### For ltv-createbumper:

Animated text-on-video: ```dnf install python3-numpy```

Compositing videos: ```pip3 install moviepy```


##### For ltv-print:

To print out your schedule like a TV guide: ```pip3 install beautifultable```

##### For ltv-getnewsweather:

Note: Some or all of these may not be needed, depending on how you want
to retrieve your news and weather content.
```
    dnf install python3-requests       (for grabbing an image from the web)
    dnf install python3-selenium       (for grabbing news)
    dnf install chromedriver           (for screenshot of web pages)
    dnf install ImageMagick            (to resize images for ffmpeg)
    pip3 install pyvirtualdisplay      (for grabbing web screenshots without disturbing local display)
    pip3 install pyscreenshot          (required by pyvirtualdisplay)
    dnf install xorg-x11-server-Xvfb   (virtual X server to host virtual display)
    dnf install python3-beautifulsoup4 (for parsing news feed)
```

- - -

## Overview

  The basic idea is to take a set of 'schedule' files consisting of 1/2 hour
'time slots', one for each day of the week, and a set of 'media list' files,
one for each TV series you have stored on local or remote media, and create a 24-hour
playlist (in one of several formats) according to said schedule, passing that
playlist to mpv or vlc. In addition, a short 'bumper' video is added to each
time slot.  Optionally, a short 'news' video can be shown at the top of each hour,
and a short 'weather' video can be shown at the bottom of each hour.  These videos
are created dynamically (called hourly by cron) while the playlist is running.
Further, each time slot is filled with randomly selected commercials from
a pool that you provide (YouTube is a rich source for these).  Even though the
commercials are chosen at random, they will not be repeated until the entire
pool is delpeted, at which point the pool is reset.  Similar to this is the
'MovieNight' feature, where full length movies can be added into the mix.
They can also be chosen at random, and are added to a list when chosen so that
they will not be repeated.

  When creating the daily schedules, each 1/2 hour time slot can specify
a particular series to play in either linear or random order.  Also supported
is a 'binge watch' mode, where a single series can be played in as many
time slots as desired.  Additionally, for those who do not watch TV 24 hours a day,
slots can be left 'blank' and a static 'fill' video will be played instead.

  While the time slots are divided into 1/2 hour intervals, you are not
limited to only 1/2 hour shows - the program will do the 'right thing'
no matter what the video duration is.  For example, say you have a series
scheduled at 8pm whose average episode length is 55 minutes.  You can simply
leave the 8:30pm slot blank, and the program will fill the remaining 5 minutes
with commercials, or specify another series for the 8:30pm slot, and the program
will insert the second series only if there is room for it without bumping into
the 9pm slot.  Conversely, if the main program video for a given time slot is
only 10 minutes long (e.g. a cartoon), rather than fill the time slot with
20 minutes of commercials, the program will try to fit more program
videos (as many as will fit) from that series into the time slot before
resorting to commercials.
- - -

  A number of utility programs are included to create the required
media list files, bumper videos, news & weather videos, and to analyze
various aspects of the system.  Note that, while the 24-hour playlist
is created with millisecond precision, network hiccups on remote filesystems
and hard drive access delays can cause a bit of drift.  I have noticed
up to a minute or two of total drift over a 24 hour period,


## Quickstart :


  Clone this repository.  Optionally add it to your $PATH.
- - -

  Look at the requirements listed above.  At a minimum, you need
  Python 3, ffprobe, and either mpv (default) or VLC.  Everything
  else is optional and used mostly for customization.  The two
  essential programs are ```leetv``` (the main program) and
  ```ltv-listmedia``` (used to generate your media lists).
- - -

  The next thing to do is run ```leetv``` once from the command line.
You will get an error message, but this will create the configuration
directory tree inside your 'HOME' directory and MOST of the necessary
files within it.  Here is a picture of what you should have after completing
this quickstart:
```
~/.leetv:
    bumper.mp4      # shown at start of every time slot
    reset.mp4       # shown in place of bumper.mp4 whenever
                    # the commercial pool is reset
    fill.mp4        # shown for 'blank' time slots
    news.mp4        # shown at top of hour (created dynamically)
    weather.mp4     # shown at bottom of hour (created dynamically)
    config/         # global settings go here
    log/            # logs go here
    media/          # all your media list files (NOT media files themselves!)
    sched/          # program schedules for each day of the week

~/.leetv/config:
    settings.ini    # global settings
    movies.ini      # list of movies already played (created as needed)
    used.lst        # list of commercials already used (created as needed)

~/.leetv/log:
                    # initially empty
                    # daily logs go here
~/.leetv/media:
                    # initially empty
                    # you will create one '.lst' file for
                    # each TV series with 'ltv-listmedia'
                    # each file will contain a list of video
                    # files belonging to that series along with
                    # the duration of each video in milliseconds
~/.leetv/sched:
    mon.ini         # each file contains 48 1/2 hour time slots
    tue.ini         # that you fill in with your desired
    wed.ini         # viewing schedule
    thu.ini
    fri.ini
    sat.ini
    sun.ini
```
- - -

  Next, create all your media list files using ```ltv-listmedia```.  Note that all of
the utilities, including ```ltv-listmedia```, support a '--help' option to explain basic usage.

An example:

```$ ltv-listmedia -v -d /mnt/tv/myshow/ -n MyShow```

This will create the media list file ```~/.leetv/media/MyShow.lst``` containing the
filenames and durations of all video files under the directory ```/mnt/tv/myshow/```.
You can then specify the name ```MyShow``` in the schedule(s) to refer to this series.
Note that the list is sorted alphanumerically, so if you want to play all the episodes
in a series in order, they must be named in that order.  It helps to prefix file
names with, e.g. 3x1 or S03E01 for season 3, episode 1.  Note also that the list is
created recursively, so a subdirectory named 'Season 1' will come before another
subdirectory named 'Season 2'.  This lends itself naturally to the way most people
organize their media files, but it helps to be aware of it.

Note that you must create one media list file named ```Commercials```.  While you will
never specify this file explicitly in the schedule, leetv will draw upon this list
to fill empty time between scheduled programs.
- - -

  Next, edit the .ini files in ```~/.leetv/sched/``` to reflect your desired schedule.  I
am working on a graphical configuration editor, but it's not finished yet.  Besides,
the schedule format is simple and easily edited with any standard text editor.
Each time slot is named ```[xxxx]```, where 'xxxx' is the start time of that slot in 24 hour
(military) format.  So slot ```[0000]``` is midnight, ```[2000]``` is 8pm, etc.  Inside each slot
are two fields: ```series``` and ```seq```.  Series is the name of one of your media lists created
above (e.g. 'MyShow', without the .lst extension).  You can leave slots blank if no
programming is desired at that time (the 'fill' video will be shown).  The 'seq' field
can be set to 'linear', 'random', or a numeric sequence.  Linear means that your shows
will be played in order, day after day.  Random will pick a random episode.  A numeric sequence is for
when you want 'binge watch' mode - the same series in more than one time slot in a given
day.  In this case, the FIRST time slot specifies linear or random for 'seq', the second
slot specifies the numeric value '2', the third slot is '3', and so on.  Here are some
examples:
```
  [0000]
  series = MidnightMystery
  seq = linear

  [0900]
  series = MorningCartoon
  seq = random

  [1400]
  series = BingeShow
  seq = linear

  [1430]
  series = BingeShow
  seq = 2

  [1500]
  series = BingeShow
  seq = 3

  [1800]        # (blank slot)
  series = blank
  seq = linear  # (can be anything)
```
  (Of course, a full daily schedule will have 48 of these 1/2 hour slots.  They were
  created automatically the first time you ran leetv.  While you can leave slots
  blank, you should not delete them.  Each schedule file must have all 48 slots present.)

  A special case is the series named ```MovieNight``` (by default - this can be changed
in ```settings.ini```).  If you specify this name for the series, leetv will keep track of all
the videos played (in ```~/.leetv/config/movies.ini```) and never play the same movie twice.
I use this to play a random movie from my collection a couple of times a week - and I
don't want to see the same movie again unless I delete it from ```movies.ini``` (or delete
the movies.ini file altogether).  Nothing says that the ```MovieNight``` list has to contain
movies - you can use it for any collection of videos, including a normal TV series.
The only difference is that with a 'regular' series, if random order is chosen, there
is the possibility of choosing an episode that has been played in the past.  I rarely
use 'normal' random mode except perhaps for cartoons and collections of unrelated videos.
- - -

  OK, there is only one more task to do before you can start enjoying your TV station!
It's time to create the 'static' videos: ```bumper.mp4```, ```reset.mp4```, and ```fill.mp4```.  Default
videos are provided in the distribution to get you started, but this is an area intended for
customization.  You can
get as fancy or creative as you want here, or you can be done with it in a minute or two.
The basic idea is to pick a still image and optionally a soundrack, and run them through
the ```makevideos``` shell script.  This will call ffmpeg to create the videos.  Optionally,
you can postprocess with the ```ltv-createbumper``` utility to create animated text effects
if you desire to.  If you don't care about being notified whenever the pool of commercials
is reset, you can make the ```bumper.mp4``` and ```reset.mp4``` videos the same.  There are two more
videos that are used in this process: ```weather.mp4``` and ```news.mp4```.  These are created
automatically on the hour by ```ltv-getnewsweather``` (if you have added it as a cron job -
see the comments in the file itself for details).

  There is one rule to remember when creating all of these videos:
```
  bumper.mp4 + news.mp4 + fill.mp4 must == 30 minutes
  bumper.mp4 + weather.mp4 + fill.mp4 must == 30 minutes

  The defaults are:
   bumper.mp4           = 5 seconds
   news.mp4/weather.mp4 = 15 seconds
   fill.mp4             = 1780 seconds (1/2 hr - 20 seconds)
```
  This ensures that 'blank' (unprogrammed) slots are filled exactly and don't
waste a bunch of commercials to fill unused time.  You can change the individual times
if you like, as long as the totals add up correctly.  For example, if you want your news
and weather videos to be 30 seconds longer, then make the fill video 30 seconds shorter.
The filenames and
durations for all these 'canned' videos are stored at the top of ```settings.ini```.  If
you change from the defaults, be sure to update ```settings.ini```.

  The other 'canned' videos, news.mp4 and weather.mp4, can be created dynamically
every hour by the utility ```ltv-getnewsweather```.  There are two samples provided
(```sample-news.mp4``` and ```sample-weather.mp4```) to show you what ltv-getnewsweather can do.
Note that you will have to edit the
source of this program somewhat to point it to the right sources for your
preferred news and weather.  See the file itself for details.  There is a 'hard'
way and an 'easy' way documented...

  Now, if you don't want to bother with this canned video business, you
can easily disable it all by running leetv with the ```--exclude``` option.  This
will totally ignore these videos and leave you with only your scheduled videos
and commercials.
The downside is that you'll be playing lots of commercials
in unprogrammed slots, you won't get hourly news and weather updates, and your
TV station won't look as 'professional' - but that may not matter to you.  Alternatively,
you can just use the provided default videos until you decide to customize.
- - -

  OK, it's time to test your setup.  run ```leetv -v``` from the command line and see
what happens.  If all goes well, you'll see a bunch of info messages as
the playlist is created, followed by the launch of mpv to start playing.
A log file will also be found in the log directory.  You can add ```-l debug```
for more verbose diagnostics.

  If all is working, you can add ```leetv``` as a cron job to start every day
at midnight, and ```ltv-getnewsweather``` to run twice an hour (once to get the
news and once to get the weather).  See the comments at the top of ```leetv```
for more details.  Enjoy your TV station!  In the meantime, I'll keep
working on the documentation and the graphical configuration editor...

