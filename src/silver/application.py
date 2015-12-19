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

from gi.repository import GObject, Gtk
import threading

import silver.config as config

from silver.gui.about import About
from silver.gui.controlpanel import ControlPanel
from silver.gui.dialog import error_show
from silver.gui.dialog import warning_show
from silver.gui.menubar import Menubar
from silver.gui.preferences import Preferences
from silver.gui.schedtree import SchedTree
from silver.gui.selection import Selection
from silver.gui.statusicon import StatusIcon
from silver.gui.window import MainWindow

from silver.messenger import Messenger
from silver.notifications import Notifications
from silver.player import SilverPlayer
from silver.player import SilverRecorder
from silver.schedule import SilverSchedule
from silver.timer import Timer
from silver.translations import _

### Application
class SilverApp():
    def __init__(self):
        # Initialize GStreamer
        self._player = SilverPlayer(self._on_player_error)
        self._recorder = SilverRecorder(self._on_recorder_error)
        # Schedule
        self._schedule = SilverSchedule()
        # On event timer
        self._t_event = Timer(self.update_now_playing)
        # Record timer
        self._t_recorder = Timer(self.stop_record)
        # Menubar
        self._menubar = Menubar(self)
        # Selection
        self._selection = Selection(self)
        # Controls
        self._panel = ControlPanel(self)
        # Main window
        self._window = MainWindow(self._menubar, self._selection, self._panel)
        # Don't show if should stay hidden
        if not config.start_hidden:
            self.show()
        # Messenger
        self._messenger = Messenger(self._window)
        # Notifications
        self._notifications = Notifications()
        # Satus icon
        self._status_icon = StatusIcon(self)
        # Update schedule
        self.update_schedule(False)
        # Autoplay
        if config.autoplay:
            self.play()

    def clean(self):
        """ Cleanup """
        self._t_event.cancel()
        self._t_recorder.cancel()
        self._player.clean()
        self._recorder.clean()

    def present(self):
        self._window.present()

# Application API
    def show(self):
        """ Show main window """
        self._window.show()
        self._window.hidden = False

    def hide(self):
        """ Hide main window """
        self._window.hide()
        self._window.hidden = True

    def toggle(self):
        """ Show/hide window """
        if self._window.hidden:
            self.show()
        else:
            self.hide()

    def about(self):
        """ Open about dialog """
        dialog = About(self._window)
        dialog.run()
        dialog.destroy()

    def im(self):
        """ Open messenger """
        self._messenger.show()

    def prefs(self):
        """ Open preferences window """
        dialog = Preferences(self._window)
        # Apply settings
        apply = []
        while dialog.run() == Gtk.ResponseType.APPLY:
            if dialog.validate():
                apply = dialog.apply_settings()
                break
            else:
                error_show(self._window, "Invalid recordings storage location")
        dialog.destroy()
        if "IM" in apply:
            # Update messenger
            self._messenger.update_sender()
        if "APPEARANCE" in apply:
            # Update schedule
            self._selection.update()
            self._sched_tree.update_model()
            self._sched_tree.mark_current()
        if "NETWORK" in apply:
            # Update player
            if self._player.playing:
                self.stop()
            self._player.reset_connection_settings()
            # Update recorder
            if self._recorder.playing:
                self.stop_record()
            self._recorder.reset_connection_settings()

    def play(self):
        """ Update interface, start player """
        # Update interface
        self._menubar.update_playback_menu(True)
        self._panel.update_playback_button(True)
        self._status_icon.update_playback_menu(True)
        # Play
        self._player.play()
        # Get current event
        title = self._schedule.get_event_title()
        host = self._schedule.get_event_host()
        img = self._schedule.get_event_icon()
        # Show notification
        self._notifications.show_playing(title=title, host=host, icon=img)

    def stop(self):
        """ Update interface, stop player """
        # Update interface
        self._menubar.update_playback_menu(False)
        self._panel.update_playback_button(False)
        self._status_icon.update_playback_menu(False)
        # Stop player
        self._player.stop()
        # Show notification
        self._notifications.show_stopped()

    def set_volume(self, value):
        """ Set player volume """
        if value == 0:
            self.mute()
        elif self._player.muted:
            self.unmute(volume=value)
        else:
            self._player.set_volume(value)

    def volume_step(self, value):
        vol = self._player.volume
        vol += value
        if vol > 100:
            vol = 100
        elif vol < 0:
            vol = 0
        self.set_volume(vol)
        if vol:
            self._panel.update_volume_scale(vol)

    def mute(self):
        """ Mute player, update interface """
        self._player.mute()
        self._menubar.update_mute_menu(True)
        self._panel.update_mute_button(True)
        self._panel.update_volume_scale(0)
        self._status_icon.update_mute_menu(True)

    def unmute(self, volume=0):
        """ Unmute player, update interface """
        if not volume:
            self._player.unmute()
        else:
            self._player.set_volume(volume)
        self._menubar.update_mute_menu(False)
        self._panel.update_mute_button(False)
        self._panel.update_volume_scale(self._player.volume)
        self._status_icon.update_mute_menu(False)

    def record(self):
        """ Update interface, start recorder """
        # Set timer
        self._t_recorder.reset(self._schedule.get_event_end())
        # Get name
        name = self._schedule.get_event_title()
        # Start recorder
        self._recorder.play(name)
        # Update interface
        self._menubar.update_recorder_menu(True)
        self._status_icon.update_recorder_menu(True)

    def stop_record(self):
        """ Update interface, stop recorder """
        self._recorder.stop()
        self._t_recorder.cancel()
        # Update interface
        self._menubar.update_recorder_menu(False)
        self._status_icon.update_recorder_menu(False)

    def refilter(self, weekday):
        """ Refilter TreeView """
        self._sched_tree.refilter(weekday)

    def update_schedule(self, refresh):
        """ Initialize schedule, create treeview and start timers
            This might take a while, so run in thread """
        def init_sched():
            # Initialize schedule
            ret = self._schedule.update_schedule(refresh)
            if not ret:
                GObject.idle_add(error)
            else:
                if not refresh:
                    # Create TreeView
                    self._sched_tree = SchedTree(self._schedule)
                    self._window.set_widget(self._sched_tree)
                else:
                    # Refresh TreeView
                    self._sched_tree.update_model()
                GObject.idle_add(cleanup)

        def cleanup():
            t.join()
            # Draw sched tree if just created
            if not refresh:
                self._sched_tree.show()
            # Reset status
            self._panel.status_set_playing()
            # Start timer
            self._t_event.reset(self._schedule.get_event_end())
            # Show agenda for today
            self._selection.update()
            # Update treeview
            self._sched_tree.mark_current()
            # Update statusicon tooltip
            title = self._schedule.get_event_title()
            host = self._schedule.get_event_host()
            time = self._schedule.get_event_time()
            img = self._schedule.get_event_icon()
            self._status_icon.update_event(title, host, time, img)
            # Update status
            self._panel.status_set_text(title)

        def error():
            t.join()
            # Show error status
            self._panel.status_set_text(_("Couldn't update schedule"))
            def f():
                title = self._schedule.get_event_title()
                self._panel.status_set_text(title)
            GObject.timeout_add(10000, f)
            self._panel.status_set_playing()

            title = self._schedule.get_event_title()
            host = self._schedule.get_event_host()
            time = self._schedule.get_event_time()
            img = self._schedule.get_event_icon()
            self._status_icon.update_event(title, host, time, img)

        # Show updating status
        self._panel.status_set_updating()
        # Show updating message
        t = threading.Thread(target=init_sched)
        t.start()

    def update_now_playing(self):
        """ Update label, bg of current event, show notifications """
        # Reset previous line
        self.refilter(self._schedule.get_event_weekday())
        self._sched_tree.reset_current()
        # Update event
        self._schedule.update_current_event()
        # Update treeview
        self._selection.update()
        self._sched_tree.mark_current()
        # Check if should be recorded
        if self._sched_tree.check_recorder():
            self.record()
        # Update statusicon tooltip
        title = self._schedule.get_event_title()
        host = self._schedule.get_event_host()
        time = self._schedule.get_event_time()
        img = self._schedule.get_event_icon()
        self._status_icon.update_event(title, host, time, img)
        # Update status
        self._panel.status_set_text(title)
        # Show notification
        self._notifications.show_playing(title, host, img)
        # Start timer
        self._t_event.reset(self._schedule.get_event_end())

    def quit(self):
        """ Exit """
        Gtk.main_quit()
    
### GStreamer callbacks
    def _on_player_error(self, type, msg):
        if type == "warning":
            warning_show(self._window, msg)
        elif type == "error":
            error_show(self._window, msg)
        self.stop()

    def _on_recorder_error(self, type, msg):
        if type == "warning":
            warning_show(self._window, msg)
        elif type == "error":
            error_show(self._window, msg)
        self.stop_record()
