#Presented by KeJi
#Date : 2026-01-20

"""
Shell - 持久化Shell进程类，随Agent启动/关闭
命令输出重定向到临时文件
"""

import subprocess
import os
import sys
import threading
import queue
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Log.Log import Log_Info


class Persistent_Shell:
    """
    持久化Shell类 - 维护一个长期运行的shell进程
    命令输出重定向到tmp_workspace中的文件
    """
    
    MODULE_NAME = "Persistent_Shell"
    
    # 黑名单命令（危险命令）
    BLOCKED_COMMANDS = [
        "rm -rf /",
        "rm -rf /*",
        "format",
        "del /f /s /q",
        "mkfs",
        ":(){:|:&};:",
    ]
    
    # 命令结束标记
    END_MARKER = "___COLUMBA_CMD_END___"
    
    def __init__(self, working_dir: str = None, tmp_workspace: str = None, timeout: int = 30):
        """
        初始化持久化Shell
        
        Args:
            working_dir: 初始工作目录（target_workspace），默认为当前目录
            tmp_workspace: 临时工作目录，用于存储命令输出文件
            timeout: 默认命令超时时间（秒）
        """
        if working_dir is None:
            working_dir = os.getcwd()
        
        self.initial_working_dir = working_dir
        self.tmp_workspace = tmp_workspace
        self.timeout = timeout
        self.process = None
        self.output_queue = queue.Queue()
        self.reader_thread = None
        self.running = False
        self.command_counter = 0
        
        # 最近一次命令的输出文件路径
        self.last_output_file = None
        
        Log_Info(self.MODULE_NAME, f"Initialized with working_dir={working_dir}, tmp_workspace={tmp_workspace}, timeout={timeout}")
    
    def Start(self):
        """
        启动持久化shell进程
        """
        if self.process is not None and self.process.poll() is None:
            Log_Info(self.MODULE_NAME, "Shell already running")
            return
        
        Log_Info(self.MODULE_NAME, "Starting persistent shell process")
        
        # 根据系统选择shell和编码
        if os.name == 'nt':
            shell_cmd = ["cmd.exe"]
            # Windows使用gbk编码
            self._encoding = 'gbk'
        else:
            shell_cmd = ["/bin/bash"]
            self._encoding = 'utf-8'
        
        self.process = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self.initial_working_dir,
            encoding=self._encoding,
            errors='replace'
        )
        
        self.running = True
        
        # 启动输出读取线程
        self.reader_thread = threading.Thread(target=self._Read_Output, daemon=True)
        self.reader_thread.start()
        
        # 等待shell启动
        time.sleep(0.1)
        
        # Windows下设置UTF-8代码页（可选，部分命令可能不支持）
        # if os.name == 'nt':
        #     self._Send_Command('chcp 65001 >nul')
        #     self._Drain_Queue()
        
        # 进入初始工作目录
        if self.initial_working_dir:
            self._Send_Command(f'cd /d "{self.initial_working_dir}"' if os.name == 'nt' else f'cd "{self.initial_working_dir}"')
            self._Drain_Queue()
        
        Log_Info(self.MODULE_NAME, f"Shell started, PID={self.process.pid}")
    
    def Stop(self):
        """
        停止持久化shell进程
        """
        if self.process is None:
            return
        
        Log_Info(self.MODULE_NAME, "Stopping persistent shell process")
        
        self.running = False
        
        try:
            if self.process.poll() is None:
                self._Send_Command("exit")
                self.process.wait(timeout=2)
        except Exception:
            pass
        
        try:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=1)
        except Exception:
            pass
        
        try:
            if self.process.poll() is None:
                self.process.kill()
        except Exception:
            pass
        
        self.process = None
        Log_Info(self.MODULE_NAME, "Shell stopped")
    
    def _Read_Output(self):
        """后台线程持续读取shell输出"""
        try:
            while self.running and self.process and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    self.output_queue.put(line)
                else:
                    time.sleep(0.01)
        except Exception as e:
            Log_Info(self.MODULE_NAME, f"Reader thread error: {e}")
    
    def _Send_Command(self, command: str):
        """发送命令到shell（不等待输出）"""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Shell process not running")
        
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
    
    def _Drain_Queue(self, timeout: float = 0.5):
        """清空输出队列"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.05)
                if self.output_queue.empty():
                    break
    
    def _Validate_Command(self, command: str) -> bool:
        """校验命令安全性"""
        cmd_lower = command.lower().strip()
        
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in cmd_lower:
                Log_Info(self.MODULE_NAME, f"Blocked dangerous command: {command}")
                return False
        
        return True
    
    def _Generate_Output_File(self) -> str:
        """
        生成命令输出文件路径
        
        Returns:
            输出文件的完整路径
        """
        if self.tmp_workspace is None:
            return None
        
        self.command_counter += 1
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"cmd_output_{timestamp}_{self.command_counter}_{unique_id}.txt"
        return os.path.join(self.tmp_workspace, filename)
    
    def _Sanitize_Output(self, output: str, max_length: int = 4096) -> str:
        """清理输出，限制长度"""
        if len(output) > max_length:
            return output[:max_length] + f"\n... [truncated, total {len(output)} chars]"
        return output
    
    def Execute(self, command: str, timeout: int = None) -> tuple:
        """
        执行命令，输出重定向到文件
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
        
        Returns:
            (stdout, stderr, return_code, output_file_path) 元组
            stdout: 命令输出内容
            stderr: 错误信息（通常为空，因为stderr已重定向到文件）
            return_code: 返回码
            output_file_path: 输出文件路径（供邮件附带使用）
        """
        if timeout is None:
            timeout = self.timeout
        
        # 确保shell正在运行
        if self.process is None or self.process.poll() is not None:
            self.Start()
        
        Log_Info(self.MODULE_NAME, f"Executing: {command}")
        
        # 安全检查
        if not self._Validate_Command(command):
            return ("", "Command blocked for security reasons", -1, None)
        
        # 生成输出文件路径
        output_file = self._Generate_Output_File()
        self.last_output_file = output_file
        
        try:
            # 清空之前的输出
            self._Drain_Queue(0.1)
            
            if output_file and os.path.isdir(self.tmp_workspace):
                # 使用文件重定向执行命令
                # 格式: command > output_file 2>&1
                if os.name == 'nt':
                    redirect_cmd = f'{command} > "{output_file}" 2>&1'
                else:
                    redirect_cmd = f'{command} > "{output_file}" 2>&1'
                
                self._Send_Command(redirect_cmd)
                
                # 发送结束标记
                self._Send_Command(f'echo {self.END_MARKER}' if os.name == 'nt' else f'echo "{self.END_MARKER}"')
                
                # 等待结束标记
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        line = self.output_queue.get(timeout=0.1)
                        if self.END_MARKER in line:
                            break
                    except queue.Empty:
                        continue
                else:
                    Log_Info(self.MODULE_NAME, f"Command timed out after {timeout}s")
                    return ("", f"Command timed out after {timeout} seconds", -2, output_file)
                
                # 等待文件写入完成
                time.sleep(0.1)
                
                # 读取输出文件（使用与shell相同的编码）
                output = ""
                if os.path.exists(output_file):
                    try:
                        # Windows cmd重定向使用系统默认编码(gbk)
                        file_encoding = self._encoding if hasattr(self, '_encoding') else ('gbk' if os.name == 'nt' else 'utf-8')
                        with open(output_file, 'r', encoding=file_encoding, errors='replace') as f:
                            output = f.read()
                    except Exception as e:
                        Log_Info(self.MODULE_NAME, f"Error reading output file: {e}")
                        output = f"[Error reading output file: {e}]"
                
                output = self._Sanitize_Output(output)
                Log_Info(self.MODULE_NAME, f"Command completed, output saved to {output_file}")
                
                return (output, "", 0, output_file)
            else:
                # 无tmp_workspace时使用原始方式
                self._Send_Command(command)
                self._Send_Command(f'echo {self.END_MARKER}' if os.name == 'nt' else f'echo "{self.END_MARKER}"')
                
                output_lines = []
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    try:
                        line = self.output_queue.get(timeout=0.1)
                        if self.END_MARKER in line:
                            break
                        output_lines.append(line)
                    except queue.Empty:
                        continue
                else:
                    Log_Info(self.MODULE_NAME, f"Command timed out after {timeout}s")
                    return ("".join(output_lines), f"Command timed out after {timeout} seconds", -2, None)
                
                output = "".join(output_lines)
                output = self._Sanitize_Output(output)
                
                Log_Info(self.MODULE_NAME, f"Command completed successfully")
                return (output, "", 0, None)
        
        except Exception as e:
            Log_Info(self.MODULE_NAME, f"Command execution error: {e}")
            return ("", str(e), -3, output_file)
    
    def Get_Working_Dir(self) -> str:
        """获取当前工作目录"""
        if self.process is None or self.process.poll() is not None:
            return self.initial_working_dir
        
        try:
            self._Drain_Queue(0.1)
            
            if os.name == 'nt':
                self._Send_Command('cd')
            else:
                self._Send_Command('pwd')
            
            self._Send_Command(f'echo {self.END_MARKER}' if os.name == 'nt' else f'echo "{self.END_MARKER}"')
            
            output_lines = []
            start_time = time.time()
            
            while time.time() - start_time < 2:
                try:
                    line = self.output_queue.get(timeout=0.1)
                    if self.END_MARKER in line:
                        break
                    output_lines.append(line.strip())
                except queue.Empty:
                    continue
            
            for line in reversed(output_lines):
                if line and not line.startswith(('cd', 'pwd', 'echo')):
                    return line
            
            return self.initial_working_dir
        except Exception:
            return self.initial_working_dir
    
    def Get_Last_Output_File(self) -> str:
        """
        获取最近一次命令的输出文件路径
        
        Returns:
            输出文件路径或None
        """
        return self.last_output_file
    
    def Is_Running(self) -> bool:
        """检查shell是否正在运行"""
        return self.process is not None and self.process.poll() is None


# 保留旧的Shell类以兼容性（非持久化版本）
class Shell:
    """Shell类 - 命令行抽象，封装subprocess（非持久化版本）"""
    
    MODULE_NAME = "Shell"
    
    BLOCKED_COMMANDS = [
        "rm -rf /",
        "rm -rf /*",
        "format",
        "del /f /s /q",
        "mkfs",
        ":(){:|:&};:",
    ]
    
    def __init__(self, working_dir: str = None, timeout: int = 30):
        if working_dir is None:
            working_dir = os.getcwd()
        
        self.working_dir = working_dir
        self.timeout = timeout
        
        Log_Info(self.MODULE_NAME, f"Initialized with working_dir={working_dir}, timeout={timeout}")
    
    def _Validate_Command(self, command: str) -> bool:
        cmd_lower = command.lower().strip()
        
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in cmd_lower:
                Log_Info(self.MODULE_NAME, f"Blocked dangerous command: {command}")
                return False
        
        return True
    
    def _Sanitize_Output(self, output: str, max_length: int = 4096) -> str:
        if len(output) > max_length:
            return output[:max_length] + f"\n... [truncated, total {len(output)} chars]"
        return output
    
    def Execute(self, command: str, timeout: int = None) -> tuple:
        if timeout is None:
            timeout = self.timeout
        
        Log_Info(self.MODULE_NAME, f"Executing: {command}")
        
        if not self._Validate_Command(command):
            return ("", "Command blocked for security reasons", -1)
        
        try:
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
