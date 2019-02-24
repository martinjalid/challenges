#!/usr/bin/env python

import glob
import csv

def parseCsv():
	users = []
	with open('usuarios.csv', mode = 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter = ',')
		for row in csv_reader:
			users.append({'Name': row[0], 'Surname': row[1], 'Mail': row[2]})

	return users

users = parseCsv();
print users