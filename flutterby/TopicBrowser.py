import sys
import os

import gtk
import gtk.glade
import gobject

import ImageDatabase
import GeoLookup
import new, types
import TextViewRichEntry
import BaseWindow
import math
import gc

class _TopicList :
    instance = None
    def __init__(self, imageDatabase):
        self.imageDatabase = imageDatabase
        self.topiclist = gtk.TreeStore(gtk.gdk.Pixbuf, str,
                                       gobject.TYPE_PYOBJECT, int, int)
        self.load_topic_tree()

    def renderer_editable_text_cell_topic_edited(self, renderer, path, newtext) :
        print "def renderer_editable_text_cell_edited(",self, renderer, path, newtext,") :"
        iter = self.topiclist.get_iter_from_string(path)
        if self.topiclist.get_value(iter,2).change_name(newtext) :
            self.topiclist.set(iter,1, newtext)

    def get_editable_from_path(self, path) :
        if path != None :
            iter = self.topiclist.get_iter(path)
            if self.topiclist.get_value(iter, 3) :
                return True
        return False
        

    def copy_images_for_topic_ids(self, oldid, newid) :
        cursor = self.imageDatabase.dbh.cursor()
        sql = 'SELECT parent_id, image_id, nextimage_id FROM topicimage WHERE parent_id=%s'
        cursor.execute(sql, oldid)
        rows = cursor.fetchall()
        for row in rows :
            sql = 'INSERT INTO topicimage(parent_id, image_id,nextimage_id) VALUES (%s,%s,%s)'
            cursor.execute(sql, newid, row[1],row[2])
        self.imageDatabase.commit_write()

    def copy_node_subtree(self, parentiter, parentid, dbid) :
        cursor = self.imageDatabase.dbh.cursor()
        if dbid == None:
            sql = 'SELECT id,name,name_changeable FROM topic WHERE parent_id IS NULL'
            cursor.execute(sql)
        else:
            sql = 'SELECT id,name,name_changeable FROM topic WHERE parent_id=%s'
            cursor.execute(sql, dbid)
            
        rows = cursor.fetchall()
        parentnode = None
        if parentiter != None :
            parentnode = self.topiclist.get_value(parentiter, 2)

        for row in rows:
            iter = self.topiclist.append(parentiter)
            self.topiclist.set(iter, 1, row[1])
            if row[2] :
                self.topiclist.set(iter, 3, 1)
            else :
                self.topiclist.set(iter, 3, 0)
            topicnode = self.imageDatabase.TopicNode(self.imageDatabase,
                                                            row[0],
                                                            parentnode,
                                                            row[1],row[2])
            self.topiclist.set(iter,2,topicnode)
            self.topiclist.set(iter, 4, topicnode.id)
            self.copy_node_subtree(iter, topicnode.id, row[0])
            self.copy_images_for_topic_ids(row[0],topicnode.id)
    def drop_at_path(self, path, selection) :
        if isinstance(selection.data, types.StringType) :
            parentiter = self.topiclist.get_iter(path)
            parentnode= self.topiclist.get_value(parentiter, 2)
            names = [n for n in selection.data.split("\n") if n != '' and n[:6] != 'topic:']
            for n in names :
                print "Dropped name ", n
            images = self.imageDatabase.find_images_from_names(names)
            parentnode.add_images(images)

            names = [n[6:] for n in selection.data.split("\n") if n != '' and n[:6] == 'topic:']
            cursor = self.imageDatabase.dbh.cursor()
            for name in names :
                sql = 'SELECT id,name,name_changeable FROM topic WHERE id=%s'
                cursor.execute(sql, name)
                rows = cursor.fetchall()
                for row in rows:
                    iter = self.topiclist.append(parentiter)
                    self.topiclist.set(iter, 1, row[1])
                    if row[2] :
                        self.topiclist.set(iter, 3, 1)
                    else :
                        self.topiclist.set(iter, 3, 0)
                    topicnode = self.imageDatabase.TopicNode(self.imageDatabase,
                                                             None,
                                                             parentnode,
                                                             row[1],row[2])
                    self.topiclist.set(iter,
                                       2,
                                       topicnode)
                    self.topiclist.set(iter, 4, topicnode.id)
                    self.copy_images_for_topic_ids(row[0],topicnode.id)
                    self.copy_images_for_topic_ids(row[0],topicnode.id)
        self.imageDatabase.commit_write()

    def get_db_id_at_iter(self,iter) :
        parent_id = self.topiclist.get_value(iter, 4)
        return parent_id
    def get_topicnode_at_iter(self,iter) :
        parent_id = self.topiclist.get_value(iter, 2)
        return parent_id
    def get_db_id_at_path(self,path) :
        iter = self.topiclist.get_iter(path)
        return self.get_db_id_at_iter(iter)

    def get_topicnode_at_path(self,path) :
        iter = self.topiclist.get_iter(path)
        return self.get_topicnode_at_iter(iter)
 
       
    def insert_new_topic_node_under_path(self, path) :
        parentiter = None
        parentnode = None
        if path != None :
            parentiter = self.topiclist.get_iter(path)
            parentnode = self.topiclist.get_value(parentiter, 2)
            
        iter = self.topiclist.append(parentiter)
        n = self.imageDatabase.TopicNode(self.imageDatabase, None,
                                         parentnode,
                                         'New Topic', True)
        self.topiclist.set(iter,1, 'New Topic')
        self.topiclist.set(iter, 2, n )
        self.topiclist.set(iter,3, True)
        self.topiclist.set(iter,4, n.id)
        
    def delete_topic_node_at_path(self, path) :
        if path != None :
            iter = self.topiclist.get_iter(path)
            if self.topiclist.get_value(iter,3) :
                node = self.topiclist.get_value(iter, 2)
                self.topiclist.remove(iter)
        
    def load_topic_tree(self, parentid = None, parentiter = None) :
        cursor = self.imageDatabase.dbh.cursor()
        if parentiter == None:
            sql = 'SELECT id,name,name_changeable FROM topic WHERE parent_id IS NULL'
            cursor.execute(sql)
        else:
            sql = 'SELECT id,name,name_changeable FROM topic WHERE parent_id=%s'
            cursor.execute(sql, parentid)
            
        rows = cursor.fetchall()
        parentnode = None
        if parentiter != None :
            parentnode = self.topiclist.get_value(parentiter, 2)

        for row in rows:
            iter = self.topiclist.append(parentiter)
            self.topiclist.set(iter, 1, row[1])
            if row[2] :
                self.topiclist.set(iter, 3, 1)
            else :
                self.topiclist.set(iter, 3, 0)
            self.topiclist.set(iter,
                               2,
                               self.imageDatabase.TopicNode(self.imageDatabase,
                                                            row[0],
                                                            parentnode,
                                                            row[1],row[2]))
            self.topiclist.set(iter, 4, row[0])
            self.load_topic_tree(row[0], iter)
        if parentid == None :
            self.imageDatabase.commit_read()



def TopicList(imageDatabase) :
    if _TopicList.instance == None:
        _TopicList.instance = _TopicList(imageDatabase)
    return _TopicList.instance
    

class TopicBrowser(BaseWindow.BaseWindow):
    def __init__(self, appmgr, whereclause = None):
        """
        In this init we are going to display the main
        serverinfo window
        """
        gladefile="flutterby.glade"
        windowname="windowTopicBrowser"
        BaseWindow.BaseWindow.__init__(self,appmgr, gladefile, windowname)

        self.treeviewTopicBrowser = self.widgets.get_widget('treeviewTopicBrowser')
        self.treeviewTopicImages = self.widgets.get_widget('treeviewTopicImages')

        self.imageDatabase = ImageDatabase.ImageDatabasePostgreSQL()

        self.topiclist = TopicList(self.imageDatabase)

        self.imagelist = gtk.ListStore(gtk.gdk.Pixbuf, str, gobject.TYPE_PYOBJECT, int)
        self.imageorder_idtonext = {}
        self.imageorder_idtoprev = {}

        self.treeviewTopicImages = self.widgets.get_widget('treeviewTopicImages')
        self.treeviewTopicBrowser = self.widgets.get_widget('treeviewTopicBrowser')

        self.treeviewTopicBrowser.set_model(self.topiclist.topiclist)
        self.treeviewTopicImages.set_model(self.imagelist)
        self.activeTopic = None
        selection = self.treeviewTopicBrowser.get_selection()
        selection.connect('changed', self.on_treeviewTopicBrowser_selection_changed)


        selection = self.treeviewTopicImages.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)

        r = gtk.CellRendererText()
        r.connect('edited', self.topiclist.renderer_editable_text_cell_topic_edited)
        col = gtk.TreeViewColumn('Name', r)
        col.set_attributes(r, text = 1, editable = 3)
        self.treeviewTopicBrowser.append_column(col)


        r = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('Image', r)
        col.set_attributes(r, pixbuf = 0)
        self.treeviewTopicImages.append_column(col)
        r = gtk.CellRendererText()
        #r.connect('edited', self.renderer_editable_text_cell_edited)
        col = gtk.TreeViewColumn('Name', r)
        col.set_attributes(r, text = 1, editable = 3)
        self.treeviewTopicImages.append_column(col)
        
        self.enableTopicBrowserTreeviewDragAndDrop(self.treeviewTopicBrowser)
        self.enableImageListTreeviewDragAndDrop(self.treeviewTopicImages)


    def enableTopicBrowserTreeviewDragAndDrop(self, treeview) :
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

    def on_treeviewTopicBrowser_drag_begin(self, drawingarea, context):
        print "    def on_treeviewTopicBrowser_drag_begin(",self, drawingarea, context,"):"

        pass
    def on_treeviewTopicBrowser_drag_data_delete(self,a,b):
        print "    def on_treeviewTopicBrowser_drag_data_delete(",self,a,b,"):"

        pass
    def on_treeviewTopicBrowser_drag_data_get(self, drawingarea, context, selection, info, time):
        print "    def on_treeviewTopicBrowser_drag_data_get(",self, drawingarea, context, selection, info, time,"):"
        sel = self.treeviewTopicBrowser.get_selection()
        selectionlist = self.TreeSelectionList()
        sel.selected_foreach(selectionlist.callback)
        selstring = '\n'.join(['topic:' + str(self.topiclist.topiclist.get_value(iter, 2).id)
                               for iter in selectionlist.selected_rows])
        selection.set(selection.target, 8, selstring) 

    def on_treeviewTopicBrowser_drag_data_received(self, treeview, context, x, y,
                                                selection, info, timestamp):
        print "    def on_treeviewTopicBrowser_drag_data_received(",self, treeview, context, x, y,  selection, info, timestamp,"):"

        r = self.treeviewTopicBrowser.get_dest_row_at_pos(x,y)
        print "Path at ", r
        if r != None :
            (path, relative) = r
            self.topiclist.drop_at_path(path, selection)

        pass
    def on_treeviewTopicBrowser_drag_drop(self, drawingarea, context, selection, info, time):
        print "    def on_treeviewTopicBrowser_drag_drop(",self, drawingarea, context, selection, info, time,"):"

        pass
    def on_treeviewTopicBrowser_drag_end(self, drawingarea, context):
        print "    def on_treeviewTopicBrowser_drag_end(",self, drawingarea, context,"):"

        pass
    def on_treeviewTopicBrowser_drag_leave(self,a,b,c):
        print "    def on_treeviewTopicBrowser_drag_leave(",self,a,b,c,"):"

        pass
    def on_treeviewTopicBrowser_drag_motion(self, drawingarea, context, selection, info, time):
        print "    def on_treeviewTopicBrowser_drag_motion(",self, drawingarea, context, selection, info, time,"):"

        pass
    def on_treeviewTopicImages_drag_begin(self, drawingarea, context):
        print "    def on_treeviewTopicImages_drag_begin(",self, drawingarea, context,"):"

        pass
    def on_treeviewTopicImages_drag_data_delete(self,a,b):
        print "!!!!!! def on_treeviewTopicImages_drag_data_deleteo(",self,a,b,"): !!!!!!"
        pass
    def on_treeviewTopicImages_drag_data_get(self, drawingarea, context, selection, info, time):
        print "    def on_treeviewTopicImages_drag_data_get(",self, drawingarea, context, selection, info, time,"):"
        sel = self.treeviewTopicImages.get_selection()
        self.displayedImages = []
        selectionlist = self.TreeSelectionList()
        sel.selected_foreach(selectionlist.callback)

        selstring = '\n'.join([self.imagelist.get_value(iter, 2).get_thumbnail_filename()
                               for iter in selectionlist.selected_rows])
        print "Selected: ", selstring
        selection.set(selection.target, 8,selstring)
        
    def on_treeviewTopicImages_drag_data_received(self, treeview, context, x, y,
                                                selection, info, timestamp):
        print "def on_treeviewTopicImages_drag_data_received(",self, treeview, context, x, y,  selection, info, timestamp,"):"
        r = self.treeviewTopicImages.get_dest_row_at_pos(x,y)
        print "Dest at pos", r
        if r != None :
            (path, relative) = r
            print "Got path", path
            if isinstance(selection.data, types.StringType) :
                parentiter = self.imagelist.get_iter(path)
                previmage= self.imagelist.get_value(parentiter, 2)
                names = [n for n in selection.data.split("\n") if n != '' and n[:6] != 'topic:']
                for n in names :
                    print "Dropped name ", n
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

    def on_treeviewTopicImages_drag_drop(self, drawingarea, context, selection, info, time):
        print "    def on_treeviewTopicImages_drag_drop(",self, drawingarea, context, selection, info, time,"):"

        pass
    def on_treeviewTopicImages_drag_end(self, drawingarea, context):
        print "    def on_treeviewTopicImages_drag_end(",self, drawingarea, context,"):"

        pass
    def on_treeviewTopicImages_drag_leave(self,a,b,c):
        print "    def on_treeviewTopicImages_drag_leave(",self,a,b,c,"):"

        pass
    def on_treeviewTopicImages_drag_motion(self,drawingarea,context,selection,info,time):
        print "    def on_treeviewTopicImages_drag_motion(",self,drawingarea,context,selection,info,time,"):"

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
                

    def browse_topic_node_under_path(self, path) :
        parentiter = None
        parentnode = None
        if path != None :
            parentiter = self.topiclist.topiclist.get_iter(path)
            self.appmanager.new_image_browser('id IN (SELECT image_id FROM topicimage WHERE parent_id=%s)' %
                                              self.topiclist.get_db_id_at_iter(parentiter))
        
    def slideshow_topic_node_under_path(self, path) :
        parentiter = None
        parentnode = None
        if path != None :
            parentiter = self.topiclist.topiclist.get_iter(path)
            self.appmanager.new_image_browser('id IN (SELECT image_id FROM topicimage WHERE parent_id=%s)' %
                                              self.topiclist.get_db_id_at_iter(parentiter))
        
    def on_treeviewTopicBrowser_button_press_event(self, widget, event):
        if event.button == 3 :
            pos = event.get_coords()
            r = widget.get_path_at_pos(int(pos[0]),int(pos[1]))
            menucontents = []
            if r != None :
                (path, column,x,y) = r
                menucontents.append(('New', self.topiclist.insert_new_topic_node_under_path, path))
                menucontents.append(('Browse', self.browse_topic_node_under_path, path))
                if self.topiclist.get_editable_from_path(path) :
                    menucontents.append(('Delete', self.topiclist.delete_topic_node_at_path, path))
            else :
                menucontents.append(('New', self.topiclist.insert_new_topic_node_under_path))

            if len(menucontents) > 0 :
                self.popup_menu(event,menucontents)
            return True
        else :
            return False

    def on_treeviewTopicImages_button_press_event(self, widget, event):
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
        self.appmanager.new_topic_browser()
    def on_people4_activate(self, menuitem):
        self.appmanager.new_subject_browser('person')
    def on_places4_activate(self, menuitem):
        self.appmanager.new_subject_browser('place')
    def on_things4_activate(self, menuitem):
        self.appmanager.new_subject_browser('thing')
    def on_events4_activate(self, menuitem):
        self.appmanager.new_subject_browser('event')
    
    def on_treeviewTopicBrowser_row_activated(self,widget,path,column):
        self.browse_topic_node_under_path(path)
        pass
    
    def on_treeviewTopicBrowser_selection_changed(self, widget):
        if self.activeTopic != None :
            previmage = None
            iter = self.imagelist.get_iter_first()
            images = []
            while iter :
                image = self.imagelist.get_value(iter, 2)
                images.append(image)
                iter = self.imagelist.iter_next(iter)

            self.activeTopic.add_images(images)

        selection = self.treeviewTopicBrowser.get_selection()
        selectionlist = self.TreeSelectionList()
        selection.selected_foreach(selectionlist.callback)

        if len(selectionlist.selected_rows) > 0 :
            topic = self.topiclist.get_topicnode_at_iter(selectionlist.selected_rows[0])
            if topic != self.activeTopic :
                self.imagelist.clear()
                self.imageorder_idtonext = {}
                self.imageorder_idtoprev = {}
                self.activeTopic = topic
                parent_id = self.topiclist.get_db_id_at_iter(selectionlist.selected_rows[0])
                self.imageDatabase.loadGTKListStore(self.imagelist,
                                                    'id IN (SELECT image_id FROM topicimage WHERE parent_id=%s)' %
                                                    str(parent_id))
                cursor = self.imageDatabase.dbh.cursor()
                cursor.execute('SELECT image_id, nextimage_id FROM topicimage WHERE parent_id=%s',
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
                gtk.timeout_add(5,self.load_preview_images);
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
