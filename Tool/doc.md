# Tool 目录文档

## download_model.py

从ModelScope下载GGUF模型文件到Model目录。

### 用法

```bash
# 下载默认模型 (Qwen3-0.6B-Q8_0.gguf)
python Tool/download_model.py

# 指定URL下载
python Tool/download_model.py -u <URL>

# 指定输出文件名
python Tool/download_model.py -o <filename>

# 组合使用
python Tool/download_model.py -u <URL> -o <filename>
```

### 参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --url | -u | 模型下载URL | Qwen3-0.6B-Q8_0.gguf |
| --output | -o | 输出文件名 | 从URL提取 |

### 示例

```bash
# 下载Qwen3-0.6B量化模型
python Tool/download_model.py

# 下载其他模型
python Tool/download_model.py -u https://www.modelscope.cn/models/xxx/resolve/master/model.gguf
```
