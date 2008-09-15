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

import os
from RapacheCore.PluginBase import PluginBaseObject
from certificate_request import CertificateRequestWindow
from RapacheCore import Shell
from text_display import TextDisplayWindow
from OpenSSL import crypto
import subprocess
import time
from RapacheCore import VirtualHost
from RapacheCore import Configuration
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
"""

<VirtualHost your-site.uwaterloo.ca:443>
# use SSL with default configuration
SSLEnable
SSLCertificateFile /software/sslCerts-1/config/certs/httpsd.pem
</VirtualHost>




"""
class AdvancedVhostPlugin(PluginBaseObject):

    def __init__(self, path):
        
        # The path to the plugin
        self.path = path
    
        # module this plugin works with
        self.module = "ssl"
        
        # Define what additional config should be read from vhost file
        self.vhosts_config = {  "SSLEngine" : 0, 
                                "SSLCertificateFile" : 0 ,
                                "SSLCertificateKeyFile" : 0 } # 0 value | 1 options
            
        self.vhost = None
        self.active_cert = None
        
        # createing a csr will create this key... so dont worry about it existing
        self.default_key = os.path.join("/etc/ssl/private/default-apache-ssl.pkey")
        
    def on_menu_item_activate(self, widget, main_window):
        #if self.is_module_enabled():
        ssl_vhost = None
        for vhost in VirtualHost.get_all_vhosts():
            if vhost.get_port() == 443: 
                
                # TODO: is this the best check... maybe check ssl property?
                ssl_vhost = vhost
                break
        
        if not ssl_vhost:
            # There is no ssl_host create one now!
            print "No ssl vhost exists creating one now"
            f = open(os.path.join(self.path , "default-ssl"), "r")
            content = f.read()
            f.close()
            Shell.command.write_file(os.path.join(Configuration.SITES_AVAILABLE_DIR, "default-ssl"), content)
            ssl_vhost = VirtualHost.VirtualHostModel("default-ssl")
            #ssl_vhost.toggle(False)
            main_window.open_edit_vhost_window("default-ssl")
            
    # Add item to tools menu
    def init_main_window(self, main_window):

        #self.menu_item = gtk.MenuItem("New SSL Host")
        #self.menu_item.connect("activate", self.on_menu_item_activate, main_window)
        #main_window.add_new_vhost_menu_item(self.menu_item)
        #return self.menu_item
        return

    def init_vhost_properties(self):
        # Get glade file XML
        f = open( os.path.join(self.path, "ssl.glade") ,"r")
        self.glade_vhost_xml =  f.read()
        f.close()
    
        # Remember you will need to recreate tree everytime the window loads
        wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "table_ssl")
        table_ssl = wtree.get_widget("table_ssl")    
        #self.entry_admin_email =  wtree.get_widget("entry_admin_email")    
        #self.entry_log_location = wtree.get_widget("entry_log_location")    
        self.treeview_requests =  wtree.get_widget("treeview_requests")
        self.linkbutton_active_cert = wtree.get_widget("linkbutton_active_cert")
        self.filechooserbutton_ssl_cert = wtree.get_widget("filechooserbutton_ssl_cert")
        self.spinbutton_port = wtree.get_widget("spinbutton_port")
        self.entry_ssl_key_location = wtree.get_widget("entry_ssl_key_location")
        self.filechooserbutton_ssl_key = wtree.get_widget("filechooserbutton_ssl_key")
        signals = {
            "on_button_csr_clicked"                 : self.on_button_csr_clicked,
            "on_treeview_requests_row_activated"    : self.on_treeview_requests_row_activated,
            "on_button_import_clicked"              : self.on_button_import_clicked,
            "on_button_import_key_clicked"          : self.on_button_import_key_clicked,
            "on_button_key_reset_clicked"           : self.on_button_key_reset_clicked
        }
        wtree.signal_autoconnect(signals)   


        # Setup tree
        column = gtk.TreeViewColumn((''))
        column.set_spacing(4)
        cell = gtk.CellRendererToggle()
        cell.set_radio(True)
        cell.connect('toggled', self.treeview_requests_toggled)
        column.pack_start(cell, False)
        column.set_attributes(cell, active=0)
        self.treeview_requests.append_column(column)
        
        column = gtk.TreeViewColumn((''))
        column.set_spacing(4)
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_attributes(cell, pixbuf=1)
        self.treeview_requests.append_column(column)

        column = gtk.TreeViewColumn(('Type'))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=2)
        self.treeview_requests.append_column(column)
        
        column = gtk.TreeViewColumn(('Domain'))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=3)
        self.treeview_requests.append_column(column)
        
        column = gtk.TreeViewColumn(('Expires'))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=4)
        self.treeview_requests.append_column(column)

        self.spinbutton_port.set_value(443)
        
        icon_theme = gtk.icon_theme_get_default()
        pixbuf = icon_theme.lookup_icon("application-certificate", 24, 0).load_icon()
        
        return table_ssl, "SSL", pixbuf


    def on_button_import_key_clicked(self, widget):
        path = self.filechooserbutton_ssl_key.get_filename()
        
        if path:
            f = open(path, "r")
            text = f.read()
            f.close()
            
            try:
                crypto.load_privatekey(crypto.FILETYPE_PEM, text) 
            except:
                md = gtk.MessageDialog(None, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format="Could not import does not appear to be a valid key!") 
                md.run()
                md.destroy()
                return
                   
            key_path = os.path.join("/etc/ssl/private/", os.path.basename(path))
            
            if not Shell.command.sudo_exists(key_path):
                Shell.command.write_file(key_path, text)
                self.entry_ssl_key_location.set_text(key_path)    
            
            else:
                md = gtk.MessageDialog(None, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format="A key with that filename already exists") 
                result = md.run()
                md.destroy()


    def on_button_key_reset_clicked(self, widget):
        self.entry_ssl_key_location.set_text(self.default_key)    

    def on_button_import_clicked(self, widget):
        path = self.filechooserbutton_ssl_cert.get_filename()
        
        if path:
            f = open(path, "r")
            text = f.read()
            f.close()
            
            cert = None
            try:
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, text) 
            except:
                md = gtk.MessageDialog(None, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format="Could not import does not appear to be a valid certificate!") 
                md.run()
                md.destroy()
                return
                
            timestamp = time.strftime("%y-%m-%d %H:%M:%S", time.localtime() )

            cert_path = os.path.join("/etc/apache2/ssl/", cert.get_subject().commonName + ' ' + timestamp +'.crt')
            
            Shell.command.write_file(cert_path, text)
            
            md = gtk.MessageDialog(None, flags=0, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="Are you sure you want to change the active SSL certificate?") 
            result = md.run()
            md.destroy()
            if result == gtk.RESPONSE_YES:
                self.update_active_cert(cert_path)
                
            self.filechooserbutton_ssl_cert.unselect_all()
            self.update_treeview()

    def on_treeview_requests_row_activated(self, widget, a, b):
        model, iter =  self.treeview_requests.get_selection().get_selected()
        if not iter: return
        path = model.get_value(iter, 5)
        self.on_treeview_checked_changed(path)
    
    def treeview_requests_toggled(self, cell, path):
        iter = self.treeview_requests_store.get_iter((int(path),))
        path = self.treeview_requests_store.get_value(iter, 5)
        self.on_treeview_checked_changed(path)
    
    def on_treeview_checked_changed(self, path):

        if path and path.endswith(".csr"):
            tdw = TextDisplayWindow(self.path)
            
            cert = crypto.load_certificate_request(crypto.FILETYPE_PEM, Shell.command.read_file(path)) 
             
            help_array = []
            
            if cert.get_subject().organizationName:
                help_array.append( ["Organisation:", cert.get_subject().organizationName] )

            if cert.get_subject().organizationalUnitName:
                help_array.append( ["Organisation Unit:", cert.get_subject().organizationalUnitName] )

            if cert.get_subject().localityName:
                help_array.append( ["Locality:", cert.get_subject().localityName] )
                
            if cert.get_subject().stateOrProvinceName:
                help_array.append( ["State:", cert.get_subject().stateOrProvinceName] )
                
            if cert.get_subject().countryName:
                help_array.append( ["Country:", cert.get_subject().countryName] )
                 
            help_array.append( ["Domain:", cert.get_subject().commonName] )
            
            text =  "<big><b>SSL Certificate Request</b></big>\nYou will need to send this certificate request, proof of your company's identity, and payment to a Certificate Authority (CA). The CA verifies the certificate request and your identity, and then sends back a certificate for your secure server."

            tdw.load(text,help_array, path)
            tdw.run()
        elif not path or path.endswith(".crt"):
            result = gtk.RESPONSE_OK
            if path:
                tdw = TextDisplayWindow(self.path)
                
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, Shell.command.read_file(path)) 
                expired = self.get_expiry_date_hack(cert, path)
                start = self.get_start_date_hack(cert, path)
                status = "Valid"
                if cert.has_expired(): status = "Expired"
                
                text = "<big><b>SSL Certificate for <i>%s</i></b></big>" % (cert.get_subject().commonName )

                help_array = []
                help_array.append( ["Status:", status ] )
                help_array.append( ["Domain:", cert.get_subject().commonName ] )
                help_array.append( ["Serial:", cert.get_serial_number() ] )
               
                help_array.append( ["Starts:", start] )
                help_array.append( ["Expires:", expired] )

                if cert.get_subject().organizationName:
                    help_array.append( ["Organisation:", cert.get_subject().organizationName] )

                if cert.get_subject().organizationalUnitName:
                    help_array.append( ["Organisation Unit:", cert.get_subject().organizationalUnitName] )

                if cert.get_subject().localityName:
                    help_array.append( ["Locality:", cert.get_subject().localityName] )
                    
                if cert.get_subject().stateOrProvinceName:
                     help_array.append( ["State:", cert.get_subject().stateOrProvinceName] )
                    
                if cert.get_subject().countryName:
                    help_array.append( ["Country:", cert.get_subject().countryName] )
                  
                #help_array.append( ["Domain:", cert.get_subject().commonName] )   
                help_array.append( ["Issued by:", cert.get_issuer().commonName] )   
                
                tdw.load( "SSL Certificate Details", text, help_array, path, True, self.active_cert != path)
                result = tdw.run()
                
            if result == gtk.RESPONSE_OK:
                md = gtk.MessageDialog(None, flags=0, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="Are you sure you want to change the active SSL certificate?") 
                result = md.run()
                md.destroy()
                if result == gtk.RESPONSE_YES:
                    self.update_active_cert(path)
                    self.update_treeview()
        
        
        
    def get_start_date_hack(self, cert, path):
        # openssl 0.6 does not have get_notAfter() method
        if hasattr(cert, "get_notBefore"):
            return cert.get_notBefore()
        return subprocess.Popen(["openssl", "x509", "-noout", "-in", path, "-dates"], stdout=subprocess.PIPE, stderr=open(os.devnull, "w")).communicate()[0].split("\n")[0][10:]
        
        
    def get_expiry_date_hack(self, cert, path):
        # openssl 0.6 does not have get_notAfter() method
        if hasattr(cert, "get_notAfter"):
            return cert.get_notAfter()
        return subprocess.Popen(["openssl", "x509", "-noout", "-in", path, "-dates"], stdout=subprocess.PIPE, stderr=open(os.devnull, "w")).communicate()[0].split("\n")[1][9:]
        
    def update_treeview(self):
        icon_theme = gtk.icon_theme_get_default()
        cert_icon = icon_theme.lookup_icon("application-certificate", 24, 0).load_icon() 
        cert_icon_self = icon_theme.lookup_icon("application-certificate", 24, 0).load_icon() 

        self.treeview_requests_store = gtk.ListStore(bool, gtk.gdk.Pixbuf,str, str, str, str)
        self.treeview_requests.set_model(self.treeview_requests_store)
        
        files = Shell.command.listdir("/etc/apache2/ssl/")
        files.sort()

        domains = list(self.vhost.get_server_alias())
        if self.vhost.config.ServerName:
              domains = [self.vhost.get_server_name()] + domains

        if not self.active_cert:
            self.treeview_requests_store.append((True, None , "<b><i>No Certificate</i></b>", "", "", None))   
        else:
            self.treeview_requests_store.append((False, None, "<i>No Certificate</i>", "", "", None)) 

        for path in files: 
            full_path = os.path.join("/etc/apache2/ssl/", path)     

            if path.endswith(".crt"):

                cert = crypto.load_certificate(crypto.FILETYPE_PEM, Shell.command.read_file(full_path)) 
                domain = cert.get_subject().commonName
                domain_match = False
                # find domains that are relevent
                for d in domains:

                    if d == domain or (domain[0] == "*" and (d.endswith( domain[1:] ) or d == domain[2:])):
                        domain_match = True      
                        
 
                        if domain_match:
                            expired = self.get_expiry_date_hack(cert, full_path)
                            icon = cert_icon
                            
                            if domain == cert.get_issuer().commonName:
                                icon = cert_icon_self
                            
                            if cert.has_expired() : expired = "<b>Expired " + expired +"</b>"

                            if full_path == self.active_cert:
                                self.treeview_requests_store.append((True, icon, "<b>Certificate</b>", "<b>"+ domain +"</b>"         ,  "<b>" +expired +"</b>", full_path))     
                                select = self.treeview_requests.get_selection()
                                select.select_path(len(self.treeview_requests_store) - 1)
                                self.treeview_requests.scroll_to_cell(len(self.treeview_requests_store) - 1)
                                
                            else: 
                                self.treeview_requests_store.append((False, icon, "Certificate", domain , expired, full_path))
                                  
                        break   

    def on_button_csr_clicked(self, widget):

        w = CertificateRequestWindow(self.path)
        ServerAdmin = ''
        if self.vhost.config.ServerAdmin:
            ServerAdmin = self.vhost.config.ServerAdmin.value
        
        domains = list(self.vhost.get_server_alias())
        if self.vhost.config.ServerName:
              domains = [self.vhost.get_server_name()] + domains
              
        w.load( domains , ServerAdmin, self.entry_ssl_key_location.get_text() )
        cert = w.run()
        
        if cert:
             self.update_active_cert( cert )
        
        self.update_treeview()

    def update_active_cert(self, cert, key=None):
        self.active_cert = cert

    # Customise the vhost properties window
    def load_vhost_properties(self, vhost):
        self.vhost = vhost
        
        if vhost.config.SSLCertificateFile:
            self.update_active_cert(vhost.config.SSLCertificateFile.value)
        else:
            self.update_active_cert("")
            
        if vhost.config.SSLCertificateKeyFile:
            self.entry_ssl_key_location.set_text(vhost.config.SSLCertificateKeyFile.value)
        else:
            self.entry_ssl_key_location.set_text(self.default_key)
        
        port = self.vhost.get_port()
        if port and not port == 80:
            self.spinbutton_port.set_value(port)
        
        self.update_treeview()      
        return
        
    # Perform action on vhost properties save
    def update_vhost_properties(self, vhost):
        self.vhost = vhost
        error = None
        if self.active_cert:
             vhost.config.SSLEngine.value = "on"
             vhost.config.SSLCertificateKeyFile.value = self.entry_ssl_key_location.get_text()
             vhost.set_port( self.spinbutton_port.get_value_as_int() )
             vhost.config.SSLCertificateFile.value = self.active_cert
        else:
            if vhost.config.SSLEngine:
                del vhost.config.SSLEngine
             
            if vhost.config.SSLCertificateFile:
                del vhost.config.SSLCertificateFile
                
            if vhost.config.SSLCertificateKeyFile:
                del vhost.config.SSLCertificateKeyFile             
             
            vhost.set_port(80)

        
        return True, ""


def register( path ):
    return AdvancedVhostPlugin( path )

