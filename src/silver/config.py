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

from gi.repository import Gtk
import configparser
import os
import re

from silver.globals import CONFIG_FILE
from silver.globals import STREAM_URL_LIST

def font_probe():
    """ Get system default font family """
    t = Gtk.Label("")
    s = t.get_style()
    font = s.font_desc.get_family()
    return font

class Default():
    """ Default configuration """
    autoplay            = False
    start_hidden        = False
    recs_dir            = os.getenv("HOME") + "/Recordings"
    recs_prefix         = "%m-%d-%y-%H:%M-"
    use_css             = True
    css_path            = ""
    stream_url          = STREAM_URL_LIST[0]
    bg_colors           = ["#FFFFFF", "#F2F2F2"]
    bg_alpha            = [0.87, 0.87]
    font_color          = "black"
    selected_bg_color   = "#FF4545"
    selected_alpha      = 0.95
    selected_font_color = "white"
    font_family         = font_probe()
    font_size           = "11"
    font                = "{0} {1}".format(font_family, font_size)
    selected_font       = "{0} Bold {1}".format(font_family, font_size)
    language            = 0
    message_sender      = ""
    proxy_required      = False
    proxy_uri           = ""
    proxy_id            = ""
    proxy_pw            = ""

def _init():
    """ Declare set of globals
        initialized with default configuration """
    global autoplay
    autoplay = Default.autoplay
    global start_hidden
    start_hidden = Default.start_hidden
    global recs_dir
    recs_dir = Default.recs_dir
    global recs_prefix
    recs_prefix = Default.recs_prefix
    global use_css
    use_css = Default.use_css
    global css_path
    css_path = Default.css_path
    global stream_url
    stream_url = Default.stream_url
    global bg_colors
    bg_colors = Default.bg_colors
    global bg_alpha
    bg_alpha = Default.bg_alpha
    global font_color
    font_color = Default.font_color
    global selected_bg_color
    selected_bg_color = Default.selected_bg_color
    global selected_alpha
    selected_alpha = Default.selected_alpha
    global selected_font_color
    selected_font_color = Default.selected_font_color
    global font
    font = Default.font
    global selected_font
    selected_font = Default.selected_font
    global language
    language = Default.language
    global message_sender
    message_sender = Default.message_sender
    global proxy_required
    proxy_required = Default.proxy_required
    global proxy_uri
    proxy_uri = Default.proxy_uri
    global proxy_id
    proxy_id = Default.proxy_id
    global proxy_pw
    proxy_pw = Default.proxy_pw

def _load():
    """ Read configuration file """
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    # General
    global autoplay
    autoplay = cfg.getboolean("GENERAL", "autoplay",
                    fallback=Default.autoplay)
    global start_hidden
    start_hidden = cfg.getboolean("GENERAL", "starthidden",
                    fallback=Default.start_hidden)
    global recs_dir
    recs_dir = cfg.get("GENERAL", "recordsdirectory",
                    fallback=Default.recs_dir)
    global recs_prefix
    recs_prefix = cfg.get("GENERAL", "recordsprefix",
                    fallback=Default.recs_prefix)
    global language
    language = int(cfg.get("GENERAL", "language",
                    fallback=Default.language))
    global message_sender
    message_sender = cfg.get("GENERAL", "messagesender",
                    fallback=Default.message_sender)
    # Appearance
    global use_css
    use_css = cfg.getboolean("APPEARANCE", "usecss",
                    fallback=Default.use_css)
    global css_path
    css_path = cfg.get("APPEARANCE", "csspath",
                    fallback=Default.css_path)
    global bg_colors
    bg_colors = cfg.get("APPEARANCE", "bgcolors",
                    fallback=":".join(Default.bg_colors)).split(":")
    global bg_alpha
    fallback = ":".join("%.2f" % x for x in Default.bg_alpha)
    bg_alpha = [float(x) for x in (cfg.get("APPEARANCE", "bgalpha",
                    fallback=fallback).split(":"))]
    global font_color
    font_color = cfg.get("APPEARANCE", "fontcolor",
                    fallback=Default.font_color)
    global selected_bg_color
    selected_bg_color = cfg.get("APPEARANCE", "selectedbgcolor",
                    fallback=Default.selected_bg_color)
    global selected_alpha
    selected_alpha = float(cfg.get("APPEARANCE", "selectedalpha",
                    fallback=Default.selected_alpha))
    global selected_font_color
    selected_font_color = cfg.get("APPEARANCE", "selectedfontcolor",
                    fallback=Default.selected_font_color)
    global font
    font = cfg.get("APPEARANCE", "Font",
                    fallback=Default.font)
    global selected_font
    selected_font = cfg.get("APPEARANCE", "selectedfont",
                    fallback=Default.selected_font)
    # Network
    global stream_url
    stream_url = cfg.get("NETWORK", "streamurl",
                    fallback=Default.stream_url)
    global proxy_required
    proxy_required = cfg.getboolean("NETWORK", "proxyrequired",
                    fallback=Default.proxy_required)
    global proxy_uri
    proxy_uri = cfg.get("NETWORK", "proxyuri",
                    fallback=Default.proxy_uri)
    global proxy_id
    proxy_id = cfg.get("NETWORK", "proxyid",
                    fallback=Default.proxy_id)
    global proxy_pw
    proxy_pw = cfg.get("NETWORK", "proxypw",
                    fallback=Default.proxy_pw)

def save():
    """ Save configuration file """
    cfg = configparser.ConfigParser()
    cfg["GENERAL"] = {
            "autoplay"          : autoplay,
            "language"          : language,
            "messagesender"     : message_sender,
            "recordsdirectory"  : recs_dir,
            "recordsprefix"     : re.sub("%", "%%", recs_prefix),
            "starthidden"       : start_hidden,
            }
    cfg["APPEARANCE"] = {
            "bgcolors"          : ":".join(bg_colors),
            "bgalpha"           : ":".join("%.2f" % x for x in bg_alpha),
            "csspath"           : css_path,
            "font"              : font,
            "fontcolor"         : font_color,
            "selectedbgcolor"   : selected_bg_color,
            "selectedalpha"     : selected_alpha,
            "selectedfont"      : selected_font,
            "selectedfontcolor" : selected_font_color,
            "usecss"            : use_css,
            }
    cfg["NETWORK"] = {
            "proxyid"           : proxy_id,
            "proxypw"           : proxy_pw,
            "proxyrequired"     : proxy_required,
            "proxyuri"          : proxy_uri,
            "streamurl"         : stream_url,
            }
    with open(CONFIG_FILE, "w") as configfile:
        cfg.write(configfile)

def setup():
    """ Setup configuration.
        Create config file if does not exist """
    if not os.path.exists(CONFIG_FILE):
        _init()
        save()
    else:
        _load()
