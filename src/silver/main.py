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
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import dbus.service
import os
import signal

import silver.config as config
from silver.application import SilverApp
from silver.globals import IMG_DIR
from silver.gui.css import css_load
from silver.translations import set_translation

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
    Gst.init(None)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Notify.init("silver-rain")
    # Create system directories
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)
    # Initialize config
    config.setup()
    # Create directory for recordings
    if not os.path.exists(config.recs_dir):
        os.makedirs(config.recs_dir)
    # Load css
    css_load()
    # Init translation
    set_translation()
    # Init application
    silver_app = SilverApp()
    # Setup dbus service
    service = SilverService(silver_app)
    # Run loop
    Gtk.main()
    # Cleanup
    silver_app.clean()
    Notify.uninit()

def exec_main():
    # Check if already running
    bus = dbus.SessionBus()
    reply = bus.request_name("org.SilverRain.Silver")
    if reply != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        object = bus.get_object("org.SilverRain.Silver",
                                "/org/SilverRain/Silver")
        method = object.get_dbus_method("show_window")
        method()
    else:
        let_it_rain()

if __name__ == '__main__':
    exec_main()
