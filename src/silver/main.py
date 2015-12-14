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
from gi.repository import Gst, Gtk, GObject, Notify

import dbus
import dbus.service
import os
import signal

from . import application
from . import config
from . import css
from . import globals
from . import translations

########################################################################
# DBus service
class SilverService(dbus.service.Object):
    """ DBus service """
    def __init__(self, win):
        self.window = win
        bus_name = dbus.service.BusName('org.SilverRain.Silver',
                                    bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name,
                                    '/org/SilverRain/Silver')

    @dbus.service.method(dbus_interface='org.SilverRain.Silver')

    def show_window(self):
        self.window.present()

def let_it_rain():
    GObject.threads_init()
    Gst.init(None)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Notify.init("Silver Rain")

    # Create directories if they don't exist
    for dir in [globals.APP_DIR, globals.IMG_DIR]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    # Read config
    if not os.path.exists(globals.CONFIG_FILE):
        # Initialize default settings
        config.init()
        # Create configuration file
        config.save()
    else:
        config.load()

    # Create directory for recordings
    if not os.path.exists(config.recs_dir):
        os.makedirs(config.recs_dir)

    # Load css
    css.css_load()
    # Init translation
    translations.set_translation()
    # Init
    silver_window = application.SilverApplication()
    #service = SilverService(silver_window)
    # Run loop
    Gtk.main()
    # Cleanup
    Notify.uninit()
    silver_window.clean()

def exec_main():
    # Check if already running
    #if (dbus.SessionBus().request_name("org.SilverRain.Silver") !=
                                    #dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER):
        #object = dbus.SessionBus().get_object("org.SilverRain.Silver",
                                    #"/org/SilverRain/Silver")
        #method = object.get_dbus_method("show_window")
        #method()
    #else:
    let_it_rain()

if __name__ == '__main__':
    exec_main()
