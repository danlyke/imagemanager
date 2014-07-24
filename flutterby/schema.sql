

computer
	['id', 'SERIAL PRIMARY KEY'],
		

mediatypes
	['id', 'SERIAL PRIMARY KEY'],
	['mimetype', 'TEXT'],


file
	computer_id INT REFERENCES computer(id),
	

	

   




