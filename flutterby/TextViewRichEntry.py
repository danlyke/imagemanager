import gtk
import pango
from xml.dom import minidom


class TextViewRichEntry:
    def __init__(self, textview):
        self.textview = textview
        self.textview.set_editable(True)
        self.textview.set_wrap_mode(gtk.WRAP_WORD)
        self.textview.set_pixels_below_lines(16)
        self.buffer = self.textview.get_buffer()
        self.tagAttributeMap = { 'place' :
                                 {'underline' : pango.UNDERLINE_SINGLE,
                                  'foreground' : '#00ff00'},
                                 'person' :
                                 {'underline' : pango.UNDERLINE_SINGLE,
                                  'foreground' : '#ffff00'},
                                 'thing' :
                                 {'underline' : pango.UNDERLINE_SINGLE,
                                  'foreground' : '#0000ff'},
                                 'event' :
                                 {'underline' : pango.UNDERLINE_SINGLE,
                                  'foreground' : '#ff00ff'},
                                 }

    def get_widget(self) :
        return self.textview
    def set_editable(self, state) :
        self.textview.set_editable(state)
    def get_editable(self) :
        return self.textview.get_editable()
    def set_sensitive(self, state) :
        self.textview.set_sensitive(state)
    def get_sensitive(self) :
        return self.textview.get_sensitive()
    def get_buffer(self) :
        return self.buffer
    def destroy(self) :
        self.textview.destroy()
        self.textview = None
        self.buffer = None
    
    def create_tag(self, name, attrs = None) :
        tag = self.buffer.create_tag()
        tag.name = name
        if attrs == None :
            attrs = {}
        tag.attrs = attrs
        if self.tagAttributeMap.has_key(name) :
            for (k,v) in self.tagAttributeMap[name].items() :
                tag.set_property(k,v)
        return tag

    class textsetter:
        def __init__(self, buffer, attrmap):
            self.buffer = buffer
            self.attrmap = attrmap
            self.tagstack = []

        def create_tag(self, name, attrs = {}) :
            tag = self.buffer.create_tag()
            tag.name = name
            tag.attrs = attrs
            if self.attrmap.has_key(name) :
                for (k,v) in self.attrmap[name].items() :
                    tag.set_property(k,v)
            return tag

        def setRecurse(self, node):
            if (node.__class__.__name__ == 'Text') :
                if 0 == len(self.tagstack) :
                    self.buffer.insert(self.buffer.get_end_iter(), node.data)
                else:
                    self.buffer.insert_with_tags(self.buffer.get_end_iter(), node.data,
                                                 *self.tagstack)
            else:
                if None != node.localName :
                    if node.hasAttributes() :
                        attr = {}
                        for (k,v) in node.attributes.items() :
                            attr[k] = v
                        tag = self.create_tag(node.localName,attr)
                    else:
                        tag = self.create_tag(node.localName)
                    self.tagstack.append(tag)
                    for child in node.childNodes :
                        self.setRecurse(child)
                    self.tagstack.pop()
                else :
                    for child in node.childNodes :
                        self.setRecurse(child)
                
        def set(self, node):
            self.buffer.delete(self.buffer.get_start_iter(), self.buffer.get_end_iter())
            for child in node.childNodes :
                for grandchild in child.childNodes :
                    self.setRecurse(grandchild)
                
                
    def set_text(self, text) :
        if text != None :
            ts = self.textsetter(self.buffer, self.tagAttributeMap)
            xmldoc = minidom.parseString('<flutterby>'+text+'</flutterby>')
            ts.set(xmldoc)
        else:
            self.buffer.set_text('')

    def get_toggledTags(self, iter) :
        turnon = iter.get_toggled_tags(True)
        turnoff = iter.get_toggled_tags(False)
        ret = ''.join(['</'+tag.name+'>' for tag in turnoff])
        ret = ret + \
              ''.join(['<'+tag.name + ''.join([' '+k+'="'+v+'"' for (k,v) in tag.attrs.items()]) + '>' \
                       for tag in turnon])
        return ret
    def get_text(self) :
        iter = self.buffer.get_start_iter()
        ret = self.get_toggledTags(iter)
        nextIter = iter.copy()
        nextIter.forward_to_tag_toggle(None)
        while not iter.is_end() :
            ret = ret + self.buffer.get_text(iter, nextIter, True) + self.get_toggledTags(nextIter)
            iter = nextIter.copy()
            nextIter.forward_to_tag_toggle(None)
        return ret

    def replace_tag_name(self, tagtype, oldname, newname) :
        iter = self.buffer.get_start_iter()
        nextIter = iter.copy()
        while not iter.is_end() :
            turnon = iter.get_toggled_tags(True)
            for tag in turnon :
                print "Tag", tag.name, 'should match', tagtype
                if tag.attrs.has_key('name') :
                    print "   ", tag.attrs['name']
                    print "   should match", oldname
                    if tag.name == tagtype :
                        print "Tag type matches"
                    if oldname == tag.attrs['name']:
                        print "Tag name attr matches"
                if (tag.name == tagtype
                    and tag.attrs.has_key('name')
                    and (tag.attrs['name'] == oldname)):
                    print "Replacing",tag.attrs['name'],"with",newname
                    tag.attrs['name'] = newname                
            iter = nextIter.copy()
            nextIter.forward_to_tag_toggle(None)
    
    def get_insert(self) :
        return self.textview.get_insert(self)
    def get_selection_bound(self) :
        return self.textview.get_selection_bound()
    def get_current_selection(self, tag = None) :
        m1 = self.buffer.get_insert()
        m2 = self.buffer.get_selection_bound()
        i1 = self.buffer.get_iter_at_mark(m1)
        i2 = self.buffer.get_iter_at_mark(m2)
        if (tag != None) :
            self.buffer.apply_tag(tag, i1, i2)
        return self.buffer.get_text(i1, i2)
    def remove_tag(self, tagname) :
        mark = self.buffer.get_insert()
        iter = self.buffer.get_iter_at_mark(mark)
        tags = iter.get_tags()
        for tag in tags :
            if tag.name == tagname :
                iterstart = iter.copy()
                iterend = iter.copy()
                iterstart.forward_to_tag_toggle(tag)
                iterend.backward_to_tag_toggle(tag)
                self.buffer.remove_tag(tag,iterstart, iterend)
                return
