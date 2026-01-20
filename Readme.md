#Presented by KeJi
#Date ： 2026-01-20

# Columba

Columba是一个基于本地LLM的远程任务执行Agent系统。用户通过发送邮件即可远程操控服务器执行各类任务，无需SSH连接或VPN。系统采用llama.cpp运行本地大语言模型，将自然语言指令转换为具体的服务器操作命令。

## 版本
Version 1.0 仅实现初步功能，更多功能有待完善

## 特性

- **邮件驱动**：通过邮件发送指令，无需复杂的远程连接配置
- **本地LLM**：基于llama.cpp，支持GGUF格式模型，无需GPU可在CPU上运行
- **安全可控**：命令黑名单机制，防止执行危险操作
- **持久化Shell**：支持状态保持，cd等命令效果持续生效
- **自动唤醒**：后台Scheduler定时检查邮箱，有指令时自动唤醒Agent处理

## 项目结构

```
Columba/
├── Src/                    # 源代码目录
│   ├── main.py             # 程序入口
│   ├── Agent/              # Agent执行器模组
│   ├── API/                # 方法调用模组（Shell执行等）
│   ├── Comm/               # 通信模组（邮件收发）
│   ├── Config/             # 配置文件
│   ├── Log/                # 日志模组
│   └── Scheduler_Daemon/   # 后台调度模组
├── Model/                  # 模型文件目录（需手动创建）
├── Tool/                   # 工具脚本
├── Test/                   # 测试脚本
└── requirements.txt        # 依赖列表
```

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/your-repo/Columba.git
cd Columba
git submodule update --init --recursive  # 初始化llama.cpp子模块
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `llama-cpp-python>=0.2.0` - LLM推理引擎

### 3. 下载模型

创建Model目录并下载GGUF格式的模型：

```bash
mkdir Model
python Tool/download_model.py
```

默认下载Qwen3-8B-Q8_0模型，也可指定其他模型：

```bash
python Tool/download_model.py --url "https://www.modelscope.cn/models/xxx/file.gguf"
```

推荐模型配置：
| 模型 | 适用场景 | 内存需求 |
|------|---------|---------|
| Qwen3-0.6B | 单步骤简单任务 | ~1GB |
| Qwen3-4B | 多步骤复杂任务 | ~5GB |
| Qwen3-8B | 生产环境推荐 | ~10GB |

### 4. 配置邮箱

编辑`Src/Config/config.json`：

```json
{
    "Comm": {
        "agent": {
            "smtp_host": "smtp.163.com",
            "smtp_port": 465,
            "imap_host": "imap.163.com",
            "imap_port": 993,
            "username": "your_agent_email@163.com",
            "password": "your_authorization_code"
        },
        "user_email": ["your_user_email@example.com"]
    }
}
```

- `agent`: Columba使用的邮箱账户配置
- `user_email`: 授权的用户邮箱列表，只接收这些邮箱的指令

### 5. 配置模型

```json
{
    "Agent": {
        "model_path": "Model/Qwen3-4B-Q8_0.gguf",
        "n_threads": 4,
        "max_iterations": 10,
        "context_length": 4096
    }
}
```

### 6. 配置工作目录

```json
{
    "Target_Workspace": {
        "target_workspace": "C:/your/project/path"
    },
    "Tmp_WorkingSpace": {
        "workspace": ".columba_tmp_workspace"
    }
}
```

- `target_workspace`: Agent的Shell初始工作目录，API操作的目标目录
- `workspace`: 临时文件存储目录，程序退出时自动清理

## 使用

### 启动服务

```bash
python Src/main.py
```

程序启动后：
1. Scheduler后台运行，每60秒检查一次邮箱
2. 收到用户邮件后自动唤醒Agent
3. Agent处理完毕后将结果邮件发送给用户
4. 按`Ctrl+C`优雅退出

### 发送指令

向Columba邮箱发送邮件，正文中写入自然语言指令即可：

**示例1：查看GPU状态**
```
邮件正文：
请帮我查看当前的GPU状况
```

Columba将执行`nvidia-smi`并把结果通过邮件返回。

**示例2：创建目录并查看**
```
邮件正文：
在当前目录创建一个名为test的文件夹，然后列出当前目录的所有文件
```

Columba将依次执行`mkdir test`和`dir`（或`ls`），返回执行结果。

**示例3：进入特定目录操作**
```
邮件正文：
进入MyProject目录，查看git状态
```

Columba将执行`cd MyProject`然后`git status`，由于持久化Shell，cd效果会保持。

### 返回结果

Agent处理完成后，会通过邮件返回：
1. Agent的总结性回复
2. 每个命令的详细输出（包含工作目录、退出码、stdout/stderr）

## 配置说明

### 完整配置示例

```json
{
    "Target_Workspace": {
        "target_workspace": "C:/workspace"
    },
    "Tmp_WorkingSpace": {
        "workspace": ".columba_tmp_workspace"
    },
    "Comm": {
        "agent": {
            "smtp_host": "smtp.163.com",
            "smtp_port": 465,
            "imap_host": "imap.163.com",
            "imap_port": 993,
            "username": "agent@163.com",
            "password": "authorization_code"
        },
        "user_email": ["user@163.com"]
    },
    "Log": {
        "log_dir": ".log"
    },
    "Scheduler": {
        "poll_interval_idle": 60,
        "poll_interval_active": 5,
        "active_timeout": 300,
        "agent_persistence": false,
        "agent_timeout": 600
    },
    "Agent": {
        "model_path": "Model/Qwen3-4B-Q8_0.gguf",
        "n_threads": 4,
        "max_iterations": 10,
        "context_length": 4096,
        "stream": true
    }
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `poll_interval_idle` | 空闲时邮箱检查间隔（秒） | 60 |
| `poll_interval_active` | 活跃时邮箱检查间隔（秒） | 5 |
| `active_timeout` | 无活动后返回空闲状态的超时时间（秒） | 300 |
| `agent_timeout` | Agent响应超时时间（秒） | 600 |
| `n_threads` | LLM推理线程数 | 4 |
| `max_iterations` | 最大工具调用轮数 | 10 |
| `context_length` | 上下文长度限制 | 4096 |

## 注意事项

1. **邮箱授权码**：使用163等邮箱时，需要在邮箱设置中开启IMAP/SMTP服务并获取授权码
2. **模型选择**：0.6B模型仅支持单步骤任务，复杂任务推荐使用4B或更大模型
3. **安全限制**：部分危险命令（如`rm -rf`、`format`）已被列入黑名单
4. **工作目录**：确保`target_workspace`配置为正确的工作目录

## License

MIT License
