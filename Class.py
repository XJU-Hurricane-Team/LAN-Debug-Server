from enum import Enum
from configurations import *
from subprocess import Popen, PIPE
import os
import fcntl
import serial
import socket
import threading


class ServerStatus(Enum):
    CLOSED = 0
    OPENED = 1



def non_block_read(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)



#客户端处理函数
def handle_client(client_socket, ser, lock):

    try:
        while True:
            # 发送数据
            with lock:
                data = ser.read(128)
            if data:
                print(f"Forwarding {len(data)} bytes")
                client_socket.sendall(data)
            # else:
            #     print("No data received")

            # 接受数据
            tcp_data = client_socket.recv(1024)
            if tcp_data:
                with lock:
                    ser.write(tcp_data)
    except (ConnectionResetError, BrokenPipeError):
        print("Client disconnected")
    finally:
        client_socket.close()



# JlinkPort class
class Jport:
    def __init__(self, sn, port_name, port_num):
        self.sn = sn
        self.port_name = port_name
        self.port_num = port_num
        self.lock = threading.Lock()
        self.ser = None
        self.client_socket = None

    def start(self, baudrate):
        self.ser = serial.Serial(self.port_name, baudrate, timeout=1)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', self.port_num))
        server.listen(5)
        print(f"Listening on {'0.0.0.0'}:{self.port_num}")

        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            # 在新的线程中处理数据
            client_handler = threading.Thread(target=handle_client, args=(client_socket, self.ser, self.lock))
            client_handler.start()



# JLinkServer class
class JLinkServer:
    def __init__(self, sn, port, ip, jport):
        self.sn = sn
        self.port = port
        self.state = ServerStatus.CLOSED
        self.proc = None
        self.ip = ip
        self.jport = jport  # JlinkPort object

    def start(self):
        self.proc = Popen(
            args=[f'{JLINK_PATH}{JLINK_REMOTE_SERVER_EXEC}', '-select', f'USB={self.sn}', '-port', f'{self.port}'],
            stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf8'
        )
        non_block_read(self.proc.stdout)
        non_block_read(self.proc.stderr)
        self.state = ServerStatus.OPENED

    def stop(self):
        self.proc.kill()
        self.state = ServerStatus.CLOSED

    def read_log_line(self):
        if self.state == ServerStatus.OPENED:
            return self.proc.stdout.readline()
        else:
            return ''

    def read_err_line(self):
        if self.state == ServerStatus.OPENED:
            return self.proc.stderr.readline()
        else:
            return ''
