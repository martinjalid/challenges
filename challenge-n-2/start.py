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
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE

config = configparser.ConfigParser()
config.read('config.ini')

LDAP = config['LDAP']
DATABASE = config['DATABASE']
GMAIL = config['GMAIL']

def printMessage(msg):
    msgLen = len(msg) + 10
    print( "-" * msgLen)
    print( "|    " + msg + "    |")
    print( "-" * msgLen + "\n")

def loginGmail():
	try:
		gmail = smtplib.SMTP('smtp.gmail.com', 587)
		gmail.ehlo()
		gmail.starttls()
		gmail.ehlo()
		gmail.login(GMAIL["ACCOUNT"], GMAIL['PASSWORD'])
		return gmail;
	except Exception as e:
		print('Error trying to login into Gmail: '+e)

def connectLdap():
	try:
		server = Server(LDAP['HOST'], get_info=ALL)
		dn = "cn={},dc={},dc={}".format(LDAP['USER'], LDAP['DC1'], LDAP['DC2'])
		connLdap = Connection(server, dn, password=LDAP['PASSWORD'], auto_bind=True)
		return connLdap
	except Exception as e:
		print('Error trying to connect to LDAP: '+e)

try:
    conn = MySQLdb.connect(host=DATABASE['HOST'],user=DATABASE['USER'],passwd=DATABASE['PASSWORD'])
    cursor = conn.cursor()
except Exception as e:
    print('Error trying to connect to the database: '+e)

def generatePassword():
	try:
		return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
	except Exception as e:
		print('Error generating random password: '+e)

def createDatabase():
	try:
		cursor.execute("CREATE DATABASE IF NOT EXISTS challenge2")
		cursor.execute("USE challenge2")
		cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(50), surname VARCHAR(50), mail VARCHAR(100) NOT NULL, password VARCHAR(100), state_id INT(11) NOT NULL, ldapUid VARCHAR(50),created_at timestamp DEFAULT CURRENT_TIMESTAMP, UNIQUE (mail))")
		cursor.execute("CREATE TABLE IF NOT EXISTS states(id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(10), description VARCHAR(100))")
		seedStatesTable()
		printMessage('Database created')
	except Exception as e:
	    print('Error trying to create the database: '+e)

def seedStatesTable():
	try:
		states = [
			"('NEWUSER', 'Just created user')",
			"('LDAPOK', 'User replicated into LDAP')",
			"('LDAPERR', 'Error replicating user into LDAP')",
			"('MAILOK', 'Email notification sent')",
			"('MAILERR', 'Email notification error')",
		]

		insert = "INSERT INTO states (name, description) VALUES "
		cursor.execute(insert+','.join(states))
		conn.commit()
	except Exception as e:
		print('Error trying to seed states table: '+e)

def parseCsv():
	try:
		users = []
		with open(config['CSV']['PATH'], mode = 'r') as csv_file:
			csv_reader = csv.reader(csv_file, delimiter = ',')
			for row in csv_reader:
				users.append({'Name': row[0].strip(), 'Surname': row[1].strip(), 'Mail': row[2].strip()})

		return users
	except Exception as e:
		print('Error in parsing csv: '+e)

def createUsers(users):
	for user in users:
		password = generatePassword()
		user['Password'] = password
		user['HashedPassword'] = bcrypt.hashpw(user['Password'], bcrypt.gensalt())
		createUserInDB(user)
		createUserInLDAP(user)
		sendMail(user)

def createUserInDB(user):
	try:
		cursor.execute('SELECT id FROM states WHERE name="NEWUSER"')
		state = cursor.fetchone()
		state_id = state[0]

		sql = "INSERT INTO users(name, surname, mail, password, state_id) VALUES(%s, %s, %s, %s, %s)"
		values = (user['Name'], user['Surname'], user['Mail'], user['HashedPassword'], str(state_id))
		cursor.execute(sql, values)
		conn.commit()
	except Exception as e:
		print('Create user in db ERROR: '+e)

def createUserInLDAP(user):
	try:
		randomID = str(random.randint(0, 2000))

		uid = user['Name'] + user['Surname'] + randomID

		username = user['Name'].lower()+'.'+user['Surname'].lower()
		useremail = user['Mail']
		userpswd = user['Password']
		exists = connLdap.search('cn={},ou=Users,dc=meli,dc=com'.format(username), '(objectclass=inetorgperson)')
		if not exists:
			connLdap.add('ou=Users,dc=meli,dc=com', 'organizationalUnit')
			created = connLdap.add('cn={},ou=Users,dc=meli,dc=com'.format(username), ['inetorgperson'], {
				'uid': uid,
				'givenName': user['Name'], 
				'displayNAme': user['Name']+ ' '+user['Surname'], 
				'sn': user['Surname'], 
				'mail': useremail, 
				'userPassword': userpswd,
			})
			if created:
				updateUserState(user, 'LDAPOK')
				updateUserLdapUid(user, uid)
			else:
				updateUserState(user, 'LDAPERR')

	except Exception as e:
		print(e)

def updateUserState(user, name):
	try:
		cursor.execute('SELECT id FROM states WHERE name="{}"'.format(name))
		state = cursor.fetchone()
		
		cursor.execute('SELECT id FROM users WHERE mail="{}"'.format(user['Mail']))
		user_db = cursor.fetchone()

		if not state:
			print('Error: state {} not found in the database'.format(name))
		if not user_db:
			print('Error: user {} not found in the database'.format(user['Mail']))
		else:
			user_id = user_db[0]
			state_id = state[0]
			update = 'UPDATE users SET state_id = {} where id = {}'.format(state_id, user_id)
			cursor.execute(update)
			conn.commit()

	except Exception as e:
		print('Error updating state of user: '+e)

def updateUserLdapUid(user, uid):
	try:
		cursor.execute('SELECT id FROM users WHERE mail="{}"'.format(user['Mail']))
		user_db = cursor.fetchone()

		if not user_db:
			print('Error: user {} not found in the database'.format(user['Mail']))
		else:
			user_id = user_db[0]
			update = 'UPDATE users SET ldapUid = "{}" where id = {}'.format(uid, user_id)
			cursor.execute(update)
			conn.commit()

	except Exception as e:
		print(e)

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
	try:
		gmail.sendmail(fromaddr, toaddr, text)
		updateUserState(user, 'MAILOK')
		printMessage('Mail sent to '+fromaddr)
	except Exception as e:
		print('Error trying to send mail: '+e)
		updateUserState(user, 'MAILERR')

gmail = loginGmail()
createDatabase()
connLdap = connectLdap()
users = parseCsv()
printMessage('{} usuarios para crear'.format(len(users)))
createUsers(users)