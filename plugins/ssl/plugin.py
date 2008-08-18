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
        
        
    def on_menu_item_activate(self, widget, main_window):
        #if self.is_module_enabled():
        ssl_vhost = None
        for vhost in VirtualHost.get_all_vhosts():
            if vhost.get_value("port", "80") == "443": 
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
        self.menu_item = gtk.MenuItem("Create SSL Host")
        self.menu_item.connect("activate", self.on_menu_item_activate, main_window)
        return self.menu_item

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
        self.entry_ssl_certificate_location = wtree.get_widget("entry_ssl_certificate_location")
        self.checkbutton_ssl_enable = wtree.get_widget("checkbutton_ssl_enable")
        self.treeview_requests =  wtree.get_widget("treeview_requests")
        self.linkbutton_active_cert = wtree.get_widget("linkbutton_active_cert")
        self.filechooserbutton_ssl_cert = wtree.get_widget("filechooserbutton_ssl_cert")
        self.entry_ssl_port = wtree.get_widget("entry_ssl_port")
        signals = {
            "on_button_csr_clicked"                 : self.on_button_csr_clicked,
            "on_treeview_requests_row_activated"    : self.on_treeview_requests_row_activated,
            "on_button_import_clicked"              : self.on_button_import_clicked
        }
        wtree.signal_autoconnect(signals)   


        # Setup tree
        column = gtk.TreeViewColumn((''))
        column.set_spacing(4)
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_attributes(cell, pixbuf=0)
        self.treeview_requests.append_column(column)

        column = gtk.TreeViewColumn(('Type'))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=1)
        self.treeview_requests.append_column(column)
        
        column = gtk.TreeViewColumn(('Domain'))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=2)
        self.treeview_requests.append_column(column)
        
        column = gtk.TreeViewColumn(('Expires'))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=3)
        self.treeview_requests.append_column(column)

        wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "hbox_label")
        return table_ssl, wtree.get_widget("hbox_label")


    def on_button_import_clicked(self, widget):
        path = self.filechooserbutton_ssl_cert.get_filename()
        
        if path:
            f = open(path, "r")
            text = f.read()
            f.close()
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, text) 
            timestamp = time.strftime("%y-%m-%d %H:%M:%S", time.localtime() )

            cert_path = os.path.join("/etc/apache2/ssl/", cert.get_subject().commonName + ' ' + timestamp +'.pem')
            
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
        path = model.get_value(iter, 4)
        
        if path.endswith(".csr"):
            tdw = TextDisplayWindow(self.path)
            
            cert = crypto.load_certificate_request(crypto.FILETYPE_PEM, Shell.command.read_file(path)) 
             
            text = "<big><b>SSL Certificate Request</b></big>" 
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
            
            text +=  "\nYou will need to send this certificate request, proof of your company's identity, and payment to a Certificate Authority (CA). The CA verifies the certificate request and your identity, and then sends back a certificate for your secure server."

            tdw.load(text,help_array, path)
            tdw.run()
        if path.endswith(".crt"):
            tdw = TextDisplayWindow(self.path)
            
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, Shell.command.read_file(path)) 
            expired = self.get_expiry_date_hack(cert, path)
            start = self.get_start_date_hack(cert, path)
            if cert.has_expired() : expired = "<b>Expired " + expired +"</b>"
            
            text = "<big><b>SSL Certificate</b></big>" 

            help_array = []
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
              
            help_array.append( ["Domain:", cert.get_subject().commonName] )   
            help_array.append( ["Issued by:", cert.get_issuer().commonName] )   
            
            tdw.load( text, help_array, path, True, self.active_cert != path)
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
        file_icon = icon_theme.load_icon(gtk.STOCK_DIALOG_INFO, 24, 0)
        auth_icon = icon_theme.load_icon(gtk.STOCK_DIALOG_AUTHENTICATION, 24, 0)
        cert_icon = icon_theme.load_icon(gtk.STOCK_ABOUT, 24, 0)
        self.treeview_requests_store = gtk.ListStore(gtk.gdk.Pixbuf,str, str, str, str)
        self.treeview_requests.set_model(self.treeview_requests_store)
        
        files = Shell.command.listdir("/etc/apache2/ssl/")
        files.sort()
        for path in files: 
            full_path = os.path.join("/etc/apache2/ssl/", path)     

            if path.endswith(".crt"):
                
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, Shell.command.read_file(full_path)) 
                expired = self.get_expiry_date_hack(cert, full_path)
                if cert.has_expired() : expired = "<b>Expired " + expired +"</b>"

                if full_path == self.active_cert:
                    self.treeview_requests_store.append((auth_icon, "<b>Active Certificate</b>", "<b>" + cert.get_subject().commonName +"</b>", expired, full_path))     
                    select = self.treeview_requests.get_selection()
                    select.select_path(len(self.treeview_requests_store) - 1)
                    self.treeview_requests.scroll_to_cell(len(self.treeview_requests_store) - 1)
                    
                else: 
                    self.treeview_requests_store.append((auth_icon, "Certificate", cert.get_subject().commonName , expired, full_path))     
            #if path.endswith(".pkey"):
            #    self.treeview_requests_store.append((auth_icon, "Key", path, path)) 

        files = Shell.command.listdir("/etc/apache2/ssl/")
        files.sort()
        for path in files: 
            full_path = os.path.join("/etc/apache2/ssl/", path)     
            if path.endswith(".csr"):
                cert_req = crypto.load_certificate_request(crypto.FILETYPE_PEM, Shell.command.read_file(full_path)) 
                self.treeview_requests_store.append((file_icon, "Request", cert_req.get_subject().commonName, "",  full_path))

    def on_button_csr_clicked(self, widget):

        w = CertificateRequestWindow(self.path)
        
        w.load( [self.vhost.get_value("ServerName")] + self.vhost.get_value("ServerAlias", []),  self.vhost.get_value("ServerAdmin", "") )
        cert = w.run()
        
        if cert:
             self.update_active_cert( cert )
        
        self.update_treeview()

    def update_active_cert(self, cert, key=None):
        self.active_cert = cert
        if key:
            self.active_key = key
        else:
            # try and guess correct key, based on cert name then vhost name
            key = os.path.basename(self.active_cert).split(' ')[0]
            key_path = os.path.join("/etc/ssl/private/", key + ".pkey")
            print key_path 
            if Shell.command.exists(key_path):
                self.active_key = key_path
            else:
                key_path = os.path.join("/etc/ssl/private/", key + ".key")
                print key_path 
                if Shell.command.exists(key_path):
                    self.active_key = key_path
                else:
                    key_path = os.path.join("/etc/ssl/private/", self.vhost.get_value("ServerName") + '.pkey')
                    print key_path 
                    if Shell.command.exists(key_path):
                        self.active_key = key_path
                    else:
                        key_path = os.path.join("/etc/ssl/private/", self.vhost.get_value("ServerName") + '.key')
                        print key_path 
                        if Shell.command.exists(key_path):
                            self.active_key = key_path

    # Customise the vhost properties window
    def load_vhost_properties(self, vhost):
        self.vhost = vhost
                  
        self.update_active_cert(vhost.get_value("SSLCertificateFile", ""), vhost.get_value("SSLCertificateKeyFile", ""))
        self.update_treeview()      

        if vhost.get_value("SSLEngine", "Off").lower() == "on":
            self.checkbutton_ssl_enable.set_active(True)
        return
        
    # Perform action on vhost properties save
    def save_vhost_properties(self, vhost):
        self.vhost = vhost
        error = None
        
        if self.active_cert:
             vhost.set_value("SSLEngine", "on" )
             vhost.set_value("Port", self.entry_ssl_port.get_text() )
        else:
             vhost.set_value("SSLEngine", "off")
             #vhost.set_value("Port", "80" )

        vhost.set_value("SSLCertificateFile", self.active_cert)
        vhost.set_value("SSLCertificateKeyFile", self.active_key)
              
        return True, error


def register( path ):
    return AdvancedVhostPlugin( path )

