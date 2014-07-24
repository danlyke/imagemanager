import sys
import os

import gtk
import gtk.glade
from pyPgSQL import PgSQL
import ImageDatabase
import GeoLookup
import new, types
import TextViewRichEntry
import fby
import PreviewPopup
import gc
import stat

class MapViewer(fby.Window) :
    class MapTransform :
        def __init__(self, drawable, scrollorigin, scale) :
            self.drawable = drawable
            self.scrollorigin = scrollorigin
            self.scale = scale

        def world_to_image(self, pos) :
            rpos = [None, None]
            for i in range(len(rpos)):
                rpos[i] = int((pos[i] - self.scrollorigin[i]) * self.scale)
            return rpos
        
    class MapPoint :
        def __init__(self, pos):
            self.pos = pos[:]
            self.geopos = [None, None]
            self.db_id = None

        def hit_test(self, hit, scale = 1.0):
            for i in range(len(hit)) :
                if abs(hit[i] - self.pos[i]) > 2 / scale :
                    return False
            else:
                return True
        def draw(self, transform, gc) :
            pos = transform.world_to_image(self.pos)
            transform.drawable.draw_rectangle(gc, False, pos[0] - 2, pos[1] - 2, 4,4)
        def draw_selected(self, transform, gc) :
            pos = transform.world_to_image(self.pos)
            transform.drawable.draw_rectangle(gc, False, pos[0] - 3, pos[1] - 3, 6,6)
        def classname(self) :
            return 'unknown';

        def store(self, imagedatabase, map_id):
            values = {
                    'map_id' : map_id,
                    'x' : self.pos[0],
                    'y' : self.pos[1],
                    'lon' : self.geopos[0],
                    'lat' : self.geopos[1],
                    }
            if self.db_id == None :
                self.db_id = imagedatabase.insert_new_record('mappoints_%s' % self.classname(),
                                                             values)
            else :
                imagedatabase.update_record('mappoints_%s' % self.classname,
                                            self.db_id, values)
    class MapPointReference(MapPoint) :
        def __init__(self, pos) :
            MapViewer.MapPoint.__init__(self, pos)
        def classname(self) :
            return 'reference'
        
    class MapPointPath(MapPoint) :
        def __init__(self, pos) :
            MapViewer.MapPoint.__init__(self, pos)
            self.nextinpath = None
        def draw(self, transform, gc) :
            pos = transform.world_to_image(self.pos)
            transform.drawable.draw_rectangle(gc, False, pos[0] - 2, pos[1] - 2, 4,4)
            if self.nextinpath != None :
                nextpos = transform.world_to_image(self.nextinpath.pos)
                transform.drawable.draw_line(gc, pos[0], pos[1], nextpos[0], nextpos[1])
        def classname(self) :
            return 'path'

        def store(self, imagedatabase, map_id):
            MapPoint.store(self, imagedatabase, map_id)
            dbh = imagedatabase.dbh
            cursor = dbh.cursor()
            sql = ('UPDATE mappoints_%s SET ' %self.classname()) \
                  + 'nextpoint_id=%s ' \
                  + 'WHERE id=%s'

            next_id = None
            if self.nextinpath != None :
                if self.nextinpath.db_id == None :
                    self.nextinpath.store(dbh, map_id)
                next_id = self.nextinpath.db_id
            cursor.execute(sql, next_id, self.db_id)

    class MapPointInterest(MapPoint):
        def __init__(self, pos) :
            MapViewer.MapPoint.__init__(self, pos)
        def classname(self) :
            return 'interest'

    class MapPointImage(MapPoint):
        def __init__(self, image, pos) :
            MapViewer.MapPoint.__init__(self, pos)
            self.image = image
            self.pixbuf = image['thumbnail']
            self.size = (self.pixbuf.get_width(),self.pixbuf.get_height())

        def hit_test(self, hit, scale = 1.0):
            for i in range(len(hit)) :
                if abs(hit[i] - self.pos[i]) > self.size[i] / (2 * scale) :
                    return False
            else:
                return True

        def draw(self, transform, gc) :
            pos = transform.world_to_image(self.pos)
            transform.drawable.draw_rectangle(gc, False,
                                              pos[0] - self.size[0] / 2 - 1,
                                              pos[1] - self.size[1] / 2 - 1,
                                              self.size[0] + 1,
                                              self.size[1] + 1)
            transform.drawable.draw_pixbuf(gc, self.pixbuf,
                                           0,0,
                                           int(pos[0] - self.size[0] / 2),
                                           int(pos[1] - self.size[1] / 2),
                                           self.size[0], self.size[1],
                                           gtk.gdk.RGB_DITHER_NONE, 0, 0)
        def draw_selected(self, transform, gc) :
            pos = transform.world_to_image(self.pos)
            transform.drawable.draw_rectangle(gc, False,
                                              pos[0] - self.size[0] / 2 - 2,
                                              pos[1] - self.size[1] / 2 - 2,
                                              self.size[0] + 2,
                                              self.size[1] + 2)
            
        def classname(self) :
            return 'image'
        def store(self, imagedatabase, map_id):
            values = {
                    'map_id' : map_id,
                    'x' : self.pos[0],
                    'y' : self.pos[1],
                    'lon' : self.geopos[0],
                    'lat' : self.geopos[1],
                    'image_id' : self.image['id'],
                    }
            if self.db_id == None :
                self.db_id = imagedatabase.insert_new_record('mappoints_%s' % self.classname(),
                                                             values)
            else :
                imagedatabase.update_record('mappoints_%s' % self.classname,
                                            self.db_id, values)
    def ReadDatabase(self):
        cursor = self.imageDatabase.dbh.cursor()
        cursor.execute('SELECT id,x,y,lon,lat FROM mappoints_reference')
        row = cursor.fetchone()
        while row :
            point = MapViewer.MapPointReference([row[1],row[2]])
            point.db_id = row[0]
            point.geopos = [row[3],row[4]]
            self.points.append(point)
            row = cursor.fetchone()
        
        cursor.execute('SELECT id,x,y,lon,lat FROM mappoints_interest')
        row = cursor.fetchone()
        while row :
            point = MapViewer.MapPointInterest([row[1],row[2]])
            point.db_id = row[0]
            point.geopos = [row[3],row[4]]
            self.points.append(point)
            row = cursor.fetchone()
        
        cursor.execute('SELECT id,x,y,lon,lat,image_id FROM mappoints_image')
        row = cursor.fetchone()
        while row :
            image = self.imageDatabase.Image(self.imageDatabase)
            image['id'] = row[5]
            point = MapViewer.MapPointImage(image,[row[1],row[2]])
            point.db_id = row[0]
            point.geopos = [row[3],row[4]]
            self.points.append(point)
            row = cursor.fetchone()
        
        cursor.execute('SELECT id,x,y,lon,lat,nextpoint_id FROM mappoints_path')
        pathpointids = {}
        row = cursor.fetchone()
        while row :
            point = MapViewer.MapPointPath([row[1],row[2]])
            point.db_id = row[0]
            point.geopos = [row[3],row[4]]
            pathpointids[point.db_id] = point
            self.nextinpath_id = row[5]
            self.points.append(point)
            row = cursor.fetchone()
        for point in self.points :
            if isinstance(point, MapViewer.MapPointPath) and point.nextinpath_id != None :
                point.nextinpath = pathpointids[point.nextinpath_id]
    
    def __init__(self, appmgr, whereclause = None):
        """
        In this init we are going to display the main
        serverinfo window
        """
        gladefile="flutterby.glade"
        windowname="windowMapViewer"
        fby.Window.__init__(self,appmgr, gladefile, windowname)
        self.subpixbufCache = None

      
        # we only have two callbacks to register, but
        # you could register any number, or use a
        # special class that automatically
        # registers all callbacks. If you wanted to pass
        # an argument, you would use a tuple like this:
        # dic = { "on button1_clicked" : 
        # (self.button1_clicked, arg1,arg2) , ...
    
        self.togglebuttonMapToolSelect = self.widgets.get_widget('togglebuttonMapToolSelect')
        self.togglebuttonMapToolRefPt = self.widgets.get_widget('togglebuttonMapToolRefPt')
        self.togglebuttonMapToolPath = self.widgets.get_widget('togglebuttonMapToolPath')
        self.togglebuttonMapToolInterest = self.widgets.get_widget('togglebuttonMapToolInterest')
        self.eventboxMap = self.widgets.get_widget('eventboxMap')
        self.drawingareaMap = self.widgets.get_widget('drawingareaMap')
        self.vscrollbarMap = self.widgets.get_widget('vscrollbarMap')
        self.hscrollbarMap = self.widgets.get_widget('hscrollbarMap')
        self.entryMapPositionLon = self.widgets.get_widget('entryMapPositionLon')
        self.entryMapPositionLat = self.widgets.get_widget('entryMapPositionLat')
        self.entryMapPositionX = self.widgets.get_widget('entryMapPositionX')
        self.entryMapPositionY = self.widgets.get_widget('entryMapPositionY')
        self.checkbuttonMapPositionLonLatMove = self.widgets.get_widget('checkbuttonMapPositionLonLatMove')
        self.checkbuttonMapPositionXYMove = self.widgets.get_widget('checkbuttonMapPositionXYMove')

        self.drawingareaMap.drag_dest_set(gtk.DEST_DEFAULT_ALL, [('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE | gtk.gdk.ACTION_LINK)
        self.drawingareaMap.connect("drag-data-received",
                                    self.on_drawingareaMap_drag_data_received_cb)
        self.drawingareaMap.connect("drag-data-get",
                                    self.on_drawingareaMap_drag_data_get_cb)
        self.drawingareaMap.connect("drag-begin",
                                    self.on_drawingareaMap_drag_begin_cb)
        self.drawingareaMap.connect("drag-motion",
                                    self.on_drawingareaMap_drag_motion_cb)
        self.drawingareaMap.connect("drag-drop",
                                    self.on_drawingareaMap_drag_drop_cb)
        self.drawingareaMap.connect("drag-end",
                                    self.on_drawingareaMap_drag_end_cb)

        self.eventboxMap.connect("drag-drop",
                                    self.on_eventboxMap_drag_drop_cb)
        self.eventboxMap.connect("drag-end",
                                    self.on_eventboxMap_drag_end_cb)

        self.eventboxMap.connect('realize', self.on_eventboxMap_show)
        self.lastPausedMouseTimeout = 0
        self.map_id = 1;
        self.pixbufBackground = gtk.gdk.pixbuf_new_from_file('/home/danlyke/geodata/c37122a1.png')
        self.scale = 1.0
        self.configureScrollbars()
        self.settingToolbuttonToggleStates = False
        self.points = []
        self.selectedpoints = []
        self.buttonpressDrag = None
        self.imageDatabase = ImageDatabase.ImageDatabase()
        self.ReadDatabase()
        
        
#####CALLBACKS


    def on_drawingareaMap_drag_data_get_cb(self, drawingarea, context, selection, info, time):
        print "def on_drawingareaMap_drag_data_get(",self, drawingarea, context, selection, info, time,"):"
    def on_drawingareaMap_drag_begin_cb(self, drawingarea, context, selection, info, time):
        print "def on_drawingareaMap_drag_begin(",self, drawingarea, context, selection, info, time,"):"
    def on_drawingareaMap_drag_motion_cb(self, drawingarea, context, selection, info, time):
        print "on_drawingareaMap_drag_motion_cb(",self, drawingarea, context, selection, info, time,"):"
        return True
    
    def on_drawingareaMap_drag_drop_cb(self, drawingarea, context, x,y, time):
        print "on_drawingareaMap_drag_drop_cb(",self, drawingarea, context, x,y, time,"):"
        if self.buttonpressDrag != None:
            origin = [self.hscrollbarMap.get_value(), self.vscrollbarMap.get_value()]
            hit = [x / self.scale + origin[0],
                   y / self.scale + origin[1]]
            for point in self.selectedpoints :
                for i in range(2) :
                    point.pos[i] = point.pos[i] + hit[i] - self.buttonpressDrag[i]
                    if self.checkbuttonMapPositionLonLatMove.get_active() \
                           and isinstance(point, MapViewer.MapPointImage):
                        point.geopos = self.get_LonLatFromXY(point.pos[0],point.pos[1])
            self.buttonpressDrag = None
            self.CheckSelectedPointsAndLabels()
            self.redraw_drawingareaMap()
        return True

    
    def on_drawingareaMap_drag_end_cb(self, drawingarea, context, selection, info, time):
        print "on_drawingareaMap_drag_end_cb(",self, drawingarea, context, selection, info, time,"):"
        return True

    def on_eventboxMap_drag_data_get_cb(self, eventbox, context, selection, info, time):
        print "def on_eventboxMap_drag_data_get(",self, eventbox, context, selection, info, time,"):"
    def on_eventboxMap_drag_begin_cb(self, eventbox, context, selection, info, time):
        print "def on_eventboxMap_drag_begin(",self, eventbox, context, selection, info, time,"):"
    def on_eventboxMap_drag_motion_cb(self, eventbox, context, selection, info, time):
        print "on_eventboxMap_drag_motion_cb(",self, eventbox, context, selection, info, time,"):"
        return True
    def on_eventboxMap_drag_drop_cb(self, eventbox, context, selection, info, time):
        print "on_eventboxMap_drag_drop_cb(",self, eventbox, context, selection, info, time,"):"
        return True
    def on_eventboxMap_drag_end_cb(self, a, b):
        print "on_eventboxMap_drag_end_cb(",self, a,b,"):"
        return True

    def on_drawingareaMap_drag_data_received_cb(self, drawingarea, context, x, y,
                                                selection, info, timestamp):
        print "on_drawingareaMap_drag_data_received_cb(",self, drawingarea, context, x, y,selection, info, timestamp,")"
        origin = [self.hscrollbarMap.get_value(), self.vscrollbarMap.get_value()]
        hit = [int(x / self.scale + origin[0]),
               int(y / self.scale + origin[1])]

        
        names = [n for n in selection.data.split("\n") if n != '']
        images = self.imageDatabase.find_images_from_names(names)
            
        for image in images:
            point = MapViewer.MapPointImage(image, hit)
            if self.checkbuttonMapPositionXYMove.get_active() \
               and image['subject_longitude'] != None and image['subject_longitude'] != '' \
               and image['subject_lattitude'] != None and image['subject_lattitude'] != '' :
                pos = self.get_XYFromLonLat([image['subject_longitude'],
                                             image['subject_lattitude']])
                if pos != None and pos[0] != None and pos[1] != None :
                    point.pos = pos
       
            elif self.checkbuttonMapPositionXYMove.get_active() \
               and image['camera_longitude'] != None and image['camera_longitude'] != '' \
               and image['camera_lattitude'] != None and image['camera_lattitude'] != '' :
                pos = self.get_XYFromLonLat([image['camera_longitude'],
                                             image['camera_lattitude']])
                if pos != None and pos[0] != None and pos[1] != None :
                    point.pos = pos
            
            elif self.checkbuttonMapPositionLonLatMove.get_active() :
                point.geopos = self.get_LonLatFromXY(hit)
            self.points.append(point)
        print "drag_data_received_cb(",self, drawingarea, context, x, y, selection, info, timestamp,")"
        print selection.data

    def on_drawingareaMap_show(self, widget):
        print "Setting eventbox pointer mask"
        self.eventboxMap.set_events(self.eventboxMap.get_events() | gtk.gdk.POINTER_MOTION_MASK )
        
    def on_eventboxMap_show(self, widget):
        print "Setting eventbox pointer mask"
        self.eventboxMap.set_events(self.eventboxMap.get_events() | gtk.gdk.POINTER_MOTION_MASK )

    def on_drawingareaMap_realize(self, widget):
        print "Setting eventbox pointer mask"
        self.eventboxMap.set_events(self.eventboxMap.get_events() | gtk.gdk.POINTER_MOTION_MASK )
        
    def on_eventboxMap_realize(self, widget):
        print "Setting eventbox pointer mask"
        self.eventboxMap.set_events(self.eventboxMap.get_events() | gtk.gdk.POINTER_MOTION_MASK )

    def on_eventboxMap_show(self, widget):
        print "Setting eventbox pointer mask"
        self.eventboxMap.set_events(self.eventboxMap.get_events() | gtk.gdk.POINTER_MOTION_MASK )

    def on_menuitemMapViewer_new_activate(self, menuitem):
        print "on_menuitemMapViewer_new_activate(",self, menuitem,")"
    def on_menuitemMapViewer_open_activate(self, menuitem):
        print "on_menuitemMapViewer_open_activate(",self, menuitem,")"
    def on_menuitemMapViewer_save_activate(self, menuitem):
        for point in self.points :
            point.store(self.imageDatabase, self.map_id)
        self.imageDatabase.dbh.commit()
        print "on_menuitemMapViewer_save_activate(",self, menuitem,")"
    def on_menuitemMapViewer_save_as_activate(self, menuitem):
        print "on_menuitemMapViewer_save_as_activate(",self, menuitem,")"
    def on_menuitemMapViewer_quit_activate(self, menuitem):
        print "on_menuitemMapViewer_quit_activate(",self, menuitem,")"
    def on_menuitemMapViewer_cut_activate(self, menuitem):
        print "on_menuitemMapViewer_cut_activate(",self, menuitem,")"
    def on_menuitemMapViewer_copy_activate(self, menuitem):
        print "on_menuitemMapViewer_copy_activate(",self, menuitem,")"
    def on_menuitemMapViewer_paste_activate(self, menuitem):
        print "on_menuitemMapViewer_paste_activate(",self, menuitem,")"
    def on_menuitemMapViewer_delete_activate(self, menuitem):
        print "on_menuitemMapViewer_delete_activate(",self, menuitem,")"
    def on_menuitemMapViewer_about_activate(self, menuitem):
        print "on_menuitemMapViewer_about_activate(",self, menuitem,")"

    def on_map3_activate(self, menuitem) :
        pass
    def on_albums3_activate(self, menuitem):
        self.appmanager.new_album_browser()
    def on_people3_activate(self, menuitem):
        self.appmanager.new_subject_browser('person')
    def on_places3_activate(self, menuitem):
        self.appmanager.new_subject_browser('place')
    def on_things3_activate(self, menuitem):
        self.appmanager.new_subject_browser('thing')
    def on_events3_activate(self, menuitem):
        self.appmanager.new_subject_browser('event')

    def on_entryMapPositionLon_focus_out_event(self, widget,event):
        if len(self.selectedpoints) == 1 :
            try :
                self.selectedpoints[0].geopos[0] = float(self.entryMapPositionLon.get_text())
            except :
                self.selectedpoints[0].geopos[0] = None
    def on_entryMapPositionLat_focus_out_event(self, widget,event):
        if len(self.selectedpoints) == 1 :
            try :
                self.selectedpoints[0].geopos[1] = float(self.entryMapPositionLat.get_text())
            except :
                self.selectedpoints[0].geopos[1] = None
    def on_entryMapPositionX_focus_out_event(self, widget,event):
        if len(self.selectedpoints) == 1 :
            try :
                self.selectedpoints[0].pos[0] = float(self.entryMapPositionX.get_text())
            except :
                pass
    def on_entryMapPositionY_focus_out_event(self, widget,event):
        if len(self.selectedpoints) == 1 :
            try :
                self.selectedpoints[0].pos[1] = float(self.entryMapPositionY.get_text())
            except :
                pass


    def get_LonLatFromXY(self, x, y = None) :
        if y == None :
            y = x[1]
            x = x[0]

        print "Searching for position of ", x, y
        lon = None
        lat = None
        positions = []
        for point in self.points :
            if isinstance(point, MapViewer.MapPointReference) and \
                   point.pos[0] != None and point.pos[1] != None \
                   and point.geopos[0] != None and point.geopos[1] != None :
                print "Found point", point.pos, point.geopos
                
                pos = (float(point.pos[0]),
                       float(point.pos[1]),
                       float(point.geopos[0]),
                       float(point.geopos[1]),
                       (x - point.pos[0]) * (x - point.pos[0]) + (y - point.pos[1]) * (y - point.pos[1]))

                j = 0
                while j < len(positions) :
                    if positions[j][4] >= pos[4] :
                        break
                    j = j + 1
                if j < len(positions) :
                    k = len(positions) - 1
                    if k < 2 :
                        positions.append(positions[-1])
                    while (k > j) :
                        positions[k] = positions[k - 1]
                        k = k - 1
                    positions[j] = pos
                elif len(positions) < 3 :
                    positions.append(pos)
        print "Got ", len(positions), ' reference points: ', positions    
        if len(positions) == 3 :
            udx = positions[1][0] - positions[0][0]
	    udy = positions[1][1] - positions[0][1]
	    vdx = positions[2][0] - positions[0][0]
	    vdy = positions[2][1] - positions[0][1]

            x = x - positions[0][0]
            y = y - positions[0][1]

            tu = (x * vdy - y * vdx) / (udx * vdy - udy * vdx) ;
            if vdy :
                tv = (y - tu * udy) / vdy
            else :
                tv = (x - tu * udx) / vdx;

            pudx = positions[1][2] - positions[0][2];
            pudy = positions[1][3] - positions[0][3];
            pvdx = positions[2][2] - positions[0][2];
            pvdy = positions[2][3] - positions[0][3];

            lon = tu * pudx + tv * pvdx + positions[0][2];
            lat = tu * pudy + tv * pvdy + positions[0][3];
        elif len(positions) > 3 :
            raise StandardError('positions not 3')
        return [lon, lat]


    # This is the same as the above function, with the position array initialized differently.
    
    def get_XYFromLonLat(self, x, y = None) :
        if y == None :
            y = x[1]
            x = x[0]

        lon = None
        lat = None
        positions = []
        for point in self.points :
            if isinstance(point, MapViewer.MapPointReference) :
                pos = (point.geopos[0], point.geopos[1], point.pos[0], point.pos[1],
                       (x - point.geopos[0]) * (x - point.geopos[0]) + (y - point.geopos[1]) * (y - point.geopos[1]))

                j = 0
                while j < len(positions) :
                    if positions[j][4] >= pos[4] :
                        break
                    j = j + 1
                if j < len(positions) :
                    k = len(positions) - 1
                    if k < 2 :
                        positions.append(positions[-1])
                    while (k > j) :
                        positions[k] = positions[k - 1]
                        k = k - 1
                    positions[j] = pos
                elif len(positions) < 3 :
                    positions.append(pos)
                    
        if len(positions) == 3 :
            udx = positions[1][0] - positions[0][0]
	    udy = positions[1][1] - positions[0][1]
	    vdx = positions[2][0] - positions[0][0]
	    vdy = positions[2][1] - positions[0][1]

            x = x - positions[0][0]
            y = y - positions[0][1]

            tu = (x * vdy - y * vdx) / (udx * vdy - udy * vdx) ;
            if vdy :
                tv = (y - tu * udy) / vdy
            else :
                tv = (x - tu * udx) / vdx;

            pudx = positions[1][2] - positions[0][2];
            pudy = positions[1][3] - positions[0][3];
            pvdx = positions[2][2] - positions[0][2];
            pvdy = positions[2][3] - positions[0][3];

            lon = tu * pudx + tv * pvdx + positions[0][2];
            lat = tu * pudy + tv * pvdy + positions[0][3];
        elif len(positions) > 3 :
            raise StandardError('positions not 3')
        return [int(lon), int(lat)]

    
    def HandleToolbuttonToggle(self, widgetTrue):
        if widgetTrue.get_active() and not self.settingToolbuttonToggleStates:
            self.settingToolbuttonToggleStates = True
            for widget in (self.togglebuttonMapToolSelect,
                           self.togglebuttonMapToolRefPt,
                           self.togglebuttonMapToolPath,
                           self.togglebuttonMapToolInterest):
                if widget != widgetTrue :
                    widget.set_active(False)
            self.settingToolbuttonToggleStates = False
            
    def on_togglebuttonMapToolSelect_toggled(self, widget):
        self.HandleToolbuttonToggle(widget)
    def on_togglebuttonMapToolRefPt_toggled(self, widget):
        self.HandleToolbuttonToggle(widget)
    def on_togglebuttonMapToolPath_toggled(self, widget):
        self.HandleToolbuttonToggle(widget)
    def on_togglebuttonMapToolInterest_toggled(self, widget):
        self.HandleToolbuttonToggle(widget)


    def configureScrollbars(self):
        imagesize = [self.pixbufBackground.get_width(), self.pixbufBackground.get_height()]
        windowsize = self.drawingareaMap.window.get_size()
        size = imagesize[:]
        for i in range(len(imagesize)) :
            size[i] = imagesize[i] - int(windowsize[i] / self.scale)
            if size[i] < 0:
                size[i] = 1
            
        self.hscrollbarMap.set_range(0, size[0])
        self.hscrollbarMap.set_increments(1, int(windowsize[0] / (2 * self.scale)))
        self.vscrollbarMap.set_range(0, size[1])
        self.vscrollbarMap.set_increments(1, int(windowsize[1] / (2 * self.scale)))

    def on_drawingareaMap_expose_event(self, widget, event):
        windowsize = self.drawingareaMap.window.get_size()
        pixmap = gtk.gdk.Pixmap(self.drawingareaMap.window,
                                windowsize[0],windowsize[1],
                                self.drawingareaMap.window.get_depth())
        gc = gtk.gdk.GC(self.drawingareaMap.window)
        color = self.drawingareaMap.get_style().bg[0]
        gc.set_rgb_fg_color(color)
        gc.set_rgb_bg_color(color)

        imagesize = [self.pixbufBackground.get_width(), self.pixbufBackground.get_height()]
        scrollorigin = [self.hscrollbarMap.get_value(), self.vscrollbarMap.get_value()]
        sourcepixelsize = imagesize[:]
        targetpixelsize = imagesize[:]
        
        for i in range(len(imagesize)):
            sourcepixelsize[i] = windowsize[i] / self.scale
            if sourcepixelsize[i] + scrollorigin[i] > imagesize[i] :
                scrollorigin[i] = imagesize[i] - sourcepixelsize[i]
                
            if scrollorigin[i] < 0:
                scrollorigin[i] = 0
                sourcepixelsize[i] = imagesize[i]
                targetpixelsize[i] = imagesize[i] * self.scale
            else:
                targetpixelsize[i] = windowsize[i]

            scrollorigin[i] = int(scrollorigin[i])
            targetpixelsize[i] = int(targetpixelsize[i])
            sourcepixelsize[i] = int(sourcepixelsize[i])

        pixmap.draw_rectangle(gc, True, targetpixelsize[0], 0, windowsize[0], windowsize[1])
        pixmap.draw_rectangle(gc, True, 0, targetpixelsize[1], windowsize[0], windowsize[1])
        if self.scale == 1.0 :
            pixmap.draw_pixbuf(gc, self.pixbufBackground,
                               scrollorigin[0], scrollorigin[1],
                               0,0,
                               targetpixelsize[0], targetpixelsize[1],
                               gtk.gdk.RGB_DITHER_NONE, 0, 0)
        else:
            # Waiting for GTK bindings to catch up. Sigh.
            #subpixbuf = self.pixbufBackground.subpixbuf( scrollorigin[0],
            #                                         scrollorigin[1],
            #                                         sourcepixelsize[0],
            #                                         sourecepixelsize[1])


            if self.subpixbufCache == None or \
               self.subpixbufCache_scrollorigin[0] != scrollorigin[0] or \
               self.subpixbufCache_scrollorigin[1] != scrollorigin[1] or \
               self.subpixbufCache_sourcepixelsize[0] != sourcepixelsize[0] or \
               self.subpixbufCache_sourcepixelsize[1] != sourcepixelsize[1] or \
               self.subpixbufCache_targetpixelsize[0] != targetpixelsize[0] or \
               self.subpixbufCache_targetpixelsize[1] != targetpixelsize[1] :

                self.subpixbufCache_scrollorigin = scrollorigin
                self.subpixbufCache_sourcepixelsize = sourcepixelsize
                self.subpixbufCache_targetpixelsize = targetpixelsize
                self.subpixbufCache_targetpixelsize1 = targetpixelsize

                self.subpixbufCache = gtk.gdk.Pixbuf(self.pixbufBackground.get_colorspace(),
                                           False,
                                           self.pixbufBackground.get_bits_per_sample(),
                                           sourcepixelsize[0],sourcepixelsize[1])

                print "Copying from ",(scrollorigin[0],
                                       scrollorigin[1],
                                       sourcepixelsize[0],
                                       sourcepixelsize[1])
                self.pixbufBackground.copy_area(scrollorigin[0],
                                                scrollorigin[1],
                                                sourcepixelsize[0],
                                                sourcepixelsize[1],
                                                self.subpixbufCache,
                                                0,0)
                print "Scaling",targetpixelsize[0],targetpixelsize[1]
                print "   from ", self.subpixbufCache.get_width(), self.subpixbufCache.get_height()
                self.subpixbufCache = self.subpixbufCache.scale_simple(targetpixelsize[0],
                                                   targetpixelsize[1],
                                                   gtk.gdk.INTERP_BILINEAR)
                print "     to ", self.subpixbufCache.get_width(), self.subpixbufCache.get_height()


            
            pixmap.draw_pixbuf(gc, self.subpixbufCache, 0, 0, 0, 0,
                               targetpixelsize[0], targetpixelsize[1],
                               gtk.gdk.RGB_DITHER_NONE, 0, 0)
            print "Drew into pixmap"

        color = gtk.gdk.Color()
        color.red = 65535
        color.green = 0
        color.blue = 32767
        pixmapgc = gtk.gdk.GC(pixmap)
        pixmapgc.set_foreground(color)
        pixmapgc.set_background(color)
        pixmapgc.set_rgb_fg_color(color)
        pixmapgc.set_rgb_bg_color(color)
        pixmapgc.set_line_attributes(2,
                                     gtk.gdk.LINE_SOLID,
                                     gtk.gdk.CAP_PROJECTING,
                                     gtk.gdk.JOIN_MITER)
        transform = MapViewer.MapTransform(pixmap, scrollorigin, self.scale)
        
        for point in self.points :
            point.draw(transform, gc)

        for point in self.selectedpoints :
            point.draw_selected(transform, gc)

        self.drawingareaMap.window.draw_drawable(gc, pixmap, 0,0,0,0, windowsize[0],windowsize[1])
        self.CollectGarbage()

    def CollectGarbage(self) :
        gc.collect()

    def bring_selected_points_to_fore(self) :
        for point in self.selectedpoints :
            i = self.points.index(point)
            self.points = self.points[:i] + self.points[i+1:] + [point]

        

    def on_eventboxMap_check_resize(self, widget, event):
        print "on_eventboxMap_check_resize(",self, widget, event,")"
    def on_eventboxMap_button_press_event(self, widget, event):
        if event.button == 1 :
            origin = [self.hscrollbarMap.get_value(), self.vscrollbarMap.get_value()]
            hit = [int(event.x / self.scale + origin[0]),
                   int(event.y / self.scale + origin[1])]

            if self.togglebuttonMapToolSelect.get_active():
                self.buttonpressDrag = hit
                for point in self.selectedpoints :
                    if point.hit_test(hit, self.scale) :
                        break
                else:
                    self.selectedpoints = []
                    for point in self.points :
                        if point.hit_test(hit, self.scale) :
                            self.selectedpoints = [point]

                    self.bring_selected_points_to_fore()
                    
                if len(self.selectedpoints) != 0 :
                    self.dragcontext = widget.drag_begin(
                        [
                        ('text/plain', 0, 1),
                        ('text/plain', gtk.TARGET_SAME_APP, 1),
                        ('text/plain', gtk.TARGET_SAME_WIDGET, 1),
                        ],
                                                         gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY,
                                                         event.button,
                                                         event)
                    print "Drag begin", self.dragcontext
            elif self.togglebuttonMapToolRefPt.get_active() :
                p = MapViewer.MapPointReference(hit)
                self.points.append(p)
                self.selectedpoints = [p]
                #(lon, lat) = self.get_LonLatFromXY(hit)
                #append new point
            elif self.togglebuttonMapToolPath.get_active() :
                p = MapViewer.MapPointPath(hit)
                self.points.append(p)
                p.geopos = self.get_LonLatFromXY(hit)
                if len(self.selectedpoints) > 0 and isinstance(self.selectedpoints[0], MapViewer.MapPointPath):
                    self.selectedpoints[0].nextinpath = p
                self.selectedpoints = [p]
                pass
            elif self.togglebuttonMapToolInterest.get_active() :
                p = MapViewer.MapPointInterest(hit)
                p.geopos = self.get_LonLatFromXY(hit)
                print "Set point of interest at ", hit, p.geopos
                self.points.append(p)
                self.selectedpoints = [p]

            self.CheckSelectedPointsAndLabels()

            self.redraw_drawingareaMap()
        else:
            print "Button:", event.button
            
    def CheckSelectedPointsAndLabels(self) :
        if len(self.selectedpoints) == 1:
            print self.selectedpoints[0].geopos, self.selectedpoints[0].pos
            self.entryMapPositionLon.set_editable(True)
            if self.selectedpoints[0].geopos[0] != None :
                self.entryMapPositionLon.set_text(str(self.selectedpoints[0].geopos[0]))
            else :
                self.entryMapPositionLon.set_text('')
            self.entryMapPositionLat.set_editable(True)
            if self.selectedpoints[0].geopos[1] != None :
                self.entryMapPositionLat.set_text(str(self.selectedpoints[0].geopos[1]))
            else :
                self.entryMapPositionLat.set_text('')
            self.entryMapPositionX.set_editable(True)
            self.entryMapPositionX.set_text(str(self.selectedpoints[0].pos[0]))
            self.entryMapPositionY.set_editable(True)
            self.entryMapPositionY.set_text(str(self.selectedpoints[0].pos[1]))
        else :
            for w in (self.entryMapPositionLon,
                      self.entryMapPositionLat,
                      self.entryMapPositionX,
                      self.entryMapPositionY) :
                w.set_text('')
                w.set_editable(False)

    def WaitForNoPointerMotion(self) :
        if self.lastPausedMouseTimeout > 0 :
            self.lastPausedMouseTimeout = self.lastPausedMouseTimeout - 1
        if 0 == self.lastPausedMouseTimeout and self.buttonpressDrag == None:
            origin = [self.hscrollbarMap.get_value(), self.vscrollbarMap.get_value()]
            hit = [self.lastPausedMousePosition[0] / self.scale + origin[0],
                   self.lastPausedMousePosition[1] / self.scale + origin[1]]
            hitpoint = None
            for point in self.points :
                if isinstance(point, MapViewer.MapPointImage) and point.hit_test(hit, self.scale) :
                    
                    hitpoint = point
            if hitpoint != None:
                PreviewPopup.PreviewPopup(hitpoint.image.get_thumbnail_filename())
        if (self.lastPausedMouseTimeout < 0) :
            self.lastPausedMouseTimeout = 0
        return 0 != self.lastPausedMouseTimeout
    
    def on_eventboxMap_motion_notify_event(self, widget, event) :
        self.lastPausedMousePosition = (event.x, event.y)
        if self.lastPausedMouseTimeout <= 0 and self.buttonpressDrag == None:
            gtk.timeout_add(250,self.WaitForNoPointerMotion);
        self.lastPausedMouseTimeout = 5

    def on_eventboxMap_button_release_event(self, widget, event):
        print "on_eventboxMap_button_release_event(",self, widget, event,")"
        if event.button == 1 :
            origin = [self.hscrollbarMap.get_value(), self.vscrollbarMap.get_value()]
            hit = [event.x / self.scale + origin[0],
                   event.y / self.scale + origin[1]]
            if self.buttonpressDrag != None:
                if len(self.selectedpoints) == 0 :
                    p1 = [None, None]
                    p2 = [None, None]
                    for i in range(2):
                        if hit[i] < self.buttonpressDrag[i] :
                            p1[i] = hit[i]
                            p2[i] = self.buttonpressDrag[i]
                        else :
                            p1[i] = self.buttonpressDrag[i]
                            p2[i] = hit[i]
                    for point in self.points :
                        for i in range(2) :
                            if point.pos[i] < p1[i] or point.pos[i] > p2[i] :
                                break
                        else:
                            self.selectedpoints.append(point)
                    self.bring_selected_points_to_fore()
                    self.buttonpressDrag = None
                self.CheckSelectedPointsAndLabels()

                self.redraw_drawingareaMap()

        return False

    def on_eventboxMap_configure_event(self, widget, event):
        print "on_eventboxMap_configure_event(",self, widget, event,")"
    def on_eventboxMap_size_allocate(self, widget, rect):
        print "on_eventboxMap_size_allocate(",self, widget, rect,")"
    def on_eventboxMap_size_request(self, event):
        print "on_eventboxMap_size_request(",self, event,")"

    def on_drawingareaMap_configure_event(self, widget, event):
        print "on_drawingareaMap_configure_event(",self, widget, event,")"
    def on_drawingareaMap_size_allocate(self, widget, rect):
        print "on_drawingareaMap_size_allocate(",self, widget, rect,")"
        self.configureScrollbars()
    def on_drawingareaMap_size_request(self, widget, event):
        print "on_drawingareaMap_size_request(",self, widget, event,")"
        
    def on_eventboxMap_key_press_event(self, widget, event):
        print "on_eventboxMap_key_press_event(",self, widget, event,")"
    def on_vscrollbarMap_value_changed(self, event):
        self.redraw_drawingareaMap()
    def on_hscrollbarMap_value_changed(self, event):
        self.redraw_drawingareaMap()

    def SetScaleInPercent(self, percent):
        self.scale = float(percent) / 100.0
        self.configureScrollbars()
        self.redraw_drawingareaMap()

    def redraw_drawingareaMap(self) :
        #self.on_drawingareaMap_expose_event(None, None)
        windowsize = self.drawingareaMap.window.get_size()
        rect = gtk.gdk.Rectangle(0,0,windowsize[0],windowsize[1])
        self.drawingareaMap.window.invalidate_rect(rect, True)
        
    def on_menuitem_10_percent_activate(self, menuitem) :
        self.SetScaleInPercent(10);
    def on_menuitem_25_percent_activate(self, menuitem) :
        self.SetScaleInPercent(25);
    def on_menuitem_50_percent_activate(self, menuitem) :
        self.SetScaleInPercent(50);
    def on_menuitem_100_percent_activate(self, menuitem) :
        self.SetScaleInPercent(100);
    def on_menuitem_200_percent_activate(self, menuitem) :
        self.SetScaleInPercent(200);
    def on_menuitem_400_percent_activate(self, menuitem) :
        self.SetScaleInPercent(400);

    def on_selected_images1_activate(self, menuitem):
        ids = []
        for point in self.selectedpoints :
            if isinstance(point, MapViewer.MapPointImage) :
                ids.append(str(point.image['id']))
        self.appmanager.new_image_browser('id IN (' + ','.join(ids) + ')')
    def on_get_images1_activate(self, menuitem) :
        cursor = self.imageDatabase.dbh.cursor()
        currentimages = {}
        cursor.execute('SELECT image_id FROM mappoints_image WHERE map_id=%s', self.map_id)
        row = cursor.fetchone()
        while row:
            currentimages[row[0]] = True
            row = cursor.fetchone()

        p1 = self.get_LonLatFromXY(0,0)
        p2 = self.get_LonLatFromXY(self.pixbufBackground.get_width(), self.pixbufBackground.get_height())

        if p1[0] == None or p1[1] == None or p2[0] == None or p2[1] == None :
            return
        p1 = [p1[0],p1[1]]
        p2 = [p2[0],p2[1]]
        
        for i in range(len(p1)) :
            if p2[i] < p1[i] :
                t = p2[i]
                p2[i] = p1[i]
                p1[i] = t

        newimages = []
        sql = 'SELECT id, subject_longitude, subject_lattitude FROM image WHERE subject_longitude > %s AND subject_longitude < %s AND subject_lattitude > %s AND subject_lattitude < %s'
        cursor.execute(sql, p1[0],p2[0],p1[1],p2[1])
        row = cursor.fetchone()
        while row :
            if not currentimages.has_key(row[0]):
                newimages.append(row)
            row = cursor.fetchone()

        for row in newimages :
            print "Creating new image with ", row
            pos = self.get_XYFromLonLat(row[1],row[2])
            point = MapViewer.MapPointImage(row[0], pos,
                                            row[0].get_thumbnail_filename())
            print "     image at ", pos, " point ", point
            point.geopos = [row[1], row[2]]
            self.points.append(point)
