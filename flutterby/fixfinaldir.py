from pyPgSQL import PgSQL
import os

dbh = PgSQL.connect("localhost::flutterby:danlyke:danlyke::")
cursor = dbh.cursor()
cursor.execute('SELECT id, path FROM directory');
cmds = []
row = cursor.fetchone()
while row :
    cmds.append((row[0], os.path.split(row[1])[-1]))
    row = cursor.fetchone()

for cmd in cmds :
    sql = 'UPDATE directory SET finaldir=%s WHERE id=%s'
    cursor.execute(sql, cmd[1], cmd[0])

dbh.commit()
