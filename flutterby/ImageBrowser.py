import sys
import os

import gtk
import gtk.glade
import gobject

import ImageDatabase
import GeoLookup
import new, types
import TextViewRichEntry
import fby
import math
import time

class ImageBrowser(fby.Window):
    def __init__(self, appmgr, whereclause = None):
        """
        In this init we are going to display the main
        serverinfo window
        """
        gladefile="flutterby.glade"
        windowname="windowImageBrowser"
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
        self.imagelist = gtk.TreeStore(gtk.gdk.Pixbuf, str, gobject.TYPE_PYOBJECT, int)
        self.treeviewImageList = self.widgets.get_widget('treeviewImageList')
        self.treeviewImageList.set_model(self.imagelist)
        selection = self.treeviewImageList.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.on_treeviewImageList_selection_changed)
        self.enableTreeviewDragAndDrop(self.treeviewImageList)

        r = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('Image', r)
        col.set_attributes(r, pixbuf = 0)
        self.treeviewImageList.append_column(col)
        
        r = gtk.CellRendererText()
        r.connect('edited', self.renderer_editable_text_cell_edited)
        col = gtk.TreeViewColumn('Name', r)
        col.set_attributes(r, text = 1, editable = 3)
        self.treeviewImageList.append_column(col)

        self.imageDatabase.loadGTKListStore(self.imagelist, whereclause)

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
        
        return

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
                print sql, description_id[0], t
                cursor.execute(sql, t, description_id[0])
            descriptions.append(t)
        print "Looping through displayed images", time.time()
        for image in self.displayedImages :
            fields = {}
            print "Gathering fields", time.time()
            for (f, w) in self.databaseFieldsToControls :
                if w.get_editable() :
                    print "Setting", f, "to", w.get_text()
                    fields[f] = w.get_text()
            print "Calling update image", time.time()
            self.imageDatabase.updateImage(image, fields, descriptions)
        print "Done looping", time.time()
        self.imageDatabase.commit_write()
        print "Committed", time.time()


    
#####CALLBACKS

    def enableTreeviewDragAndDrop(self, treeview) :
        treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                          [('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK)
        treeview.connect("drag-data-get", self.on_treeview_drag_data_get)
    def on_treeview_drag_data_get(self,treeview, context, selection, info, timestamp):
        print "on_treeview_drag_data_get(",self,treeview, context, selection, info, timestamp,")"
        print selection.get_targets()
        selection.set(selection.target, 8,
                      '\n'.join([ image.get_thumbnail_filename() for image in self.displayedImages]))
        return

    def renderer_editable_text_cell_edited(self, renderer, path, newtext) :
        
        iter = self.imagelist.get_iter_from_string(path)
        self.imagelist.set(iter,1, newtext)
                          
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
    
            
    def on_treeviewImageList_selection_changed(self, widget) :
        self.updateCurrentImageData()

        # Now collate all selected imagesinto self.displayedImages
        
        selection = self.treeviewImageList.get_selection()
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
            return
        elif len(self.displayedImages) == 1 :
            self.displaySingleInstance = gtk.gdk.pixbuf_new_from_file(self.displayedImages[0].get_image_instances()[0].get_path())

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
                print "width,widest", width, widest
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
                print "Blanking",f
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
        print "Resizing to 1, ",self.tableImageDescription.get_property("n-columns")
        self.tableImageDescription.resize(1,
                self.tableImageDescription.get_property("n-columns"))

        sql = 'SELECT description_id,count(*) FROM imagedescription WHERE image_id IN (' \
              + ','.join([str(n['id']) for n in self.displayedImages]) \
              + ') GROUP BY description_id ORDER BY count(*)'
        cursor = self.imageDatabase.dbh.cursor()
        print sql
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


    def on_treeviewImageList_button_press_event(self, widget, event) :
        if event.button == 3 :
            pos = event.get_coords()
            (path, column, px, py) = widget.get_path_at_pos(int(pos[0]), int(pos[1]))
            print "click on", path
            return True
            
    def on_treeviewImageList_row_activated(self, widget, path, column):
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
    
    def on_windowImageBrowser_destroy_event(self, event):
        print "on_windowImageBrowser_destroy_event", self, event
