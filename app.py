import json
import socket
import os
from flask import Flask, render_template, jsonify
from JSerialPort import get_serial
from JLinkServer import get_jlink

# 端口配置, 存在 json 文件中
port_config = {}


# 获取本地IP地址
def get_local_ip():
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        if s:
            s.close()
    return ip


app = Flask(__name__, static_folder='static')


@app.route('/')
def index():
    return render_template('index.html')


# 当前连接到的 JLink 配置
connected_jlink = {}


@app.route('/get_jlink_list')
def get_jlink_list():
    get_jlink(port_config, connected_jlink)
    get_serial(port_config, connected_jlink)
    json.dump(port_config, open("port.json", "w"))
    connected_jlink['ip'] = get_local_ip()
    return jsonify(connected_jlink)


if not os.path.exists("port.json"):
    f = open("port.json", "w")
    f.write('{}')
    f.close()

get_jlink(port_config, connected_jlink)
get_serial(port_config, connected_jlink)
json.dump(port_config, open("port.json", "w"))
port_config = json.load(open("port.json"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
