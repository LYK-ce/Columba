#Presented by KeJi
#Date : 2026-01-19

"""
Exec - 命令执行工具API，供Agent调用
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from API.Shell import Shell
from Log.Log import Log_Info


MODULE_NAME = "Exec"

# 全局Shell实例
_SHELL = None


def _Get_Shell() -> Shell:
    """
    获取Shell实例（延迟初始化）
    
    Returns:
        Shell实例
    """
    global _SHELL
    if _SHELL is None:
        _SHELL = Shell()
    return _SHELL


def Execute_Command(command: str, working_dir: str = None) -> str:
    """
    执行命令（供Agent调用的工具函数）
    
    Args:
        command: 要执行的命令
        working_dir: 工作目录（可选）
    
    Returns:
        命令执行结果字符串
    """
    Log_Info(MODULE_NAME, f"Execute_Command called: {command}")
    
    shell = _Get_Shell()
    
    # 验证并设置工作目录
    valid_working_dir = None
    if working_dir is not None:
        # 清理working_dir中的无效字符
        cleaned_dir = working_dir.strip().strip('"').strip("'")
        # 验证目录是否存在
        if cleaned_dir and os.path.isdir(cleaned_dir):
            valid_working_dir = cleaned_dir
            Log_Info(MODULE_NAME, f"Using working_dir: {valid_working_dir}")
        else:
            Log_Info(MODULE_NAME, f"Invalid working_dir ignored: {working_dir}")
    
    # 如果指定了有效工作目录，临时修改
    if valid_working_dir is not None:
        original_dir = shell.working_dir
        shell.working_dir = valid_working_dir
    
    stdout, stderr, return_code = shell.Execute(command)
    
    # 恢复工作目录
    if valid_working_dir is not None:
        shell.working_dir = original_dir
    
    # 格式化输出
    result_parts = []
    result_parts.append(f"[Exit Code: {return_code}]")
    
    if stdout.strip():
        result_parts.append(f"[STDOUT]\n{stdout.strip()}")
    
    if stderr.strip():
        result_parts.append(f"[STDERR]\n{stderr.strip()}")
    
    result = "\n".join(result_parts)
    
    Log_Info(MODULE_NAME, f"Command result: {result[:100]}...")
    
    return result


# 工具描述，供Agent注册使用
API_DESCRIPTION = """Execute a shell command on the system.
Arguments:
- command (str, required): The command to execute
Returns: Command output including stdout, stderr, and exit code.
Example: {"command": "nvidia-smi"} to check GPU status, {"command": "dir"} to list files."""
