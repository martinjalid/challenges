#!/usr/bin/env python

import imaplib
import MySQLdb
import glob
import re
import time
import sys
import email

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

try:
    conn = MySQLdb.connect(host='localhost',user='root',passwd='root')
    cursor = conn.cursor()
except Exception as e:
    print(e)
    sys.exit(1)

def printMessage(msg):
    msgLen = len(msg) + 10
    print( "-" * msgLen)
    print( "|    " + msg + "    |")
    print( "-" * msgLen + "\n")

def validateMail(mail):
    isMail = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', mail)
    if isMail:
        name, domain = mail.split('@')
        isGmail = domain == 'gmail.com'
        return isMail and isGmail

def authGmail(account, password):
    global IMAP_SERVER
    try:
        gmail = imaplib.IMAP4_SSL(IMAP_SERVER)
        login = gmail.login(account, password)
    
        return login[0] == 'OK'
    
    except Exception as e:
        return False

def getGmailClient(account, password):
    global IMAP_SERVER
    try:
        gmail = imaplib.IMAP4_SSL(IMAP_SERVER)
        login = gmail.login(account, password)
    
        return gmail
    
    except Exception as e:
        return False

def inputData():
    mail = raw_input("Ingrese la cuenta de Gmail para buscar: ") 

    while not validateMail(mail):
        mail = raw_input("El mail ingresado no es un mail valido, ingrese nuevamente: ")
    
    password = raw_input("Ingrese la password de la cuenta ingresada: ") 

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

        type, data = gmail.search(None, '(OR SUBJECT "DevOps" BODY \"DevOps\")')
        mail_ids = data[0]
        id_list = mail_ids.split()

        mails = [];

        for mail_id in id_list:
            mails.append(parseMail(mail_id))

        printMessage('Se encontraron '+str(len(mails))+' mails')

        return mails
    except Exception as e:
        print(e)   

def createDatabase():
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS challenge1")
        cursor.execute("USE challenge1")
        cursor.execute("CREATE TABLE IF NOT EXISTS mails(id INT AUTO_INCREMENT PRIMARY KEY,from_email VARCHAR(100), subject TEXT, date VARCHAR(100))")
    except Exception as e:
        print(e)

def insertMails(mails):
    printMessage('Insertando registros')
    try:
        for val in mails:
            sql = "INSERT INTO mails(from_email, subject, date) VALUES(%s, %s, %s)"
            values = (val['From'], val['Subject'], val['Date'])
            cursor.execute(sql, values)
            conn.commit()
    except Exception as e:
        print(e)
    
createDatabase()

account, password = inputData();
while not authGmail(account, password):
    print('Error, No se pudo loguear a la cuenta')
        
    password = raw_input('Ingrese la password nuevamente [presione z y enter para reingresar el mail]: ')
    if password == 'z':
        account, password = inputData()

printMessage('Logueado Correctamente')

gmail = getGmailClient(account, password)
mails = getMails(gmail)

insertMails(mails)