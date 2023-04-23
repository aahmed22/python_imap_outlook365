from re import template
import pandas as pd
import numpy
import smtplib, ssl
import urllib, os, json
from sqlalchemy import create_engine
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import psql_string, smtp_host, smtp_port, smtp_user, smtp_passwd, smtp_cc_list, report1, report2, psql_table1, psql_table2


class DataExport(object):
    def __init__(self, report_name, file_name, file_data, sender):
        self.psql_string = psql_string
        self.engine = create_engine(self.psql_string)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_passwd = smtp_passwd
        self.smtp_cc_list = smtp_cc_list
        self.report_name = report_name
        self.file_name = file_name
        self.file_data = file_data 
        self.sender = sender
        self.report1 = report1
        self.report2 = report2
        self.psql_table1 = psql_table1
        self.psql_table2 = psql_table2
        self.writeReportData()


    def writeReportData(self):
        report_path = "./" + str(self.report_name) + "/"
        
        if os.path.isdir(report_path):
            print("Directory exists!")
        else:
            os.mkdir(report_path)
            
        file_path = os.path.join(report_path, self.file_name)
        
        with open(file_path, mode='wb') as file:
            file.write(self.file_data)
            file.close()
            
        self.reportDataDump(file_path)
    

    def reportDataDump(self, file):
        custom_df = pd.DataFrame()
        
        if (self.report_name == self.report1):
            custom_df = pd.read_csv(file)
            custom_df.to_sql(self.psql_table1, self.engine, if_exists='append', index=False, chunksize = 20000)
            self.fileDeletion(file)
            self.sendEmail()

        if (self.report_name == self.report2):
            custom_df = pd.read_excel(file)
            custom_df.to_sql(self.psql_table2, self.engine, if_exists='replace', index=False, chunksize = 100000)
            self.fileDeletion(file)
            self.sendEmail()

    
    def fileDeletion(self, file):
        print(f"Now deleting {file}")
        os.remove(file)
        print(f"{file} is deleted...\n")
       

    def sendEmail(self):
        custom_subject = str(self.report_name) + " " + "PostgreSQL Data Drop Complete!"
        custom_body = """
          Hi,
          
          The PostgreSQL Data Export is complete!
          
          Regards,
        """
        
        smtp_server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        message = MIMEMultipart()
        message['Subject'] = custom_subject
        message['From'] = self.smtp_user
        message['To'] = self.sender
        message['Cc'] = self.smtp_cc_list
        body = custom_body
        message.attach(MIMEText(body, "plain"))

        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        smtp_server.login(self.smtp_user, self.smtp_passwd)
        smtp_server.send_message(message)
        smtp_server.quit()
        smtp_server.close()