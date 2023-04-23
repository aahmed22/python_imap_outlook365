import sys  
import base64
import json
import logging
import msal
import imaplib, email
from email.header import decode_header
import json, os, time
from email.utils import parseaddr
from re import search
from itertools import chain
from config import tenant_id, client_id, client_secret, scope, authority, service_account, imap_host, psql_string, subject1, subject2, report1, report2
from imapOperations import DataExport


uid_max = 0
criteria = {

}

def get_first_text_block(msg):
    type = msg.get_content_maintype()

    if type == 'multipart':
        for part in msg.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    elif type == 'text':
        return msg.get_payload()


def search_string(uid_max, criteria):
    c = list(map(lambda t: (t[0], '"'+str(t[1])+'"'), criteria.items())) + [('UID', '%d:*' % (uid_max+1))]
    return '(%s)' % ' '.join(chain(*c))


def get_attachments(msg, mail_sender, report_name):
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        file_name = part.get_filename()

        if bool(file_name):
            if file_name.startswith("LinkedIn"):
                file_data = part.get_payload(decode=True)
                DataExport(report_name, file_name, file_data, mail_sender)
            
            if file_name.startswith("AMEX"):
                file_data = part.get_payload(decode=True)
                DataExport(report_name, file_name, file_data, mail_sender)
            

def GenerateOAuth2String(username, access_token):
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    return auth_string

config = {
    "authority": authority,
    "client_id": client_id,
    "scope": [scope],
    "secret": client_secret,
    "tenant-id": tenant_id
}

app = msal.ConfidentialClientApplication(config['client_id'], authority=config['authority'], client_credential=config['secret'])
result = app.acquire_token_silent(config["scope"], account=None)

if not result:
    print("No suitable token exists in cache. Let's get a new one from AAD.")
    result = app.acquire_token_for_client(scopes=config["scope"])

imap = ""

if "access_token" in result:
    user = service_account
    server = imap_host
    imap = imaplib.IMAP4_SSL(server)  
    #imap.debug = 4
    imap.authenticate('XOAUTH2', lambda x: GenerateOAuth2String(user, result['access_token']))
else:
    print(result.get("error"))
    print(result.get("error_description"))
    print(result.get("correlation_id"))
    
imap.select('INBOX')
result, data = imap.uid('search', None, search_string(uid_max, criteria))

uids = [int(s) for s in data[0].split()]
if uids:
    uid_max = max(uids)

imap.logout()

while True:
    try:
        imap.select('INBOX')
    except Exception as e:
        app = msal.ConfidentialClientApplication(config['client_id'], authority=config['authority'], client_credential=config['secret'])
        result = app.acquire_token_silent(config["scope"], account=None)
        
        if not result:
            print("No suitable token exists in cache. Let's get a new one from AAD.")
            result = app.acquire_token_for_client(scopes=config["scope"])
    
        if "access_token" in result:
            print(result['token_type'])
        else:
            pass
            print(result.get("error"))
            print(result.get("error_description"))
            print(result.get("correlation_id"))
            
        
        imap = imaplib.IMAP4_SSL(server)
        #imap.debug = 4
        imap.authenticate('XOAUTH2', lambda x: GenerateOAuth2String(user, result['access_token']))
        imap.select('INBOX')
    
    result, data = imap.uid('search', None, search_string(uid_max, criteria))
    uids = [int(s) for s in data[0].split()]


    for uid in uids:
        if uid > uid_max:
            result, data = imap.uid('fetch', str(uid), '(RFC822)')  
            msg = email.message_from_bytes(data[0][1])
            subject = str(msg).split("Subject: ", 1)[1].split("\nTo:", 1)[0]
            who = str(msg).split("From: ", 1)[1].split("\nTo:", 1)[0]
            head = decode_header(str(msg))
            subject, encoding = decode_header(msg["Subject"])[0]
            
            uid_max = uid
            
            text = get_first_text_block(msg)
            print ('INCOMING NEW MESSAGE :::::::::::::::::::::')
            
            parse_name, parse_address = parseaddr(who)
            mail_sender = parse_address
            
            if search(subject1, subject.lower()):
                get_attachments(msg, mail_sender, report1)

            if search(subject2, subject.lower()):
                get_attachments(msg, mail_sender, report2)
        
imap.logout()
time.sleep(1)