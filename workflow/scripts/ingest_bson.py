import argparse
import json
import sys
import bson

parser = argparse.ArgumentParser()
parser.add_argument("outfile")
args = parser.parse_args()

with open(args.outfile, 'wb') as outfile:
    for line in sys.stdin:
        try:
            load = json.loads(line)
        except json.decoder.JSONDecodeError as e:
            print(f"ERROR: {e}, {line}", file=sys.stderr)
        else:
            outfile.write(bson.dumps(load))
