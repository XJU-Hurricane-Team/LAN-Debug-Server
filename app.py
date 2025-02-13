from flask import Flask, render_template, jsonify
import main

app = Flask(__name__)

JlinkList = main.get_jlink_list()
for Jlink in JlinkList:
        Jlink.start()

running_jlink_servers = {jlink.sn: jlink for jlink in JlinkList}
@app.route('/')
def index():
    return render_template('hello.html')

@app.route('/get_jlink_list')
def get_jlink_list():
    jlink_list = main.get_jlink_list()
    # 将对象列表转换为字典列表以便JSON序列化
    jlink_data = [{'port': server.port, 'serial': server.sn, 'ip': server.ip} for server in jlink_list]
    for Jlink in jlink_list:
        if Jlink.sn not in running_jlink_servers:
            Jlink.start()
            running_jlink_servers[Jlink.sn] = Jlink
    return jsonify(jlink_data)



