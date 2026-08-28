# -*- coding: utf-8 -*-
"""局域网演示一键启动：检测 IP → 生成二维码 → 启动后端服务

用法：
    python scripts/start_demo.py

演示当天流程：
    1. 手机开启"个人热点"
    2. 电脑连接该热点
    3. 运行本脚本（自动检测 IP、生成二维码 demo_qr.png、启动服务）
    4. 评委手机连接同一热点，扫码访问 http://<电脑IP>:8000
"""
import os
import re
import socket
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(BASE, "backend")
QR_PATH = os.path.join(BASE, "demo_qr.png")
PORT = 8000


def get_all_ips():
    """获取本机所有 IPv4 地址（优先 ipconfig，避开 VPN/虚拟网卡）"""
    ips = set()
    try:
        out = subprocess.check_output("ipconfig", shell=True).decode("gbk", errors="ignore")
        for m in re.findall(r"IPv4[^\d]*(\d+\.\d+\.\d+\.\d+)", out):
            if not m.startswith("127."):
                ips.add(m)
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass
    return sorted(ips)


def pick_best_ip(ips):
    """挑选最可能是手机热点/局域网的真实 IP"""
    if not ips:
        return "127.0.0.1"
    # Android 热点 / 家用路由器最常见 192.168.x.x
    for ip in ips:
        if ip.startswith("192.168."):
            return ip
    # iPhone 热点 172.20.10.x
    for ip in ips:
        if ip.startswith("172.20.10."):
            return ip
    # 其它 172.x / 10.x 局域网段
    for ip in ips:
        if ip.startswith("10.") or ip.startswith("172."):
            return ip
    return ips[0]


def generate_qr(url):
    import qrcode
    img = qrcode.make(url)
    img.save(QR_PATH)
    return QR_PATH


def main():
    ips = get_all_ips()
    ip = pick_best_ip(ips)
    url = f"http://{ip}:{PORT}"
    qr = generate_qr(url)

    print("=" * 52)
    print("  CFA 合规自检助手 - 局域网演示模式")
    print("=" * 52)
    print()
    print("  【两个访问地址，请记好】")
    print(f"  ① 你自己电脑测试   : http://localhost:{PORT}")
    print(f"  ② 评委手机(连热点) : {url}")
    print(f"  二维码文件         : {qr}")
    print()
    print("  检测到的本机 IP 列表：")
    for i in ips:
        mark = "  ← 使用此地址" if i == ip else ""
        print(f"    - {i}{mark}")
    print()
    print("  演示步骤：")
    print("  1. 手机已开启个人热点，电脑已连接该热点")
    print("  2. 评委手机连接同一热点")
    print("  3. 评委扫码，或直接访问上面的 ② 地址")
    print()
    print("  ⚠ 若自动选错地址，从上表手动挑 192.168.x 的地址")
    print("  ⚠ 首次启动若弹 Windows 防火墙提示，请点「允许访问」")
    print("  ⚠ 按 Ctrl+C 停止服务")
    print("=" * 52)

    os.chdir(BACKEND)
    subprocess.run([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0", "--port", str(PORT),
    ])


if __name__ == "__main__":
    main()
