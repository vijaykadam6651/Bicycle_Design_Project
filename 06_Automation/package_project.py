"""Write a portable delivery ZIP, excluding Git history, the venv and QA scratch."""
from pathlib import Path
import csv, hashlib, json, zipfile

ROOT=Path(__file__).resolve().parents[1]
def main():
    manifest=json.loads((ROOT/'04_Reference_Data/component_manifest.json').read_text())
    with (ROOT/'04_Reference_Data/bill_of_materials.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['item','component','quantity','status','exchange_file','supplier_part_number'])
        for i,m in enumerate(manifest,1):w.writerow([i,m['name'],1,m['role'],m['step_path'],'UNSELECTED'])
    excluded={'.venv','.git','tmp','__pycache__'}
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in excluded for x in p.relative_to(ROOT).parts) and p.name!='delivery_checksums.sha256')
    hashes=[]
    for p in files:hashes.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix())
    checksum=ROOT/'04_Reference_Data/delivery_checksums.sha256'
    checksum.write_text('\n'.join(hashes)+'\n')
    archive=ROOT.with_name(ROOT.name+'_Delivery.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in [*files,checksum]:z.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)+1
    print(f'Packaged {len(files)+1} files; ZIP CRC check passed: {archive} ({archive.stat().st_size:,} bytes)')
if __name__=='__main__':main()
