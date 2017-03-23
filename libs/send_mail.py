#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import ConfigParser
import base64
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header


class SendMail:
    def __init__(self, sfile, conf_name):
        self._sfile = sfile
        self._conf_name = conf_name

    def __get_mail_conf(self):
        if not os.path.exists(self._sfile):
            print sys.exc_info()
            sys.exit(-1)
        conf = ConfigParser.ConfigParser()
        conf.read(self._sfile)
        try:
            mail_host = conf.get(self._conf_name, "host")
            mail_user = conf.get(self._conf_name, "user")
            mail_passwd_base64 = conf.get(self._conf_name, "passwd")
            mail_passwd = base64.decodestring(mail_passwd_base64)
            mail_show = conf.get(self._conf_name, "show")
        except Exception as e:
            print "Error:", e
            sys.exit(-2)
        return mail_host, mail_user, mail_passwd, mail_show

    # mail_type为"html"或"plain"
    # mail_name为发件人名
    # mailto_list为收件人list
    # mailcc_list为抄送list
    # subject为主题名，content为正文
    # attachment_list为附件路径list
    def send_mail(self, mail_type, mail_name, mailto_list, subject, content, mailcc_list=None, attachment_list=None):
        # 通过配置文件获取邮箱服务器、登录名、密码、发件人地址（发件人地址和登录名可能不同，如别名）
        mail_host, mail_user, mail_passwd, mail_show = self.__get_mail_conf()
        mail_from = "%s<%s>" % (Header(mail_name, "utf-8"), mail_show)
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = mail_from
        msg["To"] = ";".join(mailto_list)
        if mailcc_list is not None:
            msg["Cc"] = ";".join(mailcc_list)
        text_msg = MIMEText(content, _subtype=mail_type, _charset="utf-8")
        msg.attach(text_msg)
        if attachment_list is not None:
            for attachment_path in attachment_list:
                attachment_name = os.path.basename(attachment_path)
                fp = open(attachment_path, "rb")
                attachment = MIMEApplication(fp.read())
                fp.close()
                attachment.add_header("Content-Disposition", "attachment", filename=attachment_name)
                msg.attach(attachment)
        try:
            server = smtplib.SMTP_SSL()
            server.connect(mail_host)
            server.login(mail_user, mail_passwd)
            if mailcc_list is not None:
                server.sendmail(mail_from, mailto_list + mailcc_list, msg.as_string())
            else:
                server.sendmail(mail_from, mailto_list, msg.as_string())
            server.close()
            return True
        except Exception as e:
            print "Error:", e
            return False
