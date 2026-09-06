"""Public CLI operates on neutral JSON only; GR2 decoding is not bundled."""
import argparse
import json
from pathlib import Path

from .fbx import write_fbx
from .neutral import audit_transform, load, validate
from .roundtrip import validate_fbx


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('inspect','validate-neutral','audit-transform','write-fbx','validate-fbx'):
        p=commands.add_parser(name);p.add_argument('neutral',type=Path)
        if name=='write-fbx':
            p.add_argument('--output',type=Path,required=True);p.add_argument('--clip')
            p.add_argument('--allow-trs-projection',action='store_true');p.add_argument('--max-shear',type=float,default=0.)
        if name=='validate-fbx':
            p.add_argument('--fbx',type=Path,required=True);p.add_argument('--reader',type=Path,required=True);p.add_argument('--workdir',type=Path,required=True);p.add_argument('--clip')
    args=parser.parse_args()
    try:
        if args.neutral.suffix.lower()!='.json': raise ValueError('Only neutral JSON is supported; no binary GR2 decoder is included')
        asset=load(args.neutral)
        if args.command in ('inspect','validate-neutral'): result=validate(asset)
        elif args.command=='audit-transform': result=audit_transform(asset)
        elif args.command=='write-fbx': result=write_fbx(asset,args.output,args.clip,args.allow_trs_projection,args.max_shear)
        else: result=validate_fbx(asset,args.fbx,args.reader,args.workdir,args.clip)
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValueError,OSError) as exc:
        parser.exit(1,str(exc)+'\n')


if __name__=='__main__': main()
