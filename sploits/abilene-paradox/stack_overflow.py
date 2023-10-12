from abilene_lib import CheckMachine, WebSocketHandler
from checklib import BaseChecker
import sys

mch = CheckMachine(BaseChecker(sys.argv[1]))

with mch.ws() as ws:
    handler = WebSocketHandler(ws=ws)
    mch.init_connection(handler)
    prog = mch.read_from_file_program('/dev/urandom', print_contents=True)
    print(mch.run_program(handler, prog))
