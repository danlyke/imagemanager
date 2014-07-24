from xml.dom import minidom

def reconstruct(node):
    for child in node.childNodes :
        if (child.__class__.__name__ == 'Text') :
            print child.data
        else :
            print '<', child.localName,
            if child.hasAttributes():
                for (k,v)in child.attributes.items() :
                    print ' ', k, '="', v, '"',
            print '>'
            reconstruct(child)
            print '</', child.localName, '>'

xmldoc = minidom.parse(open('/home/danlyke/images/pcd3632/.flutterby.xml'))

for child in xmldoc.childNodes :
    reconstruct(child)
    
        
