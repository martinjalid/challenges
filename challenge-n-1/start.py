#!/usr/bin/env python

import glob
import re
import smtplib
import time
import imaplib
import email
import MySQLdb
from datetime import datetime

SMTP_SERVER = "imap.gmail.com"
SMTP_PORT = 993

conn = MySQLdb.connect(host='localhost',user='root',passwd='root')
cursor = conn.cursor()

def printMessage(msg):
    msgLen = len(msg) + 10
    print "-" * msgLen
    print "|    " + msg + "    |"
    print "-" * msgLen + "\n"

def validateMail(mail):
    return re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', mail)

def validateDomain(mail):
    name, domain = mail.split('@')
    return domain == 'gmail.com'

def loginGmail(account, password):
    global SMTP_SERVER
    try:
        gmail = imaplib.IMAP4_SSL(SMTP_SERVER)
        x = gmail.login(account, password)
        if x[0] == 'OK':
            return gmail
    except Exception as e:
        return False

def inputData():
    mail = raw_input("Ingrese la cuenta de Gmail para buscar: ") 

    isValid = validateMail(mail)
    if validateMail(mail) and validateDomain(mail):
        password = raw_input("Ingrese la password de la cuenta ingresada: ") 
    else:
        print("El mail ingresado no es un mail valido")

    return mail, password

def parseMail(id):
    typ, data = gmail.fetch(id, '(RFC822)')
    
    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_string(response_part[1])
            return {'Subject': msg['subject'], 'From': msg['from'], 'Date': msg['date']}


def getMails(gmail):
    try:
        gmail.select('inbox')

        type, data = gmail.search(None, '(SUBJECT "Challenge")')
        # type, data = gmail.search(None, '(SUBJECT "Challenge" BODY \"desarrolarlo\")')
        mail_ids = data[0]
        id_list = mail_ids.split()

        mails = [];

        for i in id_list:
            mails.append(parseMail(i))

        printMessage('Se encontraron '+str(len(mails))+' mails')

        return mails
    except Exception as e:
        print(e)   

def createDatabase():
    printMessage('Creando la base de datos')
    try:
        # cursor.execute("DROP DATABASE IF EXISTS challenge")
        cursor.execute("CREATE DATABASE IF NOT EXISTS challenge")
        cursor.execute("USE challenge")
        cursor.execute("CREATE TABLE IF NOT EXISTS mails(id INT AUTO_INCREMENT PRIMARY KEY,from_email VARCHAR(100), subject VARCHAR(100), date DATETIME)")
    except Exception as e:
        print(e)

def insertMails(mails):
    for val in mails:
        # formated_date = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p');
        cursor.execute("INSERT INTO mails(from_email, subject, date) VALUES('"+val['From']+"', '"+val['Subject']+"', '"+val['Date']+"')")

mail = "martinjalid@gmail.com"
password = "622033940"

# mail, password = inputData();
gmail = loginGmail(mail, password)
while not gmail:
    print('Error, No se pudo loguear a la cuenta')
    
    printMessage(mail)
    
    password = raw_input('Ingrese la password nuevamente: ')

printMessage('Logueado Correctamente')

mails = getMails(gmail)

createDatabase()

for val in mails:
    print( datetime.strptime(val['Date'], '%b %d %Y %I:%M%p') )
# printMessage('Insertando registros')

# insertMails(mails)