#!/usr/bin/env python3
"""Non-destructive dependency-safe workaround for Embeddium's FCL fullscreen slider crash."""
import argparse
import json
import pathlib
import zipfile

EXTRA_ID = 654373
EXTRA_FILE = 6101745
REQUIRED_EXISTING = {908741: "Embeddium", 581495: "Oculus", 915902: "Euphoria Patcher"}

def fix_pack(source: pathlib.Path, output: pathlib.Path):
    if source.resolve() == output.resolve():
        raise ValueError("Output must not overwrite the original export")
    with zipfile.ZipFile(source) as original:
        manifest = json.loads(original.read("manifest.json"))
        if manifest.get("manifestType") != "minecraftModpack":
            raise ValueError("Source must be a CurseForge Minecraft modpack export")
        projects = {e["projectID"] for e in manifest["files"]}
        missing = [name for project_id, name in REQUIRED_EXISTING.items() if project_id not in projects]
        if missing:
            raise ValueError("Use the ORIGINAL Cave Horror export, missing: " + ", ".join(missing))
        existing_extra = [e for e in manifest["files"] if e["projectID"] == EXTRA_ID]
        if existing_extra:
            if existing_extra[0]["fileID"] != EXTRA_FILE:
                raise ValueError("Rubidium Extra already listed with a different version; check compatibility first")
            print("Already contains the intended Rubidium Extra version.")
        else:
            manifest["files"].append({"projectID": EXTRA_ID, "fileID": EXTRA_FILE, "required": True})
        manifest["name"] = manifest["name"] + " - FCL Dependency Safe"
        manifest["version"] = str(manifest.get("version", "1")) + "-FCL-Dependency-Safe"
        with zipfile.ZipFile(output, "w") as rebuilt:
            for entry in original.infolist():
                if entry.filename == "manifest.json":
                    rebuilt.writestr(entry, json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"))
                else:
                    rebuilt.writestr(entry, original.read(entry.filename))
    with zipfile.ZipFile(output) as test:
        corrupt = test.testzip()
        if corrupt:
            raise RuntimeError("Corrupt archive member: " + corrupt)
    print("Created:", output, "with", len(manifest["files"]), "mod references")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original_zip", type=pathlib.Path)
    ap.add_argument("output_zip", type=pathlib.Path)
    args = ap.parse_args()
    fix_pack(args.original_zip, args.output_zip)
