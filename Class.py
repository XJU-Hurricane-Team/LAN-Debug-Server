from enum import Enum
from configurations import *
from subprocess import Popen, PIPE
from multiprocessing import  Process
import os
import fcntl
import serial
import socket
import threading
import signal



class ServerStatus(Enum):
    CLOSED = 0
    OPENED = 1



def non_block_read(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

#获取可用端口号
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))            # 0表示自动分配
        return s.getsockname()[1]  # 返回实际分配的端口号


def receive_data(client_socket, ser, lock):
    """接收客户端数据并写入串口"""
    try:
        while True:
            # print("listening")
            tcp_data = client_socket.recv(1024)
            if not tcp_data:
                print("Graceful disconnect")
                break
            with lock:
                ser.write(tcp_data)
                print("write")
    except (ConnectionResetError, BrokenPipeError):
        print("Client disconnected")
    finally:
        client_socket.close()



def forward_data(client_socket, ser, lock):
    """从串口读取数据并转发给客户端"""
    try:
        while True:
            data = ser.readline()
            if not data:
                continue
            # print(f"Forwarding {len(data)} bytes")
            try:
                with lock:
                    client_socket.sendall(data)
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"Send failed: {str(e)}")
                break
    except Exception as e:  # 捕获所有其他异常
        print(f"Unexpected error: {str(e)}")
    finally:
        with lock:  # 加锁关闭socket
            if not getattr(client_socket, '_closed'):  # 防止重复关闭
                client_socket.close()



# JlinkPort class
class Jport:
    def __init__(self, sn, port_name):
        self.sn = sn
        self.port_name = port_name
        self.port_num = None
        self.lock = threading.Lock()
        self.ser = None
        self.client_socket = None

    def start(self, baudrate):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', self.port_num))
        server.listen(5)
        print(f"Listening on {'0.0.0.0'}:{self.port_num}")

        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            self.ser = serial.Serial(self.port_name, baudrate, timeout=1)

            # 在新的线程中处理数据
            write_thread = threading.Thread(target=receive_data, args=(client_socket, self.ser, self.lock))
            read_thread = threading.Thread(target=forward_data, args=(client_socket, self.ser, self.lock))

            write_thread.start()
            read_thread.start()



# JLinkServer class
class JLinkServer:
    def __init__(self, sn, ip, jport):
        self.sn = sn
        self.port = None
        self.state = ServerStatus.CLOSED
        self.proc = None
        self.jproc = None
        self.ip = ip
        self.jport = jport  # JlinkPort object
        self.jport_num = None

    def start(self):
        self.port = get_free_port()
        self.proc = Popen(
            args=[f'{JLINK_PATH}{JLINK_REMOTE_SERVER_EXEC}', '-select', f'USB={self.sn}', '-port', f'{self.port}',],
            stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf8'
        )
        non_block_read(self.proc.stdout)
        non_block_read(self.proc.stderr)
        self.state = ServerStatus.OPENED

    def stop(self):
        # self.proc.kill()
        # os.kill(self.proc.pid, signal.SIGKILL)
        os.kill(self.proc.pid, signal.SIGTERM)
        self.proc.wait(2)
        self.jproc.kill()
        del self.jport
        self.proc = None
        self.jproc = None
        self.jport_num = None
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
