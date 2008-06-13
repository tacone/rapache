#!/usr/bin/env python
#
# Copyright (C) Stefano Forenza 2008 <tacone@gmail.com>
# 
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# main.py is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

class Observable:   
    """Any instance to be observed with PollyObserver should extend
    this class. Note this differs from the classical Observable
    implementation because it only allows the object to be observed
    from a single Observer"""
    __observer = None
    def register (self, observer):
        self.__observer = observer
    def unregister (self):    
        self.__observer = None
    def handle_event(self, event):
        """Override this function in subclasses to implement your 
        own event handling logic"""
        print self, "- now handling:", event.name, event.args, event
    def raise_event (self, name, args = {} ):
        event = Event( self, name, args )
        if self.__observer != None: self.__observer.notify( event )
class PollyObserver:
    """Simple observer derivation. Observes and dispatches events
    from/to a poll of objects
    """
    __observed = []
    def register(self, obj):
        """adds an Observable instance to the poll of observed objects
        and register itself to it."""
        
        for registered_obj in self.__observed:
            if obj == registered_obj: return False
        self.__observed.append( obj )
        obj.register( self )
        return True
    def unregister(self, obj):
        """remove an Observable instance to the poll of observed objects
        and removes itself from it."""
        for idx, registered_obj in enumerate( self.__observed ):
            if obj == registered_obj: 
                del self.__observed[ idx]
                obj.unregister( self )
                return True
        return False
    def get_observed(self):
        """returns observed object list, mainly for debug purpouses"""
        return self.__observed
    def notify (self, event ):
        """dispatches an event all around"""
        for registered_obj in self.__observed:
            registered_obj.handle_event( event )
            
class Event:
    caller = None
    name = None
    args = {}
    def __init__(self, caller, name, args ):
        self.caller = caller
        self.name = name
        self.args = args