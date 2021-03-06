#!/usr/bin/env python

#    This file is copyrighted by Stefano Forenza <stefano@stefanoforenza.com>
#
#    The code below is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License or (if you prefer) the 
#    GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    The code below is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    To read the actual licenses see <http://www.gnu.org/licenses/>.

"""
ASSUMPTIONS
    - when multiple directive with the same name are encountered
      the last one wins.
    - directives without options could be ok.
        - ServerAlias without any option works
        
GOALS:
    - change as little as possible when updating to reduce the risk 
      of breaking something
      
TODO:
    - search for subsections and limit editing to a certain subsection
    - insert directive where it doesn't exist
    - remove a directive when it becomes empty (without options)
    - verify apache handling of case for directives
"""

import re
from Observer import PollyObserver
from Observer import Observable

class Parser (Observable):
    filename = None
    content = None
    parser = None
    
    def __init__ (self, *args, **kwargs):
        super (Parser, self).__init__ (*args, **kwargs)
        self.parser = LineParser()
        self.apply_observing_policy()
    
    def apply_observing_policy(self):
        """register the object with the observer"""
        self.observer = PollyObserver()
        self.observer.register(self)
        
    def load(self, filename ):
        """Loads a configuration file in the parser"""
        self.filename = filename
        file = open ( filename, 'r' )
        self.content = file.readlines()
        file.close()
        return self.content
    
    def dump_values (self ):
        """Dumps every directive/value into a key/value dictionary. Newer 
        keys override older ones"""
        dict = {}
        for line in self.content:            
            key = self.parser.get_directive( line )
            if key:                
                try:
                    value = self.parser.get_value(line)
                    dict[ key ] = value
                except :                    
                    dict[ key ] = "#ERROR"
        return dict
    
    def get_value(self, name):
        line = self.get_directive(name)    
        if line == None: return None
        return self.parser.get_value(line)
    def set_value (self, name, value):
        idx = self._get_last_directive_idx(name)
        if idx == None:
            idx = self._last_line_idx()
            line = name+"\t"+self.parser.value_escape( value )+"\n"
            self.insert_line( self._last_line_idx(), line )
        else:
            line = self.get_line( idx )
            line = self.parser.change_value(line, value)
            self.set_line( idx, line )
    def remove_value(self, name):
        idx = self._get_last_directive_idx(name)
        if idx: 
            self.remove_line(idx)
            return True
        return False
    def get_directive(self, name):
        idx = self._get_last_directive_idx(name)
        if ( idx == None ): return None
        line = self.get_line( idx )
        return line
    """
    def set_directive (self, name, line):
        idx = self._get_last_directive_idx(name)
        self.set_line( idx, line )
    """
    # idx starts from 0 !! it's not a line number    
    def _get_last_directive_idx (self, name ):
        last_found = None
        for key, line in enumerate(self.get_content() ):   
            if ( self.parser.get_directive(line) == name ): last_found = key            
        return last_found
    #TODO create if doesn't exist.
    def set_directive (self, name, line):
        idx = self._get_last_directive_idx(name)
        if ( idx == None ):
             return self.insert_line( self._last_line_idx() , line.rstrip()+"\n")
        self.set_line( idx, line.rstrip()+"\n" )
    
    def _last_line_idx (self):
        return 999999
    
    def has_option (self, name, option ):
        line = self.get_directive(name)
        if ( line == False or line == None ): return False
        return self.parser.has_option(line, option)  
    def get_options (self, name):
        value = self.get_value(name)
        if value == None: return []
        options = self.parser.parse_options( value )
        return options
    def add_option (self, name, option ):    
        line = self.get_directive(name)
        if ( line == False or line == None ): 
            line = name
            line = name+"\t"+self.parser.value_escape( option )+"\n"    
            self.insert_line( self._last_line_idx(), line )
            return
        line = self.parser.add_option(line, option)
        self.set_directive(name, line)
    def remove_option (self, name, option ): 
        #we need idx later if we decide to remove the whole line
        idx = self._get_last_directive_idx(name)   
        line = self.get_directive(name)
        if ( line == False or line == None ): return False
        line = self.parser.remove_option(line, option)
        new_value = self.parser.get_value( line )
        if ( new_value.strip() == "" ):
            self.remove_line( idx )
        else:
            self.set_directive(name, line)
    def get_source (self):
        return "".join( self.get_content() )
    def get_content(self):
        return self.content
    def set_content_from_string(self, string):
        self.content = string.split( "\n" )
    def get_line(self, idx):
        return self.get_content()[idx]
    def set_line(self, idx, line):
        self.content[ idx ] = line    
    def insert_line (self, idx, line):
        """Inserts a line at the given idx"""
        if idx >= len( self.content ): #out of range
            idx = self._last_line_idx()        
        self.content.insert( idx, line )
        self.raise_event( 'row_inserted', {'idx':idx, 'line':line } )
    def remove_line(self, idx ):
        del self.content[ idx ]
        self.raise_event( 'row_removed', {'idx':idx } )
class PieceParser ( Parser ):
    """Manipulates isolated parts of configuration files. Should be extended"""
    
    min = None
    max = None
    father = None
    def apply_observing_policy(self):
        """register the object with the observer"""
        self.father.observer.register(self)
    def load (self, args = {}):
        print "Please override this method !"
        exit()
    def __init__(self, father, args = {} ):
        self.father = father
        Parser.__init__( self )
        self.load( args )
    def load (self, args = {} ):
        pass
    def get_content (self):
        return self.father.get_content()[ self.min : self.max ]

class VhostParser( PieceParser ):
    """Searches for the first vhost inside the conf and allows isolated 
    manipulation  of it"""    
    
    def load(self, args = {}): 
        content = self.father.get_content()
        self.min = self._find_min(content)
        if self.min == None:  raise "VhostNotFound", "Beginning not found"
        self.max = self._find_max(content, self.min) +1
        if ( self.max == None ): raise "VhostNotFound", "End not found"

    def _last_line_idx (self):
        return -1
    def _find_min( self, content ):
        for idx, line in enumerate( content ):
            basic_regexp = r'^\s*<s*(VirtualHost)(\s+[^>]*)*>.*'
            result = re.match( basic_regexp, line, re.IGNORECASE )
            if ( result != None and result != False ): return idx
        return None
    def _find_max( self, content, min ):
        for idx, line in enumerate( content ):
            if ( idx > min ):
                basic_regexp = r'^\s*<s*(/VirtualHost)\s*>.*'
                result = re.match( basic_regexp, line, re.IGNORECASE )
                if ( result != None and result != False ): return idx
        return None
    def set_line (self, idx, line ):
        if idx >= 0: idx = idx + self.min
        return self.father.set_line( idx, line )
    def insert_line (self, idx, line ):
        if idx >= 0: idx = idx + self.min
        line = "\t"+line.lstrip() #ident
        return self.father.insert_line( idx, line )
    def remove_line(self, idx ):
        if idx >= 0: idx = idx + self.min
        return self.father.remove_line( idx )
    def handle_event(self, event):
        print self, "handling:", event.name, "raised by", event.caller
        if ( event.name == 'row_inserted' ):
            self.max = self.max + 1
        if ( event.name == 'row_removed' ):
            self.max = self.max -1
       
class LineParser:
    """Utility class. Contains methods to parse and manipulate apache conf
    directives"""
    def tokenize (self, line ):
        basic_regexp = '^(\s*)([A-Z0-9]+)((\s+)(.*))?'  
        result = re.match( basic_regexp, line, re.IGNORECASE )        
        if ( result == None ): return False
        result_list = list( result.groups() )
        #we need to strip the outer parentesys around (\s+)(.*)
        del( result_list[2] )        
        return result_list
    def value_unescape(self, value):
        #value should have no precedig or trailing spaces
        if value == None: return None
        if value == "" : return value
        char = value[0]
        if char == '"' or char == "'":
            if char != value[-1]:
                raise( 'BadQuoting', 'Bad quoting' )
                return value;
            value = value[1:-1]
            value = value.replace( '\\'+char, char )
            
        #we don't need to unescape spaces as apparently
        #apache parser doesn't handle escaped spaces
        #inside non-quote-enclosed strings
        return value

    #parse a value into a list of multiple options
    # - handles double quote-enclosed strings "example"
    #TODO: doesn't hanlde single quotes at all :(
    def parse_options ( self, s ):
        """parse a value into a list of multiple options"""
        if s == None or s == False: return []
        s = s.rstrip()
        s = s.replace ( '\\"', '&quot;' )
        result = '';    
        tokens = s.split( '"' )        
        for k, v in enumerate( tokens ):
            # replace spaces in every odd token
            if ( k & 1 ) == 1 : tokens[k] = v.replace( ' ', '&nbsp;' )

        s = '"'.join( tokens )
        s = s.replace( '"', '' )
        tokens = s.split( ' ' )
        for k, v in enumerate( tokens ):
            tokens[ k ] = v.replace( '&nbsp;', ' ' )
            tokens[ k ] = tokens[ k ].replace( '&quot;', '"' )
        tokens = [x for x in tokens if x.strip() != '' ]
        return tokens;

    def remove_option ( self, line, option ):
        options = self.get_value( line );
        options = self.parse_options( options);
        for k,o in enumerate( options ):
            if ( option == o ): del options[ k ] 
        
        return self.change_raw_value( line, " ".join( options ) )
    def has_option (self, line, option):
        options = self.parse_options( line )
        for o in options: 
            if o == option : return True
        return False
    
    def add_option ( self, line, option ):
        options = self.get_value( line );
        if options == False or options == None : options = ""   
        options = self.parse_options( options);
        found = False;
        for k,o in enumerate( options ):
            if ( option == o ): found = True;
        if ( found == False ): options.append( self.value_escape( option ) )
        return self.change_raw_value( line, " ".join( options ))

    def value_escape ( self, value ):
        if not value: return ''
        if ( value.find(' ') != -1 ):
            value = '"'+value.replace( '"', '\\"' )+'"'
        return value;

    def get_value ( self, line ):
        tokens = self.tokenize( line )
        if ( tokens == False ): return False;
        value = tokens.pop()
        if isinstance( value, str ):
            value = value.strip()
            value = self.value_unescape( value )
        return value
    def get_comment (self, line ):
        line = line.lstrip()
        if not line.startswith('#'): return False
        return line.lstrip('#')
    def get_indentation (self, line ):
        tokens = self.tokenize( line );        
        if ( tokens == False ): return False
        return tokens[ 0 ]
    def get_directive ( self, line ):
        tokens = self.tokenize( line );        
        if ( tokens == False ): return False
        return tokens[ 1 ]

    def change_value( self, line , new_value ):
        new_value = self.value_escape( new_value )
        return self.change_raw_value( line, new_value )

    def change_raw_value ( self, line , new_value ):
        tokens = self.tokenize( line )
        for idx, tok in enumerate( tokens ):
            if tok is None: tokens[idx] = ''            
        tokens[2] = tokens[2].replace( "\n", '' ) #separator shuoldn't contain newlines
        if tokens[2] == '': tokens[2] = ' ' #at least as space as separator
        line = tokens[0]+tokens[1]+tokens[2]+new_value
        line = line.rstrip() + "\n"
        return line


if __name__ == "__main__":  
    
    parser = Parser()
    parser.load( '/etc/apache2/sites-available/figa' )
    parser.set_value('DocumentRoot', '/var/www/xxxx/yyyy' )
        
    piece = VhostParser( parser )

    print piece.get_value('DocumentRoot' )
    print piece.get_value('ServerName' )
    piece.set_directive( 'fatwife' , 'fatwife 1')
    
    #piece.remove_option( 'ServerAlias', 'www.figa' )
    piece.add_option( 'ServerAlias', 'ftp.figa' ) 
    
    
    print "====="
    print piece.get_source()
    print "====="
 
