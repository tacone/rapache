import os
from RapacheCore.PluginBase import PluginBaseObject
from certificate_request import CertificateRequestWindow
from RapacheCore import Shell
from text_display import TextDisplayWindow
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
                                "SSLCertificateFile" : 0  } # 0 value | 1 options
            
        self.vhost = None
        
        self.active_cert = None
    
    
    def init_vhost_properties(self):


        # Get glade file XML
        f = open( os.path.join(self.path, "vhost.glade") ,"r")
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
        
        signals = {
            "on_button_csr_clicked"            : self.on_button_csr_clicked
        }
        wtree.signal_autoconnect(signals)   


        # Setup tree
        column = gtk.TreeViewColumn(('Item'))
        column.set_spacing(4)

        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_attributes(cell, pixbuf=0)
        self.treeview_requests.append_column(column)

        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=1)
        self.treeview_requests.append_column(column)
        
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=2)
        self.treeview_requests.append_column(column)

        wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "hbox_label")
        return table_ssl, wtree.get_widget("hbox_label")


    def update_treeview(self):

        icon_theme = gtk.icon_theme_get_default()
        file_icon = icon_theme.load_icon(gtk.STOCK_DIALOG_INFO, 24, 0)
        auth_icon = icon_theme.load_icon(gtk.STOCK_DIALOG_AUTHENTICATION, 24, 0)
        cert_icon = icon_theme.load_icon(gtk.STOCK_ABOUT, 24, 0)
        self.treeview_requests_store = gtk.ListStore(gtk.gdk.Pixbuf,str, str, str)
        self.treeview_requests.set_model(self.treeview_requests_store)
        
        files = Shell.command.listdir(self.ssl_path)
        files.sort()
        for path in files:      
            if path.endswith(".csr"):
                self.treeview_requests_store.append((file_icon, "Request", path, path))
            if path.endswith(".cert"):
                self.treeview_requests_store.append((auth_icon, "Certificate", "<b>" + path +"</b>", path)) 
            #if path.endswith(".pkey"):
            #    self.treeview_requests_store.append((auth_icon, "Key", path, path)) 

    def on_button_csr_clicked(self, widget):

        w = CertificateRequestWindow(self.path)
        
        w.load( [self.vhost.get_value("ServerName")] + self.vhost.get_value("ServerAlias", []),  self.vhost.get_value("ServerAdmin", ""), self.ssl_path )
        cert = w.run()
        
        if cert:
             self.update_active_cert( cert)
        
        self.update_treeview()

    def update_active_cert(self, cert):
        self.active_cert = cert
        self.linkbutton_active_cert.set_label(os.path.basename(cert))

    # Customise the vhost properties window
    def load_vhost_properties(self, vhost):
        self.vhost = vhost
          
        self.ssl_path = os.path.abspath(os.path.join(self.vhost.get_value( 'DocumentRoot' ), os.path.pardir, "ssl"))
        
        self.update_treeview()
        self.update_active_cert(vhost.get_value("SSLCertificateFile", ""))

        self.entry_ssl_certificate_location.set_text( self.ssl_path )  
        

        if vhost.get_value("SSLEngine", "Off").lower() == "on":
            self.checkbutton_ssl_enable.set_active(True)
        return
        
    # Perform action on vhost properties save
    def save_vhost_properties(self, vhost):
        self.vhost = vhost
        
        if self.checkbutton_ssl_enable.get_active():
             vhost.set_value("SSLEngine", "on" )
             vhost.set_value("Port", "443" )
        else:
             vhost.set_value("SSLEngine", "off")
             vhost.set_value("Port", "80" )

        vhost.set_value("SSLCertificateFile", self.active_cert)

        return True, None


def register( path ):
    return AdvancedVhostPlugin( path )

