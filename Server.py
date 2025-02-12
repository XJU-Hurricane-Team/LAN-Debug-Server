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
    def __init__(self, sn, port):
        self.sn = sn
        self.port = port
        self.state = ServerStatus.CLOSED
        self.proc = None

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
