from flask import Flask, jsonify, render_template
import psutil
import socket
import datetime
import os
import json

app = Flask(__name__)

def get_size(bytes, suffix="B"):
    """
    바이트를 적절한 단위로 변환
    예:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    # CPU 사용률
    cpu_percent = psutil.cpu_percent(interval=0.5)
    
    # 메모리 정보
    svmem = psutil.virtual_memory()
    memory_info = {
        "total": get_size(svmem.total),
        "available": get_size(svmem.available),
        "used": get_size(svmem.used),
        "percent": svmem.percent
    }

    # 디스크 정보
    def get_disk_data(path):
        try:
            if not os.path.exists(path): return None
            d = psutil.disk_usage(path)
            return {
                "total": get_size(d.total),
                "used": get_size(d.used),
                "free": get_size(d.free),
                "percent": d.percent
            }
        except: return None
    
    # C 드라이브 (호스트 마운트)
    disk_c = get_disk_data("/mnt/c")
    
    # D 드라이브 (호스트 마운트)
    disk_d = get_disk_data("/mnt/d")

    # 부팅 시간
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
    uptime = datetime.datetime.now() - bt
    
    # 네트워크 상태
    net_io = psutil.net_io_counters()
    network_info = {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv
    }

    # 온도 모니터링 로직 제거됨 (사용자 요청)
    
    return jsonify({
        "hostname": socket.gethostname(),
        "cpu": cpu_percent,
        "memory": memory_info,
        "disk_c": disk_c,
        "disk_d": disk_d,
        "network": network_info,
        "uptime": str(uptime).split('.')[0]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
