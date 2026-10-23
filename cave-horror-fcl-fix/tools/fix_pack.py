#!/usr/bin/env python3
"""Prepare a CurseForge export for FCL Android or clean up an existing instance."""
import argparse
import datetime
import json
import pathlib
import shutil
import zipfile

EXCLUDE = {908741, 581495, 915902, 1507336, 416089, 686911}
JAR_PREFIXES = ('embeddium-', 'oculus-', 'euphoriapatcher-', 'bandwidthoptimizer-', 'voicechat-forge-', 'immediatelyfast-')
CONFIG_PREFIXES = ('embeddium-', 'oculus.', 'euphoria_patcher', 'bandwidthoptimizer-', 'voicechat', 'immediatelyfast.')

def excluded_config(name):
    if not name.lower().startswith('overrides/config/'):
        return False
    relative=name[len('overrides/config/'):].lower()
    return relative.startswith(CONFIG_PREFIXES)

def fix_archive(source, target):
    with zipfile.ZipFile(source, 'r') as zin, zipfile.ZipFile(target, 'w') as zout:
        manifest=json.loads(zin.read('manifest.json'))
        original=len(manifest['files'])
        manifest['files']=[f for f in manifest['files'] if f['projectID'] not in EXCLUDE]
        removed=original-len(manifest['files'])
        if removed!=len(EXCLUDE):
            raise ValueError(f'Expected six removals, got {removed}; check your source pack.')
        manifest['name']+=' - FCL Android workaround'
        manifest['version']=str(manifest.get('version','1'))+'-FCL-Android-Fix'
        for item in zin.infolist():
            if item.filename=='manifest.json':
                zout.writestr(item,json.dumps(manifest,ensure_ascii=False,indent=2).encode())
            elif not excluded_config(item.filename):
                zout.writestr(item,zin.read(item.filename))
    print(f'Created {target} with {len(manifest["files"])} CurseForge file entries')

def fix_instance(path):
    root=pathlib.Path(path)
    mods=root/'mods'
    if not mods.is_dir():
        raise ValueError(f'Cannot locate mods directory: {mods}')
    for file in mods.iterdir():
        if file.is_file() and file.suffix.lower()=='.jar' and file.name.lower().startswith(JAR_PREFIXES):
            destination=file.with_name(file.name+'.disabled')
            if destination.exists():
                print('Already disabled:',file.name);continue
            file.rename(destination)
            print('Disabled:',file.name)
    config=root/'config'
    if config.is_dir():
        backup=root/('fcl-android-fix-backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))/'config'
        for file in config.iterdir():
            if file.name.lower().startswith(CONFIG_PREFIXES):
                backup.mkdir(parents=True,exist_ok=True)
                shutil.move(str(file),str(backup/file.name))
                print('Backed up config:',file.name)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',nargs='?')
    p.add_argument('target',nargs='?')
    p.add_argument('--instance',help='Existing installed Minecraft instance directory')
    a=p.parse_args()
    if a.instance:
        fix_instance(a.instance)
    elif a.source and a.target:
        fix_archive(a.source,a.target)
    else:
        p.error('Supply SOURCE_ZIP OUTPUT_ZIP or --instance PATH')
