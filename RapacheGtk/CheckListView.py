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
        self.set_headers_visible( False )
        self.set_rules_hint(True)
        self.set_search_column(COLUMN_SEVERITY)
        self.__add_columns()
        self.toggled_callback = None
        self.selected_callback = None
        self.icon_callback = None
        
        self.Observable = RapacheCore.Observer.Observable()
        Master.register(self)
        
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
        column = gtk.TreeViewColumn('Enabled', renderer, active=COLUMN_FIXED)

        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(40)
        self.append_column(column)

        column = gtk.TreeViewColumn()
        cellRenderer = gtk.CellRendererPixbuf()
        column.pack_start(cellRenderer, expand = False)
        column.set_cell_data_func(cellRenderer, self.__icon_requested )
        self.append_column(column)        
   
        column = gtk.TreeViewColumn('Description', gtk.CellRendererText(),
                                     markup=COLUMN_MARKUP)
        column.set_sort_column_id(COLUMN_MARKUP)
        self.append_column(column)
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