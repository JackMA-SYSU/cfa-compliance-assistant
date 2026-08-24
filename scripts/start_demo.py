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
import socket
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(BASE, "backend")
QR_PATH = os.path.join(BASE, "demo_qr.png")
PORT = 8000


def get_lan_ip():
    """获取本机在局域网中的 IP（手机热点分配的地址）"""
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # UDP 连接不真正发包，仅确定路由网卡
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            ips.append(ip)
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips[0] if ips else "127.0.0.1"


def generate_qr(url):
    import qrcode
    img = qrcode.make(url)
    img.save(QR_PATH)
    return QR_PATH


def main():
    ip = get_lan_ip()
    url = f"http://{ip}:{PORT}"
    qr = generate_qr(url)

    print("=" * 50)
    print("  CFA 合规自检助手 - 局域网演示模式")
    print("=" * 50)
    print(f"  本机 IP      : {ip}")
    print(f"  访问地址     : {url}")
    print(f"  二维码文件   : {qr}")
    print()
    print("  演示步骤：")
    print("  1. 手机已开启个人热点，电脑已连接该热点")
    print("  2. 评委手机连接同一热点")
    print("  3. 评委扫码，或直接访问上面的地址")
    print()
    print("  ⚠ 首次启动若弹出 Windows 防火墙提示，请点「允许访问」")
    print("  ⚠ 按 Ctrl+C 停止服务")
    print("=" * 50)

    os.chdir(BACKEND)
    subprocess.run([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0", "--port", str(PORT),
    ])


if __name__ == "__main__":
    main()
