import gtk

class PreviewPopup :
    def __init__(self, filename, pos = None):
        self.popup = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.scroll = gtk.ScrolledWindow()

        self.table = gtk.Table(1,2,False)
        self.edits = []
        self.buttons = []

        self.add_row_to_table()

        self.table.resize(self.table.get_property("n-rows") + 1,
                            self.table.get_property("n-columns"))
        self.add_row_to_table()

        self.table.resize(self.table.get_property("n-rows") + 1,
                            self.table.get_property("n-columns"))
        self.add_row_to_table()

        self.table.resize(self.table.get_property("n-rows") + 1,
                            self.table.get_property("n-columns"))
        self.add_row_to_table()

        self.scroll.add_with_viewport(self.table)
        self.popup.add(self.scroll)

        self.popup.show_all()

    def add_row_to_table(self) :

        rows = self.table.get_property("n-rows")
        edit = gtk.TextView()
        button = gtk.Button("row " + str(rows))
        self.table.attach(button,
                          0, # guint left_attach,
                          1, # guint right_attach,
                          rows - 1, # guint top_attach,
                          rows, # guint bottom_attach,
                          0, # GtkAttachOptions xoptions,
                          0, # GtkAttachOptions yoptions,
                          gtk.SHRINK, # guint xpadding,
                          gtk.SHRINK); # guint ypadding);
        self.table.attach(edit,
                          1, # guint left_attach,
                          2, # guint right_attach,
                          rows - 1, # guint top_attach,
                          rows, # guint bottom_attach,
                          gtk.EXPAND | gtk.FILL, # GtkAttachOptions xoptions,
                          gtk.FILL, # GtkAttachOptions yoptions,
                          0, # guint xpadding,
                          0); # guint ypadding);
        self.buttons.append(button)
        self.edits.append(edit)

        

if __name__ == '__main__':
    p = PreviewPopup('/home/danlyke/images/cdsa0001/img_4501.sm.jpg')
    gtk.main()


