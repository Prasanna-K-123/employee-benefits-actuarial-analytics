"""Fetch only four registered source blobs; verify every byte before use."""
from pathlib import Path
from urllib.request import Request,urlopen
import argparse
import hashlib
import json
from src.predictive_reserving import ROOT,STUDY,protocol_guard,json_write,sha


def git_sha(b):
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()


def collect(verify_committed=False):
    p=protocol_guard()
    records=[]
    for spec in p['new_source_blobs']:
        path=ROOT/spec['path']
        if verify_committed:
            b=path.read_bytes()
        else:
            if path.exists(): raise ValueError('Refuse source overwrite: '+str(path))
            req=Request(spec['url'],headers={'User-Agent':'registered-actuarial-portfolio/1.0'})
            with urlopen(req,timeout=45) as response: b=response.read()
        if git_sha(b)!=spec['git_blob_sha'] or len(b)!=spec['bytes']:
            raise ValueError('Source bytes differ from registration; no fallback source')
        if not verify_committed:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
        records.append(dict(path=spec['path'],url=spec['url'],git_blob_sha=spec['git_blob_sha'],
            bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),upstream_commit=p['upstream_commit']))
    old=ROOT/'data/raa.csv'
    records.append(dict(path='data/raa.csv',bytes=old.stat().st_size,sha256=sha(old),source='previously inspected original RAA benchmark'))
    result=dict(protocol_sha256=p.get('source_collection_protocol_sha256',sha(STUDY/'PROTOCOL.json')),
        registration_commit=p.get('source_collection_registration_commit',json.loads((STUDY/'registration_receipt.json').read_text())['commit']),
        license='Bundled upstream data from MPL-2.0 repository; unmodified source files; data/LICENSE-MPL-2.0.txt and data/predictive_reserving/NOTICE.md retained.',
        files=records)
    if verify_committed:
        if result!=json.loads((STUDY/'source_receipt.json').read_text()): raise ValueError('Source receipt differs')
    else:
        if (STUDY/'source_receipt.json').exists(): raise ValueError('Refuse receipt overwrite')
        json_write(STUDY/'source_receipt.json',result)
    print('SOURCE_VERIFIED '+str(len(records))+' exact files')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--verify-committed',action='store_true')
    collect(ap.parse_args().verify_committed)
