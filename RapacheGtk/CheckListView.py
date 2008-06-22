import gtk
import gobject

(
    COLUMN_FIXED,
    COLUMN_SEVERITY,
    COLUMN_MARKUP
) = range(3)
from RapacheCore import Configuration
import RapacheCore.Observer
from RapacheGtk.EventDispatcher import Master

class CheckListView (gtk.TreeView ):
    """Nice list with icons and checkboxes"""
    def __init__ (self, *args, **kwargs):                
        super (CheckListView, self).__init__ (*args, **kwargs)
        
        self.toggled_callback = None
        self.selected_callback = None
        self.icon_callback = None
        
        self.Observable = RapacheCore.Observer.Observable()
        Master.register(self)
        
        self.column_checkbox = None
        self.column_description = None
        self.column_icon = None
        
        self.__add_columns()

        self.set_headers_visible( False )
        self.set_rules_hint(True)
        self.set_search_column(COLUMN_SEVERITY)
        
    #----decorating observer    
    def register (self, *args, **kwargs): return self.Observable.register(*args, **kwargs)
    def unregister (self, *args, **kwargs): return self.Observable.unregister(*args, **kwargs)
    def handle_event (self, *args, **kwargs): return self.Observable.handle_event(*args, **kwargs)
    def raise_event (self, *args, **kwargs): return self.Observable.raise_event(*args, **kwargs)
    
    def __load (self):
        self._post_load()
    def _post_load(self, model = None):
        if ( model != None ): self.set_model( model )
    
    def __toggled(self, *args, **kwargs):
        if self.toggled_callback != None:
            self.toggled_callback( *args, **kwargs )
    def __selected(self, *args, **kwargs):
        if self.selected_callback != None:
            self.selected_callback( *args, **kwargs )
    def __icon_requested(self, *args, **kwargs):
        if self.icon_callback != None:
            self.icon_callback( *args, **kwargs )       
                                  
    def __add_columns(self):
        #model = self.get_model()
        # column for fixed toggles
        renderer = gtk.CellRendererToggle()
        renderer.connect('toggled', self.__toggled, self)
        self.column_checkbox = gtk.TreeViewColumn('Enabled', renderer, active=COLUMN_FIXED)
        self.column_checkbox.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.column_checkbox.set_fixed_width(40)
        self.append_column(self.column_checkbox)

        self.column_icon = gtk.TreeViewColumn()
        cellRenderer = gtk.CellRendererPixbuf()
        self.column_icon.pack_start(cellRenderer, expand = False)
        self.column_icon.set_cell_data_func(cellRenderer, self.__icon_requested )
        self.append_column(self.column_icon)        
   
        self.column_description = gtk.TreeViewColumn('Description', gtk.CellRendererText(),
                                     markup=COLUMN_MARKUP)
        self.column_description.set_sort_column_id(COLUMN_MARKUP)
        self.append_column(self.column_description)
        self.get_selection().connect("changed", self.__selected )
        
    def get_selected_line( self ):
        try:
            selection = self.get_selection()
            rows = selection.get_selected_rows()[1][0]
            num_row = rows[0]
            model = self.get_model()
            name = model[ num_row ][1]
            return name
        except:
            return None

gobject.type_register (CheckListView)