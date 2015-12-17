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

from gi.repository import Gst

from datetime import datetime
import sys

from . import config
from .msktz import MSK

class Player():
    """ Base class for player instances """
    def __init__(self, err_func):
        self.playing = False
        self.muted = 0
        self.volume = 100
        # Set error callbacks
        self._error_callback = err_func

    def reset_connection_settings(self):
        if self.playing:
            self.stop()
        self._on_config_changed()

    def clean(self):
        self.playing = False
        self._clean()

# Playback control API
    def play(self, arg=None):
        if not self.playing:
            self._play(arg)
            self.playing = True

    def stop(self):
        if self.playing:
            self._stop()
            self.playing = False

    def set_volume(self, volume):
        pass

# Internal
    def _play(self, arg):
        raise NotImplementedError

    def _stop(self):
        raise NotImplementedError

    def _on_config_changed(self):
        raise NotImplementedError

    def _clean(self):
        pass

    def _on_eos(self, bus, msg):
        self._error_callback("warning", "End of stream")
        self.stop()

    def _on_error(self, bus, msg):
        err, dbg = msg.parse_error()
        str = "Error on element {0}: {1}".format(msg.src.get_name, err)
        self._error_callback("error", str)
        self.stop()

class SilverPlayer(Player):
    """ GStreamer class for playing network stream
        souphttpsrc -> decodebin -> audioconvert -> volume -> autoaudiosink """

    __name__ = "SilverPlayer"

    def __init__(self, err_func):
        Player.__init__(self, err_func)

        # Create GStream pipeline
        self._pipe = Gst.Pipeline.new(self.__name__)
        if not self._pipe:
            self._error_callback("error", "Couldn't create pipeline")
            sys.exit(-1)
        self._el = dict()
        try:
            self._el["source"] = Gst.ElementFactory.make("souphttpsrc",
                                                            "source")
            self._el["decode"] = Gst.ElementFactory.make("decodebin",
                                                            "decode")
            self._el["convert"] = Gst.ElementFactory.make("audioconvert",
                                                            "convert")
            self._el["volume"] = Gst.ElementFactory.make("volume",
                                                            "volume")
            self._el["sink"] = Gst.ElementFactory.make("autoaudiosink",
                                                            "sink")
        except Gst.ElementNotFoundError:
            self._error_callback("error", "Couldn't find GStreamer element")
            sys.exit(-1)

        for e in self._el:
            if not self._el[e]:
                self._error_callback("error",
                                     "Couldn't create GStreamer element: " + e)
                sys.exit(-1)
            self._pipe.add(self._el[e])

        self._el["source"].set_property("location", config.stream_url)
        self._el["source"].set_property("is-live", True)
        self._el["source"].set_property("compress", True)
        if config.proxy_required:
            self._el["source"].set_property("proxy", config.proxy_uri)
            self._el["source"].set_property("proxy-id", config.proxy_id)
            self._el["source"].set_property("proxy-pw", config.proxy_pw)
        self._el["volume"].set_property("volume", 1.)

        # Link elements
        def on_pad_added(decode, pad):
            if not pad.is_linked():
                return pad.link(self._el["convert"].get_static_pad("sink"))
        self._el["decode"].connect("pad-added", on_pad_added)
        if (not Gst.Element.link(self._el["source"], self._el["decode"]) or
            not Gst.Element.link(self._el["convert"], self._el["volume"]) or
            not Gst.Element.link(self._el["volume"], self._el["sink"])):
            self._error_callback("error", "Elements could not be linked")
            sys.exit(-1)

        # Create message bus
        self._bus = self._pipe.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message::eos", self._on_eos)
        self._bus.connect("message::error", self._on_error)

    def set_volume(self, value):
        """ Set player volume [0-100] """
        self._pipe.get_by_name("volume").set_property("volume", value / 100.)

    def _play(self, stream=None):
        if stream:
            self._pipe.get_by_name("source").set_property("location", stream)
        ret = self._pipe.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self._error_callback("error", "Couldn't change state on pipeline")
            self.clean()
            sys.exit(-1)

    def _stop(self):
        ret = self._pipe.set_state(Gst.State.READY)
        if ret == Gst.StateChangeReturn.FAILURE:
            self._error_callback("error", "Couldn't change state on pipeline")
            self.clean()
            sys.exit(-1)

    def _clean(self):
        """ Unref pipeline """
        self._pipe.set_state(Gst.State.NULL)

    def _on_config_changed(self):
        src = self._pipe.get_by_name("source")
        if config.proxy_required:
            src.set_property("proxy", config.proxy_uri)
            src.set_property("proxy-id", config.proxy_id)
            src.set_property("proxy-pw", config.proxy_pw)
        else:
            src.set_property("proxy", "")
            src.set_property("proxy-id", "")
            src.set_property("proxy-pw", "")

class SilverRecorder(Player):
    """ GStreamer class for recording network stream
        souphttpsrc -> icydemux -> filesink """

    __name__ = "SilverRecorder"

    def __init__(self, err_func):
        Player.__init__(self, err_func)

        # Create GStream pipeline
        self._pipe = Gst.Pipeline.new(self.__name__)
        if not self._pipe:
            self._error_callback("error", "Couldn't create pipeline")
            sys.exit(-1)
        self._el = dict()
        try:
            self._el["source"] = Gst.ElementFactory.make('souphttpsrc',
                                                            'source')
            self._el["demux"] = Gst.ElementFactory.make('icydemux',
                                                            'demux')
            self._el["filesink"] = Gst.ElementFactory.make('filesink',
                                                            'filesink')
        except Gst.ElementNotFoundError:
            self._error_callback("error", "Couldn't find GStreamer element")
            sys.exit(-1)

        for e in self._el:
            if not self._el[e]:
                self._error_callback("error",
                                     "Couldn't create GStreamer element: " + e)
                sys.exit(-1)
            self._pipe.add(self._el[e])

        self._el["source"].set_property("location", config.stream_url)
        self._el["source"].set_property("is-live", True)
        self._el["source"].set_property("compress", True)
        if config.proxy_required:
            self._el["source"].set_property("proxy", config.proxy_uri)
            self._el["source"].set_property("proxy-id", config.proxy_id)
            self._el["source"].set_property("proxy-pw", config.proxy_pw)
        self._el["filesink"].set_property("location", "file.mp3")

        # Link elements
        def on_pad_added(demux, pad):
            if not pad.is_linked():
                return pad.link(self._el["filesink"].get_static_pad("sink"))
        self._el["demux"].connect('pad-added', on_pad_added)

        if not Gst.Element.link(self._el["source"], self._el["demux"]):
            self._error_callback("error", "Elements could not be linked")
            sys.exit(-1)

        # Create message bus
        self._bus = self._pipe.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message::eos", self._on_eos)
        self._bus.connect("message::error", self._on_error)

    def _play(self, name):
        file = datetime.now(MSK()).strftime(config.recs_prefix) + name
        file = "{0}/{1}.mp3".format(config.recs_dir, file)
        self._pipe.get_by_name("filesink").set_property("location", file)
        ret = self._pipe.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self._error_callback("error", "Couldn't change state on pipeline")
            self.clean()
            sys.exit(-1)

    def _stop(self):
        ret = self._pipe.set_state(Gst.State.READY)
        if ret == Gst.StateChangeReturn.FAILURE:
            self._error_callback("error", "Couldn't change state on pipeline")
            self.clean()
            sys.exit(-1)

    def _on_config_changed(self):
        src = self._pipe.get_by_name("source")
        if config.proxy_required:
            src.set_property("proxy", config.proxy_uri)
            src.set_property("proxy-id", config.proxy_id)
            src.set_property("proxy-pw", config.proxy_pw)
        else:
            src.set_property("proxy", "")
            src.set_property("proxy-id", "")
            src.set_property("proxy-pw", "")
        src.set_property("location", config.stream_url)
