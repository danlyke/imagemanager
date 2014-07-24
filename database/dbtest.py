#!/usr/bin/python

from sqlite3 import dbapi2 as db

if __name__ == '__main__':
	dbi = db.connect('test.sqlite3')
	print "paramstyle", db.paramstyle
	print "apilevel", db.apilevel

	cur = dbi.cursor()
	cur.execute('CREATE TABLE abc ( id INT AUTO_INCREMENT PRIMARY KEY, xyz TEXT )');
	cur.close();
	dbi.commit();

	cur = dbi.cursor()
	cur.execute("INSERT INTO abc(xyz) VALUES ('hey')")
	cur.execute("INSERT INTO abc(xyz) VALUES ('there')")
	cur.execute("INSERT INTO abc(xyz) VALUES ('dood')")
	cur.close();
	dbi.commit()

	cur = dbi.cursor()
	cur.execute("SELECT * FROM abc ORDER BY id DESC")
	print cur.description
	row = cur.fetchone()
	while row :
		print row
		row = cur.fetchone()

	cur.close()
	dbi.close()