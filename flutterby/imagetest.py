import gtk

pb = gtk.gdk.pixbuf_new_from_file('/home/danlyke/images/deserttripapril2004_6/img_0215.thm')

maxdimension = 48.0
if pb.get_width() > pb.get_height() :
    newwidth = int(maxdimension)
    newheight = int(maxdimension * float(pb.get_height()) /
                    float(pb.get_width()))
else:
    newheight = int(maxdimension)
    newwidth = int(maxdimension * float(pb.get_width()) /
                   float(pb.get_height()))
pb = pb.scale_simple(newwidth, newheight, gtk.gdk.INTERP_BILINEAR)

print pb.get_pixels_array()

class abc :
    def __init__(self) :
        self.s = ''
    def write(self,buf,count,data) :
        print "callback", self, buf, count,data

a = abc()
pb.save(abc.write, 'jpeg')

#f = open('test.jpg', 'w')
#f.write(s)
#f.close()
