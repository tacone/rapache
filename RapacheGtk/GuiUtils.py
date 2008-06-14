import gtk

def style_as_tooltip( obj ):
    pw = gtk.Window(gtk.WINDOW_POPUP)
    pw.set_name('gtk-tooltip')
    pw.ensure_style()
    obj.set_style(pw.get_style())
    obj.connect('expose-event', paint)
    
def paint(box, event):
        box.style.paint_flat_box(box.window, gtk.STATE_NORMAL, gtk.SHADOW_OUT, None, box, "tooltip", box.allocation.x+1, box.allocation.y+1, box.allocation.width-2, box.allocation.height-2)
