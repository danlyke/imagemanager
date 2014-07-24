#from pyPgSQL import PgSQL
import re

class GeoLookup :
    def __init__(self):
        self.dbh = PgSQL.connect("localhost::flutterby:danlyke:danlyke::")
        self.regexCityST = re.compile('^ *([A-Za-z][a-z]+( [A-Z][a-z]+)*), *([A-Za-z][a-z]+( [A-Z][a-z]+)*) *$')
        self.regexCityState = re.compile('^ *([A-Za-z][a-z]+( [A-Z][a-z]+)*), *([A-Z][A-Z]) *$')

    def lookupAddress(self, address):
        m = self.regexCityST.match(address)
        if not m :
            m = self.regexCityState.match(address)
        if m :
            city = m.group(1)
            state = m.group(3)
            print "City", city
            print "State", state
            cursor = self.dbh.cursor()
            sql = """SELECT lattitude, longitude FROM geoposition,pointofinterest,province WHERE
                     UPPER(pointofinterest.name) = UPPER(%s) AND
                     (UPPER(province.name)=UPPER(%s) OR UPPER(province.abbr)=UPPER(%s))
                     AND geoposition.id=pointofinterest.geoposition_id
                     AND province.id=pointofinterest.province_id"""
            cursor.execute(sql, city,state,state)
            latmin = None
            latmax = None
            lonmin = None
            lonmax = None
            
            row = cursor.fetchone()
            while row :
                if latmin == None or latmin > row[0] :
                    latmin = row[0]
                if latmax == None or latmax < row[0] :
                    latmax = row[0]
                if lonmin == None or lonmin > row[1] :
                    lonmin = row[1]
                if lonmax == None or lonmax < row[1] :
                    lonmax = row[1]
                row = cursor.fetchone()

            if latmin == None:
                return (None, None, None)
            return ((lonmin + lonmax) / 2, (latmin + latmax) / 2, ((latmax - latmin) + (lonmax - lonmin)) / 2)
            

if __name__ == '__main__':
    gl = GeoLookup()
    gl.lookupAddress('San Anselmo, California')
    gl.lookupAddress('San Anselmo, CA')
    gl.lookupAddress('Raleigh, North Carolina')
    gl.lookupAddress('Raleigh, NC')
    gl.lookupAddress('West Bumblefuck, South Carolina')
