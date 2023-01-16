import argparse
import json
import sys
import bson
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("outfile_path", type=Path)
args = parser.parse_args()

outfile_path = Path(args.outfile_path)
outfile_path.parent.mkdir(exist_ok=True, parents=True)

with open(outfile_path, 'wb') as outfile:
    for i, line in enumerate(sys.stdin):
        if i % 100 == 0:
            try:
                load = json.loads(line)
                outfile.write(bson.dumps(load))
            except json.decoder.JSONDecodeError as e:
                print(f"JSON Encoding error: {e}, {line}", file=sys.stderr)
            except bson.codec.UnknownSerializerError as e:
                print(f"BSON Encoding error: {e}, {line}", file=sys.stderr)
