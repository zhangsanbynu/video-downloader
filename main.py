#!/usr/bin/env python3
"""
一键下载在线视频脚本
支持 YouTube、B站、抖音等多个平台
"""

import os
import sys
import json
from pathlib import Path
from yt_dlp import YoutubeDL


class VideoDownloader:
    def __init__(self, output_dir="downloads"):
        """初始化下载器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def download(self, url):
        """下载单个视频"""
        try:
            print(f"📥 开始下载: {url}")
            
            ydl_opts = {
                "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "quiet": False,
                "no_warnings": False,
                "progress_hooks": [self._progress_hook],
                "socket_timeout": 30,
                "retries": 3,
                "fragment_retries": 3,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
            print(f"✅ 下载完成！文件位置: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ 下载失败: {str(e)}")
            return False

    def _progress_hook(self, d):
        """进度条显示"""
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "N/A")
            speed = d.get("_speed_str", "N/A")
            eta = d.get("_eta_str", "N/A")
            print(f"\r进度: {percent} | 速度: {speed} | 剩余: {eta}", end="", flush=True)
        elif d["status"] == "finished":
            print("\n✨ 下载完毕，正在处理...")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py <视频链接>")
        print("\n示例:")
        print("  python main.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        print("  python main.py 'https://www.bilibili.com/video/BV1xx411c7mD'")
        sys.exit(1)

    url = sys.argv[1]
    downloader = VideoDownloader()
    success = downloader.download(url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
