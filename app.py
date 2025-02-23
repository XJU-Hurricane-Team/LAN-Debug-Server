from flask import Flask, render_template, jsonify
import re
from Class import *
import serial.tools.list_ports

#获取本地IP地址
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

#获取可用端口号
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))            # 0表示自动分配
        return s.getsockname()[1]  # 返回实际分配的端口号



#获取Jlink串口字典 {SN:PortName}

def get_serial_ports():
    ports_list = list(serial.tools.list_ports.comports())
    ports_lib = {}

    if len(ports_list) <= 0:
        return 0
    else:
        for comport in ports_list:
            hwid = comport.hwid
            ser = re.search(r'SER=(\d+)', hwid)
            if ser:
                num = get_free_port()
                sn = str(int(ser.group(1)))
                port = Jport(sn, comport.device, num)
                ports_lib[sn] = {port}
        return ports_lib

#获取Jlink服务器列表
def get_jlink():
    proc = Popen(
        args=[f'{JLINK_PATH}{JLINK_COMMANDER_EXEC}', '-NoGui', '1', '-ExitOnError', '1'],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
        encoding='utf-8'
    )

    proc.stdin.write('ShowEmuList USB\nq')
    out, err = proc.communicate()

    jlink_filter_re = re.compile(r'J-Link\[(\d+)].*?Serial number: (\d+)')
    jlink_list = jlink_filter_re.findall(out)

    port = 19010
    server_list = []
    ip = get_local_ip()
    port_lib = get_serial_ports()
    for jlink in jlink_list:
        new_server = JLinkServer(jlink[1], port, ip, port_lib[jlink[1]])
        server_list.append(new_server)
        port += 1

    return server_list


app = Flask(__name__, static_folder='static')

JlinkList = get_jlink()
for Jlink in JlinkList:
    Jlink.start()
    Jlink.jport.start()

running_jlink_servers = {jlink.sn: jlink for jlink in JlinkList}


@app.route('/')
def index():
    return render_template('hello.html')


@app.route('/get_jlink_list')
def get_jlink_list():
    jlink_list = get_jlink()
    # 将对象列表转换为字典列表以便JSON序列化
    jlink_data = [{'port': server.port, 'serial': server.sn, 'ip': server.ip} for server in jlink_list]
    for jlink in jlink_list:
        if jlink.sn not in running_jlink_servers:
            jlink.start()
            running_jlink_servers[jlink.sn] = jlink
    return jsonify(jlink_data)
