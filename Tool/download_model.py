#Presented by KeJi
#Date : 2026-01-16

"""
模型下载脚本 - 从ModelScope下载GGUF模型到Model目录
"""

import os
import sys
import argparse
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_URL = "https://www.modelscope.cn/models/Qwen/Qwen3-0.6B-GGUF/resolve/master/Qwen3-0.6B-Q8_0.gguf"
SCRIPT_DIR = Path(__file__).parent.resolve()
MODEL_DIR = SCRIPT_DIR.parent / "Model"


def Get_Filename_From_Url(url: str) -> str:
    """从URL中提取文件名"""
    path = url.split("?")[0]
    return path.split("/")[-1]


def Download_With_Progress(url: str, dest_path: Path) -> None:
    """带进度显示的下载"""
    print(f"下载: {url}")
    print(f"保存至: {dest_path}")
    
    def Report_Progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\r进度: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
            sys.stdout.flush()
        else:
            downloaded_mb = downloaded / (1024 * 1024)
            sys.stdout.write(f"\r已下载: {downloaded_mb:.1f} MB")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=Report_Progress)
        print("\n下载完成!")
    except urllib.error.URLError as e:
        print(f"\n下载失败: {e}")
        sys.exit(1)


def Main():
    """主函数"""
    parser = argparse.ArgumentParser(description="从ModelScope下载模型文件")
    parser.add_argument(
        "-u", "--url",
        type=str,
        default=DEFAULT_URL,
        help=f"模型下载URL (默认: {DEFAULT_URL})"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出文件名 (默认: 从URL提取)"
    )
    args = parser.parse_args()
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = args.output if args.output else Get_Filename_From_Url(args.url)
    dest_path = MODEL_DIR / filename
    
    if dest_path.exists():
        print(f"文件已存在: {dest_path}")
        response = input("是否覆盖? (y/N): ").strip().lower()
        if response != 'y':
            print("取消下载")
            return
    
    Download_With_Progress(args.url, dest_path)


if __name__ == "__main__":
    Main()
