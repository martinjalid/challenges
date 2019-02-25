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
# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEText import MIMEText
from ldap3 import Server, Connection, ALL, NTLM

config = configparser.ConfigParser()
config.read('config.ini')

LDAP = config['LDAP']
DATABASE = config['DATABASE']

def loginGmail():
	try:
		gmail = smtplib.SMTP('smtp.gmail.com', 587)
		gmail.ehlo()
		gmail.starttls()
		gmail.ehlo()
		gmail.login("martinjalid@gmail.com", "622033940")
		msg = "Hello!" # The /n separates the message from the headers
		gmail.sendmail("martinjalid@gmail.com", "martin.jalid@123seguro.com.ar", msg)
		print(gmail)
	except Exception as e:
		print(e)

def connectLdap():
	try:
		server = Server(LDAP['HOST'], get_info=ALL)
		conn = Connection(server, 'cn=admin,dc=meli,dc=com', password=LDAP['PASSWORD'], auto_bind=True)
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
	    cursor.execute("CREATE DATABASE IF NOT EXISTS challenge2")
	    cursor.execute("USE challenge2")
	    cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(50), Surname VARCHAR(50), mail VARCHAR(100))")
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
		createUserInDB(user)
		createUserInLDAP(user)
		# sendMail(user['Mail'])

def createUserInDB(user):
	print(user, 'DB')

def createUserInLDAP(user):
	print(user, 'LADP')

def sendMail(mail):
	fromaddr = "martinjalid@gmail.com"
	toaddr = "martin.jalid@123seguro.com.ar"
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = "Python email"
	body = "Python test mail"
	msg.attach(MIMEText(body, 'plain'))
	text = msg.as_string()
	gmail.sendmail(fromaddr, toaddr, text)
	print('Mail sended to: '+ mail)

# loginGmail()
# createDatabase()
connectLdap()

users = parseCsv()
createUsers(users)

password = generatePassword()

hashed = bcrypt.hashpw(password, bcrypt.gensalt())