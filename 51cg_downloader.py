#!/usr/bin/env python3
"""
51cg1.com 专用视频下载脚本 - 增强版
支持 JavaScript 渲染和动态加载的视频链接
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
import time


class CG51Downloader:
    def __init__(self, output_dir="downloads"):
        """初始化下载器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://51cg1.com/',
        })

    def fetch_page_with_selenium(self, url):
        """使用 Selenium 获取动态渲染后的页面"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            
            print("🌐 使用浏览器引擎获取页面...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # 等待视频元素加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "video"))
                )
                print("✅ 页面已加载")
            except:
                print("⏱️ 等待超时，继续...")
            
            time.sleep(3)  # 额外等待
            html = driver.page_source
            driver.quit()
            return html
        except ImportError:
            print("❌ Selenium 未安装，请运行: pip install selenium")
            return None
        except Exception as e:
            print(f"⚠️ Selenium 获取失败: {str(e)}")
            return None

    def fetch_page_requests(self, url):
        """使用 requests 获取页面"""
        try:
            print(f"📄 正在获取页面: {url}")
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"❌ 获取页面失败: {str(e)}")
            return None

    def fetch_page(self, url):
        """获取页面 - 先试 requests，再试 selenium"""
        html = self.fetch_page_requests(url)
        if html and self.extract_video_url(html):
            return html
        
        # 如果 requests 失败，尝试 selenium
        print("💡 尝试使用浏览器引擎...")
        selenium_html = self.fetch_page_with_selenium(url)
        if selenium_html:
            return selenium_html
        
        return html

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
            if 'video' in src or 'player' in src or 'youku' in src or 'tudou' in src:
                video_urls.append(src)
        
        # 方法3: 查找 m3u8 链接
        m3u8_pattern = r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*'
        m3u8_urls = re.findall(m3u8_pattern, html)
        video_urls.extend(m3u8_urls)
        
        # 方法4: 查找 mp4 链接
        mp4_pattern = r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*'
        mp4_urls = re.findall(mp4_pattern, html)
        video_urls.extend(mp4_urls)
        
        # 方法5: 查找 flv 链接
        flv_pattern = r'https?://[^\s"\'<>]+\.flv[^\s"\'<>]*'
        flv_urls = re.findall(flv_pattern, html)
        video_urls.extend(flv_urls)
        
        # 方法6: 查找 JSON 中的视频数据
        json_patterns = [
            r'"(?:url|src|video|file|streamUrl)"?\s*:\s*["\']([^"\']+\.(?:mp4|m3u8|flv))["\']',
            r'(?:url|src|video|file|streamUrl)\s*:\s*["\']([^"\']+\.(?:mp4|m3u8|flv))["\']',
        ]
        for pattern in json_patterns:
            matches = re.findall(pattern, html)
            video_urls.extend(matches)
        
        # 方法7: 查找 window.player 或类似的 JS 变量
        player_patterns = [
            r'(?:window\.player|var\s+player|const\s+player|let\s+player)\s*=\s*{[^}]*(?:url|src|video|file)["\']?\s*:\s*["\']([^"\']+)["\']',
            r'player\s*=\s*["\']([^"\']+\.(?:mp4|m3u8|flv))["\']',
        ]
        for pattern in player_patterns:
            matches = re.findall(pattern, html)
            video_urls.extend(matches)
        
        # 方法8: 查找 script 标签中的 JSON 数据
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                script_text = script.string
                # 寻找可能的 JSON 对象
                json_matches = re.findall(r'{[^{}]*(?:url|src|video|file)[^{}]*}', script_text)
                for json_str in json_matches:
                    try:
                        data = json.loads(json_str)
                        urls = self._extract_urls_from_json(data)
                        video_urls.extend(urls)
                    except:
                        pass
        
        # 方法9: 特殊处理 51cg1.com 的数据格式
        # 查找类似 "https://..." 的长字符串模式
        special_pattern = r'["\']((?:https?:)?//[^"\']+\.(?:m3u8|mp4|flv)(?:[^"\']*)?)["\']'
        special_urls = re.findall(special_pattern, html)
        video_urls.extend(special_urls)
        
        # 去重并过滤有效的URL
        video_urls = list(set(filter(lambda x: x and len(x) > 10 and '://' in x, video_urls)))
        
        # 过滤掉错误的URL
        video_urls = [url for url in video_urls if not any(bad in url for bad in ['javascript:', 'data:'])]
        
        return video_urls

    def _extract_urls_from_json(self, obj, depth=0):
        """递归提取JSON中的URL"""
        urls = []
        if depth > 5:
            return urls
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    if any(ext in value for ext in ['.mp4', '.m3u8', '.flv']):
                        if value.startswith('http'):
                            urls.append(value)
                elif isinstance(value, (dict, list)):
                    urls.extend(self._extract_urls_from_json(value, depth + 1))
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, str) and any(ext in item for ext in ['.mp4', '.m3u8', '.flv']):
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
        if title and title.string:
            title_text = title.string.strip()
            # 清理标题
            title_text = re.sub(r'[<>:"/\\|?*]', '', title_text)
            title_text = title_text[:100]  # 限制长度
            if title_text:
                return title_text
        
        # 尝试获取 h1
        h1 = soup.find('h1')
        if h1 and h1.string:
            title_text = h1.string.strip()
            title_text = re.sub(r'[<>:"/\\|?*]', '', title_text)
            if title_text:
                return title_text
        
        # 如果没有找到，使用 URL 最后的部分
        path = urlparse(url).path.strip('/')
        if path:
            return path.split('/')[-1]
        
        return "video"

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
            
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ m3u8 下载完成: {output_file}")
            return True
        except FileNotFoundError:
            print("❌ 未找到 ffmpeg，请先安装:")
            print("  Windows: https://ffmpeg.org/download.html")
            print("  Mac: brew install ffmpeg")
            print("  Linux: sudo apt-get install ffmpeg")
            return False
        except Exception as e:
            print(f"❌ m3u8 下载失败: {str(e)}")
            return False

    def download_direct(self, video_url, output_file):
        """直接下载视频文件"""
        try:
            print(f"📥 开始下载: {video_url}")
            
            response = self.session.get(video_url, stream=True, timeout=30, allow_redirects=True)
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
                            mb_size = downloaded / 1024 / 1024
                            print(f"\r进度: {percent:.1f}% ({mb_size:.1f}MB)", end='', flush=True)
            
            print(f"\n✅ 下载完成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 下载失败: {str(e)}")
            if os.path.exists(output_file):
                os.remove(output_file)
            return False

    def download(self, url):
        """下载视频主流程"""
        try:
            # 获取页面
            html = self.fetch_page(url)
            if not html:
                print("❌ 无法获取页面内容")
                return False
            
            # 提取视频链接
            video_urls = self.extract_video_url(html)
            if not video_urls:
                print("❌ 未找到视频链接")
                print("💡 可能的原因:")
                print("  1. 页面需要登录")
                print("  2. 视频已删除或过期")
                print("  3. 视频被加密或受保护")
                print("\n📍 调试信息:")
                print("  - 请用浏览器访问页面，查看网络请求")
                print("  - 找到真实的视频URL (mp4/m3u8)")
                print("  - 或者运行: python 51cg_downloader.py <url> --debug")
                return False
            
            # 获取标题
            title = self.get_title(html, url)
            print(f"📌 视频标题: {title}")
            print(f"🔍 找到 {len(video_urls)} 个可能的视频源")
            
            # 尝试下载每个视频链接
            for i, video_url in enumerate(video_urls, 1):
                print(f"\n[{i}/{len(video_urls)}] 尝试下载: {video_url[:80]}...")
                
                # 确定输出文件名和格式
                if '.m3u8' in video_url:
                    output_file = str(self.output_dir / f"{title}.mp4")
                    success = self.download_m3u8(video_url, output_file)
                else:
                    # 猜测格式
                    ext = '.mp4'
                    if '.flv' in video_url:
                        ext = '.flv'
                    elif '.mkv' in video_url:
                        ext = '.mkv'
                    
                    output_file = str(self.output_dir / f"{title}{ext}")
                    success = self.download_direct(video_url, output_file)
                
                if success:
                    return True
            
            print("\n❌ 所有下载尝试都失败了")
            return False
            
        except Exception as e:
            print(f"❌ 出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    if len(sys.argv) < 2:
        print("51cg1.com 视频下载脚本 - 增强版")
        print("\n用法:")
        print("  python 51cg_downloader.py <页面链接>")
        print("\n示例:")
        print("  python 51cg_downloader.py 'https://51cg1.com/archives/264301/'")
        print("\n依赖:")
        print("  pip install requests beautifulsoup4")
        print("  (可选) 下载 m3u8 需要: ffmpeg")
        print("  (可选) 支持动态加载: pip install selenium")
        sys.exit(1)

    url = sys.argv[1]
    downloader = CG51Downloader()
    success = downloader.download(url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
