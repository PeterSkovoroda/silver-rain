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

from gi.repository import GdkPixbuf, Gtk, Gdk
import glob
import json
import logging
import os
import re
import requests
import urllib.request
from collections import deque
from datetime import datetime
from datetime import timedelta

try:
    from lxml import etree
except ImportError as err:
    import xml.etree.ElementTree as etree

import silver.config as config
from silver.globals import ICON
from silver.globals import IMG_DIR
from silver.globals import SCHED_FILE
from silver.gui.common import hex_to_rgba
from silver.msktz import MSK

SCHED_URL       = "http://silver.ru/programms/"
SILVER_RAIN_URL = "http://silver.ru"
USER_AGENT      = "Mozilla/5.0 (X11; Linux x86_64) " + \
                  "AppleWebKit/537.36 (KHTML, like Gecko) " + \
                  "Chrome/41.0.2227.0 Safari/537.36"

# Use this list to operate with schedule
SCHED_WEEKDAY_LIST = ["Monday", "Tuesday", "Wednesday", "Thursday",
                      "Friday", "Saturday", "Sunday"]
MUSIC = "Музыка"
MUSIC_URL = "http://silver.ru/programms/muzyka/"

def str_time(start, end):
    """ Return time in HH:MM-HH:MM """
    s_h, s_m = divmod(int(start), 3600)
    e_h, e_m = divmod(int(end), 3600)
    return "{0:0=2d}:{1:0=2d} - {2:0=2d}:{3:0=2d}".format(s_h, s_m, e_h, e_m)

def parse_time(str):
    """ Return time in seconds """
    try:
        x = datetime.strptime(str, "%H:%M")
    except ValueError:
        # except 24:00
        # Just return the correct value
        return 86400.0
    d = timedelta(hours=x.hour, minutes=x.minute)
    return d.total_seconds()

def parse_weekday(str):
    """ Return list from string """
    wd_parsed = []
    wd_list = str.split(", ")
    wd_name_list = {"Вс" : 6, "Пн" : 0, "Вт" : 1, "Ср" : 2,
                    "Чт" : 3, "Пт" : 4, "Сб" : 5}
    for wd in wd_list :
        x = wd.split('-')
        if len(x) > 1:
            wd_parsed += list(range(wd_name_list[x[0]], wd_name_list[x[1]]+1))
        elif x == "По будням" :
            wd_parsed += list(range(0,5))
        elif x == "По выходным" :
            wd_parsed += [5, 6]
        else :
            wd_parsed += [ wd_name_list[x[0].strip()] ]
    return wd_parsed

def parse_hosts(hosts):
    """ Return formatted string from list """
    if len(hosts) > 1 :
        str = ", ".join(hosts[:-1])
        str += " и " + hosts[-1]
    else :
        str = ''.join(hosts)
    return str

class SilverSchedule():
    """
        _sched_week      - full schedule
        _sched_day       - daily agenda
        _event           - currently playing

        Schedule list[weekday(0-6)]:
            position            int
            weekday             str
            is_parent           bool
            time  (HH:MM-HH:MM) str
            title               str
            url                 str
            host                [str]
            icon                str
            start (seconds)     float
            end   (seconds)     float
            cover               str
            record              bool
            play                bool
    """
    def __init__(self):
        self._sched_week = [ [] for x in range(7) ]
        self._sched_day = deque()
        self._event = {}
        self._SCHEDULE_ERROR = False

    def get_event_title(self):
        """ Return event title """
        if not self._SCHEDULE_ERROR:
            return self._event["title"]
        else:
            return "Silver-Rain"

    def get_event_time(self):
        """ Return event time hh:mm-hh:mm """
        if not self._SCHEDULE_ERROR:
            return self._event["time"]
        else:
            return "00:00-24:00"

    def get_event_url(self):
        """ Return event url """
        if not self._SCHEDULE_ERROR:
            return self._event["url"]
        else:
            return "http://silver.ru/"

    def get_event_end(self):
        """ Return end time in seconds """
        if not self._SCHEDULE_ERROR:
            return self._event["end"]
        else:
            return 86400.0

    def get_event_position(self):
        """ Return event position """
        if not self._SCHEDULE_ERROR:
            return self._event["position"]
        else:
            return 0

    def get_event_weekday(self):
        """ Return weekday """
        if not self._SCHEDULE_ERROR:
            return SCHED_WEEKDAY_LIST.index(self._event["weekday"])
        else:
            return datetime.now(MSK()).weekday()

    def get_event_icon(self):
        """ Return pixbuf """
        if not self._SCHEDULE_ERROR and self._event["icon"]:
            pb = GdkPixbuf.Pixbuf.new_from_file(self._event["icon"])
        else:
            icontheme = Gtk.IconTheme.get_default()
            pb = icontheme.load_icon(ICON, 256, 0)
            pb = pb.scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
        return pb

    def get_event_host(self):
        """ Return host """
        if not self._SCHEDULE_ERROR:
            str = parse_hosts(self._event["host"])
        else:
            str = ""
        return str

    def get_event_cover(self):
        file = ""
        if not self._SCHEDULE_ERROR and config.background_image:
            file = self._event["cover"]
        return file

    def get_record_status(self):
        """ Return True if should be recorded """
        if not self._SCHEDULE_ERROR:
            return self._event["record"]
        else:
            return False

    def get_play_status(self):
        """ Return True if should start playing """
        if not self._SCHEDULE_ERROR:
            return self._event["play"]
        else:
            return False

    def update_event(self):
        """ Update current event """
        if not len(self._sched_day):
            # It's a new day.
            # It's so mundane. What exciting things will happen today?
            self._sched_gen_daily_agenda()
        self._event = self._sched_day.popleft()

    def update_schedule(self, force_refresh=False):
        """ Retrieve schedule """
        self._SCHEDULE_ERROR = True
        if not force_refresh and os.path.exists(SCHED_FILE):
            # Read from file
            self._sched_load_from_file()
        else:
            # Backup
            sched_week_bak = self._sched_week
            sched_day_bak = self._sched_day
            # Clear
            self._sched_week = [ [] for x in range(7) ]
            self._sched_day = deque()
            # Load from website
            if not self._sched_load_from_html():
                if sched_week_bak[0]:
                    # Got backup. Reset error status
                    self._SCHEDULE_ERROR = False
                self._sched_week = sched_week_bak
                self._sched_day = sched_day_bak
                return False
        # Generate schedule for today
        self._sched_gen_daily_agenda()
        # Update current event
        self.update_event()
        self._SCHEDULE_ERROR = False
        return True

    def update_covers(self):
        """ Retrieve covers """
        covers = {}
        for wd in range(7):
            for item in self._sched_week[wd]:
                if not item["is_main"]:
                    continue
                elif item["title"] in covers:
                    # If already downloaded
                    item["cover"] = covers[item["title"]]
                    continue
                item["cover"] = self._get_cover(item["url"])
                covers[item["title"]] = item["cover"]
        self._sched_write_to_file()

    def fill_tree_store(self, store):
        """ Fill TreeStore object """
        it = None
        font = config.font
        fg_color = config.font_color
        icontheme = Gtk.IconTheme.get_default()

        for wd in range(7):
            bg_dark = False
            ch_dark = False
            for item in self._sched_week[wd]:
                # Get pixbuf
                if item["icon"]:
                    icon = GdkPixbuf.Pixbuf.new_from_file(item["icon"])
                else:
                    # Load default icon instead
                    icon = icontheme.load_icon(ICON, 256, 0)
                # Scale
                sz = 80
                if not item["is_main"]:
                    sz = 60
                icon = icon.scale_simple(sz, sz, GdkPixbuf.InterpType.BILINEAR)
                # Join hosts
                host = parse_hosts(item["host"])
                # Insert program
                if item["is_main"]:
                    # Main event
                    bg_color = hex_to_rgba(config.bg_colors[bg_dark])
                    bg_color.alpha = config.bg_alpha[bg_dark]
                    # Insert item
                    it = store.append(None, [item["weekday"], item["is_main"],
                                             item["time"], item["title"],
                                             item["url"], host, icon,
                                             bg_color, fg_color, font,
                                             bg_dark, item["record"],
                                             item["play"]])
                    # Alternate row color
                    bg_dark = not bg_dark
                    ch_dark = bg_dark
                else:
                    # Child event
                    bg_color = hex_to_rgba(config.bg_colors[ch_dark])
                    bg_color.alpha = config.bg_alpha[ch_dark]
                    # Insert item
                    store.append(it, [item["weekday"], item["is_main"],
                                 item["time"], item["title"], item["url"],
                                 host, icon, bg_color, fg_color, font,
                                 ch_dark, False, False])
                    # Alternate row color
                    ch_dark = not ch_dark

    def set_record_status(self, status, wd, time):
        """ Set recorder status """
        for item in self._sched_week[wd]:
            if not item["is_main"]:
                continue
            if item["time"] == time:
                item["record"] = status
                break
        else:
            logging("Program not found")
            return
        self._sched_write_to_file()

    def set_play_status(self, status, wd, time):
        """ Set playback flag """
        for item in self._sched_week[wd]:
            if not item["is_main"]:
                continue
            if item["time"] == time:
                item["play"] = status
                break
        else:
            logging("Program not found")
            return
        self._sched_write_to_file()

    def _sched_gen_daily_agenda(self):
        """ Create a list of main events for today """
        today = datetime.now(MSK())
        now = timedelta(hours=today.hour, minutes=today.minute,
                        seconds=today.second).total_seconds()
        position = 0
        for item in self._sched_week[today.weekday()]:
            if not item["is_main"]:
                continue
            else:
                item["position"] = position
                position += 1
            if item["end"] <= now:
                # Already ended. Skip
                continue
            self._sched_day.append(item)

    def _sched_load_from_file(self):
        """ Load schedule from file """
        with open(SCHED_FILE, "r") as f:
            self._sched_week = json.load(f)

    def _sched_write_to_file(self):
        """ Save schedule on disk """
        with open(SCHED_FILE, 'w') as f:
            json.dump(self._sched_week, f)

    def _sched_load_from_html(self):
        """ Load schedule from site """
        # Create session with fake user-agent
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT
        # Default event icon
        music_icon_name = ""
        # Weekdays parser
        wd_name_list = {"Вс" : [6], "Пн" : [0], "Вт" : [1], "Ср" : [2],
                        "Чт" : [3], "Пт" : [4], "Сб" : [5],
                        "По будням" : list(range(0,5)),
                        "По выходным" : [5, 6]}
        try:
            # Download schedule
            resp = session.get(SCHED_URL)
            if resp.status_code != 200:
                logging.error("Couldn't reach server. Code:", resp.status_code)
                return False
            # Get table
            r = r'^.*<div\ class="program-list">.*?(<tbody>.*?<\/tbody>).*$'
            xhtml = re.sub(r, r'\1', resp.text)
            # Handle unclosed img tags /* xhtml style */
            xhtml = re.sub(r'(<img.*?"\s*)>', r'\1/>', xhtml)
            xhtml = re.sub(r'<br>', r'<br/>', xhtml)
            xhtml = re.sub(r'&nbsp;', r'', xhtml)
            root = etree.fromstring(xhtml)

        except requests.exceptions.RequestException as e:
            logging.error(str(e))
            return False

        except ValueError as e:
            logging.error("Unexpected response")
            logging.error(str(e))
            return False

        except etree.XMLSyntaxError as e:
            logging.error("Syntax error")
            logging.error(str(e))
            return False

        # Parse xhtml text
        for obj in root:
            # If time not presented
            if not len(obj[3]):
                # Event happens randomly or never
                continue
            # Get icon
            icon_src = obj[0][0][0].attrib['src'].split("?")[0]
            icon_name = self._get_icon(icon_src)
            # Get title
            title = obj[1][0][0].text
            # Get program url
            url = obj[1][0][0].attrib['href']
            url = re.sub(r'^.*(/programms/.*?/).*$', r'\1', url)
            url = SILVER_RAIN_URL + url
            # Don't parse music. Just save icon location
            if title == MUSIC:
                music_icon_name = icon_name
                continue
            # Get hosts
            host = []
            if len(obj[2]):
                # If hosts presented
                for it in obj[2][0]:
                    h = it[0][0].text.strip()
                    # Show name first
                    h = h.split(' ')
                    h.insert(0, h.pop())
                    h = ' '.join(h)
                    host.append(h)
            # Get schedule
            # Expecting "WD: HH:MM - HH:MM" format
            sched = []
            sched_list = []
            wd_list_prev = []

            for it in obj[3][0]:
                sched_list.append(it.text)
                i = 0
                while i < len(it) - 1:
                    sched_list.append(it[i].tail)
                    i += 1

            for it in sched_list:
                # Remove extra comma
                if it[-1] == ',' :
                    it = it[:-1]
                # Split wd and time
                try:
                    weekday, time = it.split(': ')
                    wd_list = parse_weekday(weekday)
                    wd_list_prev = wd_list
                except ValueError:
                    # No weekday, use previous
                    wd_list = wd_list_prev
                    time = it

                start, end = time.split('-')
                if start.strip() == "24:00":
                    start = "00:00"
                if end.strip() == "00:00":
                    end = "24:00"
                #  Weekday number,
                #  HH:MM,
                #  start in seconds,
                #  end in seconds
                sched.append([ wd_list,
                               time,
                               parse_time(start.strip()),
                               parse_time(end.strip()) ])
            # Event type
            is_main = False
            length = sched[0][3] - sched[0][2];
            if length >= 3000:
                # At least 50 minutes
                is_main = True

                # round to hours
                #FIXME: That's rude, but I don't have time right now
                hrs, mins = divmod(length, 3600)
                if mins:
                    for it in sched:
                        it[2] = it[2] - it[2] % 3600
                        it[3] = it[2] + (hrs + 1) * 3600
                        it[1] = str_time(it[2], it[3])

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
                    program["icon"] = icon_name
                    program["cover"] = ""
                    program["start"] = it[2]
                    program["end"] = it[3]
                    program["play"] = False
                    program["record"] = False
                    self._sched_week[weekday].append(program)

        for wd in range(7):
            # Sort schedule by parent/start/end
            self._sched_week[wd].sort(key = lambda x : (-x["is_main"], \
                                                        x["start"], -x["end"]))
            # Fix common errors
            i = 1
            while i < len(self._sched_week[wd]):
                item = self._sched_week[wd][i]
                prev = self._sched_week[wd][i-1]
                next = {}

                # Fix only main items
                if not item["is_main"] :
                    break

                # Join duplicates
                if (prev["end"] >= item["start"] and
                        prev["title"] == item["title"]) :

                    if prev["end"] > item["end"]:
                        item["end"] = prev["end"]

                    if prev["start"] < item["start"]:
                        item["start"] = prev["start"]

                    item["time"] = str_time(item["start"], item["end"])

                    self._sched_week[wd][i] = item
                    self._sched_week[wd].pop(i-1)
                    continue

                # Fix one main program inside another
                elif (prev["end"] > item["start"] and
                        prev["end"] >= item["end"]) :

                    if (prev["end"] > item["end"]) :
                        # Divide bigger one in two
                        next = prev
                        next["start"] = item["end"]
                        next["time"] = str_time(next["start"], next["end"])
                        self._sched_week[wd].insert(i+1, next)

                    if (prev["start"] < item["start"]) :
                        prev["end"] = item["start"]
                        prev["time"] = str_time(prev["start"], prev["end"])
                        self._sched_week[wd][i-1] = prev
                    else :
                        # Delete left one
                        self._sched_week[wd].pop(i-1)
                        i -= 1

                    if len(next) : i += 1
                i += 1

            # Sort schedule by start/parent
            self._sched_week[wd].sort(key = lambda x : \
                                      (x["start"], -x["is_main"]))
            # Fill spaces with music
            time = 0.0
            pos = 0
            last = {"end" : 0}
            for item in self._sched_week[wd]:
                if not item["is_main"]:
                    continue
                if item["start"] > time:
                    # If doesn't start right after the last one
                    program = {}
                    program["is_main"] = True
                    program["title"] = MUSIC
                    program["url"] = MUSIC_URL
                    program["host"] = []
                    program["icon"] = music_icon_name
                    program["cover"] = ""
                    program["weekday"] = SCHED_WEEKDAY_LIST[wd]
                    program["time"] = str_time(time, item["start"])
                    program["start"] = time
                    program["end"] = item["start"]
                    program["play"] = False
                    program["record"] = False
                    self._sched_week[wd].insert(pos, program)
                    pos += 1
                time = item["end"]
                pos += 1
                last = item
            # Check if last event doesn't go till 24:00
            if last["end"] < 86400.0:
                program = {}
                program["is_main"] = True
                program["title"] = MUSIC
                program["url"] = MUSIC_URL
                program["host"] = []
                program["icon"] = music_icon_name
                program["cover"] = ""
                program["weekday"] = SCHED_WEEKDAY_LIST[wd]
                program["time"] = str_time(last["end"], 86400.0)
                program["start"] = last["end"]
                program["end"] = 86400.0
                program["play"] = False
                program["record"] = False
                self._sched_week[wd].insert(pos, program)
            # Sort again
            self._sched_week[wd].sort(key = lambda x : \
                                         (x["start"], -x["is_main"]))
        # Save sched to file
        self._sched_write_to_file()
        return True

    def _get_icon(self, src):
        """ Download icon from url """
        name = ""
        if src.split(".")[-1] not in ["jpg", "jpeg", "png"]:
            return name
        if src[:7] != "http://":
            if src[:2] == "//":
                # //url/name.png
                src = "http:" + src
            elif src[0] == "/":
                # /name.png
                src = SILVER_RAIN_URL + src
            else:
                # url/name.png
                src = "http://" + src
        name = IMG_DIR + src.split("/")[-1]
        # Download icon if it doesn't exist
        if not os.path.exists(name):
            try:
                urllib.request.urlretrieve(src, name)
            except urllib.error.URLError as e:
                err = "Couldn't download icon from url: " + src
                logging.error(err)
                logging.error(str(e))
                name = ""
        return name

    def _get_cover(self, program_page):
        """ Download program cover """
        name = ""
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT
        try:
            resp = session.get(program_page)
            if resp.status_code != 200:
                logging.error("Couldn't reach server. Code:", resp.status_code)
                return name
            # Get image src
            div = r'<div class="program-detail">.*?<div class="title".*?div>'
            found = re.findall(div, resp.text)
            src = re.sub(r'.*<img src="([^\?"]+)\??.*?".*', r'\1', found[0])
            name = self._get_icon(src)

        except requests.exceptions.RequestException as e:
            logging.error(str(e))

        except ValueError as e:
            logging.error("Unexpected response")
            logging.error(str(e))

        except IndexError:
            logging.error("Background not found")

        return name
