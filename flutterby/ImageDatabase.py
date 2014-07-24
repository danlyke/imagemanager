# from pyPgSQL import PgSQL, libpq
from xml.dom import minidom
import sqlite3 as sqlite
import GeoLookup
import types
import re    
import os
import stat
import gtk
import gobject
from EXIF import *
import time
import gc
class _AlbumList :
    instance = None
    def __init__(self, imageDatabase):
        self.imageDatabase = imageDatabase
        self.albumlist = gtk.TreeStore(gtk.gdk.Pixbuf, str,
                                       gobject.TYPE_PYOBJECT, int, int)
        self.load_album_tree()

    def FindIterFromId(self, id, parentiter = None) :
        nchildren = self.iter_n_children(parentiter)
        row = 0
        while row < nchildren :
            iter = self.iter_nth_child(parentiter, row)
            if self.get_db_id_at_iter(iter) == id :
                return iter
            subiter = self.FindIterFromId(id, iter)
            if subiter != None :
                return subiter
            row = row + 1
        return None

    def InsertOrUpdateAlbum( self, parent, album_id, name, name_editable ) :
        if parentiter != None :
            parent_id = self.get(iter, 4)
        if album_id != None :
            iter = FindIterFromId(self, album_id, parent_id )
            
    
    def UpdateAlbum( self, parentiter, parent_id, album_id, name, name_editable = False ) :
        iter = self.FindIterFromId( album_id )

        if iter == None :
            if parentiter == None :
                parentiter = self.FindIterFromId(parent_id);
                
            iter = self.albumlist.append(parentiter)
            if parentiter == None :
                parentalbum = None
            else:
                parentalbum = self.get_value(parentiter, 2)
            albumobj = self.imageDatabase.AlbumNode(self.imageDatabase,
                                                    album_id,
                                                    parentalbum,
                                                    name)
            self.set(iter, 2, albumobj)
            self.set(iter, 3, name_editable)
            self.set(iter, 4, album_id)

        self.albumlist.set(iter, 1, name)
        if name_editable :
            name_editable = '1'
        else:
            name_editable = '0'
        self.imageDatabase.update_record('album', album_id,
                                         {
            'name' : name,
            'name_changeable' : name_editable,
            })
        return iter
    
        
    def Add(self, node, parent_id, name, name_changeable) :
        """ Add a child to the treestore and the database """
        
        parentiter = None
        if parent_id != None :
            parentiter = self.FindIterFromId(parent_id)
            if parentiter == None :
                raise "Attempt to add an album to thge album list with invalid parent id %s" % str(parent_id)

        iter = self.albumlist.append(parentiter)
        self.albumlist.set(iter, 1, name)
        self.albumlist.set(iter, 2, node)
        self.albumlist.set(iter, 3, name_changeable)

        if name_changeable :
            name_changeable = '1'
        else :
            name_changeable = '0'
        id = self.imageDatabase.insert_new_record('album',
                                                  {
                    'parent_id' : parent_id,
                    'name' : name,
                    'name_changeable' : name_changeable,
                    })
        self.albumlist.set(iter, 4, id)
        return id


    def iter_n_children(self,parentiter):
        return self.albumlist.iter_n_children(parentiter)

    def iter_nth_child(self,parentiter, i):
        return self.albumlist.iter_nth_child(parentiter, i)

    def get(self, iter, n):
        return self.albumlist.get(iter, n)
    def set(self, iter, n, w):
        return self.albumlist.set(iter, n, w)

    def get_path(self,iter):
        return self.albumlist.get_path(iter)
    
    def get_value(self,iter, n):
        return self.albumlist.get_value(iter, n)
    def get_album(self, iter) :
        return self.albumlist.get_value(iter, 2)
    def get_iter(self,path):
        return self.albumlist.get_iter(path)
    
    def renderer_editable_text_cell_album_edited(self, renderer, path, newtext) :
        iter = self.albumlist.get_iter_from_string(path)
        if self.albumlist.get_value(iter,2).change_name(newtext) :
            self.albumlist.set(iter,1, newtext)

    def get_editable_from_path(self, path) :
        if path != None :
            iter = self.albumlist.get_iter(path)
            if self.albumlist.get_value(iter, 3) :
                return True
        return False
        

    def copy_images_for_album_ids(self, oldid, newid) :
        cursor = self.imageDatabase.dbh.cursor()
        sql = 'SELECT parent_id, image_id, nextimage_id FROM albumimage WHERE parent_id=%s'
        cursor.execute(sql, oldid)
        rows = cursor.fetchall()
        for row in rows :
            sql = 'INSERT INTO albumimage(parent_id, image_id,nextimage_id) VALUES (%s,%s,%s)'
            cursor.execute(sql, newid, row[1],row[2])
        self.imageDatabase.commit_write()

    def copy_node_subtree(self, parentiter, parentid, dbid) :
        cursor = self.imageDatabase.dbh.cursor()
        if dbid == None:
            sql = 'SELECT id,name,name_changeable FROM album WHERE parent_id IS NULL'
            cursor.execute(sql)
        else:
            sql = 'SELECT id,name,name_changeable FROM album WHERE parent_id=%s'
            cursor.execute(sql, dbid)
            
        rows = cursor.fetchall()
        parentnode = None
        if parentiter != None :
            parentnode = self.albumlist.get_value(parentiter, 2)

        for row in rows:
            iter = self.albumlist.append(parentiter)
            self.albumlist.set(iter, 1, row[1])
            if row[2] :
                self.albumlist.set(iter, 3, 1)
            else :
                self.albumlist.set(iter, 3, 0)
            albumnode = self.imageDatabase.AlbumNode(self.imageDatabase,
                                                            row[0],
                                                            parentnode,
                                                            row[1],row[2])
            self.albumlist.set(iter,2,albumnode)
            self.albumlist.set(iter, 4, albumnode.id)
            self.copy_node_subtree(iter, albumnode.id, row[0])
            self.copy_images_for_album_ids(row[0],albumnode.id)
    def drop_at_path(self, path, selection) :
        print "Dropping at path",path,  selection, selection.data
        
        if isinstance(selection.data, types.StringType) :
            parentiter = self.albumlist.get_iter(path)
            parentnode= self.albumlist.get_value(parentiter, 2)
            names = [n for n in selection.data.split("\n") if n != '' and n[:6] != 'album:']
            for n in names :
                print "Dropped name ", n
            images = self.imageDatabase.find_images_from_names(names)
            parentnode.add_images(images)

            names = [n[6:] for n in selection.data.split("\n") if n != '' and n[:6] == 'album:']
            cursor = self.imageDatabase.dbh.cursor()
            for name in names :
                sql = 'SELECT id,name,name_changeable FROM album WHERE id=%s'
                cursor.execute(sql, name)
                rows = cursor.fetchall()
                for row in rows:
                    iter = self.albumlist.append(parentiter)
                    self.albumlist.set(iter, 1, row[1])
                    if row[2] :
                        self.albumlist.set(iter, 3, 1)
                    else :
                        self.albumlist.set(iter, 3, 0)
                    albumnode = self.imageDatabase.AlbumNode(self.imageDatabase,
                                                             None,
                                                             parentnode,
                                                             row[1],row[2])
                    self.albumlist.set(iter,
                                       2,
                                       albumnode)
                    self.albumlist.set(iter, 4, albumnode.id)
                    self.copy_images_for_album_ids(row[0],albumnode.id)
                    self.copy_images_for_album_ids(row[0],albumnode.id)
        self.imageDatabase.commit_write()

    def get_db_id_at_iter(self,iter) :
        parent_id = self.albumlist.get_value(iter, 4)
        return parent_id
    def get_albumnode_at_iter(self,iter) :
        parent_id = self.albumlist.get_value(iter, 2)
        return parent_id
    def get_db_id_at_path(self,path) :
        iter = self.albumlist.get_iter(path)
        return self.get_db_id_at_iter(iter)

    def get_albumnode_at_path(self,path) :
        iter = self.albumlist.get_iter(path)
        return self.get_albumnode_at_iter(iter)
 
       
    def insert_new_album_node_under_path(self, path) :
        parentiter = None
        parentnode = None
        if path != None :
            parentiter = self.albumlist.get_iter(path)
            parentnode = self.albumlist.get_value(parentiter, 2)
            
        iter = self.albumlist.append(parentiter)
        n = self.imageDatabase.AlbumNode(self.imageDatabase, None,
                                         parentnode,
                                         'New Album', True)
        self.albumlist.set(iter,1, 'New Album')
        self.albumlist.set(iter, 2, n )
        self.albumlist.set(iter,3, True)
        self.albumlist.set(iter,4, n.id)

    def delete_album_node_at_path(self, path) :
        if path != None :
            iter = self.albumlist.get_iter(path)
            if self.albumlist.get_value(iter,3) :
                node = self.albumlist.get_value(iter, 2)
                self.albumlist.remove(iter)
                node.delete()
        
    def load_album_tree(self, parentid = None, parentiter = None) :
        self.imageDatabase._loadIconNamesArray()
        cursor = self.imageDatabase.dbh.cursor()
        if parentiter == None:
            sql = """SELECT album.id AS id,
                            album.name AS name,
                            album.name_changeable AS name_changeable,
                            album.type AS type
                     FROM album WHERE parent_id IS NULL ORDER BY name"""
            cursor.execute(sql)
        else:
            sql = """SELECT album.id AS id,
                            album.name AS name,
                            album.name_changeable AS name_changeable,
                            album.type AS type
                     FROM album WHERE parent_id=%s ORDER BY name"""
            cursor.execute(sql, parentid)
            
        rows = cursor.fetchall()
        parentnode = None
        if parentiter != None :
            parentnode = self.albumlist.get_value(parentiter, 2)

        for row in rows:
            iter = self.albumlist.append(parentiter)
            if row[3] != None :
                self.albumlist.set(iter,0,
                                   gtk.gdk.pixbuf_new_from_file('./icons/'+
                                                                self.imageDatabase.iconnames[row[3]]))
            self.albumlist.set(iter, 1, row[1])
            if row[2] :
                self.albumlist.set(iter, 3, 1)
            else :
                self.albumlist.set(iter, 3, 0)
            self.albumlist.set(iter,
                               2,
                               self.imageDatabase.AlbumNode(self.imageDatabase,
                                                            row[0],
                                                            parentnode,
                                                            row[1],row[2]))
            if row[0] != None :
                self.albumlist.set(iter, 4, row[0])
            self.load_album_tree(row[0], iter)
        if parentid == None :
            self.imageDatabase.commit_read()



def AlbumList(imageDatabase) :
    if _AlbumList.instance == None:
        _AlbumList.instance = _AlbumList(imageDatabase)
    return _AlbumList.instance



class ImageDatabaseSQL :
    """This is the base class for all SQL based image databases
    """
    class AlbumNode :
        """A node to represent an album in the album tree
        """
        def __init__(self,imageDatabase,id,parentnode,name,name_changeable = True,
                     prevalbum_id = None, findid = False) :
            self.imageDatabase = imageDatabase
            parentnode_id = None
            if parentnode != None:
                parentnode_id = parentnode.id
            if id == None :
                if findid :
                    cursor = self.imageDatabase.dbh.cursor()
                    if parentnode_id == None :
                        sql = 'SELECT id FROM album WHERE name=%s AND parent_id IS NULL'
                        cursor.execute(sql, name)
                    else :
                        sql = 'SELECT id FROM album WHERE name=%s AND parent_id=%s'
                        cursor.execute(sql, name, parentnode_id)
                    row = cursor.fetchone()
                    if row :
                        id = row[0]
                        albumiter = AlbumList(self.imageDatabase).UpdateAlbum(None, parentnode_id, id, name);
                if id == None :
                    id = AlbumList(self.imageDatabase).Add(self, parentnode_id, name, name_changeable)
            self.id = id
            self.name = name
            self.name_changeable = name_changeable
            self.prevalbum_id = prevalbum_id

        def get_deletable(self):
            return self.name_changeable

        def get_editable(self):
            return name_changeable

        def add_images(self, images) :
            """Add an array of image objects under the album node,
            inserting them into the database.
            """
            cursor = self.imageDatabase.dbh.cursor()
            for i in range(len(images)) :
                image = images[i]
                if i + 1 < len(images):
                    nextimage_id = images[i+1]['id']
                else :
                    nextimage_id = None
                sql = 'SELECT parent_id, image_id, nextimage_id FROM albumimage WHERE parent_id=%s AND image_id=%s'
                cursor.execute(sql, self.id, image['id'])
                row = cursor.fetchone()
                
                if row :
                    if row[2] != nextimage_id :
                        sql = 'UPDATE albumimage SET nextimage_id=%s WHERE parent_id=%s AND image_id=%s'
                        cursor.execute(sql, nextimage_id, self.id, image['id'])
                else :
                    sql = 'INSERT INTO albumimage(nextimage_id, parent_id, image_id) VALUES (%s,%s,%s)'
                    cursor.execute(sql, nextimage_id, self.id, image['id'])
            self.imageDatabase.commit_write()
                

        def change_name(self,name):
            if self.name_changeable and self.name != name:
                self.name = name
                albumiter = AlbumList(self.imageDatabase).UpdateAlbum(None, None,
                                                                      self.id, name);
                self.imageDatabase.update_record('album', self.id,
                                                 {
                    'name' : self.name,
                    })
                self.imageDatabase.commit_write()
                return True
            return False

        def _cascade_sql_delete(self, id) :
            cursor = self.imageDatabase.dbh.cursor()
            sql = 'SELECT id FROM album WHERE parent_id=%s'
            cursor.execute(sql,id)
            rows = cursor.fetchall()
            for row in rows :
                self.cascade_sql_delete(row[0])
                
            sql = 'DELETE FROM albumimage WHERE parent_id=%s'
            cursor.execute(sql,id)
            sql = 'DELETE FROM album WHERE id=%s'
            cursor.execute(sql,id)
            
            
        def delete(self):
            cursor = self.imageDatabase.dbh.cursor()
            self._cascade_sql_delete(self.id)
            self.imageDatabase.commit_write()
    
    class Image:
        """Image is an instance that can be dynamically loaded"""
        
        class ImageInstance :
            def __init__(self, id, path, size = None) :
                self.id = id
                self.size = size
                self.path = path
            def get_path(self) :
                return self.path


        def __init__(self, dbmanager, id = None):
            self.data = {}
            self.instances = None
            self.dbmanager = dbmanager
            self.data['id'] = id
            self.loaded = False
            
        def __setitem__(self, key, item):
            self.data[key] = item
        def __getitem__(self, key) :
            if key == 'thumbnail' and not self.data.has_key(key):
                try :
                    os.stat(self._get_microthumb_name())
                except:
                    pb = gtk.gdk.pixbuf_new_from_file(self.get_thumbnail_filename())
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
                    pb.save(self._get_microthumb_name(), 'jpeg')
                    pb = None
                    gc.collect()
                self['thumbnail'] = gtk.gdk.pixbuf_new_from_file(self._get_microthumb_name())
                
            return self.data[key]
        def has_key(self, key) :
            return self.data.has_key(key)

        def _get_microthumb_name(self) :
            return os.path.join(self.dbmanager.scratchdir, 'thumbs', str(self['id'])+'.jpg')

        def get_thumbnail_filename(self) :
            self.load_instances()
            return self.instances[0].get_path()
            

        def get_image_instances(self) :
            self.load_instances()
            return self.instances

        def load_instances(self) :
            assert self.data['id']
            if self.instances != None:
                return

            rows = (
                'imageinstance.id',
                'directory.path',
                'imageinstance.name',
                'imageinstance.width',
                'imageinstance.height'
                );
            
            sql = "SELECT " + ','.join(rows) +  \
                  """ FROM imageinstance,directory
                  WHERE image_id=%s AND imageinstance.directory_id = directory.id
                  ORDER BY imageinstance.width"""
            
            cursor = self.dbmanager.dbh.cursor()
            cursor.execute(sql, self.data['id'])
            self.instances = []
            row = cursor.fetchone()
            while row :
                instance = self.ImageInstance(row[0],
                                              os.path.join(row[1], row[2]),
                                              (row[3],row[4]))
                self.instances.append(instance)
                row = cursor.fetchone()

        def reload(self, id = None) :
            self.loaded = False
            self.load(id)
            
        def load(self, id = None) :
            if id != None :
                self.data['id'] = id
            assert self.data['id']

            if self.loaded :
                return
            self.loaded = True

            fields = ('id',
                      'basename',
                      'title',
                      'taken',
                      'technotes',
                      'description',
                      'camera_longitude',
                      'camera_lattitude',
                      'camera_position_accuracy',
                      'subject_longitude',
                      'subject_lattitude',
                      'subject_position_accuracy')
            sql = 'SELECT ' + ','.join(fields) + ' FROM image WHERE id=%s'
            cursor = self.dbmanager.dbh.cursor()
            cursor.execute(sql, self['id'])
            row = cursor.fetchone()
            if row :
                for i in range(len(fields)) :
                    self[fields[i]] = row[i]
                    i = i+1
                for f in ('camera_longitude',
                          'camera_lattitude',
                          'camera_position_accuracy',
                          'subject_longitude',
                          'subject_lattitude',
                          'subject_position_accuracy'):
                    if self[f] != None and self[f] != '':
                        self[f] = "%f" % self[f]

                for f in fields :
                    if self[f] == None :
                        self[f] = ''
                    self[f] = str(self[f])
            self.dbmanager.commit_read()



    def __init__(self, scratchdir):
        self.iconnames = None;
        self.scratchdir = scratchdir
        try :
            if not stat.S_ISDIR(os.stat(self.scratchdir)[0]) :
                os.makedirs(os.path.join(self.scratchdir, 'thumbs'))
        except:
            os.makedirs(os.path.join(self.scratchdir, 'thumbs'))
        self.entityClasses = ['Person', 'Place', 'Thing', 'Event']
        self.entityClassIDs = None
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
            
    def get_or_insert_record(self, table, values) :
        keys = [k for k in values.keys() if values[k] != None]
        nullkeys = [k for k in values.keys() if values[k] == None]
        
        whereclause = ' AND '.join([k + '=%s' for k in keys])
        if len(nullkeys) > 0 :
            whereclause = whereclause + ' AND ' + ' AND '.join(
                [k + ' IS NULL' for k in nullkeys])
        sql = 'SELECT id FROM %s WHERE ' % table + whereclause
        
        cursor = self.dbh.cursor()
        cursor.execute(sql, *[values[k] for k in keys])
        row = cursor.fetchone()
        if row :
            return row[0]
        return self.insert_new_record(table, values)
        
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

    def _loadEntityClassIDs(self):
        if self.entityClassIDs == None:
            self.entityClassIDs = {}
            cursor = self.dbh.cursor()
            for c in self.entityClasses :
                self.entityClassIDs[c] = self.AlbumNode(self, None, None, c,
                                                   False, None, True );
    def commit_read(self) :
        self.dbh.commit()
        
    def commit_write(self) :
        self.dbh.commit()


    def _loadIconNamesArray(self) :
        if self.iconnames == None :
            self.iconnames = {}
            cursor = self.dbh.cursor()
            cursor.execute('SELECT id,icon_name FROM filesystemaccesstypes')
            rows = cursor.fetchall()
            for row in rows :
                self.iconnames[row[0]] = row[1];
            self.commit_read()
                            
        
    def get_image_from_id(self,id):
        if self.iconnames == None :
            self._loadIconNamesArray()

        values = {}
        image = self.Image(self, id)
        image.load()
        return image
        

    def find_image_from_filename(self, name) :
        images = self.find_images_from_filenames([name])
        return images[0]


    def basename(self, f) :
        basename = f
        if '.' in f :
            basename = basename[:basename.index('.')]
        return basename

    def setAlbumToDirectoryPath(self, dir_id, dir):
        paths = []
        parent = None
        album = None;
        path = dir
        lastpath = None
        while path != lastpath :
            lastpath = path
            (path,end) = os.path.split(path)
            paths.append(end)
        while len(paths) > 0 :
            name = paths.pop()
            if name != '' :
                parent = album
                album = self.AlbumNode( self, None, parent,
                                   name, False,
                                   None,
                                   True );
                cursor = self.dbh.cursor()
                sql = 'UPDATE directory SET albumpage_id=%s WHERE id=%s'
                cursor.execute(sql,album.id, dir_id);
        return album

    def GetOrInsertImageRecord(self, dir_id, taken, techinfo, basename) :
        sql = 'SELECT id FROM image WHERE directory_id=%s AND basename=%s'
        cursor = self.dbh.cursor()
        cursor.execute(sql, dir_id, basename)
        row = cursor.fetchone()
        if row :
            return row[0]
        return self.insert_new_record('image',  {
            'directory_id' : dir_id,
            'taken' : taken,
            'technotes' : techinfo,
            'basename' : basename,
            })

    def GetImageSizeFromFilename(self, name) :
        taken = None
        techinfo = ''

        try :
            f = open(name, 'rb')
            d = process_file(f)
            f.close()
            width = d['EXIF ExifImageWidth']
            height = d['EXIF ExifImageLength']
            taken = str(d['EXIF DateTimeOriginal'])
#            if taken[4] == ':' :
#                taken[4] = '-'
#            if taken[7] == ':' :
#                taken[7] = '-'
            techinfo = ' / '.join([ v + " : " + str(d[k])
                                    for (k,v) in (
                ('Image Model','Camera model')
                ('EXIF ISOSpeedRatings', 'ISO'),
                ('EXIF ExposureTime', 'Exposure time:'),
                ('EXIF FocalLength', 'Focal length (ratio)'),
                ('EXIF ApertureValue', 'Aperture'),
                ) if d.has_key(k) ])
            d = None
        except :
            c = re.compile('.* ([0-9]+) x ([0-9]+) .*')
            p = os.popen('jpeginfo ' + name)
            a = p.readline()
            while a :
                m = c.match(a)
                if m :
                    (width, height) = m.groups()
                    p.close()
                    return (width, height, taken, techinfo)
                a = p.readline()
            p.close()
                
            return (None, None, taken, techinfo)
            pixbuf = gtk.gdk.pixbuf_new_from_file(name)
            width = pixbuf.get_width()
            height = pixbuf.get_height()
            pixbuf = None
        return (width, height, taken, techinfo)
    
    def find_images_from_filenames(self, names) :
        image_ids = {}
        dirs = {}
        ret = []
        for name in names :
            if name[0] == '.' :
                pass
            if stat.S_ISREG(os.stat(name)[0]) :
                dir,f = os.path.split(name)

                if not dirs.has_key(dir) :
                    cursor = self.dbh.cursor()
                    sql = 'SELECT id,albumpage_id FROM directory WHERE accesstype_id=1 AND path=%s'
                    cursor.execute(sql,dir)
                    row = cursor.fetchone()
                    if row :
                        dir_id = row[0]
                        if not row[1] :
                            self.setAlbumToDirectoryPath(dir_id, dir)
                    else:
                        dir_id = self.insert_new_record('directory',{'accesstype_id' : '1', 'path' : dir})
                        self.setAlbumToDirectoryPath(dir_id, dir)

                    dirs[dir] = (dir_id, {})
                basename = self.basename(f)
                if not dirs[dir][1].has_key(basename) :
                    dirs[dir][1][basename] = {}
                if not dirs[dir][1][basename].has_key(f) :
                    dirs[dir][1][basename][f] = True
            elif stat.S_ISDIR(os.stat(name)[0]) :
                sdir = [os.path.concat(name, n) for n in os.listdir(name)
                        if (stat.S_ISDIR(os.stat(os.path.concat(name,n)))
                            or (self.canViewFilename(n)
                                and stat.S_ISREG(os.path.concat(name,n))))]
                ret.extend(self.find_images_from_filenames(sdir))
        self.dbh.commit()
        for dir in dirs.iterkeys() :
            dirinfo = dirs[dir][1]
            files = os.listdir(dir)
            
            for file in files :
                basename = self.basename(file)
                if dirinfo.has_key(basename) :
                    dirinfo[basename][file] = True

        for dir in dirs.iterkeys() :
            dirinfo = dirs[dir][1]
            for basename in dirinfo.iterkeys() :
                for f in dirinfo[basename].iterkeys() :
                    sql = 'SELECT image_id FROM imageinstance WHERE name=%s AND directory_id=%s'
                    cursor.execute(sql,f,dir_id)
                    row = cursor.fetchone()
                    if row :
                        image_ids[row[0]] = True
                    else :
                        sql = 'SELECT image_id, name FROM imageinstance WHERE directory_id=%s'
                        cursor.execute(sql, dir_id)
                        rows = cursor.fetchall()
                        for row in rows :
                            if self.basename(row[1]) == basename :
                                (width, height, taken, techinfo) = self.GetImageSizeFromFilename(os.path.join(dir,f))
                                self.insert_new_record('imageinstance',
                                                       {
                                    'width' : width,
                                    'height' : height,
                                    'directory_id' : dir_id,
                                    'name' : f,
                                    'image_id' : row[0],
                                    })
                                image_ids[row[0]] = True
                                break
                        else:
                            (width, height, taken, techinfo) = self.GetImageSizeFromFilename(os.path.join(dir,f))
                            image_id = self.GetOrInsertImageRecord( dir_id, taken, techinfo, basename)
                            sql = 'INSERT INTO albumimage(generatedlink, parent_id, image_id) VALUES (1, (SELECT albumpage_id FROM directory WHERE id=%s), %s)'
                            cursor.execute(sql, dir_id, image_id)
                            
                            self.insert_new_record('imageinstance',
                                                   {
                                'width' : width,
                                'height' : height,
                                'directory_id' : dir_id,
                                'name' : f,
                                'image_id' : image_id,
                                })
                            image_ids[image_id] = True
                        self.dbh.commit()
        for id in image_ids.iterkeys() :
            image = self.Image(self,id)
            image.load()
            ret.append(image)
        self.dbh.commit()
        return ret

    def find_image_from_name(self, name) :
        if name[:8] == 'file:///' :
            filename = name[7:]
        else :
            filename = name
        return self.find_image_from_filename( name)

    def find_images_from_names(self, names) :
        filenames = []
        for name in names:
            if name[:8] == 'file:///' :
                filenames.append(name[7:])
            elif name[:7] != 'file://' and name[:6] == 'file:/' :
                filenames.append(name[5:])
            else:
                filenames.append(name)
        return self.find_images_from_filenames(filenames)

    def load_ListStore(self, liststore, imagelist) :
        cursor = self.dbh.cursor();

        imageids = []
        imagelinks = {}
        for row in imagelist :
            imageids.append(row[0])
            if len(row) > 1 :
                imagelinks[row[0]] = row[1]
                

        fields = ('id',
                  'basename',
                  'title',
                  'taken',
                  'description',
                  'camera_position_id',
                  'camera_position_accuracy'
                  )
        sql = "SELECT " + ','.join(fields) + \
               " FROM image WHERE id IN (" + ','.join(imageids) + ') ORDER BY image.basename'
        cursor.execute(sql)
        row = cursor.fetchone()

        imagerows = []
        imageorder = []
        while row:
            imagerows.append(row[:])
            imageorder.append(row[0])
            row = cursor.fetchone()

        for (id,nextid) in imagelinks :
            if id in imageorder and nextid in imageorder:
                f = imageorder.index(id)
                row = imagerows[f]
                del imagerows[f]
                del imageorder[f]
                t = imageorder.index(nextid)
                imagerows.insert(t,row)
                imageorder.insert(t,row[0])

        for row in imagerows :
            iter = liststore.append(None)
            image = self.Image(self)

            for i in range(len(fields)):
                if fields[i].count('.') :
                    f = fields[i][fields[i].rindex('.') + 1]
                elif fields[i].count(' ') :
                    f = fields[i][fields[i].rindex(' ') + 1]
                else:
                    f = fields[i]
                image[f] = row[i]
                
            liststore.set(iter, 1, image['basename'])
            liststore.set(iter, 2, image)
            liststore.set(iter, 3, True)
            


    def loadGTKListStore(self, liststore, whereclause = None) :
        cursor = self.dbh.cursor();
        if whereclause == None:
            whereclause = ''
        else:
            whereclause = 'WHERE ' + whereclause

        fields = ('id',
                  'basename',
                  'title',
                  'taken',
                  'description',
                  'camera_position_id',
                  'camera_position_accuracy'
                  )
        sql = "SELECT " + ','.join(fields) + \
               " FROM image " + whereclause + ' ORDER BY image.basename'
        cursor.execute(sql)
        row = cursor.fetchone()

        while (row):
            iter = liststore.append(None)
            image = self.Image(self)

            for i in range(len(fields)):
                if fields[i].count('.') :
                    f = fields[i][fields[i].rindex('.') + 1]
                elif fields[i].count(' ') :
                    f = fields[i][fields[i].rindex(' ') + 1]
                else:
                    f = fields[i]
                image[f] = row[i]

            liststore.set(iter,0,image['thumbnail'])
            liststore.set(iter, 1, image['basename'])
            liststore.set(iter, 2, image)
            liststore.set(iter, 3, True)
            row = cursor.fetchone()
            
    def LoadSubjectToGTKListStore(self, liststore, subject) :
        cursor = self.dbh.cursor();
        sql = 'SELECT name, id FROM %s WHERE childcount > 0 ORDER BY name' % subject
        cursor.execute(sql)
        row = cursor.fetchone()
        while (row):
            iter = liststore.append(None)
            liststore.set(iter, 1, row[0])
            liststore.set(iter, 2, row[1])
            row = cursor.fetchone()
            
    class FindSemanticLinks :
        def __init__(self):
            self.links = {}

        def parse(self, node):
            
            if node.hasAttributes() :
                attr = {}
                for (k,v) in node.attributes.items() :
                    attr[k] = v
                if attr.has_key('name') :
                    if not self.links.has_key(node.localName) :
                        self.links[node.localName] = []
                    if not str(attr['name']) in self.links[node.localName] :
                        self.links[node.localName].append(str(attr['name']))
            for child in node.childNodes :
                self.parse(child)
        def get_links(self, name) :
            if self.links.has_key(name) :
                return self.links[name]
            else:
                return []

    def addLinksFromXMLBlock(self, image, text) :
        if self.entityClassIDs == None:
            self._loadEntityClassIDs()
            
        xmldoc = minidom.parseString('<flutterby>'+text+'</flutterby>')
        sl = self.FindSemanticLinks()
        sl.parse(xmldoc)
        cursor = self.dbh.cursor()
        
        for n in self.entityClasses  :
            links = sl.get_links(n.lower())
            for link in links :
                if not self.xmlblocklinks.has_key('%s:%s:%s' % (image['id'], n, link)) :
                    album = self.AlbumNode( self, None, self.entityClassIDs[n],
                                       link, False, None, True );
                    sql = 'INSERT INTO albumimage(parent_id,image_id,generatedlink) VALUES (%s,%s,%s)'
                    try:
                        cursor.execute(sql,album.id,image['id'], self.BooleanTrue())
                    except libpq.OperationalError, (err):
                        pass
                    
                    self.xmlblocklinks['%s:%s:%s' % (image['id'], n, link)] = True

    def updateImage(self, image, fields, descriptions = None) :
        for f in ( 'taken',
                   'technotes',
                   'camera_longitude',
                   'camera_lattitude',
                   'camera_position_accuracy',
                   'subject_longitude',
                   'subject_lattitude',
                   'subject_position_accuracy',
                   'description',
                   'title') :
            if fields.has_key(f) and fields[f] == '' :
                fields[f] = None

        sql = 'UPDATE image SET ' + ','.join([k+'=%s' for k in fields.keys()]) + ' WHERE id=%s'
        v = fields.values()
        v.append( image['id'])
        cursor = self.dbh.cursor()
        cursor.execute(sql, v)

        if self.entityClassIDs == None:
            self._loadEntityClassIDs()

        for n in self.entityClasses :
            sql = 'DELETE FROM albumimage WHERE generatedlink AND image_id=%s AND parent_id IN (SELECT id FROM album WHERE album.parent_id = %s)'
            cursor.execute(sql, image['id'], self.entityClassIDs[n].id)
        self.xmlblocklinks = {}
        if fields.has_key('description') and fields['description'] != None :
            self.addLinksFromXMLBlock(image, fields['description'])

        if descriptions != None :
            for text in descriptions :
                if text != None :
                    self.addLinksFromXMLBlock(image, text)
        self.xmlblocklinks = None
        #self.UpdateEntityCounts()
        self.dbh.commit()
        
    def UpdateEntityCounts(self) :
        for c in self.entityClasses :
            cursor = self.dbh.cursor()
            cursor.execute('SELECT id,name FROM '+c)
            rows = cursor.fetchall()
            for row in rows:
                cursor.execute('UPDATE '+c+' SET childcount=(SELECT COUNT(*) FROM '+c+'image WHERE '
                                  +c+'_id=%s) WHERE id=%s',row[0],row[0])
        self.dbh.commit()
            
    def update_record(self, table, id, values) :
        sql = "UPDATE %s SET " % table + \
              ','.join([ k+"=%s" for k in values.iterkeys() ]) + \
              ' WHERE id=%s' % id
        cursor = self.dbh.cursor()
        print sql, values
        cursor.execute(sql, *values.values())

import CreateDB

class CreateDBSQLite(CreateDB.CreateDBSql) :
    def __init__(self, dbh) :
        CreateDB.CreateDBSql.__init__(self,dbh)
    def remapType(self,t) :
        if t == 'SERIAL PRIMARY KEY' :
            return 'INTEGER PRIMARY KEY'
        return t

class ImageDatabaseSQLite(ImageDatabaseSQL) :
    def __init__(self, connectstring = None):
        ImageDatabaseSQL.__init__(self, connectstring)
        if None == connectstring :
            connectstring = "."
        connectstring = os.path.join(connectstring, 'flutterby.sqlite')
        self.dbh = sqlite.connect(connectstring)
        createdb = CreateDBSQLite(self.dbh)
        if createdb.needToCreateTables() :
            createdb.createTables()

    def insert_new_record(self, table, values) :
        cursor = self.dbh.cursor()
        sql = "INSERT INTO %s (id," % table + \
              ','.join(values.keys()) + \
              ") VALUES (NULL," + ','.join(["%s" for i in values.iterkeys()]) + ")"
        print 'NEW RECORD:',sql, values
        cursor.execute(sql, *values.values())
        return self.dbh.insert_id()

    def BooleanTrue(self) :
        return '1'

class ImageDatabasePostgreSQL(ImageDatabaseSQL) :
    def __init__(self, host, port, database, username, password, scratchdir):
        ImageDatabaseSQL.__init__(self, scratchdir)
        self.dbh = PgSQL.connect(":".join([host, port, database, username, password]))
        createdb = CreateDB.CreateDBSql(self.dbh)
        if createdb.needToCreateTables() :
            createdb.createTables()

    def BooleanTrue(self) :
        return 'TRUE'

    def insert_new_record(self, table, values) :
        sql = "SELECT NEXTVAL('%s_id_seq')" % table
        cursor = self.dbh.cursor()
        cursor.execute(sql)
        id = cursor.fetchone()[0]
        sql = "INSERT INTO %s (id," % table + \
              ','.join(values.keys()) + \
              ") VALUES (%s," + ','.join(["%s" for i in values.iterkeys()]) + ")"

        cursor.execute(sql, id, *values.values())
        return id

    def UpdateLocalDatabaseFromFlutterbyCMS(self):
        fcmsdbh = PgSQL.connect('localhost:6969:flutterbycms:danlyke:danlyke')
        cursorDirs = self.dbh.cursor()
        cursorDirs.execute("SELECT id,path FROM directory ORDER BY path DESC")
        rowDirs = cursorDirs.fetchone()
        rd=[]
        while rowDirs :
            rd.append((rowDirs[:]))
            rowDirs = cursorDirs.fetchone()
        for rowDirs in rd:
            dir = os.path.split(rowDirs[1])[1]
            cursorImages = self.dbh.cursor()
            cursorUpdate = self.dbh.cursor()
            cursorRemote = fcmsdbh.cursor()
            cursorImages.execute("""SELECT basename, id, title, description, technotes,
                                           taken, taken_accuracy
                                           FROM image WHERE directory_id=%s""",
                                 rowDirs[0])
            rowImages = cursorImages.fetchone()
            while rowImages :
                basename = (basename, id, title, description, technotes, taken, taken_accuracy) = rowImages

                sql = """SELECT photos.taken, photos.tech_notes, photos.name,
                                articles.title, articles.text
                                FROM articles, photos WHERE photos.article_id=articles.id AND
                                photos.name=%s AND photos.directory=%s"""
                cursorRemote.execute(sql, basename, dir)
                rowRemote = cursorRemote.fetchone()
                if rowRemote :
                    changed = False
                    if title == None or title == '' :
                        title = rowRemote[3]
                        if title == None or title == '' :
                            changed = True
                    if description == None or description == '' :
                        description = rowRemote[4]
                        if description == None or description == '' :
                            changed = True
                    if True or technotes == None or technotes == '' :
                        technotes = rowRemote[1]
                        if technotes == None or technotes == '' :
                            changed = True
                    if True or taken == None or taken == '' :
                        taken = rowRemote[0]
                        if taken == None or taken == '' :
                            changed = True

                sql = 'UPDATE image SET title=%s, description=%s, technotes=%s,taken=%s WHERE id=%s'
                cursorUpdate.execute(sql, title,description, technotes, taken,id)
                
                rowImages = cursorImages.fetchone()
            self.dbh.commit()

    def SearchAndReplace(self, res):
        cursor = self.dbh.cursor()
        cursor.execute('SELECT id FROM image WHERE id > 2583')
        row = cursor.fetchone()
        gl = GeoLookup.GeoLookup()
        ids = {}

        positions = {}
        for (k,v) in res :
            positions[k] = gl.lookupAddress(k)
        
        while row :
            if not ids.has_key(row[0]):
                ids[row[0]] = True
            row = cursor.fetchone()
        for rowid in ids.keys() :
            fields = {}
            self.loadImage(rowid, fields)
            if re.search('<place ', fields['description']) \
               or re.search('<person ', fields['description']) \
               or re.search('<thing ', fields['description']) \
               or re.search('<event ', fields['description']) :
                pass
            else :
                for (k,v) in res :
                    fields['description'] = re.sub(k,v,fields['description'])

                    if re.search(v, fields['description']) :
                        pos =  positions[k]
                        if pos != None and pos[0] != None  and fields['camera_longitude'] == None:
                            fields['camera_longitude'] = pos[0]
                        if pos != None and pos[1] != None  and fields['camera_lattitude'] == None:
                            fields['camera_lattitude'] = pos[1]                    
                        if pos != None and pos[2] != None  and fields['camera_position_accuracy'] == None:
                            fields['camera_position_accuracy'] = pos[2]                    
                        if pos != None and pos[0] != None  and fields['subject_longitude'] == None:
                            fields['subject_longitude'] = pos[0]
                        if pos != None and pos[1] != None  and fields['subject_lattitude'] == None:
                            fields['subject_lattitude'] = pos[1]                    
                        if pos != None and pos[2] != None  and fields['subject_position_accuracy'] == None:
                            fields['subject_position_accuracy'] = pos[2]
                self.updateImage(rowid, fields)        
            self.dbh.commit()



class ManageAlbumFilesystem :
    def __init__(self, imageDatabase = None):
        if imageDatabase == None :
            imageDatabase = ImageDatabase.ImageDatabasePostgreSQL()
            
        self.imageDatabase = imageDatabase

    def build_album_tree_from_directories(self) :
        root_id = self.imageDatabase.get_or_insert_record('album',
                                                          {
            'parent_id' : None,
            'name' : 'Files',
            })
        
        cursor = self.imageDatabase.dbh.cursor()
        sql = 'SELECT id, path FROM directory'
        cursor.execute(sql)
        rows = cursor.fetchall()
        directories = {}
        for row in rows :
            dir = row[1]
            if not directories.has_key(dir) :
                dirs = []
                f = 'seeded for first iteration'
                while len(f) > 0 :
                    (dir, f) = os.path.split(dir)
                    if len(f) > 0:
                        dirs.append(f)
                dirs.reverse()
                id = root_id
                for dir in dirs :
                    id = self.imageDatabase.get_or_insert_record('album',
                                                                 {
                        'parent_id' : id,
                        'name' : dir,
                        })
                directories[row[1]] = id
            sql = 'SELECT DISTINCT(image_id) FROM imageinstance WHERE directory_id=%s'
            cursor.execute(sql, row[0])
            imageids = cursor.fetchall()
            for imageid in imageids:
                sql = 'SELECT parent_id, image_id FROM albumimage WHERE parent_id=%s AND image_id=%s'
                cursor.execute(sql, directories[row[1]], imageid[0])
                if not cursor.fetchone() :
                    sql = 'INSERT INTO albumimage(parent_id, image_id) VALUES (%s,%s)'
                    cursor.execute(sql, directories[row[1]], imageid[0])
        self.imageDatabase.commit_write()



global _dbinstance
_dbinstance = None

def ImageDatabase() :
    try :
        if _dbinstance == None :
            _dbinstance = ImageDatabasePostgreSQL()
    except :
        _dbinstance = ImageDatabasePostgreSQL()
    return _dbinstance


import sys

if __name__ == '__main__':
    imageDatabase = ImageDatabase()
    #imageDatabase.UpdateEntityCounts()
    #imageDatabase.UpdateLocalDatabaseFromFlutterbyCMS()

    images = imageDatabase.find_images_from_filenames(sys.argv[1:])

    for image in images:
        print image.get_thumbnail_filename()
    


