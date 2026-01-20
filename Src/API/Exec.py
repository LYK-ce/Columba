#Presented by KeJi
#Date : 2026-01-20

"""
Exec - 命令执行工具API，使用Agent的持久化Shell执行命令
命令输出保存到文件，同时返回给Agent
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Log.Log import Log_Info


MODULE_NAME = "Exec"

# 全局Shell引用（指向Agent的持久化Shell）
_SHELL = None

# 命令输出文件列表（供发送邮件时使用）
_OUTPUT_FILES = []


def Set_Shell(shell):
    """
    设置Shell引用（由Agent_Process初始化时调用）
    
    Args:
        shell: Agent的Persistent_Shell实例
    """
    global _SHELL
    _SHELL = shell
    Log_Info(MODULE_NAME, "Shell reference set")


def Get_Shell():
    """
    获取Shell引用
    
    Returns:
        Persistent_Shell实例或None
    """
    return _SHELL


def Get_Output_Files() -> list:
    """
    获取所有命令输出文件路径
    
    Returns:
        输出文件路径列表
    """
    return _OUTPUT_FILES.copy()


def Clear_Output_Files():
    """
    清空输出文件列表（在发送邮件后调用）
    """
    global _OUTPUT_FILES
    _OUTPUT_FILES.clear()
    Log_Info(MODULE_NAME, "Output files list cleared")


def Execute_Command(command: str) -> str:
    """
    执行命令（供Agent调用的工具函数）
    通过Agent的持久化Shell执行，输出保存到文件并返回给Agent
    
    Args:
        command: 要执行的命令
    
    Returns:
        命令执行结果字符串
    """
    global _OUTPUT_FILES
    
    Log_Info(MODULE_NAME, f"Execute_Command called: {command}")
    
    if _SHELL is None:
        Log_Info(MODULE_NAME, "Error: Shell not initialized")
        return "[Error] Shell not initialized. Agent may not be properly started."
    
    stdout, stderr, return_code, output_file = _SHELL.Execute(command)
    
    # 记录输出文件
    if output_file and os.path.exists(output_file):
        _OUTPUT_FILES.append(output_file)
        Log_Info(MODULE_NAME, f"Output file recorded: {output_file}")
    
    # 获取当前工作目录
    working_dir = _SHELL.Get_Working_Dir()
    
    # 格式化输出
    result_parts = []
    result_parts.append(f"[Exit Code: {return_code}]")
    result_parts.append(f"[Working Dir: {working_dir}]")
    
    if output_file:
        result_parts.append(f"[Output File: {output_file}]")
    
    if stdout.strip():
        result_parts.append(f"[STDOUT]\n{stdout.strip()}")
    
    if stderr.strip():
        result_parts.append(f"[STDERR]\n{stderr.strip()}")
    
    result = "\n".join(result_parts)
    
    Log_Info(MODULE_NAME, f"Command result: {result[:100]}...")
    
    return result


# 工具描述，供Agent注册使用
API_DESCRIPTION = """Execute a shell command in the persistent shell.
The shell maintains state across commands (e.g., cd changes persist).
Command output is saved to a file and also returned.
Arguments:
- command (str, required): The command to execute
Returns: Command output including stdout, stderr, exit code, working directory, and output file path.
Example: {"command": "nvidia-smi"} to check GPU status, {"command": "dir"} to list files, {"command": "cd subdir"} to change directory."""
