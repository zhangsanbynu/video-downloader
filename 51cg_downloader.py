#!/usr/bin/env python3
"""
51cg1.com 专用视频下载脚本
支持解析页面中的视频链接并下载
"""

import os
import sys
import re
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import subprocess


class CG51Downloader:
    def __init__(self, output_dir="downloads"):
        """初始化下载器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self, url):
        """获取页面内容"""
        try:
            print(f"📄 正在获取页面: {url}")
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"❌ 获取页面失败: {str(e)}")
            return None

    def extract_video_url(self, html):
        """从页面HTML中提取视频链接"""
        video_urls = []
        
        # 方法1: 查找 <video> 标签
        soup = BeautifulSoup(html, 'html.parser')
        video_tags = soup.find_all('video')
        for video in video_tags:
            source = video.find('source')
            if source and source.get('src'):
                video_urls.append(source['src'])
        
        # 方法2: 查找 <iframe> 中的视频
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if 'video' in src or 'player' in src:
                video_urls.append(src)
        
        # 方法3: 查找 m3u8 链接
        m3u8_pattern = r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*'
        m3u8_urls = re.findall(m3u8_pattern, html)
        video_urls.extend(m3u8_urls)
        
        # 方法4: 查找 mp4 链接
        mp4_pattern = r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*'
        mp4_urls = re.findall(mp4_pattern, html)
        video_urls.extend(mp4_urls)
        
        # 方法5: 查找 JSON 中的视频数据
        json_pattern = r'"video["\']?\s*:\s*["\']([^"\']+)["\']'
        json_matches = re.findall(json_pattern, html)
        video_urls.extend(json_matches)
        
        # 方法6: 查找 window.player 或类似的 JS 变量
        player_pattern = r'(?:window\.player|var\s+player|const\s+player)\s*=\s*{[^}]*["\']?(?:url|src|video|file)["\']?\s*:\s*["\']([^"\']+)["\']'
        player_matches = re.findall(player_pattern, html)
        video_urls.extend(player_matches)
        
        # 方法7: 查找 script 标签中的 JSON
        script_tags = soup.find_all('script', {'type': 'application/json'})
        for script in script_tags:
            try:
                data = json.loads(script.string)
                urls = self._extract_urls_from_json(data)
                video_urls.extend(urls)
            except:
                pass
        
        # 去重并过滤
        video_urls = list(set(filter(lambda x: x and len(x) > 10, video_urls)))
        return video_urls

    def _extract_urls_from_json(self, obj, depth=0):
        """递归提取JSON中的URL"""
        urls = []
        if depth > 5:
            return urls
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and ('mp4' in value or 'm3u8' in value or 'video' in key.lower()):
                    if value.startswith('http'):
                        urls.append(value)
                elif isinstance(value, (dict, list)):
                    urls.extend(self._extract_urls_from_json(value, depth + 1))
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, str) and ('mp4' in item or 'm3u8' in item):
                    if item.startswith('http'):
                        urls.append(item)
                elif isinstance(item, (dict, list)):
                    urls.extend(self._extract_urls_from_json(item, depth + 1))
        
        return urls

    def get_title(self, html, url):
        """从页面获取标题"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试获取 title 标签
        title = soup.find('title')
        if title:
            title_text = title.string.strip()
            # 清理标题
            title_text = re.sub(r'[<>:"/\\|?*]', '', title_text)
            title_text = title_text[:100]  # 限制长度
            if title_text:
                return title_text
        
        # 如果没有找到，使用 URL
        return urlparse(url).netloc

    def download_m3u8(self, m3u8_url, output_file):
        """下载 m3u8 视频"""
        try:
            print(f"📥 开始下载 m3u8: {m3u8_url}")
            
            # 使用 ffmpeg 下载 m3u8
            cmd = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                output_file,
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=False)
            print(f"✅ m3u8 下载完成: {output_file}")
            return True
        except FileNotFoundError:
            print("❌ 未找到 ffmpeg，请先安装: pip install ffmpeg-python")
            return False
        except Exception as e:
            print(f"❌ m3u8 下载失败: {str(e)}")
            return False

    def download_direct(self, video_url, output_file):
        """直接下载视频文件"""
        try:
            print(f"📥 开始下载: {video_url}")
            
            response = self.session.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r进度: {percent:.1f}% ({downloaded/1024/1024:.1f}MB)", end='', flush=True)
            
            print(f"\n✅ 下载完成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 下载失败: {str(e)}")
            return False

    def download(self, url):
        """下载视频主流程"""
        try:
            # 获取页面
            html = self.fetch_page(url)
            if not html:
                return False
            
            # 提取视频链接
            video_urls = self.extract_video_url(html)
            if not video_urls:
                print("❌ 未找到视频链接")
                print("💡 提示: 可能需要登录或者视频链接已过期")
                return False
            
            # 获取标题
            title = self.get_title(html, url)
            print(f"📌 视频标题: {title}")
            
            # 选择第一个有效的视频链接
            for i, video_url in enumerate(video_urls, 1):
                print(f"\n[{i}/{len(video_urls)}] 尝试下载: {video_url[:80]}...")
                
                # 确定输出文件名和格式
                if video_url.endswith('.m3u8'):
                    output_file = str(self.output_dir / f"{title}.mp4")
                    success = self.download_m3u8(video_url, output_file)
                else:
                    # 猜测格式
                    ext = '.mp4'
                    if '.m3u8' in video_url:
                        ext = '.mp4'
                    elif '.flv' in video_url:
                        ext = '.flv'
                    elif '.mkv' in video_url:
                        ext = '.mkv'
                    
                    output_file = str(self.output_dir / f"{title}{ext}")
                    success = self.download_direct(video_url, output_file)
                
                if success:
                    return True
            
            print("❌ 所有下载尝试都失败了")
            return False
            
        except Exception as e:
            print(f"❌ 出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    if len(sys.argv) < 2:
        print("51cg1.com 视频下载脚本")
        print("\n用法:")
        print("  python main.py <页面链接>")
        print("\n示例:")
        print("  python main.py 'https://51cg1.com/archives/270635/'")
        print("\n依赖:")
        print("  pip install requests beautifulsoup4")
        print("  (可选) 下载 m3u8 需要: ffmpeg")
        sys.exit(1)

    url = sys.argv[1]
    downloader = CG51Downloader()
    success = downloader.download(url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
