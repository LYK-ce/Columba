#Presented by KeJi
#Date : 2026-01-19

import os
from datetime import datetime

LOG_DIR = ".log"

def Log_Info(module, text):
    """
    按照 [时间] [信息] [模组] : 文本 的形式将日志存储到.log/日期.log当中
    """
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")
    
    log_line = f"[{time_str}] [信息] [{module}] : {text}\n"
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir_path = os.path.join(project_root, LOG_DIR)
    
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)
    
    log_file_path = os.path.join(log_dir_path, f"{date_str}.log")
    
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_line)
