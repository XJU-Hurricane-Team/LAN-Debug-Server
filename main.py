import re
from Server import *


def get_jlink_list():
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

    for jlink in jlink_list:
        new_server = JLinkServer(jlink[1], port)
        server_list.append(new_server)

        port += 1

    return server_list

