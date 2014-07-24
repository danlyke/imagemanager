from xml.dom import minidom

class Manager :
    def __init__(self) :
        self._initemptydoc()
        self.values = {}
        self.arrayValues = ['filepaths','dynamicfilepaths', 'whatever']

    def read(self, file):
        self.values = {}
        self.xmldoc = minidom.parse(open(file))

    def write(self, filename)  :
        self.xmldoc.writexml(open(filename, 'w'))
        
    def _initemptydoc(self) :
        self.xmldoc = minidom.Document()
        flutterbyelement = minidom.Element('flutterby')
        self.xmldoc.childNodes.append(flutterbyelement)

    def _getNodeText(self, node):
        ret = ""
        for child in node.childNodes :
            if (child.__class__.__name__ == 'Text') :
                ret = ret + child.data
            else:
                ret = ret + self._getNodeText(child)
        return ret;

    def _addconfigelement(self, key, value) :
        if self.xmldoc == None :
            self._initemptydoc()
            
        flutterbyelement = self.xmldoc.childNodes[0]
        configelement = None;

        for element in flutterbyelement.childNodes :
            if element.localName == 'config' \
               and element.hasAttribute('name') \
               and element.getAttribute('name') == key :
                configelement = element

        if configelement == None :
            configelement = minidom.Element('config')
            configelement.setAttribute('name', key)
            flutterbyelement.childNodes.append(configelement)
            textelement = minidom.Text()
            textelement.data = "\n"
            flutterbyelement.childNodes.append(textelement)
            

        if key in self.arrayValues :
            configelement.childNodes = []
            for v in value :
                valelement = minidom.Element('value')
                textelement = minidom.Text()
                textelement.data = v
                valelement.childNodes = [textelement]
                configelement.childNodes.append(valelement)

                textelement = minidom.Text()
                textelement.data = "\n"
                configelement.childNodes.append(textelement)
        else :
            textelement =  minidom.Text()
            textelement.data = value
            configelement.childNodes = [textelement]

    def getvalues(self) :
        values = {}
        flutterbyelement = self.xmldoc.childNodes[0]
        for element in flutterbyelement.childNodes :
            if element.localName == 'config' :
                if element.getAttribute('name') in self.arrayValues :
                    a = []
                    for v in element.getElementsByTagName('value') :
                        a.append(self._getNodeText(v))
                    values[element.getAttribute('name')] = a
                else :
                    values[element.getAttribute('name')] = self._getNodeText(element)
                    
        return values

    def setvalues(self,values) :
        for (k,v) in values.items() :
            self._addconfigelement(k,v)


if __name__ == '__main__':
    rc = Manager()
    # rc.read('./config.xml')
    print rc.getvalues()
    rc.setvalues({'hey' : 'there', 'yo': 'dude', 'whatever' : ['peeps','dweebs', 'persons']})
    rc.write('./test.xml')
