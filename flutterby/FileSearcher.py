import distutils
import re
import os
import stat
import xml.utils.iso8601
import time
from EXIF import *
import gtk
import gobject
from distutils.file_util import copy_file


class Search :
    def __init__(self, path) :
        self.path = path
        self.files = []
        self.directories = None
        self.now = xml.utils.iso8601.tostring( time.time() )

    def checkFilename(self, filename) :
        return True

    def _loadDirectory(self, path) :
        sql = 'SELECT lastchecked FROM directory WHERE accesstype_id=1 AND path=%s'
        iso_time = xml.utils.iso8601.tostring( os.stat(path)[9] )
        cursor = self.database.dbh.cursor()
        cursor.execute(sql, path)
        row = cursor.fetchone()
        if row and row[0] != None:
            if iso_time <= row[0] :
                return
        sql = 'UPDATE directory SET lastchecked=%s WHERE accesstype_id=1 AND path=%s'
        cursor.execute(sql,iso_time, path)
        self.database.commit_write()
        files = [f for f in os.listdir(path) if f[0] != '.']
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath) :
                self.directories.append(fullpath)
            elif self.checkFilename(fullpath) and os.path.isfile(fullpath):
                self.files.append(fullpath)
    def processFile(self, file) :
        pass

    def processFiles(self) :
        while len(self.files) > 0 :
            self.processFile(self.files.pop())
        
    def processTick(self) :
        if None == self.directories :
            self.directories = []
            self._loadDirectory(self.path)
            return True
        elif len(self.files) > 0 :
            self.processFiles()
            return True
        elif len(self.directories) > 0 :
            path = self.directories.pop()
            self._loadDirectory(path)
            return True
        return False
            

class ImageSearch(Search) :
    def __init__(self, database, interval, pathfrom, pathto = None) :
        Search.__init__(self, pathfrom)
        self.minTimeout = 250
        self.database = database
        self.interval = 500000 # interval
        self.pathfrom = pathfrom
        self.pathTo = self.createTargetPathFromSpec(pathto)
        self.pathToCreated = False
        self.createddirs = {}
        self.timeoutId = gobject.timeout_add(self.minTimeout, self.processTick)
        self.targetFiles = []

    def checkFilename(self, filename) :
        r = self.database.canTrackFilename(filename)
        return r
        
    def createTargetPathFromSpec(self, specpath) :
        if specpath == None :
            return None
        c = re.compile("^(.*?)(\#+)(.*)$")
        m = c.match(specpath)
        if m :
            (pre, num, post) = m.groups()
            (sub,prename) = os.path.split(pre)
            dirs = os.listdir(sub)
            n = 0
            c = re.compile("^"+prename+"(\d+)");
            for f in dirs :
                m = c.match(f)
                if m :
                    if int(m.groups()[0]) >= n :
                        n = int(m.groups()[0]) + 1
            return pre + (( "%" + ("%d.%d" % (len(num), len(num))) + "d") % n) + post
        else :
            return specpath

    def processFiles(self) :
        if self.pathTo == None :
            self.database.find_images_from_filenames(self.files)
            self.files = []
        else :
            filename = self.files.pop()
            if stat.S_ISREG(os.stat(filename)[0]) :
                (srcdir, srcfile) = os.path.split(filename)
                if not self.pathToCreated :
                    os.makedirs(self.pathTo)
                    self.pathToCreated = True
                copy_file(os.path.join(srcdir, srcfile),
                          os.path.join(self.pathTo, srcfile))
                self.targetFiles.append(os.path.join(self.pathTo, srcfile))
            if not self.files :
                self.database.find_images_from_filenames(self.targetFiles)
                self.targetFiles = []
        self.database.commit_write()
            
    def ensuredirectory(self, dir) :
        if self.createddirs.has_key(dir) :
            return
        os.makedirs(dir)
        self.createddirs[dir] = true
    
    def processTick(self) :
        gobject.source_remove(self.timeoutId);
        if Search.processTick(self) :
            self.timeoutId = gobject.timeout_add(self.minTimeout, self.processTick)
            return False
        else:
            if self.interval :
                self.timeoutId = gobject.timeout_add(self.interval, self.processTick)
                return False

        m = ImageDatabase.ManageAlbumFilesystem(self.database);
        m.build_album_tree_from_directories()
        return False




if __name__ == '__main__':
    s = Search('/home/danlyke')
    while s.processTick() :
        pass
    
    
