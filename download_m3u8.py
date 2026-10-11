#!/usr/bin/env python3
"""
51cg1.com m3u8 直接下载脚本
适用于已获取到真实 m3u8 链接的情况
"""

import os
import sys
import subprocess
from pathlib import Path


def download_m3u8(m3u8_url, output_file):
    """使用 ffmpeg 下载 m3u8 视频"""
    try:
        print(f"📥 开始下载 m3u8...")
        print(f"🔗 链接: {m3u8_url[:80]}...")
        print(f"💾 保存到: {output_file}\n")
        
        cmd = [
            'ffmpeg',
            '-i', m3u8_url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            output_file,
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            print(f"\n✅ 下载完成！")
            print(f"📁 文件位置: {os.path.abspath(output_file)}")
            print(f"📊 文件大小: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"\n❌ 下载失败")
            return False
            
    except FileNotFoundError:
        print("❌ 未找到 ffmpeg")
        print("\n请先安装 ffmpeg:")
        print("  Windows: https://ffmpeg.org/download.html")
        print("  Mac: brew install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ 出错: {str(e)}")
        return False


def main():
    if len(sys.argv) < 2:
        print("51cg1.com m3u8 下载脚本")
        print("\n用法:")
        print("  python download_m3u8.py <m3u8链接> [输出文件名]")
        print("\n示例:")
        print("  python download_m3u8.py 'https://hls.xxx.cn/xxx.m3u8?auth_key=...'")
        print("  python download_m3u8.py 'https://hls.xxx.cn/xxx.m3u8?auth_key=...' my_video.mp4")
        print("\n依赖:")
        print("  ffmpeg (必须)")
        sys.exit(1)

    m3u8_url = sys.argv[1]
    
    # 确定输出文件名
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        output_file = "video.mp4"
    
    # 创建 downloads 目录
    Path("downloads").mkdir(exist_ok=True)
    output_path = Path("downloads") / output_file
    
    success = download_m3u8(m3u8_url, str(output_path))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
