import gtk
import time
import types

class Slideshow :
    def __init__(self, filenames, pos = None):
        self.popup = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.popup.set_decorated(False)
        self.eventbox = gtk.EventBox()

        self.drawingarea = gtk.DrawingArea()
        self.currentpixbuf = None
        self.prevpixbuf = None
        
        self.width = gtk.gdk.screen_width() /  4
        self.height = gtk.gdk.screen_height() / 4
        self.scratchpb = None
        self.popup.resize(self.width, self.height)

        self.filenames = filenames
        self.currentfile = 0
        self.filedirection = 1
        self.eventbox.add(self.drawingarea)
        self.popup.add(self.eventbox)
        self.popup.set_position(gtk.WIN_POS_CENTER)
        self.preblanktime = 500
        self.postblanktime =  500
        self.showtime = 1500
        self.showntimer = 0
        self.showngranularity = 100
        self.fadein_ticks = 8
        self.fadein_ticktime = 150 
                            
        self.fadein = self.fadein_ticks

        self.load_next_image()

        self.eventbox.set_flags(gtk.CAN_FOCUS)
        self.eventbox.add_events(gtk.gdk.KEY_PRESS_MASK)
        
        self.eventbox.connect('motion-notify-event', self.on_motion_notify_event)
        self.eventbox.connect('focus-out-event', self.on_motion_notify_event)
        self.eventbox.connect('button-press-event', self.on_button_press_event)
        self.eventbox.connect('key-press-event', self.on_key_press_event)
        self.eventbox.connect('show', self.on_show_event)
        self.eventbox.set_property('events',
                                   self.eventbox.get_property('events')
                                   | gtk.gdk.KEY_PRESS_MASK)
        self.drawingarea.connect('expose-event', self.on_expose_event)
        self.popup.grab_focus()
        self.eventbox.grab_focus()
        gtk.timeout_add(self.preblanktime, self.fade_in_image_timer_tick)

        self.popup.show_all()


    def on_expose_event(self, widget, event) :
        if self.popup == None :
            return
        drawablewindow = self.popup.window
        windowsize = widget.window.get_size()
        gc = gtk.gdk.GC(drawablewindow)
        bgcolor = widget.get_style().bg[0]
        gc.set_rgb_fg_color(bgcolor)
        gc.set_rgb_bg_color(bgcolor)

        drawoffset = ((windowsize[0] / 2), (windowsize[1] / 2))
        if self.prevpixbuf == None and self.currentpixbuf == None :
            pass
        elif self.fadein > 0 :
            if self.prevpixbuf == None :
                prevsize = (0,0)
            else :
                prevsize = (self.prevpixbuf.get_width(), self.prevpixbuf.get_height())

            if self.currentpixbuf == None :
                currsize = (0,0)
            else :
                currsize = (self.currentpixbuf.get_width(), self.currentpixbuf.get_height())

            pbsize = [0,0]
            for i in range(len(pbsize)) :
                if prevsize[i] > currsize[i] :
                    pbsize[i] = prevsize[i]
                else:
                    pbsize[i] = currsize[i]
            pbsize = windowsize[:]

            if self.scratchpb == None or \
               self.scratchpb.get_width() != pbsize[0] or \
               self.scratchpb.get_height() != pbsize[1] :
                self.scratchpb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,
                                                True,8,
                                                pbsize[0],pbsize[1])
            pb = self.scratchpb

            pb.fill(long(bgcolor.red >> 8) << 24
                    | long(bgcolor.green >> 8) << 16
                    | long(bgcolor.blue >> 8) << 8 | 0xff)
            alpha = int(255.0 * self.fadein / self.fadein_ticks)

            if self.prevpixbuf != None :
                self.prevpixbuf.composite(pb,
                                          (pbsize[0] - prevsize[0]) / 2,
                                          (pbsize[1] - prevsize[1]) / 2,
                                          prevsize[0],
                                          prevsize[1],
                                          (pbsize[0] - prevsize[0]) / 2,
                                          (pbsize[1] - prevsize[1]) / 2,
                                          1.0,1.0,
                                          gtk.gdk.INTERP_BILINEAR,
                                          alpha
                                     )
            oneminusalpha = 255 - alpha

            if self.currentpixbuf != None :
                self.currentpixbuf.composite(pb,
                                             (pbsize[0] - currsize[0]) / 2,
                                             (pbsize[1] - currsize[1]) / 2,
                                             currsize[0] ,
                                             currsize[1], 
                                             (pbsize[0] - currsize[0]) / 2,
                                             (pbsize[1] - currsize[1]) / 2,
                                             1.0,1.0,
                                             gtk.gdk.INTERP_BILINEAR,
                                             oneminusalpha
                                             )
            drawoffset = [(windowsize[0] - pbsize[0]) / 2,
                      (windowsize[1] - pbsize[1]) / 2]

            widget.window.draw_pixbuf(gc, pb,
                                      0,0,
                                      drawoffset[0],drawoffset[1],
                                      pb.get_width(),
                                      pb.get_height(),
                                      gtk.gdk.RGB_DITHER_NONE, 0, 0)
        else :
            self.scratchpb = None
            if self.currentpixbuf != None :
                pbsize = (self.currentpixbuf.get_width(),
                          self.currentpixbuf.get_height())
                drawoffset = [(windowsize[0] - pbsize[0]) / 2,
                              (windowsize[1] - pbsize[1]) / 2]

                widget.window.draw_pixbuf(gc, self.currentpixbuf,
                                          0,0, drawoffset[0],drawoffset[1],
                                          pbsize[0], pbsize[1],
                                          gtk.gdk.RGB_DITHER_NONE, 0, 0)

        if drawoffset[0] > 0 :
            widget.window.draw_rectangle(gc, True, 0, 0, drawoffset[0], windowsize[1])
            widget.window.draw_rectangle(gc, True, windowsize[0]-drawoffset[0], 0,
                                         windowsize[0], windowsize[1])
        if drawoffset[1] > 0 :
            widget.window.draw_rectangle(gc, True,
                                         drawoffset[0], 0,
                                         windowsize[0]-drawoffset[0], drawoffset[1])
            widget.window.draw_rectangle(gc, True,
                                         windowsize[0]-drawoffset[0], windowsize[1]-drawoffset[1],
                                         windowsize[0], windowsize[1])
            


    def finished_timer_tick(self) :
        if self.popup != None :
            self.popup.destroy()
            self.popup = None
        return False

    def show_image_timer_tick(self) :
        if self.popup == None :
            return False

        self.showntimer = self.showntimer - 1
        if self.showntimer > 0 :
            return True
        self.showntimer == 0
        if self.filedirection == 0 :
            return True
        gtk.timeout_add(self.fadein_ticktime, self.fade_in_image_timer_tick)
        self.fadein = self.fadein_ticks
        self.load_next_image()
        return False
        
    def fade_in_image_timer_tick(self) :
        if self.prevpixbuf == None and self.currentpixbuf == None :
            gtk.timeout_add(self.postblanktime, self.finished_timer_tick)
        elif self.fadein > 0 :
            gtk.timeout_add(self.fadein_ticktime, self.fade_in_image_timer_tick)
            self.fadein = self.fadein - 1
        else :
            self.showntimer = (self.showtime + self.showngranularity - 1) / self.showngranularity
            gtk.timeout_add(self.showngranularity, self.show_image_timer_tick)

        if not isinstance(self.popup.window, types.NoneType) :
            windowsize = self.popup.window.get_size()
            rect = gtk.gdk.Rectangle(0,0,windowsize[0],windowsize[1])
            self.drawingarea.window.invalidate_rect(rect, True)
                            
        return False
    
    def load_next_image(self) :
        self.prevpixbuf = self.currentpixbuf
        self.currentpixbuf = None
        if self.currentfile < len(self.filenames) and self.currentfile >= 0 :
            filename = self.filenames[self.currentfile]
            self.currentfile = self.currentfile + self.filedirection

            print "loading",filename,"at", time.time()

            pb = gtk.gdk.pixbuf_new_from_file(filename)
            width = pb.get_width()
            height = pb.get_height()
            if float(self.width) / float(width) > float(self.height) / float(height) :
                scale = float(self.height) / float(height)
            else :
                scale = float(self.width) / float(width)
            #scale = scale * .9
            width = int(width * scale)
            height = int(height * scale)
            pb = pb.scale_simple(width,height, gtk.gdk.INTERP_BILINEAR)
            self.currentpixbuf = pb
            return True
        else :
            return False
            
    def on_show_event(self, widget):
        self.eventbox.set_events(self.eventbox.get_events() | gtk.gdk.POINTER_MOTION_MASK )
        
    def on_button_press_event(self, widget, event):
        print "Button press", event, event.button
        if event.button == 1 :
            pass
        elif event.button == 3 :
            pass
        
    def on_motion_notify_event(self, widget, event):
        #print "Motion notify called"
        #`self.popup.destroy()
        return True
    def on_key_press_event(self, widget, event):
        print "Key press called", event.type
        if event.type == gtk.gdk.KEY_PRESS :
            print "key press", event.time, event.keyval, event.string

            if event.keyval == 65363 : # right arrow
                self.filedirection = 1
                self.showntimer = 0
                pass
            if event.keyval == 65361 : # left arrow
                self.filedirection = -1
                self.showntimer = 0
                pass
            if event.keyval == 65362 : # up arrow
                pass
            if event.keyval == 65364 : # down arrow
                pass
            if event.keyval == 65360 : # home
                self.filedirection = 1
                self.currentfile = 0
                pass
            if event.keyval == 65367 : # end
                self.filedirection = -1
                self.currentfile = len(self.filenames) - 1
                pass
            if event.keyval == 65365 : # page up
                pass
            if event.keyval == 65366 : # page down
                pass
            if event.keyval == 65293 : # enter
                if self.showntimer < self.showtime / self.showngranularity :
                    self.showntimer = 65535
                else :
                    self.showntimer = 0
                pass
            if event.keyval == 65307 : # escape
                self.popup.destroy()
                self.popup = None;
                pass
        print event
        return True
    def destroy(self):
        if self.popup != None :
            self.popup.destroy()
        self.popup = None

import sys
if __name__ == '__main__':
    p = Slideshow(sys.argv[1:])
    gtk.main()
