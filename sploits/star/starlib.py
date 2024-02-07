from __future__ import annotations

import base64
import gzip
import subprocess

import websocket
from pydantic import BaseModel, Field
from checklib import *

PORT = 5555

CAPTCHA_DIFFICULTY = 6
CAPTCHA_ITERATIONS = 3

W = websocket.WebSocket


class Artifact(BaseModel):
    source_project: str = Field(default="")
    source: str
    destination: str


class Step(BaseModel):
    name: str
    artifacts: list[Artifact]


class Job(BaseModel):
    steps: list[Step]


class JobRequest(BaseModel):
    job: Job


class CheckMachine:
    def __init__(self, host: str):
        self.host = host

    def connect(self) -> W:
        return websocket.create_connection(
            f"ws://{self.host}:{PORT}/ws/",
            header={"User-Agent": "CTF"},
        )

    @staticmethod
    def create_project(conn: W, project_id: str) -> str:
        conn.send(f"project {project_id} {rnd_bytes(16).hex()}")
        print(conn.recv())
        pass_msg = conn.recv().split(" ")
        print(pass_msg)
        return pass_msg[1]

    @staticmethod
    def enter_project(conn: W, project_id: str, project_pass: str):
        conn.send(f"project {project_id} {project_pass}")
        print(conn.recv())

    @staticmethod
    def solve_captcha(conn: W):
        conn.send("captcha")
        captcha_msg = conn.recv().split(" ")
        print(captcha_msg)

        res = subprocess.check_output(["./captcha_solver", captcha_msg[1]]).strip()
        print(res)
        conn.send(res)
        print(conn.recv())

    def upload(self, conn: W, name: str, content: bytes):
        conn.send(f"upload {name} {self.compress(content)}")

    def job(self, conn: W, job: JobRequest):
        conn.send(f"job {self.compress(job.json().encode())}")

    @staticmethod
    def list(conn: W, path: str):
        conn.send(f"list {path}/")
        return conn.recv()

    def download(self, conn: W, path: str):
        conn.send(f"download {path}")
        resp = conn.recv()
        print("download response:", resp)
        return self.decompress(resp.split(" ")[-1])

    @staticmethod
    def compress(data: bytes) -> str:
        return base64.urlsafe_b64encode(gzip.compress(data)).decode()

    @staticmethod
    def decompress(data: str) -> bytes:
        return gzip.decompress(base64.urlsafe_b64decode(data))
