import gtk
import gtk.glade
import new,types
import os
class Wizard :
    def set_current_dialog(self, dialognum) :
        self.currentdialognum = dialognum
        if isinstance(self.dialoglist[self.currentdialognum], types.TupleType) :
            self.currentdialog = self.dialoglist[self.currentdialognum][1][
                self.values[self.dialoglist[self.currentdialognum][0]]]
        else :
            self.currentdialog = self.dialoglist[self.currentdialognum]
        
    def __init__(self, list, onOK = None, onCancel = None, initialvalues = None) :
        self.dialoglist = list
        self.clickedOK = False
        self.onOK = onOK
        self.onCancel = onCancel
        self.set_current_dialog(0)

        self.initialvalues = initialvalues
        if initialvalues != None :
            self.values = initialvalues
        else :
            self.values = {}

        gladefile="flutterby.glade"
        windowname="windowImageBrowser"


        self.currentdialog.run(self)
        self.currentdialog.buttonBack.set_sensitive(False)
        self.currentdialog.buttonOK.set_sensitive(False)

    def on_buttonOK_clicked(self,widget) :
        self.currentdialog.destroy()
        self.clickedOK = True
        if self.onOK != None :
            self.onOK(self)
        
    def on_buttonNext_clicked(self,widget) :
        if self.currentdialognum + 1 < len(self.dialoglist) :
            self.currentdialog.destroy()
            self.set_current_dialog(self.currentdialognum + 1)
            
            self.currentdialog.run(self)

            if self.currentdialognum + 1 == len(self.dialoglist) :
                self.currentdialog.buttonNext.set_sensitive(False)
            else :
                self.currentdialog.buttonOK.set_sensitive(False)
            

    def on_buttonBack_clicked(self,widget) :
        if self.currentdialognum > 0 :
            self.currentdialog.destroy()
            self.set_current_dialog(self.currentdialognum - 1)
            self.currentdialog.run(self)
            
            if self.currentdialognum == 0 :
                self.currentdialog.buttonBack.set_sensitive(False)
            
    def on_buttonCancel_clicked(self,widget) :
        self.currentdialog.destroy()
        if self.onCancel != None :
            self.onCancel(self)
        
    


class WizardDialog :
    def __init__(self, gladefile, windowname) :
        self.gladefile = gladefile
        self.windowname = windowname

    def run(self, wizardmanager) :
        self.wizardmanager = wizardmanager
        
        self.widgets = gtk.glade.XML (self.gladefile,self.windowname)

        callbacks = {}
        #find and store methods as bound callbacks
        class_methods = self.__class__.__dict__
        for method_name in class_methods.keys():
            method = class_methods[method_name]
            if type(method) == types.FunctionType:
                callbacks[method_name] = new.instancemethod(
                                         method, self, self.__class__)
        self.widgets.signal_autoconnect(callbacks)

        self.mainwindow = self.widgets.get_widget(self.windowname)
        self.basebuttonname = 'button' + self.windowname[6:]
        print "base button name", self.basebuttonname
    
        self.buttonOK = self.widgets.get_widget(self.basebuttonname + 'OK')
        self.buttonNext = self.widgets.get_widget(self.basebuttonname + 'Next')
        self.buttonBack = self.widgets.get_widget(self.basebuttonname + 'Back')
        self.buttonCancel = self.widgets.get_widget(self.basebuttonname + 'Cancel')

        self.buttonOK.connect('clicked', self.on_buttonOK_clicked)
        self.buttonNext.connect('clicked', self.on_buttonNext_clicked)
        self.buttonBack.connect('clicked', self.on_buttonBack_clicked)
        self.buttonCancel.connect('clicked', self.on_buttonCancel_clicked)

    def destroy(self) :
        self.mainwindow.destroy()
        self.mainwindow = None
        self.buttonok = None
        self.buttonNext = None
        self.buttonBack = None
        self.buttonCancel = None

    def gathervalues(self) :
        pass

    def set_controls_text(self, controlmap) :
        for (name,widget) in controlmap.items() :
            if self.wizardmanager.values.has_key(name) :
                print "Setting control", name, self.wizardmanager.values[name]
                widget.set_text(self.wizardmanager.values[name])

    def get_controls_text(self, controlmap) :
        for (name, widget) in controlmap.items() :
            self.wizardmanager.values[name] = widget.get_text()
        
    
    def on_buttonOK_clicked(self,widget) :
        self.gathervalues()
        self.wizardmanager.on_buttonOK_clicked(self)
        
    def on_buttonNext_clicked(self,widget) :
        self.gathervalues()
        self.wizardmanager.on_buttonNext_clicked(self)

        
    def on_buttonBack_clicked(self,widget) :
        self.gathervalues()
        self.wizardmanager.on_buttonBack_clicked(self)
        
    def on_buttonCancel_clicked(self,widget) :
        self.wizardmanager.on_buttonCancel_clicked(self)
        
class WizardDatabaseConfigDialog(WizardDialog) :
    def __init__(self) :
        WizardDialog.__init__(self, 'flutterby.glade', 'windowDatabaseConfigDialog')

    def run(self,wizardmanager) :
        WizardDialog.run(self,wizardmanager)
        self.radiobuttonDatabaseConfigDialogPostgreSQL = self.widgets.get_widget(
            'radiobuttonDatabaseConfigDialogPostgreSQL')
        if self.wizardmanager.values.has_key('database') and \
           self.wizardmanager.values['database'] != 'sqlite' :
            self.radiobuttonDatabaseConfigDialogPostgreSQL.set_active(True)

    def gathervalues(self) :
        self.wizardmanager.values['database'] = ['sqlite','postgresql'][
            self.radiobuttonDatabaseConfigDialogPostgreSQL.get_active()]

class WizardFilePathConfigDialog(WizardDialog) :
    def renderer_editable_text_cell_edited(self, renderer,path,newtext) :
        iter = self.pathlist.get_iter_from_string(path)
        self.pathlist.set(iter,0, newtext)

    def __init__(self) :
        WizardDialog.__init__(self, 'flutterby.glade', 'windowFilePathConfigDialog')

    def run(self,wizardmanager) :
        WizardDialog.run(self,wizardmanager)
        self.treeviewPathList = self.widgets.get_widget('treeviewFilePathConfigDialog')
        self.pathlist = gtk.TreeStore(str, int)
        self.treeviewPathList.set_model(self.pathlist)
        r = gtk.CellRendererText()
        r.connect('edited', self.renderer_editable_text_cell_edited)
        col = gtk.TreeViewColumn('Image Path', r)
        col.set_attributes(r, text = 0, editable = 1)
        self.treeviewPathList.append_column(col)

        if self.wizardmanager.values.has_key('filepaths') :
            for path in self.wizardmanager.values['filepaths'] :
                iter = self.pathlist.append(None)
                self.pathlist.set(iter, 0, path)
                self.pathlist.set(iter, 1, True)
        
        

    def gathervalues(self) :
        a = []
        iter = self.pathlist.get_iter_first()
        while iter :
            a.append(self.pathlist.get_value(iter,0))
            iter = self.pathlist.iter_next(iter)
        self.wizardmanager.values['filepaths'] = a
        pass


    def on_buttonFilePathConfigDialogAddLocation_clicked(self, widget) :
        chooserDialog = gtk.FileChooserDialog('Directory To Check For Images', self.mainwindow,
                                              gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

        chooserDialog.add_button('gtk-cancel', -1)
        chooserDialog.add_button('gtk-open', 101)
        if 101 == chooserDialog.run() :
            iter = self.pathlist.append(None)
            self.pathlist.set(iter, 0, chooserDialog.get_filename())
            self.pathlist.set(iter, 1, True)
        chooserDialog.destroy()
        pass

class WizardDynamicFilePathConfigDialog(WizardDialog) :
    def __init__(self) :
        WizardDialog.__init__(self, 'flutterby.glade', 'windowDynamicFilePathConfigDialog')

    def renderer_editable_text_cell_edited1(self, renderer,path,newtext) :
        iter = self.pathlist.get_iter_from_string(path)
        self.pathlist.set(iter,1, newtext)
    def renderer_editable_text_cell_edited0(self, renderer,path,newtext) :
        iter = self.pathlist.get_iter_from_string(path)
        self.pathlist.set(iter,0, newtext)

    def run(self,wizardmanager) :
        WizardDialog.run(self,wizardmanager)
        self.treeviewPathList = self.widgets.get_widget('treeviewDynamicFilePathConfigDialog')
        self.pathlist = gtk.TreeStore(str, str, int)
        self.treeviewPathList.set_model(self.pathlist)
        r = gtk.CellRendererText()
        r.connect('edited', self.renderer_editable_text_cell_edited0)
        col = gtk.TreeViewColumn('Source Path', r)
        col.set_attributes(r, text = 0, editable = 2)
        self.treeviewPathList.append_column(col)

        r = gtk.CellRendererText()
        r.connect('edited', self.renderer_editable_text_cell_edited1)
        col = gtk.TreeViewColumn('Destination Path', r)
        col.set_attributes(r, text = 1, editable = 2)
        self.treeviewPathList.append_column(col)

        if self.wizardmanager.values.has_key('dynamicfilepaths') :
            paths = self.wizardmanager.values['dynamicfilepaths']
            paths.reverse()

            while paths :
                sourcepath = paths.pop()
                targetpath = paths.pop()
                iter = self.pathlist.append(None)
                self.pathlist.set(iter, 0, sourcepath)
                self.pathlist.set(iter, 1, targetpath)
                self.pathlist.set(iter, 2, True)

    def gathervalues(self) :
        a = []
        iter = self.pathlist.get_iter_first()
        while iter :
            a.append(self.pathlist.get_value(iter,0))
            a.append(self.pathlist.get_value(iter,1))
            iter = self.pathlist.iter_next(iter)
        self.wizardmanager.values['dynamicfilepaths'] = a
        pass

    def on_buttonDynamicFilePathConfigDialogAddLocation_clicked(self, widget) :
        chooserDialog = gtk.FileChooserDialog('Directory To Check For Images', self.mainwindow,
                                              gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

        chooserDialog.add_button('gtk-cancel', -1)
        chooserDialog.add_button('gtk-open', 101)
        if 101 == chooserDialog.run() :
            iter = self.pathlist.append(None)
            self.pathlist.set(iter, 0, chooserDialog.get_filename())
            if self.wizardmanager.values.has_key('filepaths') :
                if len(self.wizardmanager.values['filepaths']) > 0 :
                    self.pathlist.set(iter,1,
                                      os.path.join(self.wizardmanager.values['filepaths'][0],
                                                   'images_####'))
            self.pathlist.set(iter, 2, True)
        chooserDialog.destroy()

class WizardThumbnailPathConfigDialog(WizardDialog) :
    def __init__(self) :
        WizardDialog.__init__(self, 'flutterby.glade', 'windowThumbnailPathConfigDialog')


    def run(self,wizardmanager) :
        WizardDialog.run(self,wizardmanager)
        self.entryThumbnailPathConfigDialogPath = self.widgets.get_widget('entryThumbnailPathConfigDialogPath')
        self.controlmap = {'thumbnailpath' : self.entryThumbnailPathConfigDialogPath}
        self.set_controls_text(self.controlmap)

    def gathervalues(self) :
        self.get_controls_text(self.controlmap)

    def on_buttonThumbnailPathConfigDialogOpenPath_clicked(self, widget) :
        chooserDialog = gtk.FileChooserDialog('Directory To Check For Images', self.mainwindow,
                                              gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

        chooserDialog.add_button('gtk-cancel', -1)
        chooserDialog.add_button('gtk-open', 101)
        if 101 == chooserDialog.run() :
            self.entryThumbnailPathConfigDialogPath.set_text(chooserDialog.get_filename())
        chooserDialog.destroy()



class WizardFileCheckTimeConfigDialog(WizardDialog) :
    def __init__(self) :
        WizardDialog.__init__(self, 'flutterby.glade', 'windowFileCheckTimeConfigDialog')


    def run(self,wizardmanager) :
        WizardDialog.run(self,wizardmanager)
        self.entryFileCheckTimeConfigDialog = self.widgets.get_widget('entryFileCheckTimeConfigDialog')
        self.controlmap = {'newfilecheckinterval' : self.entryFileCheckTimeConfigDialog}
        self.set_controls_text(self.controlmap)

    def gathervalues(self) :
        self.get_controls_text(self.controlmap)


class WizardSQLiteConfigDialog(WizardDialog) :
    def __init__(self) :
        WizardDialog.__init__(self, 'flutterby.glade', 'windowSQLiteConfigDialog')

    def run(self,wizardmanager) :
        WizardDialog.run(self,wizardmanager)
        self.entrySQLiteConfigDialogPath = self.widgets.get_widget('entrySQLiteConfigDialogPath')
        self.controlmap = {'sqlitepath' : self.entrySQLiteConfigDialogPath}
        self.set_controls_text(self.controlmap)

    def gathervalues(self) :
        self.get_controls_text(self.controlmap)

    def on_buttonSQLiteConfigDialogOpenPath_clicked(self, widget) :
        chooserDialog = gtk.FileChooserDialog('Directory For Image Database', self.mainwindow,
                                              gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

        chooserDialog.add_button('gtk-cancel', -1)
        chooserDialog.add_button('gtk-open', 101)
        if 101 == chooserDialog.run() :
            self.entrySQLiteConfigDialogPath.set_text(chooserDialog.get_filename())
        chooserDialog.destroy()
   

class WizardPostgreSQLConfigDialog(WizardDialog) :
    def __init__(self) :
        WizardDialog.__init__(self, 'flutterby.glade', 'windowPostgreSQLConfigDialog')

    def run(self,wizardmanager) :
        WizardDialog.run(self,wizardmanager)
        self.entryPostgreSQLConfigDialogHostName = self.widgets.get_widget('entryPostgreSQLConfigDialogHostName')
        self.entryPostgreSQLConfigDialogDatabase = self.widgets.get_widget('entryPostgreSQLConfigDialogDatabase')
        self.entryPostgreSQLConfigDialogUserName = self.widgets.get_widget('entryPostgreSQLConfigDialogUserName')
        self.entryPostgreSQLConfigDialogPassword = self.widgets.get_widget('entryPostgreSQLConfigDialogPassword')
        self.entryPostgreSQLConfigDialogPort = self.widgets.get_widget('entryPostgreSQLConfigDialogPort')

        self.controlmap = {
            'postgresqlhostname' : self.entryPostgreSQLConfigDialogHostName,
            'postgresqldatabase' : self.entryPostgreSQLConfigDialogDatabase,
            'postgresqlusername' : self.entryPostgreSQLConfigDialogUserName,
            'postgresqlpassword' : self.entryPostgreSQLConfigDialogPassword,
            'postgresqlport' : self.entryPostgreSQLConfigDialogPort,
            }
        self.set_controls_text(self.controlmap)
        
    def gathervalues(self) :
        self.get_controls_text(self.controlmap)


def clickedOK(wizardmanager) :
    print "Clicked OK", wizardmanager
    gtk.main_quit()
def clickedCancel(wizardmanager) :
    print "Clicked Cancel", wizardmanager
    gtk.main_quit()

import os
if __name__ == '__main__':
    dlgs = [
        WizardDatabaseConfigDialog(),
        ('database', { 'sqlite' : WizardSQLiteConfigDialog(),
                       'postgresql' : WizardPostgreSQLConfigDialog(),
                       }),
        WizardFilePathConfigDialog(),
        WizardDynamicFilePathConfigDialog(),
        WizardFileCheckTimeConfigDialog(),
        WizardThumbnailPathConfigDialog(),
        ]
    wizard = Wizard(dlgs, clickedOK, clickedCancel, {})

    wizard.values['filepaths'] = []
    wizard.values['dynamicfilepaths'] = []
    
    if os.getenv('HOME') != None :
        wizard.values['filepaths'].append(os.getenv('HOME'))

    if os.path.isdir('/mnt/film') :
        a = ('/mnt/film',
             os.path.join(os.getenv('HOME'),
                          'images',
                          'images_####'))
        wizard.values['dynamicfilepaths'].append(a)

    if os.getenv('HOME') != None :
        wizard.values['sqlitepath'] = os.path.join(os.getenv('HOME'),
                                                        '.flutterby')
    if os.getenv('HOME') != None :
        wizard.values['thumbnailpath'] = os.path.join(os.getenv('HOME'),
                                                        '.flutterby')
    wizard.values['postgresqlhostname'] = 'localhost'
    wizard.values['postgresqldatabase'] = 'flutterby'
    wizard.values['postgresqlport'] = ''
    wizard.values['postgresqlusername'] = ''
    wizard.values['postgresqlpassword'] = ''

    if os.getenv('USER') != None :
        wizard.values['postgresqlusername'] = os.getenv('USER')

    gtk.main()
