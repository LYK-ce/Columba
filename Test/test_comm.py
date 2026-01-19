#Presented by KeJi
#Date : 2026-01-19

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Src.Comm.Email import Comm

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "Src", "Config", "config.json")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    comm = Comm(config)
    
    print("发送邮件: hello world")
    comm.Send("hello world")
    print("邮件发送成功")
    
    print("尝试接收邮件...")
    text = comm.Try_Receive()
    
    if text:
        print(f"收到邮件内容:\n{text}")
    else:
        print("没有收到新邮件")

if __name__ == "__main__":
    main()
