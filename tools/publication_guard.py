"""Fail-closed publication checks for the working tree or the complete Git index.

This is a leak-prevention heuristic, not copyright clearance or a malware scanner.
It does not follow symlinks, trust .gitignore, or print matched secret values.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

PROHIBITED = set(('.gr2 .dds .msa .msm .mse .mde .msf .spt .atr .raw .wtr .pck .epk .eix '
                  '.fbx .glb .gltf .obj .blend .uasset .umap .exe .dll .lib .pdb .so .dylib '
                  '.zip .7z .rar .png .tga .jpg .jpeg .wav .mp3 .pyc').split())
PRIVATE_DIRS = {'source_snapshots','private','engine','ue','deriveddatacache','saved','intermediate','binaries'}
TEXT_SUFFIXES = {'.md','.json','.py','.c','.h','.txt','.toml','.yml','.yaml','.cmake'}
SPECIAL = {'LICENSE','.gitignore','.gitattributes','CMakeLists.txt'}
SYNTHETIC_PATH = 'examples/synthetic_asset/neutral.json'
PATTERNS = {
    'absolute-machine-path': re.compile(r'(?i)(?:\b[A-Z]:[\\/]|/(?:home|Users)/[^\s/]+/)'),
    'network-address': re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])'),
    'private-key': re.compile(r'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----'),
    'github-token': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'cloud-api-key': re.compile(r'(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{24,})'),
    'discord-token': re.compile(r'(?:mfa\.[\w-]{40,}|[\w-]{24}\.[\w-]{6}\.[\w-]{27,})'),
    'credential-assignment': re.compile(r'(?i)(?:password|secret|api[_-]?key|access[_-]?token)\s*[=:]\s*[\"\x27][A-Za-z0-9_+/=-]{16,}[\"\x27]'),
    'large-encoded-payload': re.compile(r'[A-Za-z0-9+/]{256,}={0,2}'),
    'asset-fingerprint': re.compile(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])'),
}


def check_content(relative, payload, deny_terms=(), synthetic_bytes=None):
    path=Path(relative);issues=[]
    parts=relative.replace('\\','/').split('/')
    if any(p.lower() in PRIVATE_DIRS for p in parts): issues.append('private-directory')
    if path.suffix.lower() in PROHIBITED: issues.append('prohibited-extension')
    if path.name not in SPECIAL and path.suffix.lower() not in TEXT_SUFFIXES: issues.append('unreviewed-file-type')
    if len(payload)>2_000_000: return issues+['oversized-file']
    try: text=payload.decode('utf-8')
    except UnicodeDecodeError: return issues+['binary-content']
    if '\0' in text: issues.append('binary-content')
    for term in deny_terms:
        if term and term.casefold() in (relative+'\n'+text).casefold(): issues.append('private-deny-term')
    for label, pattern in PATTERNS.items():
        matches=list(pattern.finditer(text))
        if label=='asset-fingerprint' and relative=='tools/build_reader.py':
            # Only the three audited PUBLIC upstream source identities are permitted.
            from tools.build_reader import SOURCE_HASHES
            matches=[x for x in matches if x.group().lower() not in SOURCE_HASHES.values()]
        if matches: issues.append(label)
    if relative==SYNTHETIC_PATH:
        if payload!=synthetic_bytes: issues.append('synthetic-fixture-not-reproducible')
    elif path.suffix.lower()=='.json':
        try:
            value=json.loads(text)
            if isinstance(value,dict) and ({'meshes','skeleton','animations'} & set(value) or any(k in value for k in ('frames','local_transforms','raw_vertex_buffer_base64'))):
                issues.append('unapproved-asset-payload')
        except ValueError: issues.append('invalid-json')
    return sorted(set(issues))


def workspace_files(root):
    for current,dirs,files in os.walk(root,followlinks=False):
        current=Path(current)
        for name in list(dirs):
            p=current/name
            if name=='.git':
                dirs.remove(name)
                if current!=root: yield p.relative_to(root).as_posix(),None,'nested-git'
            elif p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):
                dirs.remove(name);yield p.relative_to(root).as_posix(),None,'linked-directory'
        for name in sorted(files):
            p=current/name;relative=p.relative_to(root).as_posix()
            if p.is_symlink(): yield relative,None,'symlink'
            elif name=='.git': yield relative,None,'git-file'
            else: yield relative,p.read_bytes(),None


def index_files(root):
    raw=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=root)
    for record in raw.split(b'\0'):
        if not record: continue
        meta,name=record.split(b'\t',1);mode,oid,stage=meta.decode('ascii').split()
        relative=name.decode('utf-8')
        if mode not in ('100644','100755') or stage!='0': yield relative,None,'nonregular-or-conflicted-index-entry'
        else: yield relative,subprocess.check_output(['git','cat-file','blob',oid],cwd=root),None


def scan(root, staged=False, deny_terms=()):
    from tests.synthetic.generate import generate
    from tools.legacy_pipeline.neutral import canonical_bytes
    synthetic=canonical_bytes(generate()); root=Path(root).resolve(); failures=[];count=0
    for relative,payload,error in (index_files(root) if staged else workspace_files(root)):
        count+=1
        issues=[error] if error else check_content(relative,payload,deny_terms,synthetic)
        for issue in issues: failures.append({'path':relative,'rule':issue})
    return {'status':'PASS' if not failures else 'FAIL','scope':'complete-index' if staged else 'entire-workspace-except-root-git-metadata','files_scanned':count,'failures':failures}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('.'));parser.add_argument('--staged',action='store_true')
    parser.add_argument('--deny-term',action='append',default=[])
    args=parser.parse_args();result=scan(args.root,args.staged,args.deny_term)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='PASS' else 1)


if __name__=='__main__':
    # Script and module invocation both work without installing this repository.
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    main()
