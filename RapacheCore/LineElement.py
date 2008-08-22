#TODO: remove this
import ApacheConf
from lxml import etree
import re

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
        self.__dict__['element'] = None        
        self.__dict__['_opts'] = Options( self )        
        if element is not None: 
            self.element = element
        else:
            self.reset()
        self.__dict__['parser'] = ApacheConf.LineParser()
        
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
        if self.element == None : return False
        if self.element.attrib.get('source'): 
            del self.element.attrib['source']
        self.element.set('directive', value)
    key = property ( _get_key, _set_key )
    def _get_opts(self): 
        return self._opts
    def _set_opts(self, value): 
        return self._opts.set( value )
    opts = property ( _get_opts, _set_opts )
    def set_raw_value(self, value):  
        if value != None:
            self.element.attrib['value'] = value
            if self.element.attrib.get('source'): 
                del self.element.attrib['source']
    def changed(self):
        return not bool( self.element.attrib.get('source' ) )
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
    def dump_xml(self):
        print etree.tostring( self.element, pretty_print = True )

"""
class NotALine(object):
    def _unified_get ( self,  name ):
        raise AttributeError, "'NotALine' Object has no attribute "+name
    def _unified_set(self,  name,  value ):
        raise AttributeError, "'NotALine' Object has no attribute "+name
    def _get_value(self):
       return self._unified_get( 'value' )
    def _set_value(self, value):
        return self._unified_set( 'value',  value )
    value = property ( _get_value, _set_value )
    def _get_key(self): 
        return self._unified_get( 'key' )
    def _set_key(self, value): 
        return self._unified_set( 'key',  value )
    key = property ( _get_key, _set_key )
    def _get_opts(self): 
        return self._unified_get( 'opts' )
    def _set_opts(self, value): 
        return self._unified_set( 'opts',  value )
    opts = property ( _get_opts, _set_opts )
    def changed(self):
        return self._unified_get( 'changed' )
        
class LineGroup( NotALine ):
    def _unified_get(self,  name):
        return getattr(self[-1], name)
    def _unified_set(self,  name,  value):
        return setattr(self[-1], name, value)
"""        
class AbstractSelection( ListWrapper):
    """def _unified_get(self,  name):
        return getattr(self[-1], name)
    def _unified_set(self,  name,  value):
        return setattr(self[-1], name, value)"""
    def __getattr__(self, name):        
        return getattr(self[-1], name)
    def __setattr__(self, name, value):
        return setattr(self[-1], name, value)

class PlainSelection(AbstractSelection):    
    def __init__(self, caller, name ):
        self.__dict__['_name'] = name
        self.__dict__['_caller'] = caller
    def _get_list(self): 
        #print "query for", self._name, "in", self._caller
        name = self._name.lower()
        directive_attr = 'translate(@directive, "ABCDEFGHIJKLMNOPQRSTUVWXYZ",'\
        +'"abcdefghijklmnopqrstuvwxyz")'
        query = '*[%s="%s"]' % (directive_attr, name)    
        return self._caller.xpath( query )        
    def _set_list(self): pass
    
    def __setattr__(self, name, value):
        if len(self) == 0:
            self._create_new()
        return setattr(self[-1], name, value)
    def _create_new(self ):
        line = Line()
        line.key = self._name                
        self._caller.element.append(line.element)                
class TypeSelection(PlainSelection):    
    
    def _get_list(self):
        name = self._name.lower()        
        query = './' + name
        return self._caller.xpath( query )
    def create(self,  key,  value = None):
        if self._name == 'line':
            obj = Line()
        else:
            obj = Section()
        obj.key = key
        if value is not None: obj.value = value
        self._caller.element.append(obj.element)        
        return obj
    
class Parser(Line):
    def __init__(self, element=None):
        super (Parser, self).__init__( element )
        self.__dict__['open_child'] = None
        """
        self.__dict__['parser'] = ApacheConf.LineParser()
        self.__dict__['element'] = None
        if element is not None:
            self.__dict__['element'] = element
        else:
            self.reset()
        """
    def __getattr__(self, name):
        return PlainSelection(self, name)
    def _get_lines(self):
        return TypeSelection(self,  'line')
    """Lines returns all non-section elements"""
    lines= property ( _get_lines )
    def _get_sections(self):
        return TypeSelection(self,  'section')
    """Lines returns all non-section elements"""
    sections= property ( _get_sections )
    """""
    def _get_key(self): 
        if self.element == None : return None
        return self.element.get('directive')
    def _set_key(self, value): 
        if self.element == None : return False
        self.element.set('directive', value)
    key = property ( _get_key, _set_key )
    def _get_value(self):
        if self.element == None : return None
        #oh, by the way, should be the only element of the list
        return self.element.get('value')
    def _set_value(self, value):
        return self.set_raw_value(value)
    value = property ( _get_value, _set_value )
    """
    def load(self, filename ):
        """Loads a configuration file in the parser"""        
        file = open ( filename, 'r' )
        content = file.readlines()
        file.close()
        self.set_from_list(content)
    def reset (self):        
        #tag_name = self.key.lower()
        self.__dict__['element'] = etree.Element( 'root' )
    def _append_string(self, line):
        """Parses a line of code and appends it's xml equivalent to
        self.element"""
        if self.open_child != None:
            if self.open_child.open_child == None \
            and self.is_tag_close(line, self.open_child.key ):
                self.open_child.close( line )
                self.element.append( self.open_child.element )
                self.open_child = None
            else:
                self.open_child._append_string( line )
        else:    
            tag_open = self.is_tag_open(line)
            if tag_open is not False:
                self.open_child = Section()
                self.open_child.key = tag_open[0]
                self.open_child.value = tag_open[1]
            else:
                #unexpected closure ? we will trigger an exception
                self.is_tag_close(line, False )
                
                lineobj = Line()
                lineobj.parse(line)
                self.element.append(lineobj.element)
    def is_tag_open( self, line ):
        basic_regexp = r'^(\s*)<s*([A-Z0-9\-.]+)(\s+[^>]*)*>.*'
        result = re.match( basic_regexp, line, re.IGNORECASE )    
        if ( result == None or result == False ): return False
        result_list = list( result.groups() )
        indentation = result_list[0]
        
        line = line.strip().lstrip( '<' ).rstrip( '>' ).strip()
        key = self.parser.get_directive( line )
        try:
            value = self.parser.get_value( line )
        except AttributeError:
            value = None
            pass#value may not be a string
        #        return indentation, key," ",value
        return key, value
    def is_tag_close (self, line, name):        
        basic_regexp = r'^\s*<s*(/[A-Z0-9\-._]+)\s*>.*'
        result = re.match( basic_regexp, line, re.IGNORECASE )
        if result == None or result == False:
            return False
        if name == False:
            raise VhostNotFound \
                , 'TagEndUnexpected, Unexpected closure found: %s, there\'s no open tag in the current context node.' \
                % line.strip()
        else:
            basic_regexp = r'^\s*<s*(/'+name+r')\s*>.*'
            result = re.match( basic_regexp, line, re.IGNORECASE )
            if ( result != None and result != False ): 
                return True
            else:
                raise VhostNotFound \
                    , 'TagEndUnexpected, Unexpected closure found: %s, expecting %s' \
                    % ( line.strip(), '</%s>' % name )
        return False
    def _raw_xpath(self, query):
        xpath = etree.XPath( query )
        selection = xpath( self.element )
        #oh, by the way, should be the only element of the list
        if not selection : return []
        return selection
    def xpath(self, query):
        selection = []
        for element in self._raw_xpath(query):
            if element.tag == 'line':
                selection.append(Line(element))
            else:
                selection.append( Section(element) )
        return selection    
    def close (self, line):
        """Sets source for closing the tag"""
        self.element.attrib[ 'close_source' ] = line
    def set_from_string(self): pass
    def set_from_list(self, list):
        """uses a (line) list as the configuration file to be parsed"""
        self.reset()
        for line in list:
            #if not line.endswith( "\n" ): line = line.rstrip()+"\n"
            self._append_string(line)
        if self.open_child != None:
            #something wrong, one tag has been left open in the .conf
            raise VhostNotFound, 'TagEndExpected: expected end tag for:'+self.open_child.key
    def set_element (self, element):
        self.element = element        
    def dump_xml (self, include_comments = False):
        """prints out the internal xml structure"""
        if include_comments:
            print etree.tostring( self.element, pretty_print = True )
        else:
            #hackish
            selection = etree.XPath( './line[attribute::directive]' )
            for el in selection(self.element):
                print etree.tostring( el, pretty_print = True )
    #useful for debug
    def create(self,  *args,  **kwargs):
        return self.lines.create( *args,  **kwargs )
class Section(Parser):
    def reset (self):        
        #tag_name = self.key.lower()
        self.__dict__['element'] = etree.Element( 'section' )
