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
            outfile.write(bson.dumps(load))
        except json.decoder.JSONDecodeError as e:
            print(f"JSON Encoding error: {e}, {line}", file=sys.stderr)
        except bson.codec.UnknownSerializerError as e:
            print(f"BSON Encoding error: {e}, {line}", file=sys.stderr)
