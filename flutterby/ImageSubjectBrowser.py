import sys
import os

import gtk
import gtk.glade
# from pyPgSQL import PgSQL
import ImageDatabase
import GeoLookup
import new, types
import TextViewRichEntry
import fby

import ImageBrowser

class ImageSubjectBrowser(fby.Window):
    def __init__(self, appmgr, subject):
        """a
        In this init we are going to display the main
        serverinfo window
        """
        gladefile="flutterby.glade"
        windowname="windowImageSubjectBrowser"
        fby.Window.__init__(self,appmgr, gladefile, windowname)

        self.dbh = PgSQL.connect("localhost::flutterby:danlyke:danlyke::")

        self.subject = subject
        self.subjectlist = gtk.TreeStore(gtk.gdk.Pixbuf, str, int)
        self.treeviewImageSubject = self.widgets.get_widget('treeviewImageSubject')
        self.treeviewImageSubject.set_model(self.subjectlist)

        r = gtk.CellRendererText()
        col = gtk.TreeViewColumn('Name', r)
        col.set_attributes(r, text = 1)
        self.treeviewImageSubject.append_column(col)

        self.imageDatabase = ImageDatabase.ImageDatabase()
        self.imageDatabase.LoadSubjectToGTKListStore(self.subjectlist, subject)
        
        return

    def on_treeviewImageSubject_row_activated(self, widget, path, column):
        iter = self.subjectlist.get_iter(path)
        print "Activated subject", self.subjectlist.get_value(iter, 2)
        self.appmanager.new_image_browser('id IN (SELECT image_id FROM '+self.subject
                                          +'image WHERE '+self.subject
                                          +("_id='%s'" % self.subjectlist.get_value(iter, 2))+')')

    
