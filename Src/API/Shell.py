#Presented by KeJi
#Date : 2026-01-19

"""
Shell - 命令行抽象类，封装subprocess执行命令
"""

import subprocess
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Log.Log import Log_Info


class Shell:
    """
    Shell类 - 命令行抽象，封装subprocess
    """
    
    MODULE_NAME = "Shell"
    
    # 黑名单命令（危险命令）
    BLOCKED_COMMANDS = [
        "rm -rf /",
        "rm -rf /*",
        "format",
        "del /f /s /q",
        "mkfs",
        ":(){:|:&};:",
    ]
    
    def __init__(self, working_dir: str = None, timeout: int = 30):
        """
        初始化Shell
        
        Args:
            working_dir: 工作目录，默认为当前目录
            timeout: 默认超时时间（秒）
        """
        if working_dir is None:
            working_dir = os.getcwd()
        
        self.working_dir = working_dir
        self.timeout = timeout
        
        Log_Info(self.MODULE_NAME, f"Initialized with working_dir={working_dir}, timeout={timeout}")
    
    def _Validate_Command(self, command: str) -> bool:
        """
        校验命令安全性
        
        Args:
            command: 要执行的命令
        
        Returns:
            True表示安全，False表示命令被阻止
        """
        cmd_lower = command.lower().strip()
        
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in cmd_lower:
                Log_Info(self.MODULE_NAME, f"Blocked dangerous command: {command}")
                return False
        
        return True
    
    def _Sanitize_Output(self, output: str, max_length: int = 4096) -> str:
        """
        清理输出，限制长度
        
        Args:
            output: 原始输出
            max_length: 最大长度
        
        Returns:
            清理后的输出
        """
        if len(output) > max_length:
            return output[:max_length] + f"\n... [truncated, total {len(output)} chars]"
        return output
    
    def Execute(self, command: str, timeout: int = None) -> tuple:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒），默认使用初始化时的timeout
        
        Returns:
            (stdout, stderr, return_code) 元组
        """
        if timeout is None:
            timeout = self.timeout
        
        Log_Info(self.MODULE_NAME, f"Executing: {command}")
        
        # 安全检查
        if not self._Validate_Command(command):
            return ("", "Command blocked for security reasons", -1)
        
        try:
            # 根据系统选择shell
            if os.name == 'nt':
                # Windows
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.working_dir
                )
            else:
                # Unix/Linux
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.working_dir
                )
            
            stdout = self._Sanitize_Output(result.stdout)
            stderr = self._Sanitize_Output(result.stderr)
            
            Log_Info(self.MODULE_NAME, f"Command completed with return_code={result.returncode}")
            
            return (stdout, stderr, result.returncode)
        
        except subprocess.TimeoutExpired:
            Log_Info(self.MODULE_NAME, f"Command timed out after {timeout}s")
            return ("", f"Command timed out after {timeout} seconds", -2)
        
        except Exception as e:
            Log_Info(self.MODULE_NAME, f"Command execution error: {e}")
            return ("", str(e), -3)
