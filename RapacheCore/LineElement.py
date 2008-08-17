#TODO: remove this
import ApacheConf
from lxml import etree

class ListWrapper (object):
    
    def __init__(self):
        pass
        
    def _get_list( self ):    
        raise NotImplementedError
    def _set_list(self, options):
        raise NotImplementedError
    def set(self, options):
        return self._set_list(options)
    
    #def __repr__(self):
    #    return "<ListWrapper %x>" %  id(self)
    ##
    # Returns the number of subelements.
    #
    # @return The number of subelements.

    def __len__(self):
        
        return len( self._get_list() )

    ##
    # Returns the given subelement.
    #
    # @param index What subelement to return.
    # @return The given subelement.
    # @exception IndexError If the given element does not exist.

    def __getitem__(self, index):
        return self._get_list()[index]

    ##
    # Replaces the given subelement.
    #
    # @param index What subelement to replace.
    # @param element The new element value.
    # @exception IndexError If the given element does not exist.
    # @exception AssertionError If element is not a valid object.

    def __setitem__(self, index, element):
        if element is None: element = ''
        options = self._get_list()
        options[index] = element
        self._set_list(options)

    ##
    # Deletes the given subelement.
    #
    # @param index What subelement to delete.
    # @exception IndexError If the given element does not exist.

    def __delitem__(self, index):
        options = self._get_list()
        del options[index]
        self._set_list(options)
        
    def append(self, element):
        options = self._get_list()
        options.append(element)
        self._set_list(options)

    ##
    # Inserts a subelement at the given position in this element.
    #
    # @param index Where to insert the new subelement.
    # @exception AssertionError If the element is not a valid object.

    def insert(self, index, element):
        options = self._get_list()
        options.insert(index, element)
        self._set_list(options)

    ##
    # Removes a matching subelement.  Unlike the <b>find</b> methods,
    # this method compares elements based on identity, not on tag
    # value or contents.
    #
    # @param element What element to remove.
    # @exception ValueError If a matching element could not be found.
    # @exception AssertionError If the element is not a valid object.

    def remove(self, element):
        options = self._get_list()
        options.remove(element)
        self._set_list(options)

class Options (ListWrapper):        
    parser = None
    def __init__(self, parent):
        super (ListWrapper, self).__init__()
        self.parent = parent
        #TODO: remove this
        self.parser = ApacheConf.LineParser()
    def _get_list( self ):    
        options = self.parser.parse_options( self.parent.value )
        if not isinstance( options, list ): return []
        return options
    def _set_list(self, options):
        if options is None: options = []
        self.parent.set_raw_value(" ".join( options ))
class Line (object):
    parser = None
    def __init__(self, element = None):
        self.element = None
        self.__value = None
        self.__key = None
        self.__opts = Options( self )
        if element is not None: self.element = element
        self.element = element
        self.parser = ApacheConf.LineParser()
        self.reset()
    def reset(self):
        """resets the instance to an empty state"""        
        self.element = etree.Element( 'line' )        
    def is_empty (self):    
        """has the instance loaded a line?"""
        return self is not None
    def _get_value(self):
        if self.element == None : return None
        #oh, by the way, should be the only element of the list
        return self.element.get('value')
    def _set_value(self, value):
        return self.set_raw_value(value)
    value = property ( _get_value, _set_value )
    def _get_key(self): 
        if self.element == None : return None
        #oh, by the way, should be the only element of the list
        return self.element.get('directive')
    def _set_key(self, value): 
        pass
    key = property ( _get_key, _set_key )
    def _get_opts(self): 
        return self.__opts
    def _set_opts(self, value): 
        return self.__opts.set( value )
    opts = property ( _get_opts, _set_opts )
    def set_raw_value(self, value):
        self.element.attrib['value'] = value
        if self.element.attrib.get('source'): 
            del self.element.attrib['source']
    def parse(self, line, set_as_source = True):
        """parses a configuration line into a <line> xml element"""
        parser = self.parser
        self.reset()
        c = self.element
        directive = parser.get_directive( line )
        if directive: 
            c.attrib['directive'] = directive
            try:
                value = parser.get_value( line )
                c.attrib[ 'value' ] = value
            except:
                c.attrib['unparsable' ] = 'unparsable'
        else:
            comment = parser.get_comment( line )
            if comment: c.attrib['comment'] = comment
            
        indentation = parser.get_indentation( line )
        if indentation: c.attrib['indentation'] = indentation
        if set_as_source: c.attrib[ 'source' ] = line

class AbstractSelection(ListWrapper):
    def __getattr__(self, name):
        return getattr(self[-1], name)
    def __setattr__(self, name, value):
        return getattr(self[-1], name, value)

class PlainSelection(AbstractSelection):    
    def __init__(self, caller, xpath):
        self._xpath = xpath
        self._caller = xpath
    def _get_list(self): pass
    def _set_list(self): pass
                
class File:
    def load(self): pass
    def set_from_string(self): pass
    def set_from_element(self): pass
    

