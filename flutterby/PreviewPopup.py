import gtk

class PreviewPopup :
    def __init__(self, filename, pos = None):
        self.popup = gtk.Window(gtk.WINDOW_POPUP  )
        self.eventbox = gtk.EventBox()
        self.image = gtk.Image()
        self.image.set_from_file(filename)
        self.eventbox.add(self.image)
        self.eventbox.connect('motion-notify-event', self.on_motion_notify_event)
        self.eventbox.connect('focus-out-event', self.on_motion_notify_event)
        self.eventbox.connect('button-press-event', self.on_motion_notify_event)
        self.eventbox.connect('show', self.on_show_event)
        self.popup.add(self.eventbox)
        self.popup.set_position(gtk.WIN_POS_MOUSE)
        self.popup.show_all()

    def on_show_event(self, widget):
        self.eventbox.set_events(self.eventbox.get_events() | gtk.gdk.POINTER_MOTION_MASK )
        
    def on_motion_notify_event(self, widget, event):
        print "Motion notify called"
        self.popup.destroy()
        return True
    def destroy(self):
        if self.popup != None :
            self.popup.destroy()
        self.popup = None

if __name__ == '__main__':
    p = PreviewPopup('/home/danlyke/images/hpaa0051/HPIM0890.md.jpg')
    gtk.main()
