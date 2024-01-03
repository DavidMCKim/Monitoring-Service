# 메일 HTML 변환 클래스
import copy
import smtplib

import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


config = configparser.ConfigParser()
config.read('./config.ini', encoding='utf8')

class EmailHTMLContent:
    def __init__(self, str_subject, template):
        self.msg = MIMEMultipart()

        # email subject
        self.msg['Subject'] = str_subject

        # email content
        mime_msg = MIMEText(template, 'html')       # create MIME HTML string
        self.msg.attach(mime_msg)

    def get_message(self, str_from_email_addr, str_to_email_addrs):
        mm = copy.deepcopy(self.msg)
        mm['From'] = str_from_email_addr            # sender
        mm['To'] = ",".join(str_to_email_addrs)     # receiver list
        return mm



# 메일 설정 관련 클래스
class EmailSender:
    def __init__(self, str_host, num_port=25):
        self.str_host = str_host
        self.num_port = num_port
        self.ss = smtplib.SMTP(host=str_host, port=num_port)

        # Authorize SMTP
        self.ss.starttls()                                          # start TLS(Transport Layer Security)
        self.ss.login(config['ADD']['id'], config['ADD']['pw'])   # connect mailserver id and password

    def send_message(self, emailContent, str_from_email_addr, str_to_email_addrs):
        cc = emailContent.get_message(str_from_email_addr, str_to_email_addrs)
        self.ss.send_message(cc, from_addr=str_from_email_addr, to_addrs=str_to_email_addrs)
        del cc