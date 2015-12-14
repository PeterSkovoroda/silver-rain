#!/usr/bin/env python3
"""
Copyright (C) 2015 Petr Skovoroda <petrskovoroda@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA
"""

import json
import os
import re
import requests
import urllib.request

from collections import deque
from datetime import datetime
from datetime import timedelta
from gi.repository import GdkPixbuf

try:
    from lxml import etree
except ImportError as err:
    import xml.etree.ElementTree as etree

from . import config
from .globals import IMG_DIR, SCHED_FILE
from .msktz import MSK

SCHED_URL       = "http://silver.ru/programms/"
SILVER_RAIN_URL = "http://silver.ru"
USER_AGENT      = 'Mozilla/5.0 (X11; Linux x86_64) ' + \
                  'AppleWebKit/537.36 (KHTML, like Gecko) ' + \
                  'Chrome/41.0.2227.0 Safari/537.36'

# Use this list to operate with schedule
SCHED_WEEKDAY_LIST = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                      'Friday', 'Saturday', 'Sunday']


def str_time(start, end):
    """ Return time in HH:MM-HH:MM """
    s_h, s_m = divmod(int(start), 3600)
    e_h, e_m = divmod(int(end), 3600)
    return "{0:0=2d}:{1:0=2d}-{2:0=2d}:{3:0=2d}".format(s_h, s_m, e_h, e_m)

def parse_time(str):
    """ Return time in seconds """
    try:
        x = datetime.strptime(str, "%H:%M")
    except ValueError:
        # except 24:00
        # Fuck timedelta and python-floating-point-approximation shit
        # Just return the correct value
        return 86400.0
    d = timedelta(hours=x.hour, minutes=x.minute)
    return d.total_seconds()

class SilverSchedule():
    """
        __sched_week__      - full schedule
        __sched_day__       - daily agenda
        __event__           - currently playing

        Schedule list[weekday(0-6)]:
            0   Weekday             str
            1   IsParent            bool
            2   Time  (HH:MM-HH:MM) str
            3   Title               str
            4   URL                 str
            5   Host                [str]
            6   Icon                str
            7   start (seconds)     float
            8   end   (seconds)     float
            9   Icon URL            str
    """
    def __init__(self):
        self.__sched_week__ = [ [] for x in range(7) ]
        self.__sched_day__ = deque()
        self.__event__ = {}

    # Get current event values
    def get_event_title(self): return self.__event__["title"]
    def get_event_time(self): return self.__event__["time"]
    def get_event_url(self): return self.__event__["url"]
    def get_event_end(self): return self.__event__["end"]
    def get_event_position(self): return self.__event__["position"]
    def get_event_icon(self):
        """ Return pixbuf """
        # Download icon if it doesn't exist
        if not os.path.exists(self.__event__["icon"]):
            urllib.request.urlretrieve(self.__event__["icon_url"],
                                       self.__event__["icon"])
        return GdkPixbuf.Pixbuf.new_from_file(self.__event__["icon"])
    def get_event_host(self):
        str = ' и '.join(self.__event__["host"])
        return str

    def update_current_event(self):
        """ Update current event """
        newday = False
        if not len(self.__sched_day__):
            # It's a new day.
            # It's so mundane. What exciting things will happen today?
            self._sched_gen_daily_agenda()
            newday = True
        self.__event__ = self.__sched_day__.popleft()
        return newday

    def update_schedule(self, force_refresh=False):
        """ Retrieve schedule """
        if not force_refresh and os.path.exists(SCHED_FILE):
            # Read from file
            self._sched_get_from_file()
        else:
            # Backup
            sched_week_bak = self.__sched_week__
            sched_day_bak = self.__sched_day__
            # Clear
            self.__sched_week__ = [ [] for x in range(7) ]
            self.__sched_day__ = deque()
            # Load from website
            if not self._sched_get_from_html():
                self.__sched_week__ = sched_week_bak
                self.__sched_day__ = sched_day_bak
                return False
        # Generate schedule for today
        self._sched_gen_daily_agenda()
        # Update current event
        self.update_current_event()
        return True

    def fill_tree_strore(self, store):
        """ Fill TreeStore object """
        it = None
        for x in range(7):
            bg_dark = False
            ch_dark = bg_dark

            for item in self.__sched_week__[x]:
                ICON_EXIST = True
                host = ' и '.join(item["host"])
                font = config.font
                icon = None
                # Download icon if it doesn't exist
                if not os.path.exists(item["icon"]):
                    try:
                        urllib.request.urlretrieve(item["icon_url"],
                                                   item["icon"])
                    except urllib.error.URLError as e:
                        logging.error("Couldn't download icon from url:" +
                                      "{0}\n{1}".format(item["icon_url"], e))
                        ICON_EXIST = False
                # Insert program
                if item["is_main"]:
                    # Main event
                    bg_color = config.bg_colors[bg_dark]
                    fg_color = config.font_color
                    # Get pixbuf
                    if ICON_EXIST:
                        icon = GdkPixbuf.Pixbuf.new_from_file(item["icon"])
                    # Insert item
                    it = store.append(None, [item["weekday"], item["is_main"],
                                             item["time"], item["title"],
                                             item["url"], host, icon,
                                             bg_color, fg_color, font,
                                             False])
                    # Alternate row color
                    bg_dark = not bg_dark
                    ch_dark = bg_dark
                else:
                    # Child event
                    bg_color = config.bg_colors[ch_dark]
                    fg_color = config.font_color
                    # Get pixbuf
                    if ICON_EXIST:
                        icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                                    item["icon"], 60, 60, True)
                    # Insert item
                    store.append(it, [item["weekday"], item["is_main"],
                                 item["time"], item["title"], item["url"],
                                 host, icon, bg_color, fg_color, font,
                                 False])
                    # Alternate row color
                    ch_dark = not ch_dark

    def _sched_gen_daily_agenda(self):
        """ Create a list of main events for today """
        today = datetime.now(MSK())
        now = timedelta(hours=today.hour, minutes=today.minute,
                        seconds=today.second).total_seconds()
        position = 0
        for item in self.__sched_week__[today.weekday()]:
            if not item["is_main"]:
                continue
            else:
                item["position"] = position
                position = position + 1
            if item["end"] <= now:
                # Child or already ended. Skip
                continue
            self.__sched_day__.append(item)

    def _sched_get_from_file(self):
        """ Load schedule from file """
        f = open(SCHED_FILE, "r")
        self.__sched_week__ = json.load(f)
        f.close()

    def _sched_write_to_file(self):
        """ Save schedule on disk """
        f = open(SCHED_FILE, 'w')
        json.dump(self.__sched_week__, f)
        f.close()

    def _sched_get_from_html(self):
        """ Load schedule from site """
        # Create session with fake user-agent
        session = requests.Session()
        session.headers['User-Agent'] = USER_AGENT
        # Default event icon
        music_icon_src = ''
        # Weekdays parser
        wd_name_list = {'Вс' : [6], 'Пн' : [0], 'Вт' : [1], 'Ср' : [2],
                        'Чт' : [3], 'Пт' : [4], 'Сб' : [5],
                        'По будням' : list(range(0,5)),
                        'По выходным' : [5, 6]}
        # Download schedule
        try:
            resp = session.get(SCHED_URL)
            # Follow redirects
            resp = session.get(resp.url)
        except requests.exceptions.RequestException as e:
            logging.error(str(e))
            return False
        xhtml = resp.text
        # XXX XXX XXX
        # This is wrong
        # There must be another way
        # XXX XXX XXX
        xhtml = re.sub(
                r'^.*<div\ class="program-list">.*?(<tbody>.*?<\/tbody>).*$',
                r'\1', xhtml)
        # Handle unclosed img tags /* xhtml style */
        xhtml = re.sub(r'(<img.*?"\s*)>', r'\1/>', xhtml)
        # Parse xhtml text
        root = etree.fromstring(xhtml)
        for obj in root:
            # If time not presented
            if not len(obj[3]):
                # Event happens randomly or never
                continue
            # Get icon
            icon_src = obj[0][0][0].attrib['src'].split("?")[0]
            if icon_src[:7] != "http://":
                if icon_src[:2] == "//":
                    # //url/name.png
                    icon_src = "http:" + icon_src
                elif icon_src[0] == "/":
                    # /name.png
                    icon_src = SILVER_RAIN_URL + icon_src
                else:
                    # url/name.png
                    icon_src = "http://" + icon_src
            icon_name = icon_src.split("/")[-1]
            # Get title
            title = obj[1][0][0].text
            # Don't parse music. Just save icon location
            if title == "Музыка":
                music_icon_src = icon_src
                continue
            # Get program url
            url = SILVER_RAIN_URL + obj[1][0][0].attrib['href']
            # Get hosts
            host = []
            if len(obj[2]):
                # If hosts presented
                for it in obj[2][0]:
                    host.append(it[0][0].text[1:-1])
            # Get schedule
            sched = []
            for it in obj[3][0]:
                # Expecting "WD, WD, WD : HH:MM" format
                weekday, time = it.text.split(' : ')
                wd_list = weekday.split(', ')
                start, end = time.split('-')
                for wd in wd_list:
                    #  Weekday number,
                    #  HH:MM,
                    #  start in seconds,
                    #  end in seconds
                    sched.append([wd_name_list[wd], time,
                                  parse_time(start),
                                  parse_time(end)])
            # Event type
            is_main = False
            if sched[0][3] - sched[0][2] >= 3600:
                # At least 1 hour
                is_main = True
            # Insert
            for it in sched:
                for weekday in it[0]:
                    program = {}
                    program["weekday"] = SCHED_WEEKDAY_LIST[weekday]
                    program["is_main"] = is_main
                    program["time"] = it[1]
                    program["title"] = title
                    program["url"] = url
                    program["host"] = host
                    program["icon"] = IMG_DIR + icon_name
                    program["start"] = it[2]
                    program["end"] = it[3]
                    program["icon_url"] = icon_src
                    self.__sched_week__[weekday].append(program)

        for wd in range(7):
            # Sort schedule by start/parent
            self.__sched_week__[wd].sort(key = lambda x : \
                                         (x["start"], -x["is_main"]))
            # Remove duplicates
            prev = []
            for item in self.__sched_week__[wd]:
                if prev and prev["title"] == item["title"] and \
                        prev["end"] > item["start"]:
                    # If there are two identical programms in a row
                    # I can't resolve more complicated errors
                    # I just hope they will never happen
                    if prev["end"] > item["end"]:
                        item["end"] = prev["end"]
                    if prev["start"] < item["start"]:
                        item["start"] = prev["start"]
                    item["time"] = str_time(item["start"], item["end"])
                    self.__sched_week__[wd].remove(prev)
                prev = item
            # Fill spaces with music
            time = 0.0
            pos = 0
            last = {"end" : 0}
            for item in self.__sched_week__[wd]:
                if not item["is_main"]:
                    continue
                if item["start"] > time:
                    # If doesn't start right after the last one
                    program = {}
                    program["is_main"] = True
                    program["title"] = "Музыка"
                    program["url"] = "http://silver.ru/programms/muzyka/"
                    program["host"] = []
                    program["icon"] = IMG_DIR + music_icon_src.split("/")[-1]
                    program["icon_url"] = music_icon_src
                    program["weekday"] = SCHED_WEEKDAY_LIST[wd]
                    program["time"] = str_time(time, item["start"])
                    program["start"] = time
                    program["end"] = item["start"]
                    self.__sched_week__[wd].insert(pos, program)
                    pos = pos + 1
                time = item["end"]
                pos = pos + 1
                last = item
            # Check if last event doesn't go till 24:00
            if last["end"] < 86400.0:
                program = {}
                program["is_main"] = True
                program["title"] = "Музыка"
                program["url"] = "http://silver.ru/programms/muzyka/"
                program["host"] = []
                program["icon"] = IMG_DIR + music_icon_src.split("/")[-1]
                program["icon_url"] = music_icon_src
                program["weekday"] = SCHED_WEEKDAY_LIST[wd]
                program["time"] = str_time(last["end"], 86400.0)
                program["start"] = last["end"]
                program["end"] = 86400.0
                self.__sched_week__[wd].insert(pos, program)
            # Sort again
            self.__sched_week__[wd].sort(key = lambda x : \
                                         (x["start"], -x["is_main"]))
        # Save sched to file
        self._sched_write_to_file()
        return True
