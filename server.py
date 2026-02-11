#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电销情景演练评分系统 - Python服务器
使用方法：双击运行 启动系统_Python版.bat
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import threading
import webbrowser

# 数据文件路径
DATA_DIR = 'data'
DATA_FILE = os.path.join(DATA_DIR, 'records.json')

# 确保数据目录存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 初始化数据文件
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({'records': [], 'nextId': 1}, f, ensure_ascii=False, indent=2)

def read_data():
    """读取数据"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'records': [], 'nextId': 1}

def write_data(data):
    """写入数据"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

class APIHandler(SimpleHTTPRequestHandler):
    """API处理器"""

    def end_headers(self):
        """添加CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """处理GET请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API路由
        if path == '/api/records':
            self.handle_get_records(query)
        elif path.startswith('/api/records/'):
            record_id = int(path.split('/')[-1])
            self.handle_get_record(record_id)
        elif path == '/api/statistics':
            self.handle_get_statistics(query)
        elif path == '/api/health':
            self.send_json({'success': True, 'message': '服务器运行正常', 'timestamp': datetime.now().isoformat()})
        else:
            # 静态文件
            super().do_GET()

    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/records':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            record = json.loads(body.decode('utf-8'))
            self.handle_add_record(record)
        else:
            self.send_error(404)

    def do_DELETE(self):
        """处理DELETE请求"""
        if self.path.startswith('/api/records/'):
            record_id = int(self.path.split('/')[-1])
            self.handle_delete_record(record_id)
        else:
            self.send_error(404)

    def handle_get_records(self, query):
        """获取所有记录"""
        data = read_data()
        records = data['records']

        # 权限过滤
        role = query.get('role', [''])[0]
        username = query.get('username', [''])[0]

        if role == 'leader':
            records = [r for r in records if r.get('teamLeader') == username]

        self.send_json({'success': True, 'records': records})

    def handle_get_record(self, record_id):
        """获取单个记录"""
        data = read_data()
        record = next((r for r in data['records'] if r['id'] == record_id), None)

        if record:
            self.send_json({'success': True, 'record': record})
        else:
            self.send_json({'success': False, 'error': '记录不存在'}, 404)

    def handle_add_record(self, record):
        """添加记录"""
        data = read_data()

        # 分配ID
        record['id'] = data['nextId']
        data['nextId'] += 1
        record['submitTime'] = datetime.now().isoformat()

        data['records'].append(record)

        if write_data(data):
            self.send_json({'success': True, 'record': record})
        else:
            self.send_json({'success': False, 'error': '保存失败'}, 500)

    def handle_delete_record(self, record_id):
        """删除记录"""
        data = read_data()
        data['records'] = [r for r in data['records'] if r['id'] != record_id]

        if write_data(data):
            self.send_json({'success': True})
        else:
            self.send_json({'success': False, 'error': '删除失败'}, 500)

    def handle_get_statistics(self, query):
        """获取统计数据"""
        data = read_data()
        records = data['records']

        # 权限过滤
        role = query.get('role', [''])[0]
        username = query.get('username', [''])[0]

        if role == 'leader':
            records = [r for r in records if r.get('teamLeader') == username]

        total = len(records)
        avg_score = sum(r['totalScore'] for r in records) / total if total > 0 else 0
        excellent = sum(1 for r in records if r['totalScore'] >= 90)
        excellent_rate = (excellent / total * 100) if total > 0 else 0

        self.send_json({
            'success': True,
            'statistics': {
                'totalRecords': total,
                'avgScore': round(avg_score, 1),
                'excellentRate': f'{round(excellent_rate, 1)}%'
            }
        })

    def send_json(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def get_local_ip():
    """获取本机IP地址"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def open_browser(port):
    """延迟打开浏览器"""
    import time
    time.sleep(1)
    webbrowser.open(f'http://localhost:{port}/电销情景演练评分系统_本地版.html')

def run_server(port=3000):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)

    local_ip = get_local_ip()

    print('\n' + '=' * 50)
    print('  电销情景演练评分系统 - 服务器已启动')
    print('=' * 50)
    print(f'\n[OK] 本机访问: http://localhost:{port}')
    print(f'[OK] 数据位置: {os.path.abspath(DATA_FILE)}\n')
    print('[INFO] 其他设备请访问以下地址:\n')
    print(f'   http://{local_ip}:{port}/电销情景演练评分系统_本地版.html\n')
    print('按 Ctrl+C 停止服务器\n')
    print('=' * 50 + '\n')

    # 只在本地环境自动打开浏览器
    if os.getenv('RENDER') != 'true':
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n\n服务器已停止')
        httpd.shutdown()

if __name__ == '__main__':
    # 支持环境变量端口（云部署时使用）
    port = int(os.getenv('PORT', 3000))
    run_server(port)
