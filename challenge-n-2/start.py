#!/usr/bin/env python

import glob
import csv
import random
import string
import sys
import MySQLdb
import bcrypt
# import ldap
	
# l = ldap.initialize('ldap://localhost:389')
# l.search_s('ou=Testing,dc=stroeder,dc=de',ldap.SCOPE_SUBTREE,'(cn=fred*)',['cn','mail'])
# [('cn=Fred Feuerstein,ou=Testing,dc=stroeder,dc=de', {'cn': ['Fred Feuerstein']})]
# r = l.search_s('ou=Testing,dc=stroeder,dc=de',ldap.SCOPE_SUBTREE,'(objectClass=*)',['cn','mail'])
# for dn,entry in r:
# 	print('Processing',repr(dn))
# 	handle_ldap_entry(entry)
# print l

try:
    conn = MySQLdb.connect(host='localhost',user='root',passwd='root')
    cursor = conn.cursor()
except Exception as e:
    print(e)
    sys.exit(1)

def generatePassword():
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

def createDatabase():
	try:
	    cursor.execute("CREATE DATABASE IF NOT EXISTS challenge2")
	    cursor.execute("USE challenge2")
	    cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(50), Surname VARCHAR(50), mail VARCHAR(100))")
	except Exception as e:
	    print(e)

def parseCsv():
	users = []
	with open('usuarios.csv', mode = 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter = ',')
		for row in csv_reader:
			users.append({'Name': row[0], 'Surname': row[1], 'Mail': row[2]})

	return users

# createDatabase()
users = parseCsv();
password = generatePassword()
hashed = bcrypt.hashpw(password, bcrypt.gensalt())

for user in users:
	print user