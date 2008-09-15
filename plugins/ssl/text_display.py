#!/usr/bin/env python

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

import sys
try:
     import pygtk
     pygtk.require("2.0")
except:
      pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)

import os
from RapacheCore import Shell

class TextDisplayWindow:
    
    def __init__(self, path):
    
    
        # The path to the plugin
        self.glade_path = path
                  
        gladefile = os.path.join(path,"ssl.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("dialog_text")
        
        self.textview_content = wtree.get_widget("textview_content")
        self.label_help = wtree.get_widget("label_help")
        self.label_path = wtree.get_widget("label_path")
        #self.hbox_table_frame = wtree.get_widget("hbox_table_frame")
        self.treeview_details = wtree.get_widget("treeview_details")
        self.button_save = wtree.get_widget("button_save")
        self.button_close = wtree.get_widget("button_closel")
        self.button_apply = wtree.get_widget("button_apply")

        signals = {
           "on_button_apply_clicked"        : self.on_button_apply_clicked,
           "on_button_save_clicked"         : self.on_button_save_clicked,
           "on_button_close_clicked"        : self.on_button_close_clicked
        }
        wtree.signal_autoconnect(signals)            
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)

        self.return_value = None
        
        column = gtk.TreeViewColumn((''))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=0)
        self.treeview_details.append_column(column)
        
        column = gtk.TreeViewColumn((''))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=1)
        self.treeview_details.append_column(column)
        
    def on_button_apply_clicked(self, widget):
        self.return_value = gtk.RESPONSE_OK
        self.window.destroy()
        return
        
    def on_button_close_clicked(self, widget):
        self.window.destroy()
        return

    def on_button_save_clicked(self, widget):
        chooser = gtk.FileChooserDialog(
            title=None,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
                        buttons=(gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL,
                        gtk.STOCK_SAVE,
                        gtk.RESPONSE_OK))
        chooser.set_current_name( os.path.basename( self.path) )                
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            f = open( chooser.get_filename(), "w" )
            
            buf = self.textview_content.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter() )
            f.write( text )
            f.close()
            
            self.window.destroy()
        chooser.destroy()
        return

    def run(self):
        self.window.show()   
        
        gtk.main()
        return self.return_value
   
    def load (self, title, help_text, help_array, path, save_as_button=True, apply_button=False):
        self.window.set_title(title)
        self.path = path
        self.label_help.set_markup(help_text)
        self.label_path.set_text("File : " + path )
        
        content = Shell.command.read_file( path)
        self.textview_content.get_buffer().set_text( content )
        
        if apply_button:
            self.button_apply.show()
        else:
            self.button_apply.hide()
        
        
        
        store = gtk.ListStore(str, str, str)
        self.treeview_details.set_model(store)
        
        if help_array:
            table = gtk.Table(len(help_text), 2, False)
            row_count = 0
            for help_text_line in help_array:
                store.append(("<b>" +help_text_line[0] + "</b>", help_text_line[1], None))

        return
				
    def on_destroy(self, widget, data=None):
        gtk.main_quit()

