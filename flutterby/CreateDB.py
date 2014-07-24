# from pyPgSQL import PgSQL, libpq


class CreateDBSql :
    def __init__(self, dbh) :
        self.dbh = dbh

        self.tables = [
            'people',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['name', 'TEXT'],
            ],
            'geoposition',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['lattitude', 'DOUBLE PRECISION'],
            ['longitude', 'DOUBLE PRECISION'],
            ['altitude', 'DOUBLE PRECISION'],
            ],
            'province',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['country', 'CHAR[2]'],
            ['name', 'TEXT'],
            ['abbr', 'TEXT'],
            ],
            'interesttypes',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['type', 'TEXT'],
            ],
            'pointofinterest',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['geoposition_id', 'INT', 'REFERENCES geoposition(id)'],
            ['province_id', 'INT', 'REFERENCES province(id)'],
            ['type_id', 'INT', 'REFERENCES interesttypes(id)'],
            ['name', 'TEXT'],
            ],
            'person',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['name', 'TEXT'],
            ['childcount', 'INT'],
            ],
            'place',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['name', 'TEXT'],
            ['childcount', 'INT'],
            ],
            'thing',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['name', 'TEXT'],
            ['childcount', 'INT'],
            ],
            'event',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['name', 'TEXT'],
            ['childcount', 'INT'],
            ],
            'filesystemaccesstypes',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['name', 'TEXT'],
            ['icon_name', 'TEXT'],
            ],
            'directory',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['accesstype_id', 'INT', 'REFERENCES filesystemaccesstypes(id)'],
            ['albumpage_id', 'INT', 'REFERENCES album(id)'],
            ['lastchecked', 'TIMESTAMP'],
            ['path', 'TEXT'],
            ],
            'description',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['refcount', 'INT', '', "DEFAULT '0'"],
            ['description', 'TEXT'],
            ],
            'image',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['directory_id', 'INT NOT NULL REFERENCES directory(id)'],
            ['subject_position_id', 'INT', 'REFERENCES geoposition(id)'],
            ['subject_position_accuracy', 'DOUBLE PRECISION'],
            ['subject_lattitude', 'DOUBLE PRECISION'],
            ['subject_longitude', 'DOUBLE PRECISION'],
            ['camera_position_id', 'INT', 'REFERENCES geoposition(id)'],
            ['camera_position_accuracy', 'DOUBLE PRECISION'],
            ['camera_lattitude', 'DOUBLE PRECISION'],
            ['camera_longitude', 'DOUBLE PRECISION'],
            ['rotation', 'INT'],
            ['title', 'TEXT'],
            ['description', 'TEXT'],
            ['technotes', 'TEXT'],
            ['taken', 'TIMESTAMP'],
            ['taken_accuracy', 'INTERVAL'],
            ['photographer_id', 'INT', 'REFERENCES people(id)'],
            ['basename', 'TEXT'],
            ],
            'imagedescription',
            [
            ['description_id', 'INT', 'REFERENCES description(id)'],
            ['image_id', 'INT', 'REFERENCES image(id)'],
            ],
            'imageinstance',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['directory_id', 'INT', 'REFERENCES directory(id)'],
            ['image_id', 'INT', 'REFERENCES image(id) NOT NULL'],
            ['width', 'INT'],
            ['height', 'INT'],
            ['name', 'TEXT'],
            ],
            'personimage',
            [
            ['person_id', 'INT', 'REFERENCES person(id)'],
            ['image_id', 'INT', 'REFERENCES image(id)'],
            ],
            'placeimage',
            [
            ['place_id', 'INT', 'REFERENCES place(id)'],
            ['image_id', 'INT', 'REFERENCES image(id)'],
            ],
            'thingimage',
            [
            ['thing_id', 'INT', 'REFERENCES thing(id)'],
            ['image_id', 'INT', 'REFERENCES image(id)'],
            ],
            'eventimage',
            [
            ['event_id', 'INT', 'REFERENCES event(id)'],
            ['image_id', 'INT', 'REFERENCES image(id)'],
            ],
            'map',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['background_name', 'TEXT'],
            ],
            'mappoints_reference',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['map_id', 'INT', 'REFERENCES map(id)'],
            ['x', 'INT'],
            ['y', 'INT'],
            ['lon', 'FLOAT'],
            ['lat', 'FLOAT'],
            ],
            'mappoints_path',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['map_id', 'INT', 'REFERENCES map(id)'],
            ['nextpoint_id', 'INT', 'REFERENCES mappoints_path(id)'],
            ['x', 'INT'],
            ['y', 'INT'],
            ['lon', 'FLOAT'],
            ['lat', 'FLOAT'],
            ],
            'mappoints_interest',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['map_id', 'INT', 'REFERENCES map(id)'],
            ['y', 'INT'],
            ['x', 'INT'],
            ['lon', 'FLOAT'],
            ['lat', 'FLOAT'],
            ],
            'mappoints_image',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['map_id', 'INT', 'REFERENCES map(id)'],
            ['image_id', 'INT', 'REFERENCES image(id)'],
            ['y', 'INT'],
            ['x', 'INT'],
            ['lon', 'FLOAT'],
            ['lat', 'FLOAT'],
            ],
            'album',
            [
            ['id', 'SERIAL PRIMARY KEY'],
            ['parent_id', 'INT', 'REFERENCES album(id)'],
            ['type', 'INT', 'REFERENCES filesystemaccesstypes(id)'],
            ['name_changeable', 'BOOL', '', 'DEFAULT TRUE'],
            ['allow_user_children', 'BOOL', '', 'DEFAULT TRUE'],
            ['prevalbum_id', 'INT', 'REFERENCES album(id)'],
            ['listorder', 'FLOAT' ],
            ['name', 'TEXT'],
            ],
            'albumimage',
            [
            ['parent_id', 'INT', 'REFERENCES album(id)'],
            ['image_id', 'INT', 'REFERENCES image(id)'],
            ['listorder', 'FLOAT' ],
            ['nextimage_id', 'INT', 'REFERENCES image(id)'],
            ['generatedlink', 'BOOL', '', 'DEFAULT FALSE'],
            ],
            ]

        self.indexes = [
            'CREATE UNIQUE INDEX directory_accesspath ON directory(accesstype_id, path)',
            'CREATE UNIQUE INDEX image_basenamedir ON image(basename, directory_id)',
            'CREATE UNIQUE INDEX imagedescription_ids ON imagedescription(description_id, image_id)',
            'CREATE UNIQUE INDEX imageinstance_name ON imageinstance(image_id,name)',
            'CREATE UNIQUE INDEX album1image_bothids ON albumimage(parent_id, image_id)',
            ]
        self.initialvalues = [
            "INSERT INTO interesttypes(type) VALUES ('Post Office P')",
            "INSERT INTO interesttypes(type) VALUES ('Post Office U')",
            "INSERT INTO interesttypes(type) VALUES ('Post Office')",
            "INSERT INTO filesystemaccesstypes (id, name,icon_name) VALUES (1, 'filesystem','stock_gtk-directory_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES (2, 'gtk-directory', 'stock_gtk-directory_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES (3, 'CD-Rom', 'stock_CD-Rom_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES (4, 'Floppy', 'stock_Floppy_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES (5, 'Harddisk', 'stock_Harddisk_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES (6, 'Network', 'stock_Network_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES(7, 'None',null)",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES(8, 'People class', 'icon_Person_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES(9, 'Place class', 'icon_Place_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES(10, 'Thing class', 'icon_Thing_24.png')",
            "INSERT INTO filesystemaccesstypes(id, name, icon_name) VALUES(11, 'Event class', 'icon_Event_24.png')",

           ]

    def _createIndexes(self) :
        cursor = self.dbh.cursor()
        for idx in self.indexes :
            cursor.execute(idx)
            self.dbh.commit()
            
    def _insertDefaultData(self) :
        cursor = self.dbh.cursor()
        for idx in self.initialvalues :
            cursor.execute(idx)
        self.dbh.commit()


    def insertCreateInfoIntoSchematable(self) :
        cursor = self.dbh.cursor()
        cursor.execute('DROP TABLE schematable');
        cursor.execute('DROP TABLE schemafields');
        cursor.execute('CREATE TABLE schematable (tablename TEXT PRIMARY KEY, version INT )');
        cursor.execute('CREATE TABLE schemafields (tablename TEXT, fieldname TEXT, fieldtype TEXT, constraintname TEXT)');
        self.dbh.commit()
        
        cursor = self.dbh.cursor()
        tables = self.tables[:]
        tables.reverse()
        while len(tables) > 0:
            table = tables.pop()
            print sql, table
            cursor.execute(sql,table, '1')
            fields = tables.pop()
            for field in fields :
                field = field[:]
                field.reverse()
                fieldname = field.pop()
                fieldtype = field.pop()
                constraintname = ''
                if len(field) > 0:
                    constraintname = field.pop()
                print sql, fieldname, fieldtype, constraintname
                cursor.execute(sql,table, fieldname, fieldtype, constraintname)
        self.dbh.commit()
            


    def needToCreateTables(self) :
        needTables = False
        cursor = self.dbh.cursor()
        try :
            cursor.execute('CREATE TABLE schematable (tablename TEXT PRIMARY KEY, version INT )');
            self.dbh.commit()
            needTables = True
            cursor.execute('CREATE TABLE schemafields (tablename TEXT, fieldname TEXT, fieldtype TEXT, constraintname TEXT)');
            self.dbh.commit()
            self.insertCreateInfoIntoSchematable()
        except :
            pass
        print "Returning from needToCreateTables", needTables
        return needTables

    def remapType(self, t) :
        return t;
    def createTables(self) :
        tables = self.tables[:]
        tables.reverse()
        while len(tables) > 0 :
            tablename = tables.pop()
            fields = tables.pop()
            fields = fields[:]
            fields.reverse()
            fieldtexts = []
            while len(fields) > 0 :
                f = fields.pop()
                f = f[:]
                f.reverse()
                fn = f.pop()
                ft = f.pop()
                ft = self.remapType(ft)
                fl = [fn,ft]
                while len(f) > 0 :
                    fl.append(f.pop())
                fieldtexts.append(' '.join(fl))
            sql = "CREATE TABLE " + tablename + "(\n   " \
                  + ",\n   ".join(fieldtexts) \
                  + "\n)\n"

            cursor = self.dbh.cursor()
            print "SQL", sql
            cursor.execute(sql)
            self.dbh.commit()

        self._createIndexes()
        self._insertDefaultData()

if __name__ == '__main__':
    dbh = PgSQL.connect(":".join(['localhost', '5432', 'flutterby', 'danlyke','danlyke']))
    c = CreateDBSql(dbh)
    c.insertCreateInfoIntoSchematable()
