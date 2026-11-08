"""Development parity oracle; never part of the browser/npm runtime."""
import argparse
import json
import sys
import torch
from training.browser.export_model import open_pack

parser = argparse.ArgumentParser()
parser.add_argument('--pack', required=True)
args = parser.parse_args()
torch.set_num_threads(4)
pack = open_pack(args.pack)
for line in sys.stdin:
    request_id = None
    try:
        request = json.loads(line)
        request_id = request['id']
        result = pack.highlight(source=request['source'], document_kind=request['documentKind'])
        response = {'id': request_id, 'result': result}
    except Exception as error:
        response = {'id': request_id, 'error': {'message': str(error)}}
    print(json.dumps(response, ensure_ascii=False), flush=True)
