#!/usr/bin/env python

class Observable (object) :   
    """Any instance to be observed with PollyObserver should extend
    this class. Note this differs from the classical Observable
    implementation because it only allows the object to be observed
    from a single Observer"""
    def __init__(self):
        self.__observer = None
    def register (self, observer):
        self.__observer = observer
    def unregister (self):
        if ( self.__observer != None):
            self.__observer.unregister( self )
            self.__observer = None
    def handle_event(self, event):
        """Override this function in subclasses to implement your 
        own event handling logic"""
        print self, "- now handling:", event.name, event.args, event
    def raise_event (self, name, args = {}, no_caller = False ):
        if no_caller:
            event = Event( None, name, args )
        else:
            event = Event( self, name, args )
        print '---------------->',event.name , 'raised by' , self
        if self.__observer != None: self.__observer.notify( event )
class PollyObserver:
    """Simple observer derivation. Observes and dispatches events
    from/to a poll of objects
    """
    def __init__(self):
        self.__observed = []
    def register(self, obj):
        """adds an Observable instance to the poll of observed objects
        and register itself to it."""
        #print "checking for same obj"
        for registered_obj in self.__observed:
            #print obj, ' == ', registered_obj, '??'
            if obj == registered_obj: return False
        self.__observed.append( obj )
        #print "-->",self.__observed
        obj.register( self )
        return True
    def unregister(self, obj):
        """remove an Observable instance to the poll of observed objects
        and removes itself from it."""
        for idx, registered_obj in enumerate( self.__observed ):
            if obj == registered_obj: 
                del self.__observed[ idx]
                obj.unregister()
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
