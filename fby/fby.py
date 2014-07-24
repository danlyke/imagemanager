import gtk
import gtk.glade
import new,types


class App :
    def __init__(self) :
	self.windows = []
    def register_window(self, window) :
        print "registering window", window
        if not window in self.windows :
            self.windows.append(window)

    def unregister_window(self, window) :
        print "unregistering window", window
        if window in self.windows :
            self.windows.remove(window)
            if len(self.windows) < 1 :
                gtk.main_quit()



class Window :
    def __init__(self, app, gladefile, windowname) :
        self.appmanager = app
        self.imageDatabase = app.imageDatabase
        self.appmanager.register_window(self)
        
        self.widgets=gtk.glade.XML (gladefile,windowname)
        callbacks = {}
        #find and store methods as bound callbacks

        for c in self.__class__.__bases__ :
            class_methods = c.__dict__
            for method_name in class_methods.keys():
                method = class_methods[method_name]
                if type(method) == types.FunctionType:
                    callbacks[method_name] = new.instancemethod(
                        method, self, self.__class__)
        
        class_methods = self.__class__.__dict__
        for method_name in class_methods.keys():
            method = class_methods[method_name]
            if type(method) == types.FunctionType:
                callbacks[method_name] = new.instancemethod(
                                         method, self, self.__class__)
        self.widgets.signal_autoconnect(callbacks)
        self.window = self.widgets.get_widget(windowname)
        self.window.connect('delete-event', self.on_window_delete_event);
        self.window.connect('destroy-event', self.on_window_destroy_event);
        
    def close(self):
        self.appmanager.unregister_window(self)


    def set_minimum_size(self, widget, width, height) :
        (w,h) = widget.get_size_request()
        print "Widget", widget, "is currently", w, h
        changed = False
        if width != None and w < width:
            w = width
            changed = True
        if height != None and h < height:
            h = height
            changed = True
        if changed :
            print "Widget", widget, "setting to", w, h
            widget.set_size_request(w,h)
        

    def popup_menu(self, event, menudef) :
        menu = gtk.Menu()
        for m in menudef :
            menuitem = gtk.MenuItem(m[0])
            if len(m) == 2 :
                menuitem.connect_object("activate", m[1], None)
            else :
                menuitem.connect_object("activate", m[1], m[2])
            menuitem.show()
            menu.append(menuitem)
        menu.popup(None,None,None,event.button,event.time)

    def on_window_delete_event(self, widget, event):
        self.close();
    def on_window_destroy_event(self, widget, event):
        self.close();
    



    class TreeSelectionList :
        def __init__(self) :
            self.selected_rows = []
            
        def callback(self, model, path, iter) :
            self.selected_rows.append(iter)

