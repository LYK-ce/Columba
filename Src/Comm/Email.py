#Presented by KeJi
#Date : 2026-01-19

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import parseaddr

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Log.Log import Log_Info

class Comm:
    """
    通信模组，通过Email实现与用户的通信
    """
    
    def __init__(self, config):
        """
        读取config当中的Comm部分配置，为Comm类配置各类属性
        """
        comm_config = config["Comm"]
        agent_config = comm_config["agent"]
        
        self.smtp_host = agent_config["smtp_host"]
        self.smtp_port = agent_config["smtp_port"]
        self.imap_host = agent_config["imap_host"]
        self.imap_port = agent_config["imap_port"]
        self.password = agent_config["password"]
        
        self.agent_email = agent_config["username"]
        self.user_email = comm_config["user_email"]
    
    def _Validate_User(self, from_addr):
        """
        内部调用的函数，检查当前接收邮件的发件人是否为user_email
        """
        _, email_addr = parseaddr(from_addr)
        return email_addr in self.user_email
    
    def Send(self, text):
        """
        将text文本的内容发送到user_email当中，标题内容为"Columba Agent Info"
        """
        for recipient in self.user_email:
            msg = MIMEText(text, "plain", "utf-8")
            msg["Subject"] = "Columba Agent Info"
            msg["From"] = self.agent_email
            msg["To"] = recipient
            
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as smtp:
                smtp.login(self.agent_email, self.password)
                smtp.sendmail(self.agent_email, recipient, msg.as_string())
            
            Log_Info("Comm", f"发送邮件至 {recipient}: {text}")
    
    def _Send_Imap_Id(self, imap):
        """
        发送IMAP ID命令，163邮箱需要此信息才能正常使用
        """
        imap_id = '("name" "Columba" "version" "1.0.0" "vendor" "KeJi")'
        tag = imap._new_tag()
        imap.send(f'{tag.decode()} ID {imap_id}\r\n'.encode())
        imap.readline()
    
    def Try_Receive(self):
        """
        轮询收件箱，遍历当前未读的邮件。
        调用Validate_User方法，如果不是user_email的邮箱就不做处理。
        如果是user_email的邮件，提取正文内容，append到text，标记为已读。
        如果没有user_email的邮件，返回None，否则返回text。
        """
        text = ""
        
        try:
            imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            imap.login(self.agent_email, self.password)
            
            self._Send_Imap_Id(imap)
            
            status, data = imap.select("INBOX")
            if status != "OK":
                print(f"select失败: {data}")
                imap.logout()
                return None
        except Exception as e:
            print(f"IMAP连接错误: {e}")
            return None
        
        status, ids = imap.search(None, "UNSEEN")
        mail_ids = ids[0].split()
        
        for mid in mail_ids:
            status, data = imap.fetch(mid, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            from_addr = msg["From"]
            
            if not self._Validate_User(from_addr):
                continue
            
            body = self._Extract_Body(msg)
            text += body + "\n"
            
            imap.store(mid, '+FLAGS', '\\Seen')
        
        imap.logout()
        
        if text:
            result = text.strip()
            Log_Info("Comm", f"接收邮件内容: {result}")
            return result
        

        return None
    
    def _Extract_Body(self, msg):
        """
        从邮件中提取正文内容
        """
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    return payload.decode(charset, errors="ignore")
        else:
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            return payload.decode(charset, errors="ignore")
        return ""
