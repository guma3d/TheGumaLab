"""Local Codex preparation CLI; never invokes Gemini, image or Veo APIs."""
import argparse
import json
from app.core import prepared_packages as p

parser=argparse.ArgumentParser()
parser.add_argument('command',choices=('verify',))
parser.add_argument('target',help='recommendation JSON for prepare; idea id otherwise')
parser.add_argument('--version',type=int)
parser.add_argument('--file')
parser.add_argument('--metadata')
parser.add_argument('--date')
parser.add_argument('--regenerate',action='store_true')
args=parser.parse_args()
result=p.verify_package(args.target,args.version)
print(json.dumps(result,ensure_ascii=False))
