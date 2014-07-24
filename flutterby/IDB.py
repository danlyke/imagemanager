from pyPgSQL import PgSQL, libpq
import gtk
import gobject
import os

class GenericError :
    def __init__(self, t) :
        self.text = t
        
class IDB :
    def __init__(self) :
        pass

    def row_inserted(self, x) :
        print "row inserted", x



class SQLObj :
    def __init__(self, idb, id, table, schema,
                 treestore = None,
                 treestorefield = None) :
        self.idb = idb
        self.table = table
        self.schema = schema
        self.values = {}
        self.originalvalues = {}
        self.treestore = treestore
        self.treestorefield = treestorefield

        fields = self.SQLFields()

        cursor = self.idb.dbh.cursor()
        
        if id == None :
            sql = "SELECT NEXTVAL('" + table + "_id_seq')"
            cursor.execute(sql)
            row = cursor.fetchone()
            id = row[0]

        self.id = id
        sql = 'SELECT ' + ','.join(fields) + ' FROM ' + table + ' WHERE id=%s'
        cursor.execute(sql, self.id)
        row = cursor.fetchone()
        fields.reverse()
        if row != None :
            for v in row :
                k = fields.pop()
                self.values[k] = v
                self.originalvalues[k] = v
        else :
            for k in fields :
                self.values[k] = None
                self.originalvalues[k] = None
            self.values['id'] = self.id
            self.originalvalues['id'] = self.id
    def __getitem__(self, k) :
        return self.values[k]

    def _SetTreestoreValue(self, v, l = None) :
        return
        if l == None :
            l = self.treestore
        for r in l :
            if r[0] == self and r[1] != v :
                r[1] = v
            else :
                children = r.iterchildren()
                self._SetTreestoreValue(v, children)
        
    def _DeleteTreestoreValue(self, iter = None) :
        i = 0
        n = self.treestore.iter_n_children(iter)
        while i < n :
            childiter = self.treestore.iter_nth_child(iter, i)
            if self.treestore.get_value(childiter, 0) == r :
                self.treestore.remove(iter)
                return True
            if self._DeleteTreestoreValue(self, childiter) :
                return True
            i = i + 1
        return False
            
    def __setitem__(self, k, v) :
        if self.treestore != None and self.treestorefield == k :
            self._SetTreestoreValue(v)
        self.values[k] = v
    def keys(self) :
        return self.values.keys()
    
    def SQLFields(self) :
        return [f[0] for f in self.schema]

    def Delete(self, cursor = None) :
        self._DeleteTreestoreValue()
        self.idb.Delete(self.table, 'id', self.id, cursor)
        self.idb = None
        self.treestore = None

    def Write(self, cursor = None) :
        if cursor == None :
            cursor = self.idb.dbh.cursor()
        fields = self.SQLFields()
        f = []
        v = []
        if not self.values.has_key('id') :
            print self
            for k in fields :
                print "  ", k, self.originalvalues.has_key(k), self.values.has_key(k)
                if self.originalvalues[k] != self.values[k] :
                    f.append(k)
                    v.append(self.values[k])
            if len(f) > 0 :
                sql = 'UPDATE ' + self.table + ' SET ' + ','.join([ fd+'=%s' for fd in f]) \
                      + 'WHERE id=%s'
                v.append(self.id)
                cursor.execute(sql, *v)
        else:
            for k in fields :
                f.append(k)
                v.append(self.values[k])
            if len(f) > 0 :
                sql = 'INSERT INTO ' + self.table + '(' + ','.join(f) \
                      + ') VALUES (' + ','.join(['%s' for fs in v]) + ')'
                print sql
                print v
                cursor.execute(sql, *v)

class ImageInstance(SQLObj) :
    def __init__(self, idb, id, image) :
        SQLObj.__init__(self, idb, id, 'imageinstance', (
            ('id', 'SERIAL PRIMARY KEY'),
            ('directory_id', 'INT', 'REFERENCES directory(id)'),
            ('image_id', 'INT', 'REFERENCES image(id) NOT NULL'),
            ('width', 'INT'),
            ('height', 'INT'),
            ('name', 'TEXT'),
            ), None, None)
        self.image = image
        self.image_id = image['id']
            
class Image(SQLObj) :
    def __init__(self, idb, id, treestore) :
        SQLObj.__init__(self, idb, id, 'image', (
            ('id', 'SERIAL PRIMARY KEY'),
            ('directory_id', 'INT NOT NULL REFERENCES directory(id)'),
            ('subject_position_id', 'INT', 'REFERENCES geoposition(id)'),
            ('subject_position_accuracy', 'DOUBLE PRECISION'),
            ('subject_lattitude', 'DOUBLE PRECISION'),
            ('subject_longitude', 'DOUBLE PRECISION'),
            ('camera_position_id', 'INT', 'REFERENCES geoposition(id)'),
            ('camera_position_accuracy', 'DOUBLE PRECISION'),
            ('camera_lattitude', 'DOUBLE PRECISION'),
            ('camera_longitude', 'DOUBLE PRECISION'),
            ('rotation', 'INT'),
            ('title', 'TEXT'),
            ('description', 'TEXT'),
            ('technotes', 'TEXT'),
            ('taken', 'TIMESTAMP'),
            ('taken_accuracy', 'INTERVAL'),
            ('photographer_id', 'INT', 'REFERENCES people(id)'),
            ('basename', 'TEXT'),
        ),
                        treestore, 'title')

class Album(SQLObj) :
    def __init__(self, idb, id) :
        SQLObj.__init__(self, idb, id, 'album', (
            ('id', 'SERIAL PRIMARY KEY'),
            ('parent_id', 'INT', 'REFERENCES album(id)'),
            ('type', 'INT', 'REFERENCES filesystemaccesstypes(id)'),
            ('name_changeable', 'BOOL', '', 'DEFAULT TRUE'),
            ('allow_user_children', 'BOOL', '', 'DEFAULT TRUE'),
            ('listorder', 'FLOAT'),
            ('name', 'TEXT')),
                        idb.albumtreestore, 'name')
        self.imagetreestore = None

    def Write(self, cursor = None) :
        if cursor == None :
            cursor = self.idb.dbh.cursor()
        SQLObj.Write(self, cursor)
        if self.imagetreestore != None :
            listorder = 1
            for r in self.imagetreestore :
                sql = 'SELECT parent_id, image_id FROM albumimage WHERE parent_id=%s AND image_id=%s'
                cursor.execute(sql, self.id, r[0]['id'])
                row = cursor.fetchrow()
                if row :
                    sql = 'UPDATE albumimage SET listorder=%d WHERE parent_id=%s AND image_id=%s'
                else :
                    sql = 'INSERT INTO albumimage(listorder, parent_id, image_id) VALUES (%d,%s,%s)'
                cursor.execute(sql, listorder, self.id, r[0]['id'])
                listorder = listorder + 1
    
    def AddImage(self, image) :
        imagetreestore = self.ImageTreeStore()
        for r in imagetreestore :
            if r[0] == image :
                return
        imagetreestore.append(None, [image, image['basename'], None, 0])
        
    def ImageTreeStore(self) :
        self._CreateImageTreeStore()
        return self.imagetreestore;
    def _CreateImageTreeStore(self) :
        if self.imagetreestore == None :
            self.imagetreestore = gtk.TreeStore(gobject.TYPE_PYOBJECT,
                                                str, gtk.gdk.Pixbuf, int)
            self.imagetreestore.connect('row-inserted', self._ImageTreeStoreMessage_inserted)
            #self.imagetreestore.connect('row-changed', self._ImageTreeStoreMessage_changed)
            self.imagetreestore.connect('row-deleted', self._ImageTreeStoreMessage_deleted)
            
            sql = "SELECT image_id FROM albumimage WHERE parent_id=%s"
            cursor = self.idb.dbh.cursor()
            imagesloaded = []
            cursor.execute(sql,self['id'])
            rows = cursor.fetchall()
            for row in rows :
                imagesloaded.append(row[0])
                image = Image(self.idb,row[0], self.imagetreestore)
                self.imagetreestore.append(None, [image,
                                                  image['basename'],
                                                  None, 0])
            sql = """SELECT id FROM image WHERE directory_id IN 
                 (SELECT id FROM directory WHERE albumpage_id=%s)"""

            cursor.execute(sql, self.id)
            rows = cursor.fetchall()
            for row in rows :
                if not row[0] in imagesloaded :
                    imagesloaded.append(row[0])
                    image = Image(row[0])
                    self.imagetreestore.append(None, [image,
                                                      image['basename'],
                                                      None, 0])
            sql = """SELECT id FROM image WHERE directory_id=
                 (SELECT id FROM directory WHERE albumpage_id=%s)"""
            rows = cursor.fetchall()
            for row in rows :
                if not row[0] in imagesloaded :
                    imagesloaded.append(row[0])
                    image = Image(row[0])
                    self.imagetreestore.append(None, [image,
                                                      image['basename'],
                                                      None, 0])
            
    def _ImageTreeStoreMessage_inserted(self, a, b) :
        print "ImageTreeStoreMessage inserted", self, a, b
        
    def _ImageTreeStoreMessage_changed(self, a, b) :
        print "ImageTreeStoreMessage changed", self, a, b
        
    def _ImageTreeStoreMessage_deleted(self, a, b) :
        print "ImageTreeStoreMessage deleted", self, a, b
        
        
    def Delete(self):
        albumid = self.id
        cursor = self.idb.dbh.cursor()
        
        sql = "SELECT id FROM album WHERE parent_id=%s"
        cursor.execute(sql,albumid)
        rows = cursor.fetchall()
        for row in rows:
            self.RemoveAlbum(row[0])

        self.idb.Delete('albumimage', 'parent_id', albumid, cursor)
        cursor.execute(sql, albumid)
        sql = """DELETE FROM albumimage WHERE image_id IN 
                 (SELECT id FROM image WHERE directory_id=
                 (SELECT id FROM directory WHERE albumpage_id=%s))"""
        cursor.execute(sql, albumid)
        sql = """DELETE FROM imageinstance WHERE directory_id=
                 (SELECT id FROM directory WHERE albumpage_id=%s)"""
        cursor.execute(sql, albumid)
        sql = """DELETE FROM image WHERE directory_id=
                 (SELECT id FROM directory WHERE albumpage_id=%s)"""
        cursor.execute(sql, albumid)
        self.idb.Delete('directory', 'albumpage_id', albumid, cursor)
        self.idb.Delete('album', 'id', albumid, cursor)

    def images(self) :
        self._CreateImageTreeStore()
        return self.imagetreestore
    def albums(self) :
        self._CreateAlbumTreeStore()
        return self.albumtreestore

    def Forget(self) :
        self.imagetreestore.clear()
        self.imagetreestore = None

class IDBPostgreSQL(IDB) :
    def __init__(self, host, port, database, username, password) :
        IDB.__init__(self)
        self.dbh = PgSQL.connect(":".join([host, port, database, username, password]))
        self.albumtreestore = gtk.TreeStore(gobject.TYPE_PYOBJECT,
                                            str, gtk.gdk.Pixbuf, int, int)
        self.canViewExtensions = [
            '.jpg',
            '.jpeg',
            '.thm',
            ]
        self.canTrackExtensions = [
            '.bmp',
            '.png',
            '.jpeg',
            '.jpg',
            '.thm',
            '.gif',
            '.pcx',
            '.pnm',
            '.tiff',
            '.tiff',
            '.iff',
            '.xpm',
            '.ico',
            '.cur',
            '.ani',
            ]

    def canViewFilename(self, filename) :
        if '.' in filename :
            if filename[filename.rindex('.'):] in self.canViewExtensions :
                return True
        return False;
        
    def canTrackFilename(self, filename) :
        if '.' in filename :
            if (self.canViewFilename(filename)) :
                return True
            elif filename[filename.rindex('.'):] in self.canTrackExtensions :
                return True
        return False;

    def _ChaseAlbum(self, paths, iter = None) :
        print "Chase Album", paths, iter
        path = paths.pop()
        print "Path popped", path
        album = None
        i = 0
        n = self.albumtreestore.iter_n_children(iter)
        print "N children", n
        while i < n :
            print path, i, n
            childiter = self.albumtreestore.iter_nth_child(iter, i)
            print "Value", self.albumtreestore.get(childiter, 1), path
            ret = None
            if self.albumtreestore.get(childiter, 1)[0] == path :
                album = self._ChaseAlbum(paths, childiter)
            if album != None:
                return album
            i = i + 1

        while path != None :
            album = Album(self, None)
            album['name'] = path
            iter = self.albumtreestore.append(iter, [album, album['name'], None,
                                            0,
                                            0])
            album.Write()
            path = None
            if paths :
                path = paths.pop()
            
        return album
            
            
            
    def GetAlbumFromPath(self, path) :
        paths = []
        p,d = os.path.split(path)
        while d :
            paths.append(d)
            p,d = os.path.split(p)
        paths.append('Files')
        print "Chasing path: ", paths
        return self._ChaseAlbum(paths)


    def GetAlbumRow(self, a) :
        return [a, a['name'], None,
                a['name_changeable'] and 1 or 0,
                a['allow_user_children'] and 1 or 0]
    
    def GetAlbumFromDir(self, dir) :
        album = self.GetAlbumFromPath(dir)
        cursor = self.dbh.cursor()
        sql = 'SELECT id,albumpage_id FROM directory WHERE path=%s'
        cursor.execute(sql, dir)
        rows = cursor.fetchall()
        if rows :
            if rows[0][1] == album['id'] :
                return album
            #ZZZZZZZZZZZZZ throw GenericError("Album for " + dir
            #                   + " doesn't match entry from directory database "
            #                   + rows[0][0])
        else :
            sql = 'INSERT INTO directory(albumpage_id, path) VALUES (%s,%s)'
            cursor.execute(sql, album['id'], dir)

            sql = 'SELECT id,albumpage_id FROM directory WHERE path=%s'
            cursor.execute(sql, dir)
            rows = cursor.fetchall()
        return album, rows[0][0]

    def LoadAlbums(self, parentid = None, iter = None) :
        cursor = self.dbh.cursor()
        if parentid == None :
            sql = 'SELECT id,name,listorder FROM album WHERE parent_id IS NULL ORDER BY listorder'
            cursor.execute(sql)
        else :
            sql = 'SELECT id,name,listorder FROM album WHERE parent_id=%s ORDER BY listorder'
            cursor.execute(sql, parentid)
        rows = cursor.fetchall()
        self.CommitRead()

        for row in rows :
            a = Album(self, row[0])
            album = self.GetAlbumRow(a)
            i = self.albumtreestore.append(iter, album)
            self.LoadAlbums(a['id'], i)

    def GetAlbum(self, paths) :
        cursor = None
        album = None
        for path in paths :
            insertWhere = 0
            if album == None :
                for p in self.albumtreestore :
                    if p[0]['name'] == path :
                        album = p
#                if album == None :
#                    sql = "SELECT id,name FROM album WHERE parent_id IS NULL ORDER BY listorder"
#                    if cursor == None :
#                        cursor = self.dbh.cursor()
#                    cursor.execute(sql)
#                    rows = cursor.fetchall()
#                    for row in rows :
#                        if row[1] == path :
#                            a = Album(self, row[0])
#                            print a['name_changeable'], a['allow_user_children']
#                            album = [a, a['name'], None,
#                                     a['name_changeable'] and 1 or 0,
#                                     a['allow_user_children'] and 1 or 0]
#                            self.albumtreestore.append(None, album )
#                            album = self.albumtreestore[-1]
            else :
                parentid = album[0]['id']
                albumchildren = album.iterchildren()
                album = None
                for p in albumchildren:
                    if p[0]['name'] == path :
                        album = p
#                if album == None :
#                    if cursor == None :
#                        cursor = self.dbh.cursor()
#                    sql = "SELECT id,name FROM album WHERE parent_id=%s"
#                    print sql, path, parentid
#                    cursor.execute(sql, parentid)
#                    rows = cursor.fetchall()
#                    for row in rows :
#                        if row[1] == path :
#                            a = Album(self, row[0])
#                            album = [a, a['name'], None,
#                                     a['name_changeable'] and 1 or 0,
#                                     a['allow_user_children'] and 1 or 0]
#                            self.albumtreestore.append(None, album )
#                            album = self.albumtreestore[-1]
        if cursor != None :
            self.CommitRead()
        if album == None :
            return None
        return album[0]

    def GetImage(self, album, name) :
        if album == None:
            return None
        
        cursor = self.dbh.cursor()
        sql = """SELECT image.id FROM image, albumimage
                 WHERE image.id = albumimage.image_id
                       AND parent_id=%s AND image.basename=%s"""
        cursor.execute(sql, album['id'], name)
        row = cursor.fetchone()
        if row:
            return Image(self, row[0], album.ImageTreeStore())
        return None

    def GetAlbums(self, album ) :
        cursor = self.dbh.cursor()
        if (album   == None) :
            sql = "SELECT id FROM album WHERE parent_id IS NULL"
            cursor.execute(sql)
        else:
            sql = "SELECT id FROM album WHERE parent_id=%s"
            cursor.execute(sql, album['id'])
        rows = cursor.fetchall()
        return [Album(self,row[0]) for row in rows]

    def GetImages(self, album) :
        cursor = self.dbh.cursor()
        if (album == None) :
            sql = """SELECT image_id FROM albumimage
                     WHERE parent_id IS NULL"""
            cursor.execute(sql)
        else:
            sql = """SELECT image_id FROM albumimage
                     WHERE parent_id=%s"""
            cursor.execute(sql, album['id'])
        rows = cursor.fetchall()
        return [Image(self,row[0], album.ImageTreeStore()) for row in rows]


        
    def CommitWrite(self) :
        self.dbh.commit()
    def CommitRead(self) :
        self.dbh.commit()

class Importer :
    def __init__(self, idb, dir) :
        self.idb = idb
        self.paths = []
        for root, dirs, files in os.walk(dir) :
            self.paths.append((root, files))

    def tick(self) :
        if not self.paths :
            return False
        dir, files = self.paths.pop()
        album,dirid = self.idb.GetAlbumFromDir(dir)
        extantimages = album.images()
        imageexists = {}
        for image in extantimages :
            imageexists[image['basename']] = image
        
        basenames = {}
#        for file in files :
#            if '.' in file and self.idb.canTrackFilename(file) :
#                basename = file[:file.index('.')]
#                if basename != "" :
#                    if not basenames.has_key(basename) :
#                        basenames[basename] = []
#                    basenames[basename].append(file)
#                    
#        for basename, files in basenames.iteritems() :
#            if imageexists.has_key(basename) :
#                image = imageexists[basename]
#            else :
#                sql = 'SELECT id FROM image WHERE directory_id=%s AND basename=%s'
#                cursor = self.idb.dbh.cursor()
#                cursor.execute(sql, dirid, basename)
#                row = cursor.fetchone()
#                if row :
#                    print "Creating image with", row[0]
#                    image = Image(self.idb, row[0], album.ImageTreeStore())
#                else :
#                    print "Creating new image"
#                    image = Image(self.idb, None, album.ImageTreeStore())
#                image['directory_id'] = dirid
#                image['basename'] = basename
#                image.Write()
#                album.AddImage(image)
#            for file in files :
#                imageinstance = ImageInstance(self.idb, None, image)
#                imageinstance['name'] = file
#                imageinstance['directory_id'] = dirid
#                imageinstance['image_id'] = image['id']
#                fullname = os.path.join(dir, file)
#                height = None
#                width = None
#                try :
#                    d = process_file(fullname)
#                    width = d['EXIF ExifImageWidth']
#                    height = d['EXIF ExifImageLength']
#                    d = None
#                except :
#                    try:
#                        pixbuf = gtk.gdk.pixbuf_new_from_file(fullname)
#                        width = pixbuf.get_width()
#                        height = pixbuf.get_height()
#                        pixbuf = None
#                    except :
#                        pass
#                imageinstance['width'] = width
#                imageinstance['height'] = height
#                imageinstance.Write()
#                imageInstance = None
#            image = None
#            self.idb.CommitWrite()
        album.Forget()
        album = None
        if self.paths :
            return True
        return False    

import sys
if __name__ == '__main__':
    idb = IDBPostgreSQL('127.0.0.1','','flutterby', 'danlyke', 'danlyke')
    cmd = sys.argv[1]
    if cmd == 'ls' :
        idb.LoadAlbums()
        album = idb.GetAlbum(sys.argv[2:])
        albums = idb.GetAlbums(album)
        for a in albums:
            print "d ", a['name']
        images = idb.GetImages(album)
        for i in album.images() :
            print "i ", i[0]['id'], i[0]['basename']
        idb.CommitRead()
        
    if cmd == 'rm' :
        album = idb.GetAlbum(sys.argv[2:])
        album.Delete()
        idb.CommitWrite()

    if cmd == 'show' :
        fields = sys.argv[2]
        idb.LoadAlbums()
        album = idb.GetAlbum(sys.argv[2:-1])
        image = idb.GetImage(album, sys.argv[-1])
        for f in image.keys() :
            print f, image[f]
        idb.CommitRead()

    if cmd == 'set' :
        field = sys.argv[2]
        value = sys.argv[3]
        idb.LoadAlbums()
        album = idb.GetAlbum(sys.argv[3:-1])
        image = idb.GetImage(album, sys.argv[-1])
        image[field] = value
        image.Write(idb.dbh.cursor())
        idb.CommitWrite()
        
    if cmd == 'import' :
        for dir in sys.argv[2:] :
            idb.LoadAlbums()
            importObj = Importer(idb, dir)
            while importObj.tick() :
                pass
