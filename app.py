from flask import Flask, render_template, jsonify
import re
from Class import *
import serial
import serial.tools.list_ports

#获取本地IP地址
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
                sn = str(int(ser.group(1)))
                port = Jport(sn, comport.device)
                ports_lib[sn] = port
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
    Jlink.jport.port_num  = get_free_port()
    Jlink.jport_num = Jlink.jport.port_num
    Jlink.jproc = Process(target=Jlink.jport.start, args=(115200,))
    Jlink.jproc.start()
    print(Jlink.jport_num)

running_jlink_servers = {jlink.sn: jlink for jlink in JlinkList}


@app.route('/')
def index():
    return render_template('hello.html')


@app.route('/get_jlink_list')
def get_jlink_list():
    jlink_list = get_jlink()
    for jlink in jlink_list:
        if jlink.sn not in running_jlink_servers:
            jlink.start()
            jlink.jport.port_num = get_free_port()
            jlink.jport_num = jlink.jport.port_num
            jlink.jproc = Process(target=Jlink.jport.start, args=(115200,))
            jlink.jproc.start()
            print(Jlink.jport_num)
            running_jlink_servers[jlink.sn] = jlink
    # 将对象列表转换为字典列表以便JSON序列化
    jlink_data = [{'port': server.port, 'sn': server.sn, 'ip': server.ip, 'jportnum': server.jport_num,} for server in running_jlink_servers.values()]
    return jsonify(jlink_data)
