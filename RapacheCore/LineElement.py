#TODO: remove this
import ApacheConf


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
        
    """
    ##
    # Returns a list containing subelements in the given range.
    #
    # @param start The first subelement to return.
    # @param stop The first subelement that shouldn't be returned.
    # @return A sequence object containing subelements.

    def __getslice__(self, start, stop):
        return self._get_list()[start:stop]

    ##
    # Replaces a number of subelements with elements from a sequence.
    #
    # @param start The first subelement to replace.
    # @param stop The first subelement that shouldn't be replaced.
    # @param elements A sequence object with zero or more elements.
    # @exception AssertionError If a sequence member is not a valid object.

    def __setslice__(self, start, stop, elements):
        for element in elements:
            assert iselement(element)
        self._get_list()[start:stop] = list(elements)

    ##
    # Deletes a number of subelements.
    #
    # @param start The first subelement to delete.
    # @param stop The first subelement to leave in there.

    def __delslice__(self, start, stop):
        del self._get_list()[start:stop]

    ##
    # Adds a subelement to the end of this element.
    #
    # @param element The element to add.
    # @exception AssertionError If a sequence member is not a valid object.
    """
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
        self.parent.value = " ".join( options )    
class Line (object):
    def __init__(self, element = None):
        self.element = None
        self.__value = None
        self.__key = None
        self.opts = Options( self )
        if element is not None: self.element = element
        self.element = element
        self.parser = ApacheConf.LineParser()
    def reset(self):
        """resets the instance to an empty state"""        
        self.element = etree.Element( tag_name )        
    def is_empty (self):    
        """has the instance loaded a line?"""
        return self is not None
    def _get_value(self):
        return self.__value
    def _set_value(self, new_value): 
        pass
    value = property ( _get_value, _set_value )
    def _get_key(self): 
        pass
    def _set_key(self, new_value): 
        pass
    key = property ( _get_key, _set_key )