import gtk
import gtksourceview
import pango

def style_as_tooltip( obj ):
    pw = gtk.Window(gtk.WINDOW_POPUP)
    pw.set_name('gtk-tooltip')
    pw.ensure_style()
    obj.set_style(pw.get_style())
    obj.connect('expose-event', paint)
    
def paint(box, event):
        box.style.paint_flat_box(box.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT, None, box, "tooltip", box.allocation.x+1, box.allocation.y+1, box.allocation.width-2, box.allocation.height-2)

def change_button_label ( button, new_label ):
        """Changes the label of a button"""
        button.show()
        alignment = button.get_children()[0]
        hbox = alignment.get_children()[0]
        image, label = hbox.get_children()
        label.set_text( new_label )

def new_apache_sourceview():
    bufferS = gtksourceview.SourceBuffer()
    manager = gtksourceview.SourceLanguagesManager()
    language = manager.get_language_from_mime_type("text/xml")
    bufferS.set_language(language)
    bufferS.set_highlight(True)
    sourceview = gtksourceview.SourceView(bufferS)
    sourceview.set_show_line_numbers(True)
    #TODO sniff gnome default monospace font
    sourceview.modify_font(pango.FontDescription("monospace 10"))
    return sourceview