from enum import Enum
from configurations import *
from subprocess import Popen, PIPE
import os
import fcntl


class ServerStatus(Enum):
    CLOSED = 0
    OPENED = 1


def non_block_read(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


class JLinkServer:
    def __init__(self, sn, port, ip):
        self.sn = sn
        self.port = port
        self.state = ServerStatus.CLOSED
        self.proc = None
        self.ip = ip
        self.log = ''
        self.err = ''

    def start(self):
        self.proc = Popen(
            args=[f'{JLINK_PATH}{JLINK_REMOTE_SERVER_EXEC}', '-select', f'USB={self.sn}', '-port', f'{self.port}', '-SelectEmuBySN', f'{self.sn}'],
            stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf8'
        )
        non_block_read(self.proc.stdout)
        non_block_read(self.proc.stderr)
        self.state = ServerStatus.OPENED

    def stop(self):
        self.proc.kill()
        self.state = ServerStatus.CLOSED
        self.log = ''

    def get_log(self):
        if self.state == ServerStatus.OPENED:
            self.log += self.proc.stdout.read()

    def get_err(self):
        if self.state == ServerStatus.OPENED:
            self.log += self.proc.stderr.read()
