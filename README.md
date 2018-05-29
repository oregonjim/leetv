# leetv
A personal television station designed for 24/7 unattended operation

NOTE:  This is a fully working program (I've been using it 24/7 for several
months now).  However, I have not finished the documentation nor have I added
the kind of exception handling necessary for a 'general public use' type of
application.  Also missing is an automated 'setup.py' installer.  These elements
will be added as time allows.

  LeeTV and its utilities are written in Python 3.x.  I have tested it heavily
under Linux, almost as heavily under MacOS X, and lightly under Windows.  While
Windows 'works', it's not really suitable for use with anything labeled '24/7'.

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

  A number of utility programs are included to create the required
media list files, bumper videos, news & weather videos, and to analyze
various aspects of the system.  Note that, while the 24-hour playlist
is created with millisecond precision, network hiccups on remote filesystems
and hard drive access delays can cause a bit of drift.  I have noticed
up to a minute or two of total drift over a 24 hour period,


Quickstart (until the documentation is finished):
-------------------------------------------------

  Clone this repository.  Optionally add it to your $PATH.

  The first thing to do is look at the file 'prerequisites.txt'.
It lists all of the necessary (and optional) components required
to run leetv.  There is nothing esoteric in there - most, if not all,
are included in the repositories of most Linux distributions.  Same
goes for MacOS using macports or homebrew, or Windows using Cygwin.

  The next thing to do is to run 'leetv' once from the command line.
This will create the configuration directory tree inside your 'HOME'
directory and most of the necessary files within it.  Here is a picture
of what you should have:
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
    tue.ini         # that you fill in with your desired schedule
    wed.ini
    thu.ini
    fri.ini
    sat.ini
    sun.ini
```
  Next, create all your media list files using ltv-listmedia.  All of
the utilities support a '--help' flag to show basic usage.  An example:

$ ltv-listmedia -v -d /mnt/tv/myshow -n MyShow

This will create the media list file '~/.leetv/media/MyShow.lst' containing the
filenames and durations of all video files under the directory '/mnt/tv/myshow'.
You can then specify the name 'MyShow' in the schedule(s) to refer to this series.
Note that the list is sorted alphanumerically, so if you want to play all the episodes
in a series in order, they must be named in that order.  It helps to prefix file
names with, e.g. 3x1 or S03E01 for season 3, episode 1.  Note also that the list is
created recursively, so a subdirectory named 'Season 1' will come before another
subdirectory named 'Season 2'.  This lends itself naturally to the way most people
organize their media files, but it helps to be aware of it.


  Next, edit the .ini files in ~/.leetv/sched/ to reflect your desired schedule.  I
am working on a graphical configuration editor, but it's not finished yet.  Besides,
the schedule format is simple and easily edited with any standard text editor.
Each time slot is named [xxxx], where 'xxxx' is the start time of that slot in 24 hour
(military) format.  So slot [0000] is midnight, [2000] is 8pm, etc.  Inside each slot
are two fields: series and seq.  Series is the name of one of your media lists created
above (e.g. 'MyShow', without the .lst extension).  You can leave slots blank if no
programming is desired at that time (the 'fill' video will be shown).  The 'seq' field
can be set to 'linear', 'random', or a numeric sequence.  Linear means that your shows
will be played in order.  Random will pick a random episode.  A numeric sequence is for
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
  series =
  seq =
```
  (Of course, a full daily schedule will have 48 of these 1/2 hour slots.  They were
  created automatically the first time you ran leetv.  While you can leave slots
  blank, you cannot delete them.  Each schedule file must have all 48 slots present.)

  A special case is the series named 'MovieNight' (by default - this can be changed
in settings.ini).  If you specify this name for the series, leetv will keep track of all
the videos played (in ~/.leetv/config/movies.ini) and never play the same movie twice.
I use this to play a random movie from my collection a couple of times a week - and I
don't want to see the same movie again unless I delete it from movies.ini (or delete
the movies.ini file altogether).  Nothing says that the MovieNight list has to contain
movies - you can use it for any collection of videos, including a normal TV series.
The only difference is that with a 'regular' series, if random order is chosen, there
is the possibility of choosing an episode that has been played in the past.  I rarely
use 'normal' random mode except perhaps for cartoons and collections of unrelated videos.

  OK, there is only one more task to do before you can start enjoying your TV station!
It's time to create the 'static' videos: bumper.mp4, reset.mp4, and fill.mp4.  You can
get as fancy or creative as you want here, or you can be done with it in a minute or two.
The basic idea is to pick a still image and optionally a soundrack, and run them through
the 'makevideos' shell script.  This will call ffmpeg to create the videos.  Optionally,
you can postprocess with the 'ltv-createbumper' utility to create animated text effects
if you desire to.  If you don't care about being notified whenever the pool of commercials
is reset, you can make the bumper.mp4 and reset.mp4 videos the same.  There are two more
videos that are used in this process: weather.mp4 and news.mp4.  These are created
automatically on the hour by 'ltv-getnewsweather' (if you have added it as a cron job -
see the comments in the file itself for details).

  There is one trick to remember when creating these videos:
```
  bumper.mp4 + news.mp4 + fill.mp4 must == 30 minutes
  bumper.mp4 + weather.mp4 + fill.mp4 must == 30 minutes

  The defaults are:
   bumper.mp4           = 5 seconds
   news.mp4/weather.mp4 = 15 seconds
   fill.mp4             = 1780 seconds (1/2 hr - 20 seconds)
```
  This ensures that 'blank' (unprogrammed) slots are filled exactly and don't
waste a bunch of commercials to fill unused time.  You can change the times
if you like, as long as the totals add up correctly.  The filenames and
durations for all these 'canned' videos are store at the top of settings.ini.

  Two other 'canned' videos, news.mp4 and weather.mp4, can be created dynamically
every hour by the utility 'ltv-getnewsweather'.  Note that you will have to edit the
source of this program somewhat to point it to the right sources for your
preferred news and weather.  See the file itself for details.  There is a 'hard'
way and an 'easy' way documented...

  Now, if you don't want to bother at all with this canned video business, you
can easily disable it all by running leetv with the --exclude option.
The downside is that you'll be playing lots of commercials
in unprogrammed slots, you won't get hourly news and weather updates, and your
TV station won't look as 'professional' - but that may not matter to you.

  OK, it's time to test your setup.  run 'leetv -v' from the command line and see
what happens.  If all goes well, you'll see a bunch of info messages as
the playlist is created, followed by the launch of mpv to start playing.
A log file will also be found in the log directory.  You can add '-l debug'
for more verbose diagnostics.

  If all is working, you can add leetv as a cron job to start every day
at midnight, and ltv-getnewsweather to run twice an hour (once to get the
news and once to get the weather).  See the comments at the top of leetv
for more details.  Enjoy your TV station!  In the meantime, I'll keep
working on the documentation and the graphical configuration editor...

