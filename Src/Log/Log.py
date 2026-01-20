#Presented by KeJi
#Date : 2026-01-20

import os
import glob
import time
from datetime import datetime

LOG_DIR = ".log"

def Get_Log_Dir():
    """获取日志目录完整路径"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, LOG_DIR)

def Log_Info(module, text):
    """
    按照 [时间] [信息] [模组] : 文本 的形式将日志存储到.log/日期.log当中
    """
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")
    
    log_line = f"[{time_str}] [信息] [{module}] : {text}\n"
    
    log_dir_path = Get_Log_Dir()
    
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)
    
    log_file_path = os.path.join(log_dir_path, f"{date_str}.log")
    
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_line)

def Cleanup_Old_Logs(days):
    """
    清理超过指定天数的日志文件
    
    Args:
        days: 保留天数，超过此天数的日志将被删除
    """
    if days <= 0:
        return
    
    log_dir_path = Get_Log_Dir()
    
    if not os.path.exists(log_dir_path):
        return
    
    cutoff_time = time.time() - days * 86400
    log_pattern = os.path.join(log_dir_path, "*.log")
    deleted_count = 0
    
    for log_file in glob.glob(log_pattern):
        try:
            if os.path.getmtime(log_file) < cutoff_time:
                os.remove(log_file)
                deleted_count += 1
        except OSError:
            pass
    
    if deleted_count > 0:
        Log_Info("Log", f"已清理{deleted_count}个过期日志文件(超过{days}天)")
