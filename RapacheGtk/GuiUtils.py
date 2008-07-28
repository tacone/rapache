# Rapache - Apache Configuration Tool
# Copyright (C) 2008 Stefano Forenza,  Jason Taylor, Emanuele Gentili
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import gtksourceview2
import pango
from RapacheCore import Configuration

def style_as_tooltip( obj ):
    pw = gtk.Window(gtk.WINDOW_POPUP)
    pw.set_name('gtk-tooltip')
    pw.ensure_style()
    obj.set_style(pw.get_style())
    obj.connect('expose-event', paint)
    
def paint(box, event):
        box.style.paint_flat_box(box.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT, None, box, "tooltip", box.allocation.x+1, box.allocation.y+1, box.allocation.width-2, box.allocation.height-2)

def change_button_label ( button, new_label ):
        """Changes the label of a button"""
        button.show()
        alignment = button.get_children()[0]
        hbox = alignment.get_children()[0]
        image, label = hbox.get_children()
        label.set_text( new_label )

def new_apache_sourceview():
    bufferS = gtksourceview2.Buffer()
    manager = gtksourceview2.LanguageManager()
    
    #language = manager.get_language_from_mime_type("text/xml")
    manager.set_search_path( [ Configuration.GLADEPATH ] + manager.get_search_path() )
    language = manager.get_language('apache')
    bufferS.set_language(language)
    bufferS.set_highlight_syntax(True)
    sourceview = gtksourceview2.View(bufferS)
    sourceview.set_show_line_numbers(True)
    #TODO sniff gnome default monospace font
    sourceview.modify_font(pango.FontDescription("monospace 10"))
    return sourceview