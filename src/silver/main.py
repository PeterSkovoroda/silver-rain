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

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
from gi.repository import Gst, Gtk, GObject, Gdk, GdkPixbuf, Notify

try:
    from gi.repository import AppIndicator3 as appindicator
    APP_INDICATOR = True
except ImportError:
    APP_INDICATOR = False

import configparser
import json
import logging
import os
import random
import re
import requests
import signal
import string
import subprocess
import textwrap
import threading
import urllib.request

import dbus, dbus.service, dbus.glib

from collections import deque
from datetime import datetime
from datetime import timedelta
from datetime import tzinfo

try:
    from lxml import etree
except ImportError as err:
    import xml.etree.ElementTree as etree

########################################################################
# System files and variables
from silver.globals import VERSION
APP_DIR = os.getenv("HOME") + "/.silver/"
IMG_DIR = APP_DIR + "imgs/"
SCHED_FILE = APP_DIR + "sched.dump"
CONFIG_FILE = APP_DIR + "config.ini"
ICON = "silver-rain"
# Network

STREAM_URL_LIST = [ 'http://radiosilver.corbina.net:8000/silver128a.mp3',
                    'http://radiosilver.corbina.net:8000/silver48a.mp3',
                    'http://icecast.silver.cdnvideo.ru/silver' ]
SILVER_RAIN_URL = "http://silver.ru"
SCHED_URL       = "http://silver.ru/programms/"
MESSENGER_URL   = "http://silver.ru/ajax/send_message_in_studio.php"
BX_USER_ID      = ""
PHPSESSID       = ""
SESSID          = ""
USER_AGENT      = 'Mozilla/5.0 (X11; Linux x86_64) ' + \
                  'AppleWebKit/537.36 (KHTML, like Gecko) ' + \
                  'Chrome/41.0.2227.0 Safari/537.36'
BITRIX_SERVER   = "http://bitrix.info/ba.js"

########################################################################
# Timezone
# It's hard to work with utc, since schedule defined for MSK zone,
# so use timezone synchronization, which is actually a bad idea
class MSK(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=3)

    def dst(self, dt):
        return timedelta(hours=0)

    def tzname(self, dt):
        return "MSK"

########################################################################
# Translations
LANGUAGES_LIST  = ["English", "Русский"]
TRANSLATIONS    = [
                    {'WeekdayList'      : ['Monday', 'Tuesday', 'Wednesday',
                                           'Thursday', 'Friday', 'Saturday',
                                           'Sunday'],
                     'MenuMusic'        : 'Music',
                     'MenuHelp'         : 'Help',
                     'Play'             : 'Play',
                     'Stop'             : 'Stop',
                     'Record'           : 'Record program',
                     'StopRecording'    : 'Stop recording',
                     'Mute'             : 'Mute',
                     'Quit'             : 'Quit',
                     'Preferences'      : 'Preferences',
                     'UpdateSchedule'   : 'Update schedule',
                     'SendMessage'      : 'Send message',
                     'Time'             : 'Time',
                     'Title'            : 'Title',
                     'Host'             : 'Host',
                     'Updating'         : 'Updating schedule...',
                     'UpdateFailed'     : 'Couldn\'t update schedule',
                     'SilverRain'       : 'Silver Rain',
                     'General'          : 'General',
                     'Appearance'       : 'Appearance',
                     'Network'          : 'Network',
                     'Autoplay'         : 'Autoplay when starts',
                     'StartHidden'      : 'Start hidden',
                     'Language'         : 'Language:',
                     'NeedRestart'      : 'Requires restart',
                     'Recordings'       : 'Recordings',
                     'Recsdirpath'      : 'Recordings directory path:',
                     'Recsprefix'       : 'Recordings prefix:',
                     'Messenger'        : 'Send message',
                     'IMTitle'          : 'Send a message to the studio',
                     'IMHeader'         : 'Default message sender:',
                     'Colors'           : 'Colors',
                     'BgColor'          : 'Background color:',
                     'AltBgColor'       : 'Alternate background color:',
                     'SelBgColor'       : 'Selection color:',
                     'Fonts'            : 'Fonts',
                     'Font'             : 'Font:',
                     'SelFont'          : 'Selection font:',
                     'ResetDefault'     : 'Reset default settings',
                     'StreamUrl'        : 'Stream url:',
                     'IMHeaderPlaceholder' : 'Name e-mail/phone number',
                     'IMTextPlaceholder' : 'Text',
                     'Send'             : 'Send',
                     'ProgramPage'      : 'Program page',
                     'DontRecord'       : 'Don\'t record',
                     'MessengerSuccess' : 'Message sent',
                     'MessengerError'   : 'Couldn\'t send message',
                     'Proxy'            : 'Proxy',
                     'UseProxy'         : 'Use proxy',
                     'ProxyUri'         : 'URI:',
                     'ProxyUsername'    : 'Username:',
                     'ProxyPassword'    : 'Password:',
                    },

                    {'WeekdayList'      : ['Понедельник', 'Вторник', 'Среда',
                                           'Четверг', 'Пятница', 'Суббота',
                                           'Воскресенье'],
                     'MenuMusic'        : 'Музыка',
                     'MenuHelp'         : 'Помощь',
                     'Play'             : 'Играть',
                     'Stop'             : 'Стоп',
                     'Record'           : 'Записать программу',
                     'Mute'             : 'Выключить звук',
                     'StopRecording'    : 'Остановить запись',
                     'Quit'             : 'Выход',
                     'Preferences'      : 'Настройки',
                     'UpdateSchedule'   : 'Обновить расписание',
                     'SendMessage'      : 'Отправить сообщение',
                     'Time'             : 'Время',
                     'Title'            : 'Название',
                     'Host'             : 'Ведущие',
                     'Updating'         : 'Обновление расписания...',
                     'UpdateFailed'     : 'Не удалось выполнить обновление',
                     'SilverRain'       : 'Серебряный Дождь',
                     'General'          : 'Основные',
                     'Appearance'       : 'Внешний вид',
                     'Network'          : 'Сеть',
                     'Autoplay'        : 'Начинать воспроизведение при старте',
                     'StartHidden'      : 'Сворачивать в трей при запуске',
                     'Language'         : 'Язык:',
                     'NeedRestart'      : 'Требуется перезапуск приложения',
                     'Recordings'       : 'Записи',
                     'Recsdirpath'      : 'Путь для сохранения записей:',
                     'Recsprefix'       : 'Префикс:',
                     'Messenger'        : 'SMS-портал',
                     'IMTitle'          : 'Отправить сообщение в студию',
                     'IMHeader'         : 'Подпись:',
                     'Colors'           : 'Цвета',
                     'BgColor'          : 'Цвет фона:',
                     'AltBgColor'       : 'Альтернативный цвет фона:',
                     'SelBgColor'       : 'Цвет выделенной области:',
                     'Fonts'            : 'Шрифты',
                     'Font'             : 'Основной шрифт:',
                     'SelFont'          : 'Шрифт выделенной области:',
                     'ResetDefault'     : 'Восстановить стандартные настройки',
                     'StreamUrl'        : 'Адрес стрима:',
                     'IMHeaderPlaceholder' : 'Имя, e-mail/номер телефона',
                     'IMTextPlaceholder' : 'Текст сообщения',
                     'Send'             : 'Отправить',
                     'ProgramPage'      : 'Страница программы',
                     'DontRecord'       : 'Не записывать',
                     'MessengerSuccess' : 'Сообщение отправлено',
                     'MessengerError'   : 'Не удалось отправить сообщение',
                     'Proxy'            : 'Прокси',
                     'UseProxy'         : 'Использовать прокси',
                     'ProxyUri'         : 'URI:',
                     'ProxyUsername'    : 'Username:',
                     'ProxyPassword'    : 'Password:',
                    }
                  ]
WEEKDAY_LIST = TRANSLATIONS[0]['WeekdayList']

########################################################################
# Style sheet
def css_load():
    style_provider = Gtk.CssProvider()
    css = open(CSS_PATH, 'rb')
    css_data = css.read()
    css.close()
    style_provider.load_from_data(css_data)
    Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

########################################################################
# Default settings
def font_probe():
    """ Get system default font family """
    t = Gtk.Label("")
    s = t.get_style()
    font = s.font_desc.get_family()
    return font

DEFAULT_AUTOPLAY            = False
DEFAULT_START_HIDDEN        = False
DEFAULT_RECS_DIR            = os.getenv("HOME") + "/SilverRain"
DEFAULT_RECS_PREFIX         = "%m-%d-%y-%H:%M-"
DEFAULT_USE_CSS             = False
DEFAULT_CSS_PATH            = ""
DEFAULT_STREAM_URL          = STREAM_URL_LIST[0]
DEFAULT_BG_COLORS           = ["white", "gray95"]
DEFAULT_FONT_COLOR          = "black"
DEFAULT_SELECTED_BG_COLOR   = "#FF4545"
DEFAULT_SELECTED_FONT_COLOR = "white"
DEFAULT_FONT_FAMILY         = font_probe()
DEFAULT_FONT_SIZE           = "11"
DEFAULT_FONT                = "{0} {1}".format(DEFAULT_FONT_FAMILY,
                                               DEFAULT_FONT_SIZE)
DEFAULT_SELECTED_FONT       = "{0} Bold {1}".format(DEFAULT_FONT_FAMILY,
                                                    DEFAULT_FONT_SIZE)
DEFAULT_LANGUAGE            = 0
DEFAULT_MESSAGE_SENDER      = ""
DEFAULT_PROXY_REQUIRED      = False
DEFAULT_PROXY_URI           = ""
DEFAULT_PROXY_ID            = ""
DEFAULT_PROXY_PW            = ""

COLOR_TEXTVIEW_BORDER       = "#7C7C7C"
COLOR_INVALID               = "#FF4545"

def config_init_default():
    global AUTOPLAY
    AUTOPLAY = DEFAULT_AUTOPLAY
    global START_HIDDEN
    START_HIDDEN = DEFAULT_START_HIDDEN
    global RECS_DIR
    RECS_DIR = DEFAULT_RECS_DIR
    global RECS_PREFIX
    RECS_PREFIX = DEFAULT_RECS_PREFIX
    global USE_CSS
    USE_CSS = DEFAULT_USE_CSS
    global CSS_PATH
    CSS_PATH = DEFAULT_CSS_PATH
    global STREAM_URL
    STREAM_URL = DEFAULT_STREAM_URL
    global BG_COLORS
    BG_COLORS = DEFAULT_BG_COLORS
    global FONT_COLOR
    FONT_COLOR = DEFAULT_FONT_COLOR
    global SELECTED_BG_COLOR
    SELECTED_BG_COLOR = DEFAULT_SELECTED_BG_COLOR
    global SELECTED_FONT_COLOR
    SELECTED_FONT_COLOR = DEFAULT_SELECTED_FONT_COLOR
    global FONT
    FONT = DEFAULT_FONT
    global SELECTED_FONT
    SELECTED_FONT = DEFAULT_SELECTED_FONT
    global LANGUAGE
    LANGUAGE = DEFAULT_LANGUAGE
    global MESSAGE_SENDER
    MESSAGE_SENDER = DEFAULT_MESSAGE_SENDER
    global PROXY_REQUIRED
    PROXY_REQUIRED = DEFAULT_PROXY_REQUIRED
    global PROXY_URI
    PROXY_URI = DEFAULT_PROXY_URI
    global PROXY_ID
    PROXY_ID = DEFAULT_PROXY_ID
    global PROXY_PW
    PROXY_PW = DEFAULT_PROXY_PW

########################################################################
# Settings
def config_save():
    """ Create configuration file with default values """
    config = configparser.ConfigParser()
    config['GENERAL'] = {
            'Autoplay'          : AUTOPLAY,
            'StartHidden'       : START_HIDDEN,
            'RecordsDirectory'  : RECS_DIR,
            'RecordsPrefix'     : re.sub('%', '%%', RECS_PREFIX),
            'UseCSS'            : USE_CSS,
            'CSSPath'           : CSS_PATH,
            'StreamURL'         : STREAM_URL,
            'BgColor0'          : BG_COLORS[0],
            'BgColor1'          : BG_COLORS[1],
            'FontColor'         : FONT_COLOR,
            'SelectedBgColor'   : SELECTED_BG_COLOR,
            'SelectedFontColor' : SELECTED_FONT_COLOR,
            'Font'              : FONT,
            'SelectedFont'      : SELECTED_FONT,
            'Language'          : LANGUAGE,
            'MessageSender'     : MESSAGE_SENDER,
            'ProxyRequired'     : PROXY_REQUIRED,
            'ProxyUri'          : PROXY_URI,
            'ProxyId'           : PROXY_ID,
            'ProxyPw'           : PROXY_PW
            }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def config_load():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    global AUTOPLAY
    AUTOPLAY = config.getboolean('GENERAL', 'Autoplay',
                                fallback=DEFAULT_AUTOPLAY)
    global START_HIDDEN
    START_HIDDEN = config.getboolean('GENERAL', 'StartHidden',
                                fallback=DEFAULT_START_HIDDEN)
    global RECS_DIR
    RECS_DIR = config.get('GENERAL', 'RecordsDirectory',
                                fallback=DEFAULT_RECS_DIR)
    global RECS_PREFIX
    RECS_PREFIX = config.get('GENERAL', 'RecordsPrefix',
                                fallback=DEFAULT_RECS_PREFIX)
    global USE_CSS
    USE_CSS = config.getboolean('GENERAL', 'UseCSS',
                                fallback=DEFAULT_USE_CSS)
    global CSS_PATH
    CSS_PATH = config.get('GENERAL', 'CSSPath',
                                fallback=DEFAULT_CSS_PATH)
    global STREAM_URL
    STREAM_URL = config.get('GENERAL', 'StreamURL',
                                fallback=DEFAULT_STREAM_URL)
    global BG_COLORS
    BG_COLORS = []
    BG_COLORS.append(config.get('GENERAL', 'BgColor0',
                                fallback=DEFAULT_BG_COLORS[0]))
    BG_COLORS.append(config.get('GENERAL', 'BgColor1',
                                fallback=DEFAULT_BG_COLORS[1]))
    global FONT_COLOR
    FONT_COLOR = config.get('GENERAL', 'FontColor',
                                fallback=DEFAULT_FONT_COLOR)
    global SELECTED_BG_COLOR
    SELECTED_BG_COLOR = config.get('GENERAL', 'SelectedBgColor',
                                fallback=DEFAULT_SELECTED_BG_COLOR)
    global SELECTED_FONT_COLOR
    SELECTED_FONT_COLOR = config.get('GENERAL', 'SelectedFontColor',
                                fallback=DEFAULT_SELECTED_FONT_COLOR)
    global FONT
    FONT = config.get('GENERAL', 'Font', fallback=DEFAULT_FONT)
    global SELECTED_FONT
    SELECTED_FONT = config.get('GENERAL', 'SelectedFont',
                                fallback=DEFAULT_SELECTED_FONT)
    global LANGUAGE
    LANGUAGE = int(config.get('GENERAL', 'Language',
                                fallback=DEFAULT_LANGUAGE))
    global MESSAGE_SENDER
    MESSAGE_SENDER = config.get('GENERAL', 'MessageSender',
                                fallback=DEFAULT_MESSAGE_SENDER)
    global PROXY_REQUIRED
    PROXY_REQUIRED = config.getboolean('GENERAL', 'ProxyRequired',
                                fallback=DEFAULT_PROXY_REQUIRED)
    global PROXY_URI
    PROXY_URI = config.get('GENERAL', 'ProxyUri',
                                fallback=DEFAULT_PROXY_URI)
    global PROXY_ID
    PROXY_ID = config.get('GENERAL', 'ProxyId',
                                fallback=DEFAULT_PROXY_ID)
    global PROXY_PW
    PROXY_PW = config.get('GENERAL', 'ProxyPw',
                                fallback=DEFAULT_PROXY_PW)

########################################################################
# GStreamer
class SilverPlayer():
    """ Gstreamer container for playing and recording network audio stream
        Player:
            souphttpsrc -> decodebin -> audioconvert -> volume -> autoaudiosink
        Recorder:
            souphttpsrc -> icydemux -> filesink """
    def __init__(self):
        self.__playing__ = False
        self.__recording__ = False

    def clean(self):
        """ Unref pipeline """
        self.__playing__ = False
        self.__recording__ = False
        self.__pipeline__.set_state(Gst.State.NULL)
        self.__recorder__.set_state(Gst.State.NULL)

    def reset_network_settings(self):
        """ Set new network settings """
        self.__pipeline__.get_by_name('source').set_property('location',
                                                    STREAM_URL)
        self.__recorder__.get_by_name('source').set_property('location',
                                                    STREAM_URL)
        if PROXY_REQUIRED:
            self.__pipeline__.get_by_name('source').set_property('proxy',
                                                    PROXY_URI)
            self.__pipeline__.get_by_name('source').set_property(
                                                    'proxy-id', PROXY_ID)
            self.__pipeline__.get_by_name('source').set_property(
                                                    'proxy-pw', PROXY_PW)
            self.__recorder__.get_by_name('source').set_property('proxy',
                                                    PROXY_URI)
            self.__recorder__.get_by_name('source').set_property(
                                                    'proxy-id', PROXY_ID)
            self.__recorder__.get_by_name('source').set_property(
                                                    'proxy-pw', PROXY_PW)
        else:
            self.__pipeline__.get_by_name('source').set_property('proxy',
                                                    '')
            self.__pipeline__.get_by_name('source').set_property(
                                                    'proxy-id', '')
            self.__pipeline__.get_by_name('source').set_property(
                                                    'proxy-pw', '')
            self.__pipeline__.get_by_name('source').set_property('proxy',
                                                    '')
            self.__pipeline__.get_by_name('source').set_property(
                                                    'proxy-id', '')
            self.__pipeline__.get_by_name('source').set_property(
                                                    'proxy-pw', '')

    def playback_toggle(self):
        """ Playback trigger """
        self.__playing__ = not self.__playing__
        if self.__playing__:
            ret = self.__pipeline__.set_state(Gst.State.PLAYING)
        else:
            # Switch state to READY instead of STOP to prevent EOS
            ret = self.__pipeline__.set_state(Gst.State.READY)

        if ret == Gst.StateChangeReturn.FAILURE:
            self.error_func("Couldn't change state")
            self.clean()
            exit(-1)

    def recorder_toggle(self, name):
        """ Record trigger """
        self.__recording__ = not self.__recording__
        if self.__recording__:
            file = RECS_DIR + "/" + \
                   datetime.now(MSK()).strftime(RECS_PREFIX) + name + ".mp3"
            self.__recorder__.get_by_name('filesink').set_property('location',
                                                                   file)
            ret = self.__recorder__.set_state(Gst.State.PLAYING)
        else:
            ret = self.__recorder__.set_state(Gst.State.READY)

        if ret == Gst.StateChangeReturn.FAILURE:
            self.error_func("Couldn't change state")
            self.clean()
            exit(-1)

    def set_error_function(self, er_func, warn_func,
                           playback_stop_func, rec_stop_func):
        """ Set callback to show error messages """
        self.error_func = er_func
        self.warning_func = warn_func
        self.playback_stop_callback = playback_stop_func
        self.recorder_stop_callback = rec_stop_func

    def volume_set(self, value):
        """ Set player volume [0-100] """
        self.__pipeline__.get_by_name('volume').set_property('volume',
                                                             value / 100.)

    def create_pipeline(self):
        self.elements = dict()
        self.__pipeline__ = Gst.Pipeline.new("SilverPlayer")
        if not self.__pipeline__:
            self.error_func("Couldn't create pipeline")
            exit(-1)
        # Create GStream elements
        try:
            self.elements["source"] = Gst.ElementFactory.make('souphttpsrc',
                                                              'source')
            self.elements["decode"] = Gst.ElementFactory.make('decodebin',
                                                              'decode')
            self.elements["convert"] = Gst.ElementFactory.make('audioconvert',
                                                               'convert')
            self.elements["volume"] = Gst.ElementFactory.make('volume',
                                                              'volume')
            self.elements["sink"] = Gst.ElementFactory.make('autoaudiosink',
                                                            'sink')
        except Gst.ElementNotFoundError:
            str = "Couldn't find GStreamer element" + \
                  "Check if packages" + \
                  "'GStreamer Good Plugins 1.0'" + \
                  "'GStreamer Base Plugins 1.0'" + \
                  "are installed"
            self.error_func(str)
            exit(-1)

        for key in self.elements:
            if not self.elements[key]:
                self.error_func("Couldn't create element: " + key)
                exit(-1)
            else:
                self.__pipeline__.add(self.elements[key])

        self.elements["source"].set_property('location', STREAM_URL)
        self.elements["source"].set_property('is-live', True)
        self.elements["source"].set_property('compress', True)
        if PROXY_REQUIRED:
            self.elements["source"].set_property('proxy', PROXY_URI)
            self.elements["source"].set_property('proxy-id', PROXY_ID)
            self.elements["source"].set_property('proxy-pw', PROXY_PW)
        self.elements["volume"].set_property('volume', 1.)

        # Link elements
        def pad_added_callback(decode, pad):
            if pad.is_linked():
                # Already linked. Skip
                return
            return pad.link(self.elements["convert"].get_static_pad('sink'))

        self.elements["decode"].connect('pad-added', pad_added_callback)

        if (not Gst.Element.link(self.elements["source"],
                                 self.elements["decode"]) or
            not Gst.Element.link(self.elements["convert"],
                                 self.elements["volume"]) or
            not Gst.Element.link(self.elements["volume"],
                                 self.elements["sink"])):
            self.error_func("Elements could not be linked")
            exit(-1)

        # Create message bus
        msg_bus = self.__pipeline__.get_bus()
        msg_bus.add_signal_watch()
        msg_bus.connect('message', self._message_handler)

    def create_recorder(self):
        self.relements = dict()
        self.__recorder__ = Gst.Pipeline.new("SilverRecorder")
        if not self.__recorder__:
            self.error_func("Couldn't create pipeline")
            exit(-1)

        # Create GStreamer elements
        try:
            self.relements["source"] = Gst.ElementFactory.make('souphttpsrc',
                                                               'source')
            self.relements["demux"] = Gst.ElementFactory.make('icydemux',
                                                              'demux')
            self.relements["filesink"] = Gst.ElementFactory.make('filesink',
                                                                 'filesink')
        except Gst.ElementNotFoundError:
            str = "Couldn't find GStreamer element " + \
                  "Check if packages " + \
                  "'GStreamer Good Plugins 1.0' " + \
                  "'GStreamer Base Plugins 1.0' " + \
                  "are installed"
            self.error_func(str)
            exit(-1)

        for key in self.relements:
            if not self.relements[key]:
                self.error_func("Couldn't create element: " + key)
                exit(-1)
            else:
                self.__recorder__.add(self.relements[key])

        self.relements["source"].set_property('location', STREAM_URL)
        self.relements["source"].set_property('is-live', True)
        self.relements["source"].set_property('compress', True)
        if PROXY_REQUIRED:
            self.relements["source"].set_property('proxy', PROXY_URI)
            self.relements["source"].set_property('proxy-id', PROXY_ID)
            self.relements["source"].set_property('proxy-pw', PROXY_PW)
        self.relements["filesink"].set_property('location', "file.mp3")

        # Link relements
        def pad_added_callback(demux, pad):
            if pad.is_linked():
                # Already linked. Skip
                return
            return pad.link(self.relements["filesink"].get_static_pad('sink'))

        self.relements["demux"].connect('pad-added', pad_added_callback)

        if not Gst.Element.link(self.relements["source"],
                                self.relements["demux"]):
            self.error_func("Elements could not be linked")
            exit(-1)
        # Create message bus
        msg_bus = self.__recorder__.get_bus()
        msg_bus.add_signal_watch()
        msg_bus.connect('message', self._rec_message_handler)

    def _message_handler(self, bus, msg):
        """ Player message bus """
        struct = msg.get_structure()
        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            self.error_func("Error from element %s: %s" % (msg.src.get_name(),
                                                         err))
            self.playback_stop_callback()
        elif msg.type == Gst.MessageType.EOS:
            self.warning_func("End of stream")
            self.playback_stop_callback()

    def _rec_message_handler(self, bus, msg):
        """ Recorder message bus """
        struct = msg.get_structure()
        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            self.error_func("Error from element %s: %s" % (msg.src.get_name(),
                                                         err))
            self.recorder_stop_callback()
        elif msg.type == Gst.MessageType.EOS:
            # Stop recorder timers
            self.warning_func("End of stream")
            self.recorder_stop_callback()

########################################################################
# Schedule
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
                font = FONT
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
                    bg_color = BG_COLORS[bg_dark]
                    fg_color = FONT_COLOR
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
                    bg_color = BG_COLORS[ch_dark]
                    fg_color = FONT_COLOR
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
                    program["weekday"] = WEEKDAY_LIST[weekday]
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
                    program["weekday"] = WEEKDAY_LIST[wd]
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
                program["weekday"] = WEEKDAY_LIST[wd]
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

########################################################################
# DBus service
class SilverService(dbus.service.Object):
    """ DBus service """
    def __init__(self, win):
        self.window = win
        bus_name = dbus.service.BusName('org.SilverRain.Silver',
                                        bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/org/SilverRain/Silver')

    @dbus.service.method(dbus_interface='org.SilverRain.Silver')

    def show_window(self):
        self.window.present()

########################################################################
# GUI
class SilverGUI(Gtk.Window):
    """ GUI """
    def __init__(self, player, sched):
        ## GStreamer
        self._player = player
        self.__muted__ = 0
        self.__playing__ = False
        self.__recording__ = False
        self.__volume__ = 100
        ## Schedule
        self._schedule = sched
        self.__SCHEDULE_ERROR__ = False
        ## Timers
        # On event timer
        self._t_event = threading.Timer(0, None)
        # Record timer
        self._t_recorder = threading.Timer(0, None)
        ## Interface
        # Main window
        self.__main_window__ = True
        # Messenger
        self.__im_window__ = False
        # Notifications
        self.notification = Notify.Notification.new("Header", "Body", "image")
        # TreeView
        self.__weekday_filter__ = datetime.now(MSK()).strftime("%A")
        self.__today__ = datetime.now(MSK())
        self.__cell_bg_old__ = ''
        self.__cell_fg_old__ = ''
        # Create main window
        self.main_window_create()
        # Create messenger
        self.im_create()
        # Initialize GStreamer
        self._player.set_error_function(self.error_show, self.warning_show,
                                        self.playback_emergency_stop,
                                        self.recorder_emergency_stop)
        self._player.create_pipeline()
        self._player.create_recorder()
        # Create status icon
        self.status_icon_create()
        # Create treeview
        self.schedule_update()
        if AUTOPLAY:
            self.playback_toggle(None)

### Cleanup
    def clean(self):
        self.timers_clean()

### Main Window
    def main_window_create(self):
        """ Init parent window """
        Gtk.Window.__init__(self, title="Silver Rain")
        self.set_border_width(0)
        self.set_icon_name(ICON)
        self.set_default_size(650, 450)
        self.connect("delete-event", self.main_window_on_delete_event)
        # Container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        ## Menubar
        menubar = self.menubar_create()
        vbox.pack_start(menubar, False, False, 0)
        sep = Gtk.Separator()
        vbox.pack_start(sep, False, False, 0)
        ## Scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_min_content_height(100)
        vbox.pack_start(self.scrolled_window, True, True, 0)
        ## Selection
        selection = self.selection_create()
        vbox.pack_start(selection, False, False, 0)
        # Controls
        control_panel = self.control_panel_create()
        vbox.pack_end(control_panel, False, False, 0)
        vbox.show_all()
        self.add(vbox)
        # Don't show if should stay hidden
        if not START_HIDDEN:
            self.show()

    def main_window_on_delete_event(self, window, event):
        """ Hide parent window instead of destroying it """
        self.__main_window__ = False
        window.hide()
        return True

### Menubar
    def menubar_create(self):
        """ Menu bar """
        agr = Gtk.AccelGroup()
        self.add_accel_group(agr)
        menubar = Gtk.MenuBar()
        # Music
        music_menu = Gtk.Menu()
        music = Gtk.MenuItem(TRANSLATIONS[LANGUAGE]["MenuMusic"])
        music.set_submenu(music_menu)
        ## Play
        self.menubar_play = self.create_menuitem(
                                          TRANSLATIONS[LANGUAGE]["Play"],
                                          "media-playback-start")
        self.menubar_play.set_size_request(90, -1)
        self.menubar_play.connect("activate", self.playback_toggle)
        key, mod = Gtk.accelerator_parse("F6")
        self.menubar_play.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Stop
        self.menubar_stop = self.create_menuitem(
                                          TRANSLATIONS[LANGUAGE]["Stop"],
                                          "media-playback-stop")
        self.menubar_stop.set_sensitive(False)
        self.menubar_stop.connect("activate", self.playback_toggle)
        key, mod = Gtk.accelerator_parse("F7")
        self.menubar_stop.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Record
        self.menubar_record = self.create_menuitem(
                                          TRANSLATIONS[LANGUAGE]["Record"],
                                          "media-record")
        self.menubar_record.connect("activate", self.recorder_toggle)
        key, mod = Gtk.accelerator_parse("F8")
        self.menubar_record.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Stop recording
        self.menubar_stop_recording = self.create_menuitem(
                                      TRANSLATIONS[LANGUAGE]["StopRecording"],
                                          "media-playback-stop")
        self.menubar_stop_recording.set_sensitive(False)
        self.menubar_stop_recording.connect("activate", self.recorder_stop)
        key, mod = Gtk.accelerator_parse("F9")
        self.menubar_stop_recording.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Mute
        self.menubar_mute = Gtk.CheckMenuItem(TRANSLATIONS[LANGUAGE]["Mute"])
        self.menubar_mute.set_active(self.__muted__)
        self.menubar_mute.connect("toggled", self.mute_toggle)
        key, mod = Gtk.accelerator_parse("<Control>M")
        self.menubar_mute.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Refresh
        refresh = self.create_menuitem(
                TRANSLATIONS[LANGUAGE]["UpdateSchedule"],
                "gtk-refresh")
        refresh.connect("activate", self.schedule_refresh)
        key, mod = Gtk.accelerator_parse("F5")
        refresh.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Messenger
        msg = self.create_menuitem(TRANSLATIONS[LANGUAGE]["Messenger"],
                                          "gtk-edit")
        msg.connect("activate", self.im_show)
        key, mod = Gtk.accelerator_parse("<Control>S")
        msg.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Preferences
        prefs = self.create_menuitem(TRANSLATIONS[LANGUAGE]["Preferences"],
                                          "gtk-preferences")
        prefs.connect("activate", self.prefs_window_create)
        key, mod = Gtk.accelerator_parse("<Control>P")
        prefs.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Quit
        quit = self.create_menuitem(TRANSLATIONS[LANGUAGE]["Quit"], "gtk-quit")
        quit.connect("activate", Gtk.main_quit)
        key, mod = Gtk.accelerator_parse("<Control>Q")
        quit.add_accelerator("activate", agr,
                                          key, mod, Gtk.AccelFlags.VISIBLE)
        ## Separator
        sep = []
        for i in range(5):
            sep.append(Gtk.SeparatorMenuItem())
        ## Pack
        for item in [ self.menubar_play,
                      self.menubar_stop,
                      self.menubar_record,
                      self.menubar_stop_recording,
                      sep[0],
                      self.menubar_mute,
                      sep[1],
                      refresh,
                      sep[2],
                      msg,
                      sep[3],
                      prefs,
                      sep[4],
                      quit ]:
            music_menu.append(item)
        # Help
        help_menu = Gtk.Menu()
        help = Gtk.MenuItem(TRANSLATIONS[LANGUAGE]['MenuHelp'])
        help.set_submenu(help_menu)
        ## About
        about = self.create_menuitem("About", "gtk-about")
        about.set_size_request(90, -1)
        about.connect("activate", self.about_window_create)
        key, mod = Gtk.accelerator_parse("F1")
        about.add_accelerator("activate", agr, key,
                              mod, Gtk.AccelFlags.VISIBLE)
        help_menu.append(about)

        menubar.append(music)
        menubar.append(help)
        return menubar

    def menubar_mute_toggle(self, widget=None):
        """ Since it's impossible to just set checkbox status
            without activating it (which is stupid, by the way),
            this function should be called to toggle mute """
        self.menubar_mute.set_active(not self.__muted__)

### Selection
    def selection_create(self):
        """ Create selection buttons """
        self.selection_buttons = []
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        for day in TRANSLATIONS[LANGUAGE]['WeekdayList']:
            button = Gtk.Button(day)
            button.set_focus_on_click(True)
            button.set_size_request(80, 0)
            button.connect("clicked", self.selection_on_clicked)
            hbox.pack_start(button, True, True, 0)
            self.selection_buttons.append(button)
        return hbox

    def selection_on_clicked(self, button):
        """ Refilter treeview by selected weekday """
        weekday_n = TRANSLATIONS[LANGUAGE]['WeekdayList'].index(
                                                            button.get_label())
        self.__weekday_filter__ = WEEKDAY_LIST[weekday_n]
        self.sched_tree_model.refilter()

### Control panel
    def control_panel_create(self):
        """ Playback control panel """
        toolbar = Gtk.Toolbar()
        toolbar.set_orientation(Gtk.Orientation.HORIZONTAL)
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)

        control_panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        control_panel.set_spacing(6)
        control_panel.set_border_width(6)
        ## Playback Button
        icon = self.get_playback_label()[1]
        self.playback_button = self.create_toolbutton(icon)
        self.playback_button.connect("clicked", self.playback_toggle)
        self.playback_button.set_tooltip_text(TRANSLATIONS[LANGUAGE]["Play"])
        ## Send message Button
        send_msg = self.create_toolbutton("gtk-edit")
        send_msg.connect("clicked", self.im_show)
        send_msg.set_tooltip_text(TRANSLATIONS[LANGUAGE]["SendMessage"])
        ## Separator
        sep = Gtk.SeparatorToolItem()
        ## Update schedule Button
        self.sched_refresh_button = self.create_toolbutton("gtk-refresh")
        self.sched_refresh_button.connect("clicked", self.schedule_refresh)
        self.sched_refresh_button.set_tooltip_text(
                                      TRANSLATIONS[LANGUAGE]["UpdateSchedule"])
        ## Spinner
        self.spinner = Gtk.Spinner()
        ## Label
        self.status = Gtk.Label()
        self.status.set_selectable(True)
        self.status.set_alignment(-1, 0.45)
        ## Mute Button
        icon = self.get_volume_icon()
        self.mute_button = self.create_toolbutton(icon)
        self.mute_button.connect("clicked", self.menubar_mute_toggle)
        ## Volume scale
        ad = Gtk.Adjustment(value=self.__volume__, lower=0,
                            upper=100, step_increment=5,
                            page_increment=10, page_size=0)
        self.volume = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL,
                                adjustment=ad)
        self.volume.set_property('draw-value', False)
        self.volume.connect("value-changed", self.cp_on_volume_changed)
        self.volume.set_size_request(80, 0)
        # Pack toolbar
        for x, el in enumerate ([ self.playback_button,
                                  send_msg,
                                  sep,
                                  self.sched_refresh_button ]):
            toolbar.insert(el, x)
        # Pack panel
        control_panel.pack_start(toolbar, False, False, 0)
        control_panel.pack_start(self.spinner, False, False, 0)
        control_panel.pack_start(self.status, True, False, 0)
        control_panel.pack_end(self.volume, False, False, 0)
        control_panel.pack_end(self.mute_button, False, False, 0)
        return control_panel

    def cp_on_volume_changed(self, scale):
        """ This actually changes volume """
        self.__volume__ = scale.get_value()
        if not self.__muted__ and self.__volume__ == 0:
            self.menubar_mute_toggle()
        elif self.__muted__ and self.__volume__ > 0:
            self.__muted__ = self.__volume__
            self.menubar_mute_toggle()
        self._player.volume_set(self.__volume__)

### App Indicator
    def appindicator_create(self):
        """ Ubuntu appindicator """
        self.status_icon = appindicator.Indicator.new(
                                "SilverRain",
                                ICON,
                                appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.status_icon.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.status_icon.connect("scroll-event", self.appindicator_on_scroll)
        # Popup menu
        self.appindicator_update_menu()

    def appindicator_update_menu(self):
        """ Creates popup menu attached to appindicator """
        if APP_INDICATOR:
            self.status_icon.set_menu(self.status_icon_popup_menu_create())

### Status Icon
    def status_icon_create(self):
        """ Status icon """
        if APP_INDICATOR:
            # Ubuntu workaround
            return self.appindicator_create()
        self.status_icon = Gtk.StatusIcon()
        self.status_icon.set_from_icon_name(ICON)
        # Default events
        self.status_icon.connect("activate", self.status_icon_on_activate)
        self.status_icon.connect("scroll-event", self.status_icon_on_scroll)
        # Popup menu
        self.status_icon.connect("popup-menu", self.status_icon_on_popup)
        # Tooltip
        self.status_icon.set_property("has-tooltip", True)
        self.status_icon.connect("query-tooltip", self.status_icon_tooltip)

    def status_icon_popup_menu_create(self):
        """ Show menu on right click """
        popup_menu = Gtk.Menu()
        if APP_INDICATOR:
            # Since appindicator doesn't support left click event
            activate = Gtk.MenuItem("Activate")
            activate.connect("activate", self.status_icon_on_activate)
            popup_menu.append(activate)
            separator = Gtk.SeparatorMenuItem()
            popup_menu.append(separator)
        # Playback
        text, icon = self.get_playback_label()
        play = self.create_menuitem(text, icon)
        play.connect("activate", self.playback_toggle)
        play.set_size_request(100, -1)
        # Record
        text, icon = self.get_record_label()
        record = self.create_menuitem(text, icon)
        if text == TRANSLATIONS[LANGUAGE]["Record"]:
            record.connect("activate", self.recorder_toggle)
        else:
            record.connect("activate", self.recorder_stop)
        # Mute
        mute = Gtk.CheckMenuItem(TRANSLATIONS[LANGUAGE]["Mute"])
        mute.set_active(self.__muted__)
        mute.connect("toggled", self.menubar_mute_toggle)
        # IM
        im = self.create_menuitem(TRANSLATIONS[LANGUAGE]["Messenger"],
                                 "gtk-edit")
        im.connect("activate", self.im_show)
        # Preferences
        preferences = self.create_menuitem(
                                 TRANSLATIONS[LANGUAGE]["Preferences"],
                                 "gtk-preferences")
        preferences.connect("activate", self.prefs_window_create)
        # Quit
        quit = self.create_menuitem(TRANSLATIONS[LANGUAGE]["Quit"], "gtk-quit")
        quit.connect("activate", Gtk.main_quit)
        # Separator
        sep = []
        for i in range(4):
            sep.append(Gtk.SeparatorMenuItem())

        for item in [play, record, sep[0], mute, sep[1],
                     im, sep[2], preferences, sep[3], quit]:
            popup_menu.append(item)
        popup_menu.show_all()
        return popup_menu

    def status_icon_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        # Silver Rain
        silver = Gtk.Label()
        silver.set_markup("<b>{0}</b>".format(
                                         TRANSLATIONS[LANGUAGE]["SilverRain"]))
        # Icon
        img = Gtk.Image.new_from_pixbuf(self._schedule.get_event_icon())
        # Program
        title = Gtk.Label()
        str = '\n'.join(textwrap.wrap(self._schedule.get_event_title(), 21))
        title.set_markup("<b>" + str + "</b>")
        title.set_alignment(0, 0.5)
        host = Gtk.Label()
        str = '\n'.join(textwrap.wrap(self._schedule.get_event_host(), 21))
        host.set_text(str)
        host.set_alignment(0, 0.5)
        time = Gtk.Label()
        time.set_text(self._schedule.get_event_time())
        time.set_alignment(0, 0.5)
        # Pack
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_border_width(10)
        grid = Gtk.Grid()
        grid.set_column_spacing(20)
        grid.attach(img,    0, 0, 1, 3)
        grid.attach(title,  1, 0, 1, 1)
        grid.attach(host,   1, 1, 1, 1)
        grid.attach(time,   1, 2, 1, 1)
        box.pack_start(silver, False, False, 0)
        box.pack_start(grid, False, False, 0)
        # Show
        box.show_all()
        tooltip.set_custom(box)
        return True

    def status_icon_on_activate(self, icon):
        """ Show/hide main window on left click """
        self.__main_window__ = not self.__main_window__
        if self.__main_window__:
            self.show()
        else:
            self.hide()

    def status_icon_on_popup(self, icon, button, time):
        self.popup_menu = self.status_icon_popup_menu_create()
        def pos_func(menu, x, y, icon):
            return (Gtk.StatusIcon.position_menu(menu, x, y, icon))
        self.popup_menu.popup(None, None, pos_func,
                         self.status_icon, button, time)

    def status_icon_on_scroll(self, icon, data):
        """ Change volume by scrolling on status icon """
        self.appindicator_on_scroll(None, 0, data.direction)

    def appindicator_on_scroll(self, indicator, steps, direction):
        """ Change volume by scrolling on indicator """
        if direction == Gdk.ScrollDirection.UP:
            if self.__volume__ >= 95:
                self.__volume__ = 100
            else:
                self.__volume__ = self.__volume__ + 5
        elif direction == Gdk.ScrollDirection.DOWN:
            if self.__volume__ <= 5:
                self.__volume__ = 0
            else:
                self.__volume__ = self.__volume__ - 5
        self.volume.set_value(self.__volume__)

### TreeView
    def sched_tree_model_create(self):
        """ Create schedule tree """
        store = Gtk.TreeStore(str,              #  0 Weekday
                              bool,             #  1 IsParent
                              str,              #  2 Time
                              str,              #  3 Title
                              str,              #  4 URL
                              str,              #  5 Host
                              GdkPixbuf.Pixbuf, #  6 Icon
                              str,              #  7 BackgroundColor
                              str,              #  8 FontColor
                              str,              #  9 Font
                              bool)             # 10 Recorder set
        self.sched_tree_model = store.filter_new()
        self.sched_tree_model.set_visible_func(self.sched_tree_model_func)
        self._schedule.fill_tree_strore(store)
        self.__cell_bg_old__ = ''
        self.__cell_fg_old__ = ''

    def sched_tree_model_func(self, model, iter, data):
        """ Filter by weekday """
        return model[iter][0] == self.__weekday_filter__

    def sched_tree_create(self):
        """ Create schedule tree """
        self.sched_tree_model_create()
        self.sched_tree = Gtk.TreeView.new_with_model(self.sched_tree_model)
        self.sched_tree.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.sched_tree.connect('button-release-event',
                           self.sched_tree_on_button_release_event)
        # Icon
        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn(" ", renderer, pixbuf=6)
        renderer.set_alignment(1, 0.5)
        self.sched_tree.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_padding(10, 0)
        renderer.set_alignment(0.5, 0.5)
        renderer.set_property('height', 50)
        # Time
        column = Gtk.TreeViewColumn(TRANSLATIONS[LANGUAGE]["Time"], renderer,
                                    text=2, background=7, foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(10)
        self.sched_tree.append_column(column)
        # Title
        renderer.set_alignment(0, 0.5)
        renderer.set_property("wrap_mode", Gtk.WrapMode.WORD)
        renderer.set_property("wrap_width", 200)
        column = Gtk.TreeViewColumn(TRANSLATIONS[LANGUAGE]["Title"], renderer,
                                    text=3, background=7, foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(50)
        column.set_resizable(True)
        self.sched_tree.append_column(column)
        # Host
        column = Gtk.TreeViewColumn(TRANSLATIONS[LANGUAGE]["Host"], renderer,
                                    text=5, background=7, foreground=8, font=9)
        column.set_alignment(0.5)
        column.set_min_width(50)
        column.set_resizable(True)
        self.sched_tree.append_column(column)
        # Add to scrolled window
        self.scrolled_window.add(self.sched_tree)

    def sched_tree_on_button_release_event(self, widget, event):
        if not event.button == 3:
            return
        selection = self.sched_tree.get_selection()
        model, iter = selection.get_selected()
        # Create popup menu
        self.sched_popup = Gtk.Menu()
        # Program url
        url = self.create_menuitem(TRANSLATIONS[LANGUAGE]["ProgramPage"],
                                   "web-browser")
        url.set_size_request(100, -1)
        event_url = model.get_value(iter, 4)
        url.connect("activate", self.url_open, event_url)
        self.sched_popup.append(url)
        # Record program
        if model.get_value(iter, 1):
            if not model.get_value(iter, 10):
                rec = self.create_menuitem(
                        TRANSLATIONS[LANGUAGE]["Record"],
                        "media-record")
                rec.connect("activate", self.sched_record_set, model, iter)
            else:
                rec = self.create_menuitem(
                        TRANSLATIONS[LANGUAGE]["DontRecord"], "gtk-cancel")
                rec.connect("activate", self.sched_record_cancel, model, iter)
            self.sched_popup.append(rec)

        self.sched_popup.show_all()
        self.sched_popup.popup(None, None,
                               None, None,
                               event.button, event.time)

    def url_open(self, button, url):
        subprocess.Popen(['xdg-open', url], stdout=subprocess.PIPE)

    def sched_record_set(self, button, model, iter):
        """ Record program """
        model.set_value(iter, 10, True)

    def sched_record_cancel(self, button, model, iter):
        """ Cancel recording """
        model.set_value(iter, 10, False)

### Timers
    def timers_clean(self):
        """ Cancel timer """
        self._t_event.cancel()
        self._t_recorder.cancel()

    def timers_reset(self):
        """ Reset timer """
        self.timers_clean()
        self.timers_init_event_timer()

    def timers_init_event_timer(self):
        """ Raise handler when event ends """
        today = datetime.now(MSK())
        now = timedelta(hours=today.hour,
                minutes=today.minute, seconds=today.second).total_seconds()
        timeout = int(self._schedule.get_event_end() - now)
        self._t_event = threading.Timer(timeout, self.timers_callback_event)
        self._t_event.start()

    def timers_callback_event(self):
        """ Update schedule """
        # Init new timer
        def func():
            self.update_now_playing()
            self.timers_init_event_timer()
        GObject.idle_add(func)

    def timers_callback_recorder_stop(self):
        """ Update schedule """
        # Init new timer
        GObject.idle_add(self.recorder_toggle, None)

### Updater
    def schedule_refresh(self, button): self.schedule_update(refresh=True)

    def schedule_update(self, refresh=False):
        """ Initialize schedule, create treeview and start timers
            This might take a while, so run in thread """
        def init_sched():
            # Initialize schedule
            ret = self._schedule.update_schedule(refresh)
            if not ret:
                if not refresh:
                    self.__SCHEDULE_ERROR__ = True
                GObject.idle_add(error)
            else:
                # Reset error flag
                self.__SCHEDULE_ERROR__ = False
                if not refresh:
                    # Initialization
                    # Create treeview
                    self.sched_tree_create()
                    # Initialize timers
                    self.timers_init_event_timer()
                else:
                    # Refresh treeview
                    self.sched_tree_model_create()
                    self.sched_tree.set_model(self.sched_tree_model)
                    self.timers_reset()
                GObject.idle_add(cleanup)

        def cleanup():
            t.join()
            # Draw sched tree if just created
            if not refresh:
                self.sched_tree.show()
            # Show playing status
            self.status_set_playing()
            # Update selection
            self.selection_update()
            # Mark current row
            self.sched_tree_mark_current()

        def error():
            t.join()
            # Show error status
            self.status_set_error()

        # Show updating status
        self.status_set_schedule_updating()
        # Show updating message
        t = threading.Thread(target=init_sched)
        t.start()

    def selection_update(self):
        """ Update selection """
        self.selection_buttons[self.__today__.weekday()].clicked()
        Gtk.Widget.grab_focus(self.selection_buttons[self.__today__.weekday()])

    def status_set_schedule_updating(self):
        """ Show spinner and "Updating" message """
        self.sched_refresh_button.hide()
        self.spinner.show()
        self.spinner.start()
        self.status.set_text("<span size='12000'><b>{0}</b></span>".format(
                             TRANSLATIONS[LANGUAGE]["Updating"]))
        self.status.set_use_markup(True)

    def status_set_playing(self):
        """ Hide spinner and show currently playing """
        self.spinner.stop()
        self.spinner.hide()
        self.sched_refresh_button.show()
        self.status_update()

    def status_set_error(self):
        """ Hide spinner and show error """
        self.spinner.stop()
        self.spinner.hide()
        self.sched_refresh_button.show()
        self.status.set_text("<span size='12000'><b>{0}</b></span>".format(
                             TRANSLATIONS[LANGUAGE]["UpdateFailed"]))
        self.status.set_use_markup(True)
        GObject.timeout_add(10000, self.status_update)

    def status_update(self):
        """ Show program name in status """
        if not self.__SCHEDULE_ERROR__:
            self.status.set_text("<span size='12000'><b>{0}</b></span>".format(
                                 self._schedule.get_event_title()))
            self.status.set_use_markup(True)

    def sched_tree_reset_current(self):
        """ Reset previously marked row """
        if self.__SCHEDULE_ERROR__ or not self.__cell_bg_old__:
            return
        pos = self._schedule.get_event_position()
        path = Gtk.TreePath(pos)
        iter = self.sched_tree_model.get_iter(path)
        self.sched_tree_model[iter][7] = self.__cell_bg_old__
        self.sched_tree_model[iter][8] = self.__cell_fg_old__
        self.sched_tree_model[iter][9] = FONT
        self.cell_bg_old = ''
        self.cell_fg_old = ''

    def sched_tree_mark_current(self):
        """ Set current event colors """
        if self.__SCHEDULE_ERROR__:
            return
        # Get current position
        pos = self._schedule.get_event_position()
        path = Gtk.TreePath(pos)
        self.__ref__ = Gtk.TreeRowReference.new(self.sched_tree_model,  path)
        iter = self.sched_tree_model.get_iter(path)
        # Backup original style
        self.__cell_bg_old__ = self.sched_tree_model[iter][7]
        self.__cell_fg_old__ = self.sched_tree_model[iter][8]
        # Set current row color
        self.sched_tree_model[iter][7] = SELECTED_BG_COLOR
        self.sched_tree_model[iter][8] = SELECTED_FONT_COLOR
        self.sched_tree_model[iter][9] = SELECTED_FONT
        # Scroll to current cell
        self.sched_tree.scroll_to_cell(path, use_align=True, row_align=0.5)

    def update_now_playing(self):
        """ Update label, bg of current event, show notifications """
        # Show agenda for today if not shown
        if not (self.__weekday_filter__ == self.__today__.strftime("%A")):
            self.selection_update()
        # Reset previous line
        self.sched_tree_reset_current()
        if self._schedule.update_current_event():
            # Update selection
            self.__today__ = datetime.now(MSK())
            self.selection_update()
        self.sched_tree_check_recorder()
        self.sched_tree_mark_current()
        self.status_update()
        self.show_notification_on_event()

    def sched_tree_check_recorder(self):
        """ Start recording if set """
        pos = self._schedule.get_event_position()
        path = Gtk.TreePath(pos)
        iter = self.sched_tree_model.get_iter(path)
        if self.sched_tree_model[iter][10]:
            self.sched_tree_model[iter][10] = False
            if self.__recording__:
                # Recorder was started manually
                return
            # Toggle recorder
            self.recorder_toggle(None)

### Messenger
    def im_create(self):
        """ Create messenger dialog """
        self.im = Gtk.Dialog.new()
        self.im.connect("delete-event", self.im_on_delete_event)
        self.im.set_title("Silver Rain: Messenger")
        self.im.set_resizable(True)
        self.im.set_transient_for(self)
        self.im.set_modal(False)
        # Background
        eventbox = Gtk.EventBox()
        # Header
        header = Gtk.HBox(spacing=5)
        header.set_border_width(10)
        img = Gtk.Image.new_from_icon_name(ICON, 64)
        img.set_pixel_size(50)
        title = Gtk.Label()
        title.set_markup("<span size='18000'><b>" +
                         "Silver Rain" +
                         "</b></span>\n<span size='11000'>{0}</span>".format(
                         TRANSLATIONS[LANGUAGE]["IMTitle"]))
        title.set_alignment(0, 0)
        title.set_selectable(True)
        header.pack_start(img, False, False, 0)
        header.pack_start(title, False, False, 0)
        eventbox.add(header)
        # Sender
        self.im_sender = Gtk.Entry()
        self.im_sender.set_text(MESSAGE_SENDER)
        self.im_sender.set_max_length(40)
        self.im_sender.set_placeholder_text(
                                TRANSLATIONS[LANGUAGE]["IMHeaderPlaceholder"])
        # Message
        win = Gtk.ScrolledWindow()
        win.set_policy(Gtk.PolicyType.AUTOMATIC,
                       Gtk.PolicyType.AUTOMATIC)
        win.set_min_content_height(100)
        self.eb_msg = Gtk.EventBox()
        eb = Gtk.EventBox()
        eb.set_border_width(1)
        self.msg = Gtk.TextView()
        self.msg.set_wrap_mode(Gtk.WrapMode.WORD)
        self.msg.set_left_margin(5)
        self.msg.set_border_window_size(Gtk.TextWindowType.TOP, 5)
        self.msg.set_border_window_size(Gtk.TextWindowType.RIGHT, 15)
        self.msg.set_border_window_size(Gtk.TextWindowType.BOTTOM, 15)
        win.add(self.msg)
        eb.add(win)
        self.eb_msg.add(eb)
        # Set border color
        color = Gdk.RGBA()
        color.parse(COLOR_TEXTVIEW_BORDER)
        self.eb_msg.override_background_color(Gtk.StateType.NORMAL, color)
        # Message status
        self.messenger_status = Gtk.Label()
        self.messenger_status.set_alignment(0.1, 0.5)
        # Pack
        box = Gtk.VBox(spacing=5)
        box.set_border_width(5)
        box.pack_start(self.im_sender, False, False, 0)
        box.pack_start(self.eb_msg, True, True, 0)
        box.pack_end(self.messenger_status, False, False, 0)
        area = self.im.get_content_area()
        area.set_border_width(0)
        area.set_spacing(0)
        area.pack_start(eventbox, False, False, 0)
        area.pack_start(box, True, True, 0)
        # Button
        self.im_send_button = self.im.add_button("", Gtk.ResponseType.OK)
        self.im_send_button.set_label(TRANSLATIONS[LANGUAGE]["Send"])
        self.im_send_button.connect("clicked", self.im_on_send)
        self.im_send_button.set_size_request(50, 30)
        # Ctrl+Enter to send
        agr = Gtk.AccelGroup()
        self.im.add_accel_group(agr)
        key, mod = Gtk.accelerator_parse("<Control>Return")
        self.im_send_button.add_accelerator("activate", agr,
                                            key, mod, Gtk.AccelFlags.VISIBLE)
        # Show
        area.show_all()
        self.messenger_status.hide()

    def im_show(self, widget):
        """ Show messenger """
        if self.__im_window__:
            return
        self.__im_window__ = True
        self.im.show()
        self.msg.grab_focus()

    def im_on_delete_event(self, window, event):
        """ Hide messenger """
        self.__im_window__ = False
        window.hide()
        return True

    def im_on_send(self, button):
        """ Check if forms are empty, otherwise send the message """
        color = Gdk.RGBA()
        color.parse(COLOR_TEXTVIEW_BORDER)
        msg_buf = self.msg.get_buffer()
        self.eb_msg.override_background_color(Gtk.StateType.NORMAL, color)
        if not self.im_sender.get_text_length():
            self.im_sender.grab_focus()
            return
        if not msg_buf.get_char_count():
            color.parse(COLOR_INVALID)
            self.eb_msg.override_background_color(Gtk.StateType.NORMAL, color)
            self.msg.grab_focus()
            return
        start = msg_buf.get_start_iter()
        end = msg_buf.get_end_iter()
        res = self.send_message(self.im_sender.get_text(),
                                msg_buf.get_text(start, end, True))
        if res == "error":
            self.messenger_status.set_markup("<i>{0}</i>".format(
                                   TRANSLATIONS[LANGUAGE]["MessengerError"]))
            self.messenger_status.show()
        elif res == "success":
            self.messenger_status.set_markup("<i>{0}</i>".format(
                                   TRANSLATIONS[LANGUAGE]["MessengerSuccess"]))
            self.messenger_status.show()
            # Clear text form
            msg_buf.delete(start, end)
            # Set 120s timer
            self.im_send_button.set_sensitive(False)
            self.im_countdown(120)
        else:
            # This should never happen
            pass
        GObject.timeout_add(10000, self.messenger_status.hide)

    def im_countdown(self, count):
        """ Set countdown timer """
        counter = count
        while counter >= 0:
            GObject.timeout_add(counter * 1000,
                                self.countdown_func, count - counter)
            counter -= 1

    def countdown_func(self, count):
        """ Show seconds remaining """
        if count > 0:
            self.im_send_button.set_label(TRANSLATIONS[LANGUAGE]["Send"] +
                                          " (" + str(count) + "s)")
        else:
            self.im_send_button.set_label(TRANSLATIONS[LANGUAGE]["Send"])
            self.messenger_status.hide()
            self.im_send_button.set_sensitive(True)


    def send_message(self, header, text):
        """ Send message in studio """
        # XXX XXX XXX
        # Emulate post request to server
        # I don't know, if it's legal, but definitely wrong.
        # XXX XXX XXX

        if not SESSID:
            # Get session vars
            try:
                self.get_session()
            except requests.exceptions.RequestException as e:
                self.error_show(str(e))
                return "error"
        # Emulate browser session
        s = requests.Session()
        headers = {
                'User-Agent' : USER_AGENT,
                'Accept'            : '*/*',
                'Accept-Encoding'   : 'gzip, deflate',
                'Accept-Language'   : 'en-US,en;q=0.8,ru;q=0.6',
                'Content-Type'      : 'application/x-www-form-urlencoded; ' + \
                                      'charset=UTF-8',
                'Cookie' : 'BX_USER_ID={0}; PHPSESSID={1}'.format(BX_USER_ID,
                                                                  PHPSESSID),
                'X-Requested-With'  : 'XMLHttpRequest' }
        # Serialize message
        message = urllib.parse.urlencode({'sessid' : SESSID,
                                          'web_form_submit' : 'Y',
                                          'WEB_FORM_ID' : 4,
                                          'form_text_81' : header,
                                          'form_text_82' : text})
        # POST request
        try:
            response = s.post(MESSENGER_URL, data=message, headers=headers)
        except requests.exceptions.RequestException as e:
            self.error_show(str(e))
            return "error"

        if response.status_code != 200:
            self.error_show("Connection error {0}".format(
                            response.status_code))
            logging.error(response)
            return "error"

        response_data = response.json()
        return response_data["type"]

    def get_session(self):
        global BX_USER_ID
        global PHPSESSID
        global SESSID
        # Download index page
        s = requests.Session()
        s.headers = {
                'User-Agent' : USER_AGENT,
                'Accept'     : 'text/html,application/xhtml+xml,' + \
                               'application/xml;q=0.9,image/webp,' + \
                               '*/*;q=0.8',
                'Accept-Encoding' : 'gzip, deflate, sdch',
                'Accept-Language' : ' en-US,en;q=0.8',
                'DNT' : '1',
                'Upgrade-Insecure-Requests' : '1' }
        resp = s.get(SILVER_RAIN_URL)
        # Get phpsessid from cookies
        PHPSESSID = re.sub(r'PHPSESSID=(.*?);.*$', r'\1',
                           resp.headers['Set-Cookie'])
        # Get sessid from form
        SESSID = re.sub(r'^.*name="sessid" id="sessid_6" value="(.*?)".*$',
                        r'\1', resp.text)
        # Get bitrix session id
        s = requests.Session()
        s.headers = {
                'User-Agent' : USER_AGENT,
                'Accept'     : '*/*',
                'Accept-Encoding' : 'gzip, deflate, sdch',
                'Accept-Language' : ' en-US,en;q=0.8',
                'Cookie' : 'PHPSESSID=' + PHPSESSID,
                'DNT' : '1',
                'Referer' : 'http://silver.ru/'}
        resp = s.get(BITRIX_SERVER)
        BX_USER_ID = re.sub(r'bx_user_id=(.*?);.*$', r'\1',
                           resp.headers['Set-Cookie'])

### Preferences window
    def prefs_window_create(self, widget):
        ## Dialog
        prefs = Gtk.Dialog.new()
        prefs.set_title("Silver Rain: Preferences")
        prefs.set_size_request(400, 300)
        prefs.set_transient_for(self)
        prefs.set_resizable(False)
        ## Header
        # Image
        img = Gtk.Image.new_from_icon_name(ICON, 64)
        img.set_pixel_size(50)
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='18000'><b>" +
                         "Silver Rain\n" +
                         "</b></span>" +
                         "<span size='11000'>" +
                         TRANSLATIONS[LANGUAGE]["Preferences"] +
                         "</span>")
        title.set_alignment(0, 0)
        title.set_selectable(True)
        # Pack
        eventbox = Gtk.EventBox()
        hbox = Gtk.HBox(spacing=5)
        hbox.set_border_width(10)
        hbox.pack_start(img, False, False, 0)
        hbox.pack_start(title, False, False, 0)
        eventbox.add(hbox)

        def create_page():
            page = Gtk.VBox()
            page.set_border_width(15)
            return page

        def create_prefs_grid():
            grid = Gtk.Grid()
            grid.set_border_width(10)
            grid.set_column_spacing(10)
            grid.set_row_spacing(5)
            return grid

        def pack_prefs_box(page, text, grid):
            title = Gtk.Label()
            title.set_alignment(0, 0.5)
            title.set_markup("<span size='11000'><b>" + text + "</b></span>")
            page.pack_start(title, False, False, 0)
            page.pack_start(grid, False, False, 0)

        ###############
        ### General ###
        ###############
        page_general = create_page()
        ## General
        general = create_prefs_grid()
        # Autoplay
        self.prefs_autoplay = Gtk.CheckButton()
        self.prefs_autoplay.set_label(TRANSLATIONS[LANGUAGE]["Autoplay"])
        self.prefs_autoplay.set_active(AUTOPLAY)
        general.attach(self.prefs_autoplay, 0, 0, 2, 1)
        # Start Hidden
        self.prefs_start_hidden = Gtk.CheckButton()
        self.prefs_start_hidden.set_label(
                                      TRANSLATIONS[LANGUAGE]["StartHidden"])
        self.prefs_start_hidden.set_active(START_HIDDEN)
        general.attach_next_to(self.prefs_start_hidden, self.prefs_autoplay,
                               Gtk.PositionType.BOTTOM, 2, 1)
        # Languages
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["Language"])
        text.set_size_request(180, -1)
        text.set_alignment(0, 0.5)
        general.attach_next_to(text, self.prefs_start_hidden,
                               Gtk.PositionType.BOTTOM, 1, 1)
        lang_store = Gtk.ListStore(str)
        for lang in LANGUAGES_LIST:
            lang_store.append([lang])
        self.prefs_language = Gtk.ComboBox.new_with_model(lang_store)
        renderer_text = Gtk.CellRendererText()
        self.prefs_language.pack_start(renderer_text, True)
        self.prefs_language.add_attribute(renderer_text, "text", 0)
        self.prefs_language.set_active(LANGUAGE)
        self.prefs_language.connect("changed", self.prefs_on_language_changed)
        general.attach_next_to(self.prefs_language, text,
                               Gtk.PositionType.RIGHT, 1, 1)
        self.prefs_need_restart = Gtk.Label()
        self.prefs_need_restart.set_alignment(0, 0)
        self.prefs_need_restart.set_markup(
                                        "<i>" +
                                        TRANSLATIONS[LANGUAGE]["NeedRestart"] +
                                        "</i>")
        general.attach_next_to(self.prefs_need_restart, text,
                               Gtk.PositionType.BOTTOM, 2, 1)
        pack_prefs_box(page_general,
                       TRANSLATIONS[LANGUAGE]["General"], general)
        ## Recordings
        recordings = create_prefs_grid()
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["Recsdirpath"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        recordings.attach(text, 0, 0, 1, 1)
        self.prefs_recs_dir = Gtk.FileChooserButton()
        self.prefs_recs_dir.set_filename(RECS_DIR)
        self.prefs_recs_dir.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        recordings.attach_next_to(self.prefs_recs_dir, text,
                                  Gtk.PositionType.RIGHT, 1, 1)
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["Recsprefix"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        recordings.attach(text, 0, 1, 1, 1)
        self.prefs_recs_prefix = Gtk.Entry()
        self.prefs_recs_prefix.set_text(RECS_PREFIX)
        self.prefs_recs_prefix.set_editable(True)
        recordings.attach_next_to(self.prefs_recs_prefix, text,
                                  Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_general,
                       TRANSLATIONS[LANGUAGE]["Recordings"], recordings)
        ## Messages
        im = create_prefs_grid()
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["IMHeader"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        im.attach(text, 0, 0, 1, 1)
        self.prefs_message_header = Gtk.Entry()
        self.prefs_message_header.set_editable(True)
        self.prefs_message_header.set_text(MESSAGE_SENDER)
        self.prefs_message_header.set_placeholder_text(
                                TRANSLATIONS[LANGUAGE]["IMHeaderPlaceholder"])
        im.attach_next_to(self.prefs_message_header, text,
                          Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_general, TRANSLATIONS[LANGUAGE]["Messenger"], im)
        ################
        ## Appearance ##
        ################
        page_appearance = create_page()
        # Background
        colors = create_prefs_grid()
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["BgColor"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        colors.attach(text, 0, 0, 1, 1)
        color = Gdk.RGBA()
        color.parse(BG_COLORS[0])
        self.prefs_bg_color_light = Gtk.ColorButton.new_with_rgba(color)
        colors.attach_next_to(self.prefs_bg_color_light, text,
                              Gtk.PositionType.RIGHT, 1, 1)
        # Alternate background
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["AltBgColor"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        colors.attach(text, 0, 1, 1, 1)
        color.parse(BG_COLORS[1])
        self.prefs_bg_color_dark = Gtk.ColorButton.new_with_rgba(color)
        colors.attach_next_to(self.prefs_bg_color_dark, text,
                              Gtk.PositionType.RIGHT, 1, 1)
        # Selection
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["SelBgColor"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        colors.attach(text, 0, 2, 1, 1)
        color.parse(SELECTED_BG_COLOR)
        self.prefs_selection_color = Gtk.ColorButton.new_with_rgba(color)
        colors.attach_next_to(self.prefs_selection_color, text,
                              Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_appearance,
                       TRANSLATIONS[LANGUAGE]["Colors"], colors)
        # Default font
        fonts = create_prefs_grid()
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["Font"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        fonts.attach(text, 0, 0, 1, 1)
        self.prefs_font = Gtk.FontButton()
        self.prefs_font.set_font_name(FONT)
        fonts.attach_next_to(self.prefs_font, text,
                             Gtk.PositionType.RIGHT, 1, 1)
        color.parse(FONT_COLOR)
        self.prefs_font_color = Gtk.ColorButton.new_with_rgba(color)
        fonts.attach_next_to(self.prefs_font_color, self.prefs_font,
                             Gtk.PositionType.RIGHT, 1, 1)
        # Selected font
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["SelFont"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        fonts.attach(text, 0, 1, 1, 1)
        self.prefs_selection_font = Gtk.FontButton()
        self.prefs_selection_font.set_font_name(SELECTED_FONT)
        fonts.attach_next_to(self.prefs_selection_font, text,
                             Gtk.PositionType.RIGHT, 1, 1)
        color.parse(SELECTED_FONT_COLOR)
        self.prefs_selection_font_color = Gtk.ColorButton.new_with_rgba(color)
        fonts.attach_next_to(self.prefs_selection_font_color,
                             self.prefs_selection_font,
                             Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_appearance,
                       TRANSLATIONS[LANGUAGE]["Fonts"], fonts)
        ## Reset button
        reset = Gtk.Button(TRANSLATIONS[LANGUAGE]["ResetDefault"])
        reset.connect("clicked", self.prefs_reset_appearance)
        page_appearance.pack_end(reset, False, False, 0)
        ###############
        ### Network ###
        ###############
        page_network = create_page()
        # Stream url
        network = create_prefs_grid()
        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["StreamUrl"])
        text.set_size_request(180, -1)
        text.set_alignment(0, 0.5)
        network.attach(text, 0, 0, 1, 1)
        stream_url_store = Gtk.ListStore(str)
        # If stream address defined by user
        if STREAM_URL not in STREAM_URL_LIST:
            STREAM_URL_LIST.append(STREAM_URL)
        for url in STREAM_URL_LIST:
            stream_url_store.append([url])
        self.prefs_stream_url = Gtk.ComboBox.new_with_model_and_entry(
                                                              stream_url_store)
        self.prefs_stream_url.set_entry_text_column(0)
        self.prefs_stream_url.set_active(STREAM_URL_LIST.index(STREAM_URL))
        network.attach_next_to(self.prefs_stream_url, text,
                               Gtk.PositionType.RIGHT, 1, 1)
        pack_prefs_box(page_network,
                       TRANSLATIONS[LANGUAGE]["Network"], network)
        # Proxy
        proxy = create_prefs_grid()
        self.prefs_use_proxy = Gtk.CheckButton()
        self.prefs_use_proxy.set_label(TRANSLATIONS[LANGUAGE]["UseProxy"])
        self.prefs_use_proxy.set_active(PROXY_REQUIRED)
        self.prefs_use_proxy.connect("toggled", self.prefs_on_use_proxy)
        proxy.attach(self.prefs_use_proxy, 0, 0, 2, 1)

        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["ProxyUri"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        proxy.attach(text, 0, 1, 1, 1)
        self.prefs_proxy_uri = Gtk.Entry()
        self.prefs_proxy_uri.set_text(PROXY_URI)
        self.prefs_proxy_uri.set_editable(True)
        self.prefs_proxy_uri.set_sensitive(PROXY_REQUIRED)
        proxy.attach_next_to(self.prefs_proxy_uri, text,
                             Gtk.PositionType.RIGHT, 1, 1)

        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["ProxyUsername"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        proxy.attach(text, 0, 2, 1, 1)
        self.prefs_proxy_username = Gtk.Entry()
        self.prefs_proxy_username.set_text(PROXY_ID)
        self.prefs_proxy_username.set_editable(True)
        self.prefs_proxy_username.set_sensitive(PROXY_REQUIRED)
        proxy.attach_next_to(self.prefs_proxy_username, text,
                             Gtk.PositionType.RIGHT, 1, 1)

        text = Gtk.Label(TRANSLATIONS[LANGUAGE]["ProxyPassword"])
        text.set_alignment(0, 0.5)
        text.set_size_request(180, -1)
        proxy.attach(text, 0, 3, 1, 1)
        self.prefs_proxy_password = Gtk.Entry()
        self.prefs_proxy_password.set_text(PROXY_PW)
        self.prefs_proxy_password.set_editable(True)
        self.prefs_proxy_password.set_sensitive(PROXY_REQUIRED)
        proxy.attach_next_to(self.prefs_proxy_password, text,
                             Gtk.PositionType.RIGHT, 1, 1)

        pack_prefs_box(page_network, TRANSLATIONS[LANGUAGE]["Proxy"], proxy)

        ## Notebook
        notebook = Gtk.Notebook()
        notebook.set_show_border(True)
        notebook.set_border_width(10)
        notebook.append_page(page_general,
                             Gtk.Label(TRANSLATIONS[LANGUAGE]["General"]))
        notebook.append_page(page_appearance,
                             Gtk.Label(TRANSLATIONS[LANGUAGE]["Appearance"]))
        notebook.append_page(page_network,
                             Gtk.Label(TRANSLATIONS[LANGUAGE]["Network"]))
        ## Pack
        area = prefs.get_content_area()
        area.set_border_width(0)
        area.set_spacing(5)
        area.pack_start(eventbox, False, False, 0)
        area.pack_start(notebook, True, True, 0)
        area.show_all()
        ## Buttons
        prefs.add_button(Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)
        prefs.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        ## Show
        self.prefs_need_restart.hide()
        # Apply settings
        while prefs.run() == Gtk.ResponseType.APPLY:
            new_path = self.prefs_recs_dir.get_filename()
            if os.access(new_path, os.W_OK):
                Gtk.Widget.grab_focus(self.prefs_recs_dir)
                self.prefs_apply_settings()
                break
            else:
                self.error_show("Invalid recordings storage location")
                self.prefs_recs_dir.set_filename(RECS_DIR)
                Gtk.Widget.grab_focus(self.prefs_recs_dir)

        prefs.destroy()

    def prefs_on_use_proxy(self, combo):
        state = combo.get_active()
        self.prefs_proxy_uri.set_sensitive(state)
        self.prefs_proxy_username.set_sensitive(state)
        self.prefs_proxy_password.set_sensitive(state)

    def prefs_on_language_changed(self, combo):
        self.prefs_need_restart.show()

    def prefs_apply_settings(self):
        """ Apply settings and save config file """
        # General
        global AUTOPLAY
        AUTOPLAY = self.prefs_autoplay.get_active()
        global START_HIDDEN
        START_HIDDEN = self.prefs_start_hidden.get_active()
        global LANGUAGE
        LANG_OLD = LANGUAGE
        iter = self.prefs_language.get_active_iter()
        if iter:
            model = self.prefs_language.get_model()
            lang = model[iter][0]
            LANGUAGE = LANGUAGES_LIST.index(lang)
        global RECS_DIR
        RECS_DIR = self.prefs_recs_dir.get_filename()
        global RECS_PREFIX
        RECS_PREFIX = self.prefs_recs_prefix.get_text()
        global MESSAGE_SENDER
        MESSAGE_SENDER = self.prefs_message_header.get_text()
        # Appearance
        global SELECTED_BG_COLOR
        SELECTED_BG_COLOR = rgba_to_hex(self.prefs_selection_color.get_rgba())
        global BG_COLORS
        BG_COLORS[0] = rgba_to_hex(self.prefs_bg_color_light.get_rgba())
        BG_COLORS[1] = rgba_to_hex(self.prefs_bg_color_dark.get_rgba())
        global FONT
        FONT = self.prefs_font.get_font_name()
        global FONT_COLOR
        FONT_COLOR = rgba_to_hex(self.prefs_font_color.get_rgba())
        global SELECTED_FONT
        SELECTED_FONT = self.prefs_selection_font.get_font_name()
        global SELECTED_FONT_COLOR
        SELECTED_FONT_COLOR = rgba_to_hex(
                                   self.prefs_selection_font_color.get_rgba())
        # Network
        global STREAM_URL
        iter = self.prefs_stream_url.get_active_iter()
        if iter:
            model = self.prefs_stream_url.get_model()
            STREAM_URL = model[iter][0]
        else:
            STREAM_URL = self.prefs_stream_url.get_child().get_text()
        global PROXY_REQUIRED
        PROXY_REQUIRED = self.prefs_use_proxy.get_active()
        global PROXY_URI
        PROXY_URI = self.prefs_proxy_uri.get_text()
        global PROXY_ID
        PROXY_ID = self.prefs_proxy_username.get_text()
        global PROXY_PW
        PROXY_PW = self.prefs_proxy_password.get_text()
        # Save config file
        config_save()
        # Restore language
        LANGUAGE = LANG_OLD
        # Update schedule
        self.selection_update()
        self.sched_tree_model_create()
        self.sched_tree.set_model(self.sched_tree_model)
        self.sched_tree_mark_current()
        # Update messenger
        self.im_sender.set_text(MESSAGE_SENDER)
        # Update player
        self._player.reset_network_settings()

    def prefs_reset_appearance(self, widget):
        """ Reset default settings """
        color = Gdk.RGBA()
        # BG colors
        color.parse(DEFAULT_BG_COLORS[0])
        self.prefs_bg_color_light.set_rgba(color)
        color.parse(DEFAULT_BG_COLORS[1])
        self.prefs_bg_color_dark.set_rgba(color)
        # Selection color
        color.parse(DEFAULT_SELECTED_BG_COLOR)
        self.prefs_selection_color.set_rgba(color)
        # Font
        self.prefs_font.set_font_name(DEFAULT_FONT)
        color.parse(DEFAULT_FONT_COLOR)
        self.prefs_font_color.set_rgba(color)
        # Selection font
        self.prefs_selection_font.set_font_name(DEFAULT_SELECTED_FONT)
        color.parse(DEFAULT_SELECTED_FONT_COLOR)
        self.prefs_selection_font_color.set_rgba(color)

### About dialog
    def about_window_create(self, icon):
        about = Gtk.Dialog.new()
        about.set_title("Silver Rain: About")
        about.set_transient_for(self)
        about.set_size_request(200, -1)
        about.set_resizable(False)
        # Header
        eventbox = Gtk.EventBox()
        header = Gtk.HBox(spacing=5)
        header.set_border_width(0)
        img = Gtk.Image.new_from_icon_name(ICON, 64)
        img.set_pixel_size(50)
        title = Gtk.Label()
        title.set_markup("<span size='18000'><b>Silver Rain</b></span>\n" +
                         "<span size='11000'>Version " + VERSION + "</span>")
        title.set_alignment(0, 0)
        title.set_selectable(True)
        header.pack_start(img, False, False, 0)
        header.pack_start(title, False, False, 0)
        eventbox.add(header)
        # Text
        text = Gtk.Label()
        text.set_selectable(True)
        text.set_markup(
                "Silver Rain radio application for Linux\n" +
                "This pruduct is not approved in any way\n" +
                "by Silver Rain Radio or anybody else.\n" +
                "\n" +
                "Check for the latest version " +
                "<a href='https://github.com/PetrSkovoroda/silver-rain'>" +
                "here" + "</a>\n" +
                "Copyright \xa9 2015 Petr Skovoroda"
                )
        # Pack
        area = about.get_content_area()
        area.set_spacing(10)
        area.set_border_width(10)
        area.pack_start(eventbox, False, False, 0)
        area.pack_start(text, False, False, 0)
        about.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        about.show_all()
        about.run()
        about.destroy()

### Dialog
    def dialog_create(self, title, icon_name, message):
        dialog = Gtk.Dialog.new()
        dialog.set_title("Silver Rain: " + title)
        dialog.set_resizable(False)
        dialog.set_transient_for(self)
        # Image
        icontheme = Gtk.IconTheme.get_default()
        icon = icontheme.load_icon(icon_name, 48, 0)
        img = Gtk.Image()
        img.set_from_pixbuf(icon)
        # Message
        text = Gtk.Label("{0}: {1}".format(title,
                         "\n".join(textwrap.wrap(message, 50))))
        # Pack
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_border_width(10)
        grid.attach(img, 0, 0, 1, 1)
        grid.attach(text, 1, 0, 1, 1)
        # Content
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.pack_start(grid, True, True, 0)
        # Button
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

    def warning_show(self, msg):
        self.dialog_create("Warning", "dialog-warning", msg)

    def error_show(self, msg):
        self.dialog_create("Error", "dialog-error", msg)

### GStreamer callbacks
    def playback_emergency_stop(self):
        """ Change buttons """
        if self.__playing__:
            self.playback_toggle(None)

    def recorder_emergency_stop(self):
        """ Change buttons, cancel timer """
        if self.__recording__:
            self.recorder_toggle(None)

### Common
    def create_menuitem(self, text, icon):
        """ Create menu item with icon """
        icontheme = Gtk.IconTheme.get_default()
        icon = icontheme.load_icon(icon, 16, 0)
        img = Gtk.Image()
        img.set_from_pixbuf(icon)
        menuitem = Gtk.ImageMenuItem()
        menuitem.set_image(img)
        menuitem.set_label(text)
        return menuitem

    def create_toolbutton(self, icon):
        """ Toolbar button """
        button = Gtk.ToolButton()
        button.set_icon_name(icon)
        return button

    def playback_toggle(self, button):
        """ Update interface, toggle player """
        self.__playing__ = not self.__playing__
        self.playback_button.set_icon_name(self.get_playback_label()[1])
        # Menubar
        self.menubar_play.set_sensitive(not self.__playing__)
        self.menubar_stop.set_sensitive(self.__playing__)
        # Control panel
        self.playback_button.set_tooltip_text(self.get_playback_label()[0])
        # Appindicator
        self.appindicator_update_menu()
        self._player.playback_toggle()
        self.show_notification_on_playback()

    def recorder_toggle(self, button):
        """ Change status, toggle recorder, set timer """
        self.__recording__ = not self.__recording__
        # Menubar
        self.menubar_record.set_sensitive(not self.__recording__)
        self.menubar_stop_recording.set_sensitive(self.__recording__)
        # Appindicator
        self.appindicator_update_menu()
        if self.__recording__:
            # Set timer
            today = datetime.now(MSK())
            now = timedelta(hours=today.hour,
                            minutes=today.minute,
                            seconds=today.second).total_seconds()
            timeout = int(self._schedule.get_event_end() - now)
            self._t_recorder = threading.Timer(timeout,
                            self.timers_callback_recorder_stop)
            self._t_recorder.start()
        # Get name
        if not self.__SCHEDULE_ERROR__:
            name = self._schedule.get_event_title()
        else:
            name = "SilverRain"
        # Start recorder
        self._player.recorder_toggle(name)

    def recorder_stop(self, button):
        """ Cancel timer, toggle recorder """
        self._t_recorder.cancel()
        self.recorder_toggle(None)

    def mute_toggle(self, button, val=0):
        """ Set volume, update interface """
        if self.__muted__:
            self.__volume__ = self.__muted__
            self.__muted__ = 0
        else:
            self.__muted__ = self.__volume__ or 5
            self.__volume__ = 0
        # Control panel
        self.mute_button.set_icon_name(self.get_volume_icon())
        # Appindicator
        self.appindicator_update_menu()
        # This actually gonna mute player
        self.volume.set_value(self.__volume__)

    def get_playback_label(self):
        """ Return label and icon for Playback menu/button """
        if not self.__playing__:
            label = TRANSLATIONS[LANGUAGE]["Play"]
            icon = "media-playback-start"
        else:
            label = TRANSLATIONS[LANGUAGE]["Stop"]
            icon = "media-playback-stop"
        return label, icon

    def get_record_label(self):
        """ Return label and icon for Playback menu/button """
        if not self.__recording__:
            label = TRANSLATIONS[LANGUAGE]["Record"]
            icon = "media-record"
        else:
            label = TRANSLATIONS[LANGUAGE]["StopRecording"]
            icon = "media-playback-stop"
        return label, icon

    def get_volume_icon(self):
        """ Return label and icon for Playback menu/button """
        if self.__muted__:
            icon = "audio-volume-muted"
        else:
            icon = "audio-volume-high"
        return icon

    def show_notification_on_event(self):
        """ Show currently playing """
        text = "Silver Rain"
        if not self.__SCHEDULE_ERROR__:
            body = "<b>" + self._schedule.get_event_title() + "</b>" + \
                   "\n" + self._schedule.get_event_host()
            self.notification.set_icon_from_pixbuf(
                    self._schedule.get_event_icon())
            self.notification.update(text, body)
        else:
            body = "Playing"
            img = "notification-audio-stop"
            self.notification.update(text, body, img)
        self.notification.show()

    def show_notification_on_playback(self):
        if self.__playing__:
            self.show_notification_on_event()
        else:
            text = "Silver Rain"
            body = "Stopped"
            img = "notification-audio-stop"
            self.notification.update(text, body, img)
            self.notification.show()

# Common
def rgba_to_hex(rgba):
    r = int(rgba.red * 255)
    g = int(rgba.green * 255)
    b = int(rgba.blue * 255)
    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

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

########################################################################
# Boom, baby
def let_it_rain():
    GObject.threads_init()
    Gst.init(None)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Notify.init("Silver Rain")

    # Create directories if they don't exist
    for dir in [APP_DIR, IMG_DIR]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    # Read config
    if not os.path.exists(CONFIG_FILE):
        # Initialize default settings
        config_init_default()
        # Create configuration file
        config_save()
    else:
        config_load()

    if not os.path.exists(RECS_DIR):
        os.makedirs(RECS_DIR)

    # Load css
    if USE_CSS and CSS_PATH:
        css_load()

    # Init
    silver_player = SilverPlayer()
    silver_schedule = SilverSchedule()
    silver_window = SilverGUI(silver_player, silver_schedule)
    service = SilverService(silver_window)
    # Run loop
    Gtk.main()
    # Cleanup
    Notify.uninit()
    silver_window.clean()
    silver_player.clean()

def exec_main():
    # Check if already running
    if (dbus.SessionBus().request_name("org.SilverRain.Silver") !=
                                    dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER):
        object = dbus.SessionBus().get_object("org.SilverRain.Silver",
                                              "/org/SilverRain/Silver")
        method = object.get_dbus_method("show_window")
        method()
    else:
        let_it_rain()

if __name__ == '__main__':
    exec_main()
