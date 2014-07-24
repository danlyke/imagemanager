# s/treeviewAlbumImages/treeviewAlbumImages/


import sys
import os
import time

import gtk
import gtk.glade
import gobject

import GeoLookup
import new, types
import TextViewRichEntry
import fby
import math
import gc
from xml.dom import minidom
import ImageDatabase

    

class AlbumBrowser(fby.Window):
    def __init__(self, appmgr, cursorwhere = None):
        """
        In this init we are going to display the main
        serverinfo window
        """
        gladefile="flutterby.glade"
        windowname="windowAlbumBrowser"
        fby.Window.__init__(self,appmgr, gladefile, windowname)

        self.entryImageDate = self.widgets.get_widget('entryImageDate')
        self.entryImageTech = self.widgets.get_widget('entryImageTech')
        self.entryImageDescriptionDetail = self.widgets.get_widget('entryImageDescriptionDetail')
        self.entryImageCameraLongitude = self.widgets.get_widget('entryImageCameraLongitude')
        self.entryImageCameraLattitude = self.widgets.get_widget('entryImageCameraLattitude')
        self.entryImageCameraAccuracy = self.widgets.get_widget('entryImageCameraAccuracy')
        self.entryImageSubjectLongitude = self.widgets.get_widget('entryImageSubjectLongitude')
        self.entryImageSubjectLattitude = self.widgets.get_widget('entryImageSubjectLattitude')
        self.entryImageSubjectAccuracy = self.widgets.get_widget('entryImageSubjectAccuracy')
        self.tableImageDescription = self.widgets.get_widget('tableImageDescription')

        self.drawingareaImage = self.widgets.get_widget('drawingareaImage')
        self.drawingareaImage.image_rows = 0
        self.drawingareaImage.image_columns = 0
        self.drawingareaImage.embedded_image_size = None
        self.drawingareaImage.embedded_image_list = None
        self.eventboxImage = self.widgets.get_widget('eventboxImage')
        self.scrolledwindowImage = self.widgets.get_widget('scrolledwindowImage')
        self.viewportImage = self.widgets.get_widget('viewportImage')
        self.optionmenuImageSize = self.widgets.get_widget('optionmenuImageSize')
        print "self.optionmenuImageSize", self.optionmenuImageSize
        self.togglebuttonImageDescriptionPerson = self.widgets.get_widget('togglebuttonImageDescriptionPerson')
        self.togglebuttonImageDescriptionPlace = self.widgets.get_widget('togglebuttonImageDescriptionPlace')
        self.togglebuttonImageDescriptionThing = self.widgets.get_widget('togglebuttonImageDescriptionThing')
        self.togglebuttonImageDescriptionEvent = self.widgets.get_widget('togglebuttonImageDescriptionEvent')

        self.textviewImageDescription = TextViewRichEntry.TextViewRichEntry(self.widgets.get_widget('textviewImageDescription'))
        self.entryImageTitle = self.widgets.get_widget('entryImageTitle')
        self.displaySingleInstance = None

        self.currentTextview = self.textviewImageDescription

        self.treeviewAlbumBrowser = self.widgets.get_widget('treeviewAlbumBrowser')
        self.treeviewAlbumImages = self.widgets.get_widget('treeviewAlbumImages')


        self.hpanedFolderContent = self.widgets.get_widget('hpanedFolderContent')
        self.hpanedCenterContent = self.widgets.get_widget('hpanedCenterContent')

        self.hpanedCenterContent.set_position(100)
        self.hpanedFolderContent.set_position(100)
        
        self.albumlist = ImageDatabase.AlbumList(self.imageDatabase)

        self.imagelist = gtk.ListStore(gtk.gdk.Pixbuf, str, gobject.TYPE_PYOBJECT, int)
        self.imageorder_idtonext = {}
        self.imageorder_idtoprev = {}

        self.treeviewAlbumImages = self.widgets.get_widget('treeviewAlbumImages')
        self.treeviewAlbumBrowser = self.widgets.get_widget('treeviewAlbumBrowser')

        self.treeviewAlbumBrowser.set_model(self.albumlist.albumlist)
        self.treeviewAlbumImages.set_model(self.imagelist)
        self.activeAlbum = None
        selection = self.treeviewAlbumBrowser.get_selection()
        selection.connect('changed', self.on_treeviewAlbumBrowser_selection_changed)


        selection = self.treeviewAlbumImages.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)

        rp = gtk.CellRendererPixbuf()
        r = gtk.CellRendererText()
        r.connect('edited', self.albumlist.renderer_editable_text_cell_album_edited)
        col = gtk.TreeViewColumn('Name')
        col.pack_start(rp, False)
        col.set_attributes(rp, pixbuf = 0)
        col.pack_start(r, False)
        col.set_attributes(r, text = 1, editable = 3)
        self.treeviewAlbumBrowser.append_column(col)
        selection.connect('changed', self.on_treeviewAlbumImages_selection_changed)
        self.enableTreeviewDragAndDrop(self.treeviewAlbumImages)


        r = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('Image', r)
        col.set_attributes(r, pixbuf = 0)
        self.treeviewAlbumImages.append_column(col)
        r = gtk.CellRendererText()
        #r.connect('edited', self.renderer_editable_text_cell_edited)
        col = gtk.TreeViewColumn('Name', r)
        col.set_attributes(r, text = 1, editable = 3)
        self.treeviewAlbumImages.append_column(col)
        
        self.enableAlbumBrowserTreeviewDragAndDrop(self.treeviewAlbumBrowser)
        self.enableImageListTreeviewDragAndDrop(self.treeviewAlbumImages)

        self.displayedImages = []
        self.displayedDescriptions = []
        self.manipulatingToggleButtonStates = False

        self.databaseFieldsToControls = (
            ('taken', self.entryImageDate),
            ('technotes', self.entryImageTech),
            ('camera_longitude', self.entryImageCameraLongitude),
            ('camera_lattitude', self.entryImageCameraLattitude),
            ('camera_position_accuracy', self.entryImageCameraAccuracy),
            ('subject_longitude', self.entryImageSubjectLongitude),
            ('subject_lattitude', self.entryImageSubjectLattitude),
            ('subject_position_accuracy', self.entryImageSubjectAccuracy),
            ('description', self.textviewImageDescription),
            ('title', self.entryImageTitle),
            )

        self.spacing = 10
        self.display_thumbnails = {}

        if cursorwhere != None :
            (album_id, image) = cursorwhere
            idstack = []
            cursor = self.imageDatabase.dbh.cursor()
            sql = 'SELECT parent_id FROM album WHERE id=%s'
            cursor.execute(sql, album_id)
            row = cursor.fetchone()
            while row and album_id:
                idstack.append(album_id)
                album_id = row[0]
                cursor.execute(sql, album_id)
                row = cursor.fetchone()

            parentiter = None
            idstack.reverse()
            for album_id in idstack :
                n = self.albumlist.iter_n_children(parentiter)
                for i in range(n) :
                    iter = self.albumlist.iter_nth_child(parentiter, i)
                    albumnode = self.albumlist.get(iter, 2)[0]
                    if albumnode.id == album_id :
                        parentiter = iter
                        path = self.albumlist.get_path(iter)
                        self.treeviewAlbumBrowser.expand_to_path(path)
                        break
                    
            selection = self.treeviewAlbumBrowser.get_selection()
            selection.select_path(path)
            for i in range(self.imagelist.iter_n_children(None)) :
                iter = self.imagelist.iter_nth_child(None, i)
                if self.imagelist.get_value(iter,2)['id'] == image['id'] :
                    selection = self.treeviewAlbumImages.get_selection()
                    path = self.imagelist.get_path(iter)
                    selection.select_path(path)

    def enableAlbumBrowserTreeviewDragAndDrop(self, treeview) :
        treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                          [('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_MOVE)
        treeview.enable_model_drag_dest([('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_MOVE)

    def enableImageListTreeviewDragAndDrop(self, treeview) :
        treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                          [('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_LINK)
        treeview.enable_model_drag_dest([('text/plain', 0, 0)],
                                        gtk.gdk.ACTION_LINK)

    def on_treeviewAlbumBrowser_drag_begin(self, drawingarea, context):
        print "--> on_treeviewAlbumBrowser_drag_begin(",self, drawingarea, context,"):"

        pass
    def on_treeviewAlbumBrowser_drag_data_delete(self,a,b):
        print "--> on_treeviewAlbumBrowser_drag_data_delete(",self,a,b,"):"

        pass
    def on_treeviewAlbumBrowser_drag_data_get(self, drawingarea, context, selection, info, time):
        print "--> on_treeviewAlbumBrowser_drag_data_get(",self, drawingarea, context, selection, info, time,"):"
        sel = self.treeviewAlbumBrowser.get_selection()
        selectionlist = self.TreeSelectionList()
        sel.selected_foreach(selectionlist.callback)
        selstring = '\n'.join(['album:' + str(self.albumlist.get_value(iter, 2).id)
                               for iter in selectionlist.selected_rows])
        selection.set(selection.target, 8, selstring) 

    def on_treeviewAlbumBrowser_drag_data_received(self, treeview, context, x, y,
                                                selection, info, timestamp):
        print "--> on_treeviewAlbumBrowser_drag_data_received(",self, treeview, context, x, y,  selection, info, timestamp,"):"

        r = self.treeviewAlbumBrowser.get_dest_row_at_pos(x,y)
        print "Path at ", r
        if r != None :
            (path, relative) = r
            self.albumlist.drop_at_path(path, selection)

        pass
    def on_treeviewAlbumBrowser_drag_drop(self, drawingarea, context, selection, info, time):
        print "--> on_treeviewAlbumBrowser_drag_drop(",self, drawingarea, context, selection, info, time,"):"

        pass
    def on_treeviewAlbumBrowser_drag_end(self, drawingarea, context):
        print "--> on_treeviewAlbumBrowser_drag_end(",self, drawingarea, context,"):"

        pass
    def on_treeviewAlbumBrowser_drag_leave(self,a,b,c):
#        print "--> on_treeviewAlbumBrowser_drag_leave(",self,a,b,c,"):"

        pass
    def on_treeviewAlbumBrowser_drag_motion(self, drawingarea, context, selection, info, time):
#        print "--> on_treeviewAlbumBrowser_drag_motion(",self, drawingarea, context, selection, info, time,"):"

        pass
    def on_treeviewAlbumImages_drag_begin(self, drawingarea, context):
        print "--> on_treeviewAlbumImages_drag_begin(",self, drawingarea, context,"):"

        pass
    def on_treeviewAlbumImages_drag_data_delete(self,a,b):
        print "!!!!!! def on_treeviewAlbumImages_drag_data_deleteo(",self,a,b,"): !!!!!!"
        pass
    def on_treeviewAlbumImages_drag_data_get(self, drawingarea, context, selection, info, time):
        print "--> on_treeviewAlbumImages_drag_data_get(",self, drawingarea, context, selection, info, time,"):"
        sel = self.treeviewAlbumImages.get_selection()
        self.displayedImages = []
        selectionlist = self.TreeSelectionList()
        sel.selected_foreach(selectionlist.callback)

        selstring = '\n'.join([self.imagelist.get_value(iter, 2).get_thumbnail_filename()
                               for iter in selectionlist.selected_rows])
        print "Selected: ", selstring
        selection.set(selection.target, 8,selstring)
        
    def on_treeviewAlbumImages_drag_data_received(self, treeview, context, x, y,
                                                selection, info, timestamp):
        print "def on_treeviewAlbumImages_drag_data_received(",self, treeview, context, x, y,  selection, info, timestamp,"):"
        r = self.treeviewAlbumImages.get_dest_row_at_pos(x,y)
        if r != None :
            (path, relative) = r
            if isinstance(selection.data, types.StringType) :
                parentiter = self.imagelist.get_iter(path)
                previmage= self.imagelist.get_value(parentiter, 2)
                names = [n for n in selection.data.split("\n") if n != '' and n[:6] != 'album:']
                if len(names) > 0 :
                    firstimage = self.imageDatabase.find_images_from_names(names[:1])[0]
                    images = [firstimage] + self.imageDatabase.find_images_from_names(names[1:])

                    imageids = [image['id'] for image in images]
                    print "IDs:", imageids
                    count = 0
                    iter = self.imagelist.get_iter_first()
                    while iter :
                        count = count + 1
                        image  = self.imagelist.get_value(iter, 2)
                        if str(image['id']) in imageids :
                            self.imagelist.remove(iter)
                        else :
                            iter = self.imagelist.iter_next(iter)

                    count = 0
                    iter = self.imagelist.get_iter_first()
                    while iter :
                        count = count + 1
                        iter = self.imagelist.iter_next(iter)

                    reorderlist = range(count)
                    count = 0
                    for image in images :
                        iter = self.imagelist.append(None)
                        #print "Appended iter"
                        #self.imagelist.move_after(iter, parentiter)
                        #print "at position", inspos
                        #inspos = inspos + 1
                        count = count + 1
                        print "Got filename", image.get_thumbnail_filename()
                        icon = gtk.gdk.pixbuf_new_from_file(image.get_thumbnail_filename())
                        self.imagelist.set(iter, 0, icon)
                        self.imagelist.set(iter, 1, image['basename'])
                        self.imagelist.set(iter, 2, image)
                        self.imagelist.set(iter, 3, True)

                    newlist = [n + len(reorderlist) for n in range(count)]
                    reorderlist = reorderlist[:path[0]] + newlist + reorderlist[path[0]:]
                    self.imagelist.reorder(reorderlist)
        pass

    def on_treeviewAlbumImages_drag_drop(self, drawingarea, context, selection, info, time):
        print "--> on_treeviewAlbumImages_drag_drop(",self, drawingarea, context, selection, info, time,"):"

        pass
    def on_treeviewAlbumImages_drag_end(self, drawingarea, context):
        print "--> on_treeviewAlbumImages_drag_end(",self, drawingarea, context,"):"

        pass
    def on_treeviewAlbumImages_drag_leave(self,a,b,c):
#        print "--> on_treeviewAlbumImages_drag_leave(",self,a,b,c,"):"

        pass
    def on_treeviewAlbumImages_drag_motion(self,drawingarea,context,selection,info,time):
#        print "--> on_treeviewAlbumImages_drag_motion(",self,drawingarea,context,selection,info,time,"):"

        pass


                                        


    def load_preview_images(self) :
        iter = self.imagelist.get_iter_first()
        while iter :
            icon = self.imagelist.get_value(iter, 0)
            if icon == None:
                image = self.imagelist.get_value(iter, 2)
                icon = gtk.gdk.pixbuf_new_from_file(image.get_thumbnail_filename())
                self.imagelist.set(iter, 0, icon)
                return True
            iter = self.imagelist.iter_next(iter)
        return False
                

    def on_treeviewAlbumBrowser_button_press_event(self, widget, event):
        if event.button == 3 :
            pos = event.get_coords()
            r = widget.get_path_at_pos(int(pos[0]),int(pos[1]))
            menucontents = []
            if r != None :
                (path, column,x,y) = r
                menucontents.append(('New', self.albumlist.insert_new_album_node_under_path, path))
                iter = self.albumlist.get_iter(path)
                album = self.albumlist.get_album(iter)
                if album.get_deletable() :
                    menucontents.append(('Delete', self.albumlist.delete_album_node_at_path, path))
            else :
                menucontents.append(('New', self.albumlist.insert_new_album_node_under_path))
            if len(menucontents) > 0 :
                self.popup_menu(event,menucontents)
            return True
        else :
            return False

    def on_treeviewAlbumImages_button_press_event(self, widget, event):
        if event.button == 3 :
            pos = event.get_coords()
            r = widget.get_path_at_pos(int(pos[0]),int(pos[1]))
            if r != None :
                (path, column,x,y) = r
                iter = self.imagelist.get_iter(path)
                print "Got iter for", self.imagelist.get_value(iter, 1)

            menu = gtk.Menu()
            for t in ('New', 'Yo', 'Dude') :
                menuitem = gtk.MenuItem(t)
                menuitem.show()
                menu.append(menuitem)
            menu.popup(None,None,None,event.button,event.time)
            return True
        else :
            return False


    def on_map4_activate(self, menuitem) :
        pass
    def on_albums4_activate(self, menuitem):
        self.appmanager.new_album_browser()
    def on_people4_activate(self, menuitem):
        self.appmanager.new_subject_browser('person')
    def on_places4_activate(self, menuitem):
        self.appmanager.new_subject_browser('place')
    def on_things4_activate(self, menuitem):
        self.appmanager.new_subject_browser('thing')
    def on_events4_activate(self, menuitem):
        self.appmanager.new_subject_browser('event')
    
    def on_treeviewAlbumBrowser_row_activated(self,widget,path,column):
        self.browse_album_node_under_path(path)
        pass
    def on_treeviewAlbumBrowser_selection_changed(self, widget):
        if self.activeAlbum != None :
            previmage = None
            iter = self.imagelist.get_iter_first()
            images = []
            while iter :
                image = self.imagelist.get_value(iter, 2)
                images.append(image)
                iter = self.imagelist.iter_next(iter)

            self.activeAlbum.add_images(images)

        selection = self.treeviewAlbumImages.get_selection()
        selection.unselect_all()

        selection = self.treeviewAlbumBrowser.get_selection()
        selectionlist = self.TreeSelectionList()
        selection.selected_foreach(selectionlist.callback)

        if len(selectionlist.selected_rows) > 0 :
            album = self.albumlist.get_albumnode_at_iter(selectionlist.selected_rows[0])
            if album != self.activeAlbum :
                self.imagelist.clear()
                self.imageorder_idtonext = {}
                self.imageorder_idtoprev = {}
                self.activeAlbum = album
                parent_id = self.albumlist.get_db_id_at_iter(selectionlist.selected_rows[0])
                self.imageDatabase.loadGTKListStore(self.imagelist,
                                                    'id IN (SELECT image_id FROM albumimage WHERE parent_id=%s)' %
                                                    str(parent_id))
                cursor = self.imageDatabase.dbh.cursor()
                cursor.execute('SELECT image_id, nextimage_id FROM albumimage WHERE parent_id=%s',
                               parent_id)
                self.imageorder_idtonext = {}
                self.imageorder_idtoprev = {}
                rows = cursor.fetchall()
                for row in rows :
                    print "Ordering", row[0], "to", row[1]
                    self.imageorder_idtonext[str(row[0])] = str(row[1])
                    self.imageorder_idtoprev[str(row[1])] = str(row[0])
        
                self.set_image_order()
                gc.collect()
                print "Row loaded"
                gobject.timeout_add(5,self.load_preview_images);
        else :
            self.imagelist.clear()
            self.imageorder_idtonext = {}
            self.imageorder_idtoprev = {}

    def set_image_order(self) :
        ids = []
        reorder_ids = []
        sorted_ids = []
        first_ids = []
        iter = self.imagelist.get_iter_first()
        while iter :
            image = self.imagelist.get_value(iter,2)
            id = str(image['id'])
            ids.append(id)
            if self.imageorder_idtoprev.has_key(id) :
                sorted_ids.append(id)
            elif self.imageorder_idtonext.has_key(id) :
                first_ids.append(id)
            else:
                reorder_ids.append(id)
            iter = self.imagelist.iter_next(iter)

        if len(ids) == 0 :
            return
        

        # if first_ids has elements, then we've specified the order for something
        # here, so let's run through first_ids, then follow the chain and prepend
        # them to reorder_ids:
        
        for id in first_ids :
            print "Inserting",id,"at position 0"
            reorder_ids.insert(0,id)
            # Now follow the linked list as far as it goes
            previd = id
            nextid = self.imageorder_idtonext[id]
            while nextid in sorted_ids :
                print "Inserting", nextid, "at psotion",reorder_ids.index(previd)
                reorder_ids.insert(reorder_ids.index(previd),nextid)
                del sorted_ids[sorted_ids.index(nextid)]
                previd = nextid
                if not self.imageorder_idtonext.has_key(nextid) :
                    break
                nextid = self.imageorder_idtonext[nextid]

        # if there's anything left in sorted_ids, it's because we've
        # got some sort of loop
        
        while len(sorted_ids) > 0:
            previd = None
            nextid = sorted_ids[0]
            while nextid in sorted_ids :
                if None == previd :
                    print "Inserting", nextid, "at posizion 0 - leftover"
                    reorder_ids.insert(0,nextid)
                else:
                    print "Inserting", nextid, "at position", reorder_ids.index(previd), "- leftover"
                    reorder_ids.insert(reorder_ids.index(previd),nextid)
                del sorted_ids[sorted_ids.index(nextid)]
                previd = nextid
                if not self.imageorder_idtonext.has_key(nextid) :
                    break
                nextid = self.imageorder_idtonext[nextid]
        reorder_ids.reverse()

        for i in range(len(ids)) :
            print "reordering", reorder_ids[i],"from", ids[i], "to", i, "meaning", ids.index(reorder_ids[i])
            reorder_ids[i] = ids.index(reorder_ids[i])
        self.imagelist.reorder(reorder_ids)

################## New

    def find_rich_text_view_for_text_view(self, widget) :
        if isinstance(widget, TextViewRichEntry.TextViewRichEntry) :
            return widget
        if widget == self.textviewImageDescription.get_widget() :
            return self.textviewImageDescription
        for description_id in self.displayedDescriptions :
            if widget == description_id[2].get_widget() :
                return description_id[2]
        return None
        

    def updateCurrentImageData(self):
        descriptions = []
        for description_id in self.displayedDescriptions :
            t = description_id[2].get_text()
            if description_id[0] == None :
                if t != None and t != '' :
                    id = self.imageDatabase.insert_new_record('description',
                                                          {
                        'description' : t,
                        })
                    for image in self.displayedImages :
                        cursor = self.imageDatabase.dbh.cursor()
                        sql = 'INSERT INTO imagedescription(description_id, image_id) VALUES (%s,%s)'
                        cursor.execute(sql, id, image['id'])
                    self.imageDatabase.commit_write()
            else:
                cursor = self.imageDatabase.dbh.cursor()
                sql = 'UPDATE description SET description=%s WHERE id=%s'
                cursor.execute(sql, t, description_id[0])
            descriptions.append(t)
        for image in self.displayedImages :
            fields = {}
            for (f, w) in self.databaseFieldsToControls :
                if w.get_editable() :
                    fields[f] = w.get_text()
            self.imageDatabase.updateImage(image, fields, descriptions)
        self.imageDatabase.commit_write()


    
#####CALLBACKS

    def enableTreeviewDragAndDrop(self, treeview) :
        treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                          [('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK)
        #treeview.connect("drag-data-get", self.on_treeview_drag_data_get)
    def on_treeview_drag_data_get(self,treeview, context, selection, info, timestamp):
        print "on_treeview_drag_data_get(",self,treeview, context, selection, info, timestamp,")"
        print selection.get_targets()
        selection.set(selection.target, 8,
                      '\n'.join([ image.get_thumbnail_filename() for image in self.displayedImages]))
        return

    def renderer_editable_text_cell_edited(self, renderer, path, newtext) :
        
        iter = self.imagelist.get_iter_from_string(path)
        if newtext != None and newtext != '' :
            self.imagelist.set(iter,1, newtext)
            album = self.imagelist.get_album()
            album.set_name(newtext)
                          
    class PopupImageGroup :
        def __init__(self, window, whereclause) :
            self.window = window
            self.whereclause = whereclause
        def clicked(self, widget) :
            self.window.appmanager.new_image_browser(self.whereclause)


    def add_description(self, description_count,description_id, text) :
        self.tableImageDescription.resize(
            self.tableImageDescription.get_property("n-rows") + 2,
            self.tableImageDescription.get_property("n-columns"))
        rows = self.tableImageDescription.get_property("n-rows")
        edit = gtk.TextView()
        separator = gtk.HSeparator()

        if description_count == None :
            button = gtk.Button(str(len(self.displayedImages)) + " of " + str(len(self.displayedImages)))
        else :
            button = gtk.Button(str(len(self.displayedImages)) + " of " + str(description_count))
        if description_id[0] == None :
            buttonevent = self.PopupImageGroup(self,
                                               'id IN (SELECT image_id FROM imagedescription WHERE description_id='
                                               +str(description_id[0])
                                               +')')
        else :
            button = gtk.Button(str(len(self.displayedImages)) + " of " + str(description_count))
            buttonevent = self.PopupImageGroup(self,
                                               'id IN (SELECT image_id FROM imagedescription WHERE description_id='
                                               +str(description_id[0])
                                               +')')
        button.connect('clicked', buttonevent.clicked)
        self.tableImageDescription.attach(
            button,
            0, 				# guint left_attach,
            1, 				# guint right_attach,
            rows - 1, 			# guint top_attach,
            rows, 			# guint bottom_attach,
            0, 				# GtkAttachOptions xoptions,
            0, 				# GtkAttachOptions yoptions,
            gtk.SHRINK, 		# guint xpadding,
            gtk.SHRINK); 		# guint ypadding);
        self.tableImageDescription.attach(
            edit,
            1, # guint left_attach,
            2, # guint right_attach,
            rows - 1, # guint top_attach,
            rows, # guint bottom_attach,
            gtk.EXPAND | gtk.FILL, # GtkAttachOptions xoptions,
            gtk.FILL, # GtkAttachOptions yoptions,
            0, # guint xpadding,
            0); # guint ypadding);
        self.tableImageDescription.attach(
            separator,
            1, 				# guint left_attach,
            2, 				# guint right_attach,
            rows - 2, 			# guint top_attach,
            rows, 			# guint bottom_attach,
            gtk.EXPAND | gtk.FILL, 	# GtkAttachOptions xoptions,
            gtk.FILL, 			# GtkAttachOptions yoptions,
            0, 				# guint xpadding,
            0); 			# guint ypadding);
        description_id.append(button)
        edit.connect('move-cursor', self.on_textviewImageDescription_move_cursor)
        edit.connect('button-press-event', self.on_textviewImageDescription_button_press_event)
        edit.connect('button-release-event', self.on_textviewImageDescription_button_release_event)
        edit.connect('populate-popup', self.on_textviewImageDescription_populate_popup)
        edit.connect('popup-menu', self.on_textviewImageDescription_popup_menu)
        edit = TextViewRichEntry.TextViewRichEntry(edit)
        description_id.append(edit)
        description_id.append(separator)
        edit.set_text(text)
    
            
    def on_treeviewAlbumImages_selection_changed(self, widget) :
        print "Calling updateCurrentImageData", time.time()
        self.updateCurrentImageData()
        print "Called updateCurrentImageData", time.time()

        # Now collate all selected imagesinto self.displayedImages
        
        selection = self.treeviewAlbumImages.get_selection()
        self.displayedImages = []
        selectionlist = self.TreeSelectionList()
        selection.selected_foreach(selectionlist.callback)

        for iter in selectionlist.selected_rows :
            self.displayedImages.append(self.imagelist.get_value(iter, 2))

        for key in self.display_thumbnails.keys() :
            if not key in self.displayedImages :
                del self.display_thumbnails[key]

        self.displaySingleInstance = None
        if len(self.displayedImages) == 0 :
            print "Returning", time.time()
            return
        elif len(self.displayedImages) == 1 :
            self.displaySingleInstance = \
                gtk.gdk.pixbuf_new_from_file(self.displayedImages[0].get_image_instances()[0].get_path())

        # put all of the images into an array for drawing
        
        self.drawingareaImage.image_rows = int(math.sqrt(len(self.displayedImages)))
        self.drawingareaImage.image_columns = int(len(self.displayedImages) / self.drawingareaImage.image_rows)
        if len(self.displayedImages) % self.drawingareaImage.image_rows != 0 :
            self.drawingareaImage.image_columns = self.drawingareaImage.image_columns + 1
        
        print "Rows and columns: ", self.drawingareaImage.image_rows, self.drawingareaImage.image_columns
        x = 0
        y = 0
        widest = 0
        highest = 0
        width = 0
        height = 0
        
        for key in self.displayedImages :
            if not key in self.display_thumbnails :
                self.display_thumbnails[key] = gtk.gdk.pixbuf_new_from_file(key.get_thumbnail_filename())
            width = width + self.display_thumbnails[key].get_width()
            if highest < self.display_thumbnails[key].get_height() :
                highest = self.display_thumbnails[key].get_height()
            x = x + 1
            if x >= self.drawingareaImage.image_columns :
                if width > widest :
                    widest = width
                width = 0
                height = height + highest
                highest = 0
                print "Resetting, width is now ", widest, height
                x = 0
                y = y + 1
                
        if x != 0 :
            height = height + highest

        self.drawingareaImage.embedded_image_size = (widest + self.spacing * (self.drawingareaImage.image_columns + 1),
                                                     height + self.spacing * (self.drawingareaImage.image_rows + 1))

        self.drawingareaImage.set_size_request(self.drawingareaImage.embedded_image_size[0],
                                                      self.drawingareaImage.embedded_image_size[1])

        self.drawingareaImage.embedded_image_list = []

        x = 0
        y = 0
        width = self.spacing
        height = self.spacing
        highest = 0
        
        for key in self.displayedImages :
            self.drawingareaImage.embedded_image_list.append(
                ( width, height,
                  self.display_thumbnails[key].get_width(),
                  self.display_thumbnails[key].get_height(),
                  key
                  ))
            width = width + self.display_thumbnails[key].get_width() + self.spacing
            if highest < self.display_thumbnails[key].get_height() :
                highest = self.display_thumbnails[key].get_height()
            x = x + 1
            if x >= self.drawingareaImage.image_columns :
                height = height + highest + self.spacing
                highest = 0
                width = self.spacing
                x = 0
                y = y + 1

        vals = {}
        show = {}
        for image in self.displayedImages :
            image.reload()
            for (f, w) in self.databaseFieldsToControls :
                if vals.has_key(f) :
                    if vals[f] != image[f] :
                        show[f] = False
                else:
                    show[f] = True
                    vals[f] = image[f]
        for (f,w) in self.databaseFieldsToControls :
            if show[f] :
                w.set_text(vals[f])
            else:
                w.set_text('')
            w.set_sensitive(show[f])
            w.set_editable(show[f])

        self.setToolbuttonToggleStateFromBufferTags()

        menuSizes = gtk.Menu()
        if len(self.displayedImages) == 1:
            instances = self.displayedImages[0].get_image_instances()
            image = None
            for instance in instances:
                menuItem = gtk.MenuItem('%d' % instance.size[0] + ' x ' + ' %d' % instance.size[1])
                menuItem.connect_object("activate", self.on_optionmenuImageSize_size_change, instance)
                menuItem.show()
                menuSizes.append(menuItem)
            self.loadImageInstance(instances[0])
        else :
            menuItem = gtk.MenuItem('thumbs')
            menuItem.show()
            menuSizes.append(menuItem)
            


        for id in self.displayedDescriptions :
            id[3].destroy()
            id[2].destroy()
            id[1].destroy()
        self.tableImageDescription.resize(1,
                self.tableImageDescription.get_property("n-columns"))

        sql = 'SELECT description_id,count(*) FROM imagedescription WHERE image_id IN (' \
              + ','.join([str(n['id']) for n in self.displayedImages]) \
              + ') GROUP BY description_id ORDER BY count(*)'
        cursor = self.imageDatabase.dbh.cursor()
        cursor.execute(sql)
        self.displayedDescriptions = []
        row = cursor.fetchone()

        while row :
            if row[1] == len(self.displayedImages) :
                self.displayedDescriptions.append([row[0]])
            row = cursor.fetchone()

        show_empty_description = True
        for description_id in self.displayedDescriptions :
            sql = 'SELECT description FROM description WHERE id=%s'
            cursor.execute(sql, description_id[0])
            row = cursor.fetchone()
            text = row[0]
            if text == None :
                text = ''
            sql = 'SELECT COUNT(*) FROM imagedescription WHERE description_id=%s'
            cursor.execute(sql, description_id[0])
            row = cursor.fetchone()

            self.add_description(row[0],description_id, text)
            if len(self.displayedImages) == row[0] :
                show_empty_description = False
            
        if show_empty_description and len(self.displayedImages) > 1:
            description_id = [None]
            self.add_description(None, description_id, None)
            self.displayedDescriptions.append(description_id)
        
        self.tableImageDescription.show_all()
            
        self.optionmenuImageSize.set_menu(menuSizes)

        
     
    def  on_drawingareaImage_expose_event(self, widget, event) :
        drawableWindow = self.viewportImage.window
        windowsize = self.drawingareaImage.window.get_size()
        gc = gtk.gdk.GC(drawableWindow)

        pixmap = gtk.gdk.Pixmap(drawableWindow,
                                event.area.width, event.area.height,
                                drawableWindow.get_depth())
        color = self.viewportImage.get_style().bg[0]
        
        gc.set_rgb_fg_color(color)
        gc.set_rgb_bg_color(color)
        
        pixmap.draw_rectangle(gc, True, 0, 0, event.area.width, event.area.height)

        
        if len(self.displayedImages) == 1 and self.displaySingleInstance != None:
            pixmap.draw_pixbuf(gc, self.displaySingleInstance, 0,0,
                               self.spacing - event.area.x, self.spacing - event.area.y,
                               self.displaySingleInstance.get_width(),
                               self.displaySingleInstance.get_height(),
                               gtk.gdk.RGB_DITHER_NONE, 0, 0)
        else :
            x = 0
            y = 0
            width = self.spacing
            height = self.spacing
            highest = 0


            for key in self.displayedImages :
                if width < event.area.width + event.area.x \
                   and width + self.display_thumbnails[key].get_width() > event.area.x \
                   and height < event.area.height + event.area.y \
                   and height + self.display_thumbnails[key].get_height() > event.area.y :

                    pixmap.draw_pixbuf(gc, self.display_thumbnails[key],
                                       0,0,
                                       width - event.area.x, height - event.area.y,
                                       self.display_thumbnails[key].get_width(),
                                       self.display_thumbnails[key].get_height(),
                                       gtk.gdk.RGB_DITHER_NONE, 0, 0)

                width = width + self.display_thumbnails[key].get_width() + self.spacing
                if highest < self.display_thumbnails[key].get_height() :
                    highest = self.display_thumbnails[key].get_height()
                x = x + 1
                if x >= self.drawingareaImage.image_columns :
                    height = height + highest + self.spacing
                    highest = 0
                    width = self.spacing
                    x = 0
                    y = y + 1

        self.drawingareaImage.window.draw_drawable(gc, pixmap, 0,0,  event.area.x, event.area.y,
                                                   event.area.width, event.area.height)


    def populate_references_menu_popup(self, submenu, path) :
        sql = """SELECT album.name, album.id FROM album, albumimage WHERE albumimage.parent_id = album.id
        AND albumimage.image_id=%s"""
        iter = self.imagelist.get_iter(path)
        image = self.imagelist.get(iter, 2)[0]
        print "Got image", image
        image_id = image['id']
        cursor = self.imageDatabase.dbh.cursor()
        cursor.execute(sql, image_id)
        rows = cursor.fetchall()
        for row in rows :
            print "   Adding place", row
            t = '__'.join([x for x in row[0].split('_')])
            subItem = gtk.MenuItem(t)
            subItem.connect_object("activate", self.openAlbumWindowWithID, (row[1], image))
            subItem.show()
            submenu.append(subItem)

    def replaceLinks(self, arg):
        (name, link) = arg
        dlg = gtk.Dialog('Replace ' + name, self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                         (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                          gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        vbox = dlg.vbox

        label = gtk.Label(' '.join(('Replace all',name,'references to',link,'with:')))
        entry = gtk.Entry()
        entry.set_text(link)
        vbox.pack_start(label)
        vbox.pack_start(entry)
        entry.show()
        label.show()
        if gtk.RESPONSE_ACCEPT == dlg.run() :
            print "Doing replacement"
            for description_id in self.displayedDescriptions :
                description_id[2].replace_tag_name(name.lower(), link, entry.get_text())
            self.textviewImageDescription.replace_tag_name(name.lower, link, entry.get_text())
        dlg.destroy()

    def populate_change_link_menu_popup(self, menu, path) :
        selection = self.treeviewAlbumImages.get_selection()
        selectionlist = self.TreeSelectionList()
        selection.selected_foreach(selectionlist.callback)

        if selectionlist.selected_rows :
            sl = self.imageDatabase.FindSemanticLinks()
            for description_id in self.displayedDescriptions :
                t = description_id[2].get_text()
                xmldoc = minidom.parseString('<flutterby>'+t+'</flutterby>')
                sl.parse(xmldoc)
            t = self.textviewImageDescription.get_text()
            xmldoc = minidom.parseString('<flutterby>'+t+'</flutterby>')
            sl.parse(xmldoc)
            
            for n in self.imageDatabase.entityClasses  :
                links = sl.get_links(n.lower())
                if links :
                    classItem = gtk.MenuItem('Change ' + n)
                    classItem.show()
                    submenu = gtk.Menu()
                    classItem.set_submenu(submenu)
                    menu.append(classItem)
                    for link in links:
                        item = gtk.MenuItem(link)
                        item.show();
                        item.connect_object("activate", self.replaceLinks, (n, link))
                        submenu.append(item)
        else:
            pass
                            

    def on_treeviewAlbumImages_button_press_event(self, widget, event) :
        if event.button == 3 :
            pos = event.get_coords()
            (path, column, px, py) = widget.get_path_at_pos(int(pos[0]), int(pos[1]))
            print "Right click at ", path
            
            menu = gtk.Menu();
            placeItem = gtk.MenuItem("References");
            placeItem.show();
            submenu = gtk.Menu();
            placeItem.set_submenu(submenu)
            self.populate_references_menu_popup(submenu, path)
            menu.append(placeItem)

            self.populate_change_link_menu_popup(menu, path)

            placeItem = gtk.MenuItem("Export Metadata")
            placeItem.show();
            placeItem.connect_object("activate",self.exportMetadata, None)
            menu.append(placeItem)
                                     
            menu.popup(None, None, None, event.button, event.time)
            return True

    def exportMetadata(self, path):
        selection = self.treeviewAlbumImages.get_selection()
        selectionlist = self.TreeSelectionList()
        selection.selected_foreach(selectionlist.callback)

        xmldoc = minidom.Document()
        flutterbyelement = minidom.Element('flutterby')
        xmldoc.childNodes.append(flutterbyelement)
        albumelement = minidom.Element('album')
        flutterbyelement.childNodes.append(albumelement)

        for iter in selectionlist.selected_rows :
            imageelement = minidom.Element('image')
            image = self.imagelist.get(iter, 2)[0]
            for att in ('id',
                        'basename',
                        'title',
                        'taken',
                        'technotes',
                        'camera_longitude',
                        'camera_lattitude',
                        'camera_position_accuracy',
                        'subject_longitude',
                        'subject_lattitude',
                        'subject_position_accuracy') :
                if image.has_key(att) :
                    imageelement.setAttribute(att, image[att])
            if image.has_key('description') :
                desc = minidom.parseString('<flutterby>'
                                           +image['description']+'</flutterby>')
                for n in desc.childNodes :
                    imageelement.childNodes.append(n)
            sql = """SELECT imageinstance.width, imageinstance.height,
                    imageinstance.name, directory.path, directory.accesstype_id
                FROM imageinstance, directory
                WHERE imageinstance.image_id = %s
                    AND imageinstance.directory_id = directory.id"""
            cursor = self.imageDatabase.dbh.cursor()
            cursor.execute(sql, image['id'])
            rows = cursor.fetchall()
            self.imageDatabase.commit_read()
            for row in rows :
                instanceelement = minidom.Element('instance')
                instanceelement.setAttribute('width', str(row[0]))
                instanceelement.setAttribute('height', str(row[1]))
                instanceelement.setAttribute('name', row[2])
                instanceelement.setAttribute('path', row[3])
                instanceelement.setAttribute('accesstype', str(row[4]))
                imageelement.childNodes.append(instanceelement)
            albumelement.childNodes.append(imageelement)
                
        print xmldoc.toprettyxml()
        # xmldoc.writexml(sys.stdout)
        
    def openAlbumWindowWithID(self, cursorwhere) :
        AlbumBrowser(self.appmanager, cursorwhere)
        print "Open album window with id ", id

            
    def on_treeviewAlbumImages_row_activated(self, widget, path, column):
        return

    def on_optionmenuImageSize_size_change(self, instance):
        self.loadImageInstance(instance)
        
    def loadImageInstance(self, instance):
        self.displaySingleInstance = gtk.gdk.pixbuf_new_from_file(instance.get_path())
        self.drawingareaImage.set_size_request(self.spacing * 2 + self.displaySingleInstance.get_width(),
                                               self.spacing * 2 + self.displaySingleInstance.get_height())
        if self.drawingareaImage.window != None:
            windowsize = self.drawingareaImage.window.get_size()
            rect = gtk.gdk.Rectangle(0,0,windowsize[0],windowsize[1])
            self.drawingareaImage.window.invalidate_rect(rect, True)

        
        
    def on_buttonImageLocationLookup_clicked(self,widget):
        print "button clicked"


    def setToolbuttonToggleStateFromBufferTags(self):
        self.manipulatingToggleButtonStates = True
        if None != self.currentTextview and None != self.currentTextview.get_buffer() :
            mark = self.currentTextview.get_buffer().get_insert()
            iter = self.currentTextview.get_buffer().get_iter_at_mark(mark)
            tags = iter.get_tags()
            buttons = { 'person' : False, 'place' : False, 'thing' :False, 'event' : False }
            for tag in tags :
                if buttons.has_key(tag.name) :
                    buttons[tag.name] = True
            self.togglebuttonImageDescriptionPerson.set_active(buttons['person'])
            self.togglebuttonImageDescriptionPlace.set_active(buttons['place'])
            self.togglebuttonImageDescriptionThing.set_active(buttons['thing'])
            self.togglebuttonImageDescriptionEvent.set_active(buttons['event'])
            if tags :
                try:
                    self.entryImageDescriptionDetail.set_text(tags[-1].attrs['name'])
                except:
                    self.entryImageDescriptionDetail.set_text('')
            else:
                self.entryImageDescriptionDetail.set_text('')
        self.manipulatingToggleButtonStates = False

        

    def on_textviewImageDescription_move_cursor(self, widget, step, count, extend_selection) :
        print "Calling setToolbuttonToggleStateFromBufferTags from move_cursor"
        self.currentTextview = self.find_rich_text_view_for_text_view(widget)
        self.setToolbuttonToggleStateFromBufferTags()

    def on_textviewImageDescription_button_press_event(self, widget, event):
        print "Button press"
        self.currentTextview = self.find_rich_text_view_for_text_view(widget)
        #self.setToolbuttonToggleStateFromBufferTags()

    def on_textviewImageDescription_button_release_event(self, widget, event):
        print "Calling setToolbuttonToggleStateFromBufferTags from Button release"
        self.currentTextview = self.find_rich_text_view_for_text_view(widget)
        self.setToolbuttonToggleStateFromBufferTags()
        
    def on_textviewImageDescription_populate_popup(self, widget, menu):
        print self, widget, menu
        self.currentTextview = self.find_rich_text_view_for_text_view(widget)

        personItem = gtk.MenuItem("Person")
        placeItem = gtk.MenuItem("Place")
        thingItem = gtk.MenuItem("Thing")
        eventItem = gtk.MenuItem("Event")
        separator = gtk.SeparatorMenuItem()

        personItem.show()
        placeItem.show()
        thingItem.show()
        eventItem.show()
        separator.show()

        menu.insert(separator,0)
        menu.insert(personItem,0)
        menu.insert(placeItem,0)
        menu.insert(thingItem,0)
        menu.insert(eventItem,0)

        personItem.connect_object("activate", self.on_textviewImageDescription_popup_menu, "person")
        placeItem.connect_object("activate", self.on_textviewImageDescription_popup_menu, "place")
        thingItem.connect_object("activate", self.on_textviewImageDescription_popup_menu, "thing")
        eventItem.connect_object("activate", self.on_textviewImageDescription_popup_menu, "event")

    def lookupAddress(self, address):
        noGeographyInfo = True
        for w in (self.entryImageCameraLongitude,
                  self.entryImageCameraLattitude,
                  self.entryImageCameraAccuracy,
                  self.entryImageSubjectLongitude,
                  self.entryImageSubjectLattitude,
                  self.entryImageSubjectAccuracy) :
            if len(w.get_text()) > 0:
                noGeographyInfo = False
        if noGeographyInfo :
            lookup = GeoLookup.GeoLookup()
            (lon,lat,acc) =  lookup.lookupAddress(address)
            if lon != None :
                self.entryImageCameraLongitude.set_text("%f" % lon)
                self.entryImageSubjectLongitude.set_text("%f" % lon)
            if lat != None :
                self.entryImageCameraLattitude.set_text("%f" % lat)
                self.entryImageSubjectLattitude.set_text("%f" % lat)
            if acc != None :
                self.entryImageCameraAccuracy.set_text("%f" % acc)
                self.entryImageSubjectAccuracy.set_text("%f" % acc)

    def on_textviewImageDescription_popup_menu(self, tagType):
        tag = self.currentTextview.create_tag(tagType)
        tag.attrs['name'] = self.currentTextview.get_current_selection(tag);
        self.lookupAddress(tag.attrs['name'])

    def handleToggleButtonToggle(self, widget, name) :
        print "Handling toggle", widget, name, self.manipulatingToggleButtonStates
        if not self.manipulatingToggleButtonStates :
            if widget.get_active():
                tag = self.currentTextview.create_tag(name)
                tag.attrs['name'] = self.currentTextview.get_current_selection(tag);
                if 'place' == name :
                    self.lookupAddress(tag.attrs['name'])
            else:
                self.currentTextview.remove_tag(name)
            
    def on_togglebuttonImageDescriptionPerson_toggled(self, widget):
        self.handleToggleButtonToggle(widget, 'person')
        
    def on_togglebuttonImageDescriptionPlace_toggled(self, widget):
        self.handleToggleButtonToggle(widget,'place')

    def on_togglebuttonImageDescriptionThing_toggled(self, widget):
        self.handleToggleButtonToggle(widget,'thing')

    def on_togglebuttonImageDescriptionEvent_toggled(self, widget):
        self.handleToggleButtonToggle(widget,'event')

    def on_comboboxImageDisplaySize_changed(self, widget):
        pass

    def on_entryImageDescriptionDetail_focus_out_event(self, widget, event):
        print "on_entryImageDescriptionDetail_focus_out_event(",self, widget, event,"):"
        mark = self.currentTextview.get_buffer().get_insert()
        iter = self.currentTextview.get_buffer().get_iter_at_mark(mark)
        tags = iter.get_tags()
        if tags :
            tags[-1].attrs['name'] = widget.get_text()

    def on_map1_activate(self, menuitem) :
        pass
    def on_albums1_activate(self, menuitem):
        self.appmanager.new_album_browser()
    def on_people1_activate(self, menuitem):
        self.appmanager.new_subject_browser('person')
    def on_places1_activate(self, menuitem):
        self.appmanager.new_subject_browser('place')
    def on_things1_activate(self, menuitem):
        self.appmanager.new_subject_browser('thing')
    def on_events1_activate(self, menuitem):
        self.appmanager.new_subject_browser('event')

    def on_window_delete_event(self, widget, event):
        self.updateCurrentImageData()
        fby.Window.on_window_delete_event(self, widget, event)
        return
    def on_windowImageBrowser_destroy_event(self, widget, event):
        self.updateCurrentImageData()
        fby.Window.on_window_destroy_event(self, widget, event)
        return


    def eventboxImage_find_id(self, pos) :
        id = None
        for i in self.drawingareaImage.embedded_image_list :
            if pos[0] > i[0] and pos[0] < i[0]+i[2] \
               and pos[1] > i[1] and pos[1] < i[1]+i[3] :
                id = i[4]
                break
        return id
    
    def on_eventboxImage_button_press_event(self, widget, event):
        print "on_eventboxImage_button_press_event",self, widget, event.x, event.y
        print " id", self.eventboxImage_find_id((event.x, event.y))
        pass
    
    def on_eventboxImage_button_release_event(self, widget, event):
        print "on_eventboxImage_button_release_event",self, widget, event.x, event.y
        print " id", self.eventboxImage_find_id((event.x, event.y))
        pass

    def on_eventboxImage_motion_notify_event(self, widget, event):
        print "on_eventboxImage_motion_notify_event",self, widget, event.x, event.y
        print " id", self.eventboxImage_find_id((event.x, event.y))
        pass
        
