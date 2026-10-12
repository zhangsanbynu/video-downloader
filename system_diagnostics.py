#!/usr/bin/env python3
"""
系统资源诊断工具
查找占用内存和CPU的进程，帮助识别问题程序
"""

import os
import sys
import psutil
import platform
from datetime import datetime
from tabulate import tabulate


class SystemDiagnostics:
    def __init__(self):
        self.system = platform.system()
        
    def get_memory_info(self):
        """获取内存信息"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024**3),
            'used': memory.used / (1024**3),
            'available': memory.available / (1024**3),
            'percent': memory.percent
        }
    
    def get_cpu_info(self):
        """获取CPU信息"""
        return {
            'count': psutil.cpu_count(),
            'percent': psutil.cpu_percent(interval=1),
            'freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
    
    def get_top_processes_by_memory(self, limit=10):
        """获取占用内存最多的进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
            try:
                processes.append({
                    'PID': proc.info['pid'],
                    '进程名': proc.info['name'][:40],
                    '内存占比': f"{proc.info['memory_percent']:.2f}%",
                    '内存用量': f"{proc.info['memory_info'].rss / (1024**2):.2f} MB"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 按内存占比排序
        processes.sort(key=lambda x: float(x['内存占比'].rstrip('%')), reverse=True)
        return processes[:limit]
    
    def get_top_processes_by_cpu(self, limit=10):
        """获取占用CPU最多的进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                cpu_percent = proc.cpu_percent(interval=0.1)
                if cpu_percent > 0:
                    processes.append({
                        'PID': proc.info['pid'],
                        '进程名': proc.info['name'][:40],
                        'CPU占比': f"{cpu_percent:.2f}%"
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes.sort(key=lambda x: float(x['CPU占比'].rstrip('%')), reverse=True)
        return processes[:limit]
    
    def get_disk_info(self):
        """获取磁盘信息"""
        disk_data = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_data.append({
                    '磁盘': partition.device,
                    '挂载点': partition.mountpoint,
                    '总容量': f"{usage.total / (1024**3):.2f} GB",
                    '已用': f"{usage.used / (1024**3):.2f} GB",
                    '可用': f"{usage.free / (1024**3):.2f} GB",
                    '使用率': f"{usage.percent:.1f}%"
                })
            except:
                pass
        return disk_data
    
    def print_summary(self):
        """打印系统摘要"""
        print("=" * 80)
        print(f"🖥️  系统诊断报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 内存信息
        print("\n📊 内存状态:")
        mem = self.get_memory_info()
        print(f"  总内存: {mem['total']:.2f} GB")
        print(f"  已用: {mem['used']:.2f} GB ({mem['percent']:.1f}%)")
        print(f"  可用: {mem['available']:.2f} GB")
        if mem['percent'] > 80:
            print("  ⚠️  警告: 内存占用过高！")
        
        # CPU信息
        print("\n⚙️  CPU状态:")
        cpu = self.get_cpu_info()
        print(f"  核心数: {cpu['count']}")
        print(f"  使用率: {cpu['percent']:.1f}%")
        print(f"  频率: {cpu['freq']:.2f} MHz")
        if cpu['percent'] > 80:
            print("  ⚠️  警告: CPU占用过高！")
    
    def print_top_memory_processes(self):
        """打印占用内存最多的进程"""
        print("\n🔴 占用内存最多的进程 (TOP 10):")
        print("-" * 80)
        processes = self.get_top_processes_by_memory(10)
        if processes:
            print(tabulate(processes, headers="keys", tablefmt="grid"))
        else:
            print("  无法获取进程信息")
    
    def print_top_cpu_processes(self):
        """打印占用CPU最多的进程"""
        print("\n🟠 占用CPU最多的进程 (TOP 10):")
        print("-" * 80)
        processes = self.get_top_processes_by_cpu(10)
        if processes:
            print(tabulate(processes, headers="keys", tablefmt="grid"))
        else:
            print("  无法获取进程信息")
    
    def print_disk_info(self):
        """打印磁盘信息"""
        print("\n💾 磁盘状态:")
        print("-" * 80)
        disks = self.get_disk_info()
        if disks:
            print(tabulate(disks, headers="keys", tablefmt="grid"))
        else:
            print("  无法获取磁盘信息")
    
    def print_suspicious_processes(self):
        """打印可疑进程"""
        print("\n🔍 可疑进程检查:")
        print("-" * 80)
        
        suspicious = []
        suspicious_names = [
            'miner', 'crypto', 'bitcoin', 'ethereum',
            'virus', 'trojan', 'malware',
            'svchost', 'rundll32', 'lsass'
        ]
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.name().lower()
                if any(sus in name for sus in suspicious_names):
                    suspicious.append({
                        'PID': proc.pid,
                        '进程名': proc.name(),
                        '状态': '⚠️ 可疑'
                    })
            except:
                pass
        
        if suspicious:
            print(tabulate(suspicious, headers="keys", tablefmt="grid"))
            print("\n💡 建议: 检查这些进程，必要时可以在任务管理器中结束")
        else:
            print("  ✅ 未发现明显可疑进程")
    
    def run_full_diagnosis(self):
        """运行完整诊断"""
        self.print_summary()
        self.print_top_memory_processes()
        self.print_top_cpu_processes()
        self.print_disk_info()
        self.print_suspicious_processes()
        
        print("\n" + "=" * 80)
        print("💡 常见解决方案:")
        print("=" * 80)
        print("""
1. 打开任务管理器 (Ctrl+Shift+Esc):
   - 查看内存占用最多的进程
   - 右键选择"结束进程树"

2. 查看启动项:
   - Windows: 设置 > 应用 > 启动
   - 禁用不需要的后台程序

3. 检查 Windows 更新:
   - 可能在后台下载/安装更新

4. 检查病毒/恶意软件:
   - 运行 Windows Defender 扫描
   - 或使用专业反病毒软件

5. 清理临时文件:
   - 运行 cleanmgr (磁盘清理)
   - 清理浏览器缓存

6. 禁用不必要的服务:
   - services.msc 查看服务
   - 禁用不需要的后台服务
        """)
        print("=" * 80)


def main():
    try:
        diagnostics = SystemDiagnostics()
        diagnostics.run_full_diagnosis()
    except Exception as e:
        print(f"❌ 诊断失败: {str(e)}")
        print("\n请确保已安装依赖:")
        print("  pip install psutil tabulate")
        sys.exit(1)


if __name__ == "__main__":
    main()
