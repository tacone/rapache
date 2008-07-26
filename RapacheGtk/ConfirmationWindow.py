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
import re

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
    
try:
    from RapacheCore import Configuration
except:
    if __name__ != "__main__":
        sys.exit(1)

import os

        
class ConfirmationWindow:
    
    def __init__ ( self, parent = None):
           
        self.parent = parent
        self.title = None
        self.question = None
        self.return_value = None
        
        gladefile = os.path.join(Configuration.GLADEPATH, "confirmation.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("confirmation_window")
        self.ok_button = wtree.get_widget("ok_button")
        self.cancel_button = wtree.get_widget("cancel_button")
        self.question_label = wtree.get_widget("question_label")
        signals = {
            "on_ok_button_clicked"       : self.on_ok_button_clicked,
            "on_cancel_button_clicked"     : self.on_cancel_button_clicked
        }
        wtree.signal_autoconnect(signals)
                
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)
                
    def run(self):
        if self.title: self.window.set_title ( self.title )
        if self.question: self.question_label.set_text( self.question )
        
        self.window.show()           
        gtk.main()

    def on_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_ok_button_clicked(self, widget):
        self.return_value = True
        self.window.destroy()
    def on_cancel_button_clicked(self, widget):
        self.return_value = False
        self.window.destroy()

def ask_confirmation ( question = None, title = None):
    win = ConfirmationWindow()
    win.title = title
    win.question = question    
    win.run()
    answer = win.return_value
    print "Question: ", question
    print "Answer: ", answer
    return answer
    
    
if __name__ == "__main__":
    class Configuration:
        GLADEPATH = '../Glade'
    value = ask_confirmation( 'did you solve bug #1 ?', 'bug confirmation')
    print '================='
    print value
    
    