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
sys.path.append('../RapacheCore')
from ApacheConf import *
import unittest


class LineParserTest( unittest.TestCase ):
    def test_tokenize (self):
        lp = LineParser()
        
        line = "\t\tDocumentRoot /var/www/"
        expected = ['\t\t', 'DocumentRoot', ' ', '/var/www/']
        result = lp.tokenize( line )
        self.assertEqual( result, expected)
        
        line = "\t\t ServerAlias\twww.example.net www.example.org"
        expected = ['\t\t ', 'ServerAlias', '\t', 'www.example.net www.example.org']
        result = lp.tokenize( line )
        self.assertEqual( result, expected)
    def test_value_unescape (self):
        lp = LineParser()        
        
        #first value is the escaped value, second value is the expected result
        please_test =[
          [ 'simple value' , 'simple value' ]
        , [ r'"simple value"' , r'simple value' ]
        #, [ r' "simple value"' , r'simple value' ] #TODO: fix this
        , [ r'"value with \"quotes\" included"', r'value with "quotes" included' ]        
        , [ r'"value with \'quotes\' included"', r'value with \'quotes\' included' ]
        ]
        for case in please_test:
            value, expected = case
            result = lp.value_unescape( value )            
            self.assertEqual( result, expected)
        
        """ # works, but gives warning
        try:
            lp.value_unescape( '"oij" ')
            #preceding and trailing spaces are not supported by this method
            self.assertTrue( False ) #Prev. line should have thrown exception
        except 'BadQuoting':
            self.assertTrue( True )
        """
    def test_parse_options(self):
        lp = LineParser()
        please_test =[
          [ 'option1 option2' , ['option1','option2'] ]
          # TODO: fix this
          #, [ 'option1 "spaced option"' , ['option1','"spaced option"'] ]
        ]
        for case in please_test:
            value = case[0]
            expected = case [1]            
            result = lp.parse_options( value )            
            self.assertEqual( result, expected)
    def test_remove_option(self):
        lp = LineParser()
        please_test = [
          [   '\t\tServerAlias www.example.com beta.example.com example.net'
            , 'beta.example.com'
            , '\t\tServerAlias www.example.com example.net' ]
          ,[  '\t\tServerAlias www.example.com beta.example.com example.net'
            , 'www.example.com'
            , '\t\tServerAlias beta.example.com example.net' ]
          ,[  '\t\tServerAlias www.example.com beta.example.com example.net'
            , 'example.net'
            , '\t\tServerAlias www.example.com beta.example.com' ]
          # removing the only option
          ,[  '\t\tServerAlias www.example.com'
            , 'www.example.com'
            , '\t\tServerAlias' ]
          # removing non-existant option
          ,[  '\t\tServerAlias www.example.com'
            , 'example.com'
            , '\t\tServerAlias www.example.com' ]          
        ]
        for case in please_test:
            line, option, expected = case 
            result = lp.remove_option( line, option )
            # TODO: fix the newlines to be consistent and remove rstrip
            self.assertEqual( result.rstrip(), expected.rstrip())
    def test_has_option(self):
        lp = LineParser()
        please_test =[
          [ '\t\tServerAlias www.example.com beta.example.com example.net'
            , 'beta.example.com'
            , True ]
         ,[ '\t\tServerAlias www.example.com beta.example.com example.net'
            , 'gamma.example.com'
            , False ]
          ,[  '\t\tServerAlias'
            , 'beta.example.com'
            , False ]
          ,[  '\t\tServerAlias beta.example.com'
            , 'beta.example.com'
            , True ]
        ]
        for case in please_test:
            line, option, expected = case 
            result = lp.has_option( line, option )
            # TODO: fix the newlines to be consistent and remove rstrip
            self.assertEqual( result, expected )
    def test_add_option(self):
        lp = LineParser()
        please_test = [          
          [   
              #it already exists, don't add                        
              '\t\tServerAlias www.example.com beta.example.com example.net'
            , 'beta.example.com'
            , '\t\tServerAlias www.example.com beta.example.com example.net' ]
          ,[  
              #should be added at the end of the line
              '\t\tServerAlias www.example.com beta.example.com example.net'
            , 'gamma.example.com'
            , '\t\tServerAlias www.example.com beta.example.com example.net gamma.example.com' ]          
          # adding to an 1 option directive
          ,[  '\t\tServerAlias www.example.com'
            , 'www.example.net'
            , '\t\tServerAlias www.example.com www.example.net' ]
          # TODO: this fails, please fix
          # # adding to an empty directive
          #,[  '\t\tServerAlias'
          #  , 'example.com'
          #  , '\t\tServerAlias example.com' ]          
        ]
        for case in please_test:
            line, option, expected = case 
            result = lp.add_option( line, option )
            # TODO: fix the newlines to be consistent and remove rstrip
            self.assertEqual( result.rstrip(), expected.rstrip())
    def test_value_escape (self):
        lp = LineParser()        
        
        #first value is the escaped value, second value is the expected result
        please_test =[
          [ 'value', 'value' ] #we don't need quotes here, won't be quoted
        , [ 'simple value' , '"simple value"' ]
        , [ r'simple value', r'"simple value"' ]        
        , [ r'value with "quotes" included', r'"value with \"quotes\" included"' ]        
        , [ r'value with \'quotes\' included', r'"value with \'quotes\' included"' ]
        ]
        for case in please_test:
            value, expected = case  
            result = lp.value_escape( value )            
            self.assertEqual( result, expected)
    def test_get_value(self):
        lp = LineParser()
        please_test =[
            [ 'DocumentRoot /var/www/', '/var/www/' ],
            #should strip trailing spaces
            [ 'DocumentRoot /var/www/    ', '/var/www/' ],
            #should strip preceding spaces
            [ 'DocumentRoot \t\t  /var/www/    ', '/var/www/' ], 
            #should return all the options as one single string
            [ '\t\tServerAlias www.example.com beta.example.com ', 'www.example.com beta.example.com' ]            
          ]
        for case in please_test:
            value, expected = case  
            result = lp.get_value( value )            
            self.assertEqual( result, expected)
    def test_get_directive(self):
        lp = LineParser()
        please_test =[
         [ 'DocumentRoot /var/www/', 'DocumentRoot' ],
         [ '\t\t  DocumentRoot /var/www/', 'DocumentRoot' ]
        ]
        for case in please_test:
            value, expected = case  
            result = lp.get_directive( value )            
            self.assertEqual( result, expected)
    def test_change_raw_value(self):
        lp = LineParser()
        please_test =[
         [ 'DocumentRoot /var/www/', '/srv/www/something',     'DocumentRoot /srv/www/something' ]
         #todo fix this
         #, [ '\t\t  ServerAlias', 'www.test.com', '\t\t  ServerAlias www.test.com' ]
         , [ '\t\t  ServerAlias aaa.com bbb.com', 'ccc.com', '\t\t  ServerAlias ccc.com' ]
         , [ '\t\t  ServerAlias aaa.com', 'bbb.com ccc.com', '\t\t  ServerAlias bbb.com ccc.com' ]
        ]
        for case in please_test:
            value, new_value, expected = case  
            result = lp.change_raw_value( value, new_value )
            self.assertEqual( result.rstrip(), expected.rstrip())
    def test_change_value(self):
        lp = LineParser()
        please_test =[
         [ 'DocumentRoot /var/www/', '/srv/www/something',     'DocumentRoot /srv/www/something' ]
         #todo fix this
         #, [ '\t\t  ServerAlias', 'www.test.com', '\t\t  ServerAlias www.test.com' ]
         , [ '\t\t  ServerAlias aaa.com bbb.com', 'ccc.com', '\t\t  ServerAlias ccc.com' ]
         #change_value escape automatically any value containing a space by quoting it
         , [ '\t\t  ServerAlias aaa.com', 'bbb.com ccc.com', '\t\t  ServerAlias "bbb.com ccc.com"' ]
        ]
        for case in please_test:
            value, new_value, expected = case  
            result = lp.change_value( value, new_value )
            self.assertEqual( result.rstrip(), expected.rstrip())

class ParserTest ( unittest.TestCase ):
    pass
          
if __name__ == "__main__":
    unittest.main()
    