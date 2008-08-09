import ApacheConf
from lxml.builder import E
from lxml import etree

import copy
import re #temporary ?

lineparser = ApacheConf.LineParser()

class TagEndExpected( Exception ):
    pass

class TagEndUnexpected( Exception ):    
    pass

class ApacheParser( object ):
    def __init__(self, line = None):
        self.parser = ApacheConf.LineParser()
        self.element = None
        if line == None:
            self.key = 'root'
            self.value = None
        else:
            self._update_from_line(line)
        #print "======> init: ", self.key
        self._reset_document()
        #temporary reference for the currently opened subtag
        self.open_child = None
    
    def _update_from_line(self, line ):
            self.key, self.value = self.is_tag_open(line)            
    def _reset_document (self):        
        tag_name = self.key.lower()
        self.element = etree.Element( tag_name )
    def linescount(self):
        """returns line count, subtags lines excluded"""
        
        query = './line'
        xpath = etree.XPath( query )
        selection = xpath( self.element )
        #oh, by the way, should be the only element of the list
        if not selection : return 0
        return len( selection )
        #return len( self.element )
    def load(self, filename ):
        """Loads a configuration file in the parser"""
        self.filename = filename
        file = open ( filename, 'r' )
        content = file.readlines()
        file.close()
        self.set_content(content)
    def set_content_from_string(self, string_content):
        """uses a string as the configuration file to be parsed"""
        return self.set_content( string_content.split( "\n" ) )
    def set_content(self, content):
        """uses a (line) list as the configuration file to be parsed"""
        self._reset_document()
        for line in content:
            self.append(line)
        if self.open_child != None:
            #something wrong, one tag has been left open in the .conf
            raise TagEndExpected, 'expected end tag for:'+self.open_child.key
        #print '..... ends with:', line
    def append(self, line):
        """Parses a line of code and appends it's xml equivalent to
        self.element"""
        #print self.key, '==>', [line]
        
        #children_key = False
        #if self.open_child != None:
        #    children_key = self.open_child.key            
        
        if self.open_child != None:
            if self.open_child.open_child == None \
            and self.is_tag_close(line, self.open_child.key ):
                self.element.append( self.open_child.element )
                self.open_child = None
            else:
                self.open_child.append( line )
        else:    
            tag_open = self.is_tag_open(line)
            if tag_open is not False:
                #print self.key,'--> opening', tag_open[0], tag_open[1]
                #self.open_child = SubTag( tag_open[0], tag_open[1] )
                self.open_child = SubTag( line )
            else:
                #unexpected closure ? we will trigger an exception
                self.is_tag_close(line, False )
                
                c = self._parse_line(line, True)
                self.element.append( c )
        
    def get_content (self):
        """returns the content as a string (i.e. for saving)"""
        content = []
        for line in self.element:
            content.append( self.compile_line(line) )        
        return content
    def _parse_line(self, line, with_source = False):
        """parses a configuration line into a <line> xml element"""
        parser = self.parser
        c = etree.Element("line")
        directive = parser.get_directive( line )
        #print line
        #print 'directive', directive
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
        if with_source: c.attrib[ 'source' ] = line
        return c
    def is_tag_open( self, line ):
        basic_regexp = r'^(\s*)<s*([A-Z0-9\-.]+)(\s+[^>]*)*>.*'
        result = re.match( basic_regexp, line, re.IGNORECASE )    
        if ( result == None or result == False ): return False
        
        result_list = list( result.groups() )
        indentation = result_list[0]
        
        line = line.strip().lstrip( '<' ).rstrip( '>' ).strip()
        #print "========> CHECKING :",line
        key = self.parser.get_directive( line )
        try:
            value = self.parser.get_value( line )
        except AttributeError:
            value = None
            pass#value may not be a string
        #        return indentation, key," ",value
        return key, value
    def is_tag_close (self, line, name):
        #print '..............',self.key
        basic_regexp = r'^\s*<s*(/[A-Z0-9\-._]+)\s*>.*'
        result = re.match( basic_regexp, line, re.IGNORECASE )
        if result == None or result == False:
            return False
        if name == False:
            raise TagEndUnexpected \
                , 'Unexpected closure found: %s, there\'s no open tag in the current context node.' \
                % line.strip()
        else:
            basic_regexp = r'^\s*<s*(/'+name+r')\s*>.*'
            result = re.match( basic_regexp, line, re.IGNORECASE )
            if ( result != None and result != False ): 
                return True
            else:
                raise TagEndUnexpected \
                    , 'Unexpected closure found: %s, expecting %s' \
                    % ( line.strip(), '</%s>' % name )
                
        
        
        
        
        
        return False
        
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
    def dump_values(self):
        """dumps all the key/values. key are unique, later keys override 
        previous ones """
        dict = {}
        for line in self.element:
            name = line.get('directive')
            if name:
                if line.get('unparsable' ) == 'unparsable':
                    dict[ name ] = "#ERROR"
                else:
                    dict[ name ] = line.get('value')
        #print dict
        return dict
    def make_line (self, properties = {}): 
        """returns a <line> xml element starting from a dictionary"""
        c = etree.Element("line")
        directive = properties.get( 'directive' )
        if directive: 
            c.attrib['directive'] = directive
            value = properties.get( 'value' )
            if value:
                c.attrib[ 'value' ] = value            
        else:
            comment = properties.get( 'comment' )
            if comment: c.attrib['comment'] = comment
            
        indentation = properties.get( 'indentation' )
        if indentation: c.attrib['indentation'] = indentation
        return c
    def insert_line(self, properties = {}):
        line = self.make_line(properties)
        if line == None:
            return False
        self.element.append( line )
        return True
    def compile_line(self, obj_line):
        source = obj_line.attrib.get('source')
        if source: return source
        line = ''
        
        indentation = obj_line.attrib.get('indentation')
        if indentation: line += indentation
        
        directive = obj_line.attrib.get('directive')
        if directive: 
            if line != '': line += ' '
            line += directive
            
        value = obj_line.attrib.get('value')
        if value: 
            if line != '': line += ' '
            line += value
            
        comment = obj_line.attrib.get('comment')
        if comment: 
            if line != '': line += ' '
            line += "#" + comment
        return line
    def _get_last_line (self, key ):
        """ returns the last <line> found with the directive "key" """
        escaped_key = key.replace( '"', '\\"' )
        query = './line[attribute::directive="%s"][position()=last()]' % escaped_key
        xpath = etree.XPath( query )
        selection = xpath( self.element )
        #oh, by the way, should be the only element of the list
        if not selection : return None
        return selection[-1]
    def get_directive (self, key):
        line = self._get_last_line(key)
        if line == None: return None
        source = line.attrib.get('source')
        if source: return source
        return self.compile_line(line)
    def set_directive(self, key, string_line):
        line = self._parse_line(string_line)
        existing_line = self._get_last_line(key)
        if existing_line != None:            
            idx = self.element.index( existing_line )
            self.element[ idx ] = line
        else:
            self.element.append( line )
    def remove_option (self, name, option ): 
        #we need idx later if we decide to remove the whole line
        existing_line = self._get_last_line(name)
        if ( existing_line == False or existing_line == None ): return False
        line = self.compile_line( existing_line )
        line = self.parser.remove_option(line, option)
        new_value = self.parser.get_value( line )
        if ( new_value.strip() == "" ):
            idx = self.element.index( existing_line )
            del( self.element[idx] )
        else:
            self.set_directive(name, line)
    def get_raw_value(self, key):
        #print "---->", key
        line = self._get_last_line(key)
        #print etree.tostring( line )
        
        if line == None : return None
        #oh, by the way, should be the only element of the list
        return line.get('value')
    def set_raw_value (self, name, value):
        line = self._get_last_line( name )
        #value = self.parser.value_escape( value )
        if line == None:            
            self.insert_line( {"directive": name, "value":value} )
        else:            
            line.attrib['value'] = value
            if line.attrib.get('source'): del line.attrib['source'] 
    def get_value(self, key):
        value = self.get_raw_value( key )
        if not value: return value
        return self.parser.value_unescape( value )
    def set_value(self, name, value):
        if value:
            value = self.parser.value_escape( value )
        return self.set_raw_value(name, value)
    def has_option (self, name, option ):
        line = self._get_last_line(name)
        if ( line == False or line == None ): return False
        return self.parser.has_option(self.compile_line( line ), option)  
    def get_options (self, name):
        value = self.get_value(name)
        #self.dump_xml()
        if value == None: return []
        options = self.parser.parse_options( value )
        return options
    def add_option (self, name, option ):    
        line = self._get_last_line(name)
        if ( line == False or line == None ):             
            self.set_value(name, option)
            return True
        compiled_line = self.compile_line( line )        
        if compiled_line == True or compiled_line == False: exit()
        string_line = self.parser.add_option(compiled_line, option)
        self.set_directive(name, string_line)
    def is_modified (self, key):
        line = self._get_last_line(key)
        if line == None or line == False : return False
        #print key, '==>', bool( line.attrib.get('source' ) ), line.attrib.get('source')
        return not bool( line.attrib.get('source' ) )
    def get_virtualhost(self):
        tag =  SubTag ( )
        tag.set_element( self.element )
        return tag
    
class SubTag ( ApacheParser ):
    
    def set_element (self, element):
        self.element = element
        self._update_from_line(line)

    """def __init__(self, key, value):
        super (SubTag, self).__init__()
        self.key = key
        self.value = value
    def _reset_document (self):        
        tag_name = self.key.lower()
        self.element = etree.Element( tag_name )
    """    
        
class Line():
    def __init__(self, line = None):
        self.element = etree.Element("line")
        if line != None: self.load( line )
        pass
    def load(self, line):
        self._source = line
    def _get_directive(self):
        return 'DocumentRoot'
    def _set_directive (self, value):
        pass
    directive = property( _get_directive, _set_directive )
    
    
    
"""
Draft (not implemented)

p = ApacheParser( "myconf.conf" )
line = p.get('DocumentRoot')
line.comment = 'this is the root of your site'
line.value = '/var/www/webmix'

lines = p.get_all( 'ErrorDocument' ) # ???
l = lines[0]








"""    