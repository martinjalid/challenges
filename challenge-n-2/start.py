#!/usr/bin/env python

import glob
import csv
import random
import string
import sys
import MySQLdb
import bcrypt
import configparser
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ldap3 import Server, Connection, ALL, NTLM

config = configparser.ConfigParser()
config.read('config.ini')

LDAP = config['LDAP']
DATABASE = config['DATABASE']
GMAIL = config['GMAIL']

def loginGmail():
	try:
		passwor_gmail = input('Pass Gmail')
		gmail = smtplib.SMTP('smtp.gmail.com', 587)
		gmail.ehlo()
		gmail.starttls()
		gmail.ehlo()
		gmail.login(GMAIL["ACCOUNT"], GMAIL['PASSWORD'])
		return gmail;
	except Exception as e:
		print(e)

def connectLdap():
	try:
		server = Server(LDAP['HOST'], get_info=ALL)
		connLdap = Connection(server, 'cn=admin,dc=meli,dc=com', password=LDAP['PASSWORD'], auto_bind=True)
		print(server, connLdap)
		return connLdap
	except Exception as e:
		print(e)

try:
    conn = MySQLdb.connect(host=DATABASE['HOST'],user=DATABASE['USER'],passwd=DATABASE['PASSWORD'])
    cursor = conn.cursor()
except Exception as e:
    print(e)
    sys.exit(1)

def generatePassword():
	try:
		return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
	except Exception as e:
		print(e)

def createDatabase():
	try:
	    cursor.execute("DROP DATABASE challenge2")
	    cursor.execute("CREATE DATABASE IF NOT EXISTS challenge2")
	    cursor.execute("USE challenge2")
	    cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(50), surname VARCHAR(50), mail VARCHAR(100), password VARCHAR(100))")
	except Exception as e:
	    print(e)

def parseCsv():
	try:
		users = []
		with open(config['CSV']['PATH'], mode = 'r') as csv_file:
			csv_reader = csv.reader(csv_file, delimiter = ',')
			for row in csv_reader:
				users.append({'Name': row[0].strip(), 'Surname': row[1].strip(), 'Mail': row[2].strip()})

		return users
	except Exception as e:
		print(e)

def createUsers(users):
	for user in users:
		password = generatePassword()
		
		user['Password'] = password
		# createUserInDB(user)
		createUserInLDAP(user)
		# sendMail(user)

def createUserInDB(user):
	try:
		hashed = bcrypt.hashpw(user['Password'], bcrypt.gensalt())
		sql = "INSERT INTO users(name, surname, mail, password) VALUES(%s, %s, %s, %s)"
		values = (user['Name'], user['Surname'], user['Mail'], hashed)
		cursor.execute(sql, values)
		conn.commit()
	except Exception as e:
		print(e)

def createUserInLDAP(user):
	domain = 'meli.com'
	username = 'john.smith'
	useremail = 'john@smith.com'
	userpswd = 'AbcDef$$1234567'
	userdn = 'CN=john.smith,OU=Users,DC=meli,DC=com'

	connLdap.add(userdn, attributes={
	   'objectClass': ['organizationalPerson', 'person', 'top', 'user'],
	   'sAMAccountName': username,
	   'userPrincipalName': "{}@{}".format(username, domain),
	   'displayName': username,
	   'mail': useremail  # optional
	})

	result = connLdap.add_s(dn, ldap.modlist.addModlist(modlist))
	print(connLdap.result)

def sendMail(user):
	fromaddr = GMAIL['ACCOUNT']
	toaddr = user['Mail']
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = "Bienvenido a MercadoLibre!"
	body = "Su nuevo usuario es: {} \nLa contraseña para ingresar: {}".format(user['Name'], user['Password'])
	msg.attach(MIMEText(body, 'plain'))
	text = msg.as_string()
	gmail.sendmail(fromaddr, toaddr, text)
	print(gmail)

gmail = loginGmail()
createDatabase()
connLdap = connectLdap()
users = parseCsv()
createUsers(users)