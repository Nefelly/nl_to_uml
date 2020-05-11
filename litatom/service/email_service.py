# coding: utf-8
import random
import logging
import json
import smtplib
from email.mime.text import MIMEText  # 邮件文本
from email.mime.multipart import MIMEMultipart


logger = logging.getLogger(__name__)

class EmailService(object):
    """
    告警系统，
    qq邮箱发送：https://blog.csdn.net/qlzy_5418/article/details/86683856
    """

    @classmethod
    def send_mail(cls, to, content, subject='Alert'):
        sender = '382365209@qq.com'
        pwd = 'vshditifewnhcajb'
        message = MIMEText(content, "plain", "utf-8")
        message['Subject'] = 'alert' if not subject else subject
        if not isinstance(to, list):
            to = [to]
        message['To'] = ','.join(to)
        message['From'] = sender
        smtp = smtplib.SMTP_SSL("smtp.qq.com", 465)
        smtp.login(sender, pwd)
        smtp.sendmail(sender, to, message.as_string())

    @classmethod
    def send_file(cls, to, file_add, subject='stat'):
        message = MIMEMultipart()
        subject = file_add

        att2 = MIMEText(open(file_add, 'rb').read(), 'base64', 'utf-8')
        att2["Content-Type"] = 'application/octet-stream'
        att2["Content-Disposition"] = 'attachment; filename="%s"' % file_add
        message.attach(att2)

        sender = '382365209@qq.com'
        pwd = 'vshditifewnhcajb'
        message['Subject'] = 'alert' if not subject else subject
        if not isinstance(to, list):
            to = [to]
        message['To'] = ','.join(to)
        message['From'] = sender
        smtp = smtplib.SMTP_SSL("smtp.qq.com", 465)
        smtp.login(sender, pwd)
        smtp.sendmail(sender, to, message.as_string())