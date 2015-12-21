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

from gi.repository import Gdk, Gtk

import silver.config as config
from silver.gui.common import rgba_to_hex

__all__ = ["css_load"]

_silver_style = b"""
@define-color silver_rain_red #FF4545;
/*************************
 *      Scale color  *
 *************************/
GtkScale.slider:hover {
    background-image: -gtk-gradient(linear, left top, left bottom,
    from (shade(mix(@theme_bg_color, shade(@silver_rain_red, 0.9), 0.4), 1.2)),
    to (shade(mix(@theme_bg_color, shade(@silver_rain_red, 0.9), 0.4),0.97)));
}

GtkTreeView {
    background-color: transparent;
}

.menubar .menuitem .scale.highlight.left,
.scale.highlight.left {
    background-image: -gtk-gradient(linear, left top, left bottom,
    from (shade(shade(@silver_rain_red, 0.9), 1.1)),
    to (shade(shade(@silver_rain_red, 0.9), 0.9)));
    border-color: transparent;
}

.scale.highlight.bottom {
    background-image: -gtk-gradient(linear, left top, right top,
    from (shade(shade(@silver_rain_red, 0.9), 1.1)),
    to (shade(shade(@silver_rain_red, 0.9), 0.9)));
    border-color: transparent;
}
/**************************
 * Selected button color  *
 **************************/
.button:focus,
.button:hover:focus,
.button:active:focus,
.button:active:hover:focus,
.button:checked:focus,
.button:checked:hover:focus {
    border-color: shade(@silver_rain_red, 0.8);
}
"""

_treeview_selected = """
GtkTreeView:selected {{
    background-color: {0};
}}
"""

def color_probe():
    """ Get system default selection color """
    s = Gtk.TreeView().get_style_context()
    return rgba_to_hex(s.lookup_color('selected_bg_color')[1])

def css_load():
    """ Load style """
    if not config.use_css:
        return

    if config.css_path:
        with open(config.css_path, 'rb') as css:
            css_data = css.read()
    else:
        css_data = _silver_style
        css_data += bytes(_treeview_selected.format(color_probe()), 'utf-8')

    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(css_data)
    Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
