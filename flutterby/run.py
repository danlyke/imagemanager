#!/usr/bin/env python

# stolen from http://www.linuxjournal.com/article.php?sid=6586
import sys
import os

sys.path.append("../fby/");

try:
    import pygtk
    #tell pyGTK, if possible, that we want GTKv2
    pygtk.require("2.0")
except:
    #Some distributions come with GTK2, but not pyGTK
    pass

try:
    import gtk
    import gtk.glade
except:
    print "You need to install pyGTK or GTKv2 ",
    print "or set your PYTHONPATH correctly."
    print "try: export PYTHONPATH=",
    print "/usr/local/lib/python2.2/site-packages/"
    sys.exit(1)

#now we have both gtk and gtk.glade imported
#Also, we know we are running GTK v2
import new, types

import fby
import ImageSubjectBrowser         
import MapViewer
import AlbumBrowser
import ImageDatabase
import FileSearcher

class AppManager(fby.App) :
    def __init__(self) :
	fby.App.__init__(self)

    def init_config_values(self, values) :
        if values['database'] == 'sqlite' :
            self.imageDatabase = ImageDatabase.ImageDatabaseSQLite(values['sqlitepath'])
        elif values['database'] == 'postgresql' :
            self.imageDatabase = ImageDatabase.ImageDatabasePostgreSQL(
                values['postgresqlhostname'],
                values['postgresqlport'],
                values['postgresqldatabase'],
                values['postgresqlusername'],
                values['postgresqlpassword'],
                values['thumbnailpath'])

        for paths in values['filepaths'] :
            searcher = FileSearcher.ImageSearch(self.imageDatabase,
                                    values['newfilecheckinterval'],
                                    paths)
        paths = values['dynamicfilepaths']
        paths.reverse()
        while paths :
            sourcepath = paths.pop()
            targetpath = paths.pop()
            searcher = FileSearcher.ImageSearch(self.imageDatabase,
                                    values['newfilecheckinterval'],
                                    sourcepath, targetpath)


    def new_subject_browser(self, subject) :
        ImageSubjectBrowser.ImageSubjectBrowser(self, subject)
    def new_album_browser(self) :
        AlbumBrowser.AlbumBrowser(self)



import Config
import Wizard

class StartupManager :
    def get_home_dir(self,subkey = 'Personal'):
        """Return the closest possible equivalent to a 'home' directory.

        For Posix systems, this is $HOME, and on NT it's $HOMEDRIVE\$HOMEPATH.
        
        Currently only Posix and NT are implemented, a HomeDirError
        exception is raised for all other OSes.

        Taken from
        http://mail.python.org/pipermail/python-list/2003-February/150829.html
        """ #'
    
        if os.name == 'posix':
            return os.environ['HOME']
        elif os.name == 'nt':
            # For some strange reason, win9x returns 'nt' for os.name.
            try:
                return os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'])
            except:
                try:
                    # Use the registry to get the 'My Documents' folder.
                    import _winreg as wreg
                    key = wreg.OpenKey(wreg.HKEY_CURRENT_USER,
                                       "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                    homedir = wreg.QueryValueEx(key,subkey)[0]
                    key.Close()
                    return homedir
                except:
                    return 'C:\\'
        elif os.name == 'dos':
            # Desperate, may do absurd things in classic MacOS. May work under DOS.
            return 'C:\\'
        else:
            raise HomeDirError,'support for your operating system not implemented.'
    
    def __init__(self, app) :
        self.app = app
        self.configvalues = {}
        self.requiredvalues = [
            'database',
            ]
        self.configmanager = Config.Manager()
        xmldoc = None
        if os.name == 'posix' :
            self.configfile = os.path.join(self.get_home_dir('AppData'), '.flutterby.xml')
        else :
            self.configfile = os.path.join(self.get_home_dir('AppData'),
                                           'Application Data',
                                           'Flutterby', 'flutterby.xml');
        if os.path.isfile(self.configfile) :
            self.configmanager.read(self.configfile)
                    
        self.configvalues = self.configmanager.getvalues()
        startconfigwizard = False;

        for v in self.requiredvalues :
            if not self.configvalues.has_key(v) :
                startconfigwizard = True

        if startconfigwizard :
            self._startconfigwizard()
        else :
            self.app.init_config_values(self.configvalues)
            self.app.new_album_browser()

    def _startconfigwizard(self) :
        dlgs = [
            Wizard.WizardDatabaseConfigDialog(),
            ('database', { 'sqlite' : Wizard.WizardSQLiteConfigDialog(),
                           'postgresql' : Wizard.WizardPostgreSQLConfigDialog(),
                           }),
            Wizard.WizardFilePathConfigDialog(),
            Wizard.WizardDynamicFilePathConfigDialog(),
            Wizard.WizardFileCheckTimeConfigDialog(),
            Wizard.WizardThumbnailPathConfigDialog(),
        ]

        if not self.configvalues.has_key('filepaths') :
            self.configvalues['filepaths'] = [self.get_home_dir()]
        if not self.configvalues.has_key('dynamicfilepaths') :
            self.configvalues['dynamicfilepaths'] = []
            if os.path.isdir('/mnt/film') :
                self.configvalues['dynamicfilepaths'].append('/mnt/film')
                self.configvalues['dynamicfilepaths'].append(os.path.join(self.get_home_dir(),
                                                                          'images',
                                                                          'images_####'))

        if not self.configvalues.has_key('sqlitepath') :
            if os.name == 'posix' :
                self.configvalues['sqlitepath'] = os.path.join(self.get_home_dir('AppData'),
                                                               '.flutterby')
            else :
                self.configvalues['sqlitepath'] = os.path.join(self.get_home_dir('AppData'),
                                                               'Application Data',
                                                               'Flutterby');
        if not self.configvalues.has_key('thumbnailpath') :
            if os.name == 'posix' :
                self.configvalues['thumbnailpath'] = os.path.join(self.get_home_dir('AppData'),
                                                                  '.flutterby')
            else :
                self.configvalues['thumbnailpath'] = os.path.join(self.get_home_dir('AppData'),
                                                                  'Application Data',
                                                                  'Flutterby');

        if not self.configvalues.has_key('postgresqlhostname') :
            self.configvalues['postgresqlhostname'] = 'localhost'
            self.configvalues['postgresqldatabase'] = 'flutterby'
            self.configvalues['postgresqlport'] = ''
            self.configvalues['postgresqlusername'] = ''
            self.configvalues['postgresqlpassword'] = ''

            if os.getenv('USER') != None :
                self.configvalues['postgresqlusername'] = os.getenv('USER')
                
        wizard = Wizard.Wizard(dlgs, self.on_config_wizard_OK_clicked,
                               self.on_config_wizard_Cancel_clicked, self.configvalues)        

    def on_config_wizard_OK_clicked(self, wizard) :
        print "Setting values", wizard.values
        self.configmanager.setvalues(wizard.values)
        self.configmanager.write(self.configfile)
        self.app.init_config_values(wizard.values)
        self.app.new_album_browser()
            
    def on_config_wizard_Cancel_clicked(self, wizard) :
        gtk.main_quit()
    
# we start the app like this...

app = AppManager()
sm = StartupManager(app)


#app=ImageBrowser.ImageBrowser()
#app=ImageSubjectBrowser.ImageSubjectBrowser('person')
#app=MapViewer.MapViewer()
#app.new_map_viewer(1)
#app.new_map_viewer(1)
#app.new_image_browser(' id IN (SELECT image_id FROM albumimage WHERE parent_id=5)')
#app.new_subject_browser('person')
#app.new_album_browser()
#app.new_album_browser()
gtk.main()

