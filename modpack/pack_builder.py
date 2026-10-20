#!/usr/bin/env python3
"""Official-source Minecraft 1.21.1 NeoForge modpack assembler."""
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

MC = "1.21.1"
LOADER = "neoforge"
BASE = "OptimizedHomeSecurity-1.21.1-NeoForge"
API = "https://api.modrinth.com/v2"
UA = "OptimizedHomeSecurity/1.0 (+github-actions)"
PERFORMANCE = [
    ("Sodium","sodium"), ("Lithium","lithium"), ("FerriteCore","ferrite-core"),
    ("ModernFix","modernfix"), ("ImmediatelyFast","immediatelyfast"),
    ("Entity Culling","entityculling"), ("More Culling","moreculling"),
    ("Dynamic FPS","dynamic-fps"), ("Clumps","clumps")
]
CONTENT = [
    ("SecurityCraft","security-craft"),
    ("Farmer's Delight","farmers-delight"),
    ("Sophisticated Storage","sophisticated-storage"),
    ("Sophisticated Backpacks","sophisticated-backpacks"),
    ("Refurbished More Apps","refurbished-more-apps"),
]
# Official CurseForge files: fixed Minecraft 1.21.1 / NeoForge versions.
CURSE = [
    ("AllTheLeaks", 8943912, "alltheleaks-1.1.13+1.21.1-neoforge.jar"),
    ("MrCrayfish's Furniture Mod: Refurbished", 7473565, "refurbished_furniture-neoforge-1.21.1-1.0.22.jar"),
    ("Framework", 7530361, "framework-neoforge-1.21.1-0.13.11.jar"),
]
HEADERS = {"User-Agent": UA, "Accept": "*/*"}

def get(url, timeout=65):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def jsonget(path):
    return json.loads(get(API + path))

def version_for(project):
    q = urllib.parse.urlencode({
        "game_versions": json.dumps([MC]),
        "loaders": json.dumps([LOADER]),
    })
    versions = jsonget("/project/" + urllib.parse.quote(project, safe="") + "/version?" + q)
    versions = [v for v in versions if v.get("version_type") == "release" and
                MC in v.get("game_versions", []) and LOADER in v.get("loaders", [])]
    if not versions:
        raise RuntimeError("No NeoForge 1.21.1 release available for " + project)
    return sorted(versions, key=lambda v: v.get("date_published", ""), reverse=True)[0]

def sha(path, name):
    digest = hashlib.new(name)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()

def ismod(path):
    try:
        with ZipFile(path) as z:
            n = z.namelist()
            return any(t in n for t in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"))
    except Exception:
        return False

def dl(url, dest, hashes=None, expected_size=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(".tmp")
    if temp.exists():
        temp.unlink()
    data = get(url, timeout=120)
    if len(data) > 250 * 1024 * 1024:
        raise RuntimeError("Refusing unusually big JAR")
    temp.write_bytes(data)
    if expected_size is not None and len(data) != expected_size:
        raise RuntimeError("Incorrect file length: " + dest.name)
    for algorithm, expected in (hashes or {}).items():
        if algorithm in ("sha1","sha512") and sha(temp, algorithm).lower() != expected.lower():
            raise RuntimeError("Checksum mismatch: " + dest.name)
    if not ismod(temp):
        raise RuntimeError("Not a NeoForge mod jar: " + dest.name)
    temp.replace(dest)

def neoforge():
    try:
        tree = ET.fromstring(get("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"))
        vs = [v.text for v in tree.findall("./versioning/versions/version") if v.text]
        vs = [v for v in vs if re.fullmatch(r"21\.1\.\d+", v)]
        return max(vs, key=lambda v: int(v.split(".")[-1]))
    except Exception:
        return "21.1.214"

def build():
    out = Path("output")
    mods = out / "mods"
    mods.mkdir(parents=True, exist_ok=True)
    chosen = {}
    pending = [(label, slug, "performance" if (label,slug) in PERFORMANCE else "gameplay", None)
               for label,slug in PERFORMANCE + CONTENT]
    clientonly = set()
    while pending:
        label, slug, group, pinned = pending.pop(0)
        v = jsonget("/version/" + pinned) if pinned else version_for(slug)
        if MC not in v.get("game_versions", []) or LOADER not in v.get("loaders", []):
            v = version_for(v.get("project_id", slug))
        pid = v["project_id"]
        if pid in chosen:
            continue
        chosen[pid] = (label, group, v)
        if slug in ("sodium","immediatelyfast","entityculling","moreculling","dynamic-fps"):
            clientonly.add(pid)
        print("MODRINTH:", label, v["version_number"], flush=True)
        for dep in v.get("dependencies", []):
            if dep.get("dependency_type") != "required":
                continue
            did = dep.get("project_id")
            dversion = dep.get("version_id")
            if not did and dversion:
                did = jsonget("/version/" + dversion)["project_id"]
            if did and did not in chosen and not any(row[1] == did for row in pending):
                pending.append(("Dependency for " + label, did, "dependency", dversion))
    indexfiles = []
    manifest = []
    for pid, (label, group, version) in chosen.items():
        files = [f for f in version["files"] if f["filename"].endswith(".jar")]
        if not files:
            raise RuntimeError("No JAR for " + label)
        file = next((f for f in files if f.get("primary")), files[0])
        name = file["filename"]
        if Path(name).name != name or not name.endswith(".jar"):
            raise RuntimeError("Unsafe mod filename")
        hashes = {k:v for k,v in file["hashes"].items() if k in ("sha1","sha512")}
        if not hashes:
            raise RuntimeError("No checksum for " + name)
        path = mods / name
        dl(file["url"], path, hashes, file.get("size"))
        env = {"client":"required","server":"unsupported"} if pid in clientonly else {
            "client":"required","server":"required"
        }
        indexfiles.append({"path":"mods/"+name,"hashes":hashes,
                           "env":env,"downloads":[file["url"]],"fileSize":path.stat().st_size})
        manifest.append({"name":label,"version":version["version_number"],"category":group,
                         "source":"Modrinth"})
    embedded = []
    for label, fid, name in CURSE:
        path = mods / name
        folder = str(fid)[:-3] + "/" + str(fid)[-3:]
        errors = []
        for cdn in ("mediafilez.forgecdn.net","edge.forgecdn.net","media.forgecdn.net"):
            try:
                dl("https://" + cdn + "/files/" + folder + "/" + urllib.parse.quote(name), path)
                break
            except Exception as exc:
                errors.append(str(exc))
        if not ismod(path):
            raise RuntimeError("Failed to download " + label + " from official CurseForge CDN. "+
                               "https://www.curseforge.com/minecraft/mc-mods/"+
                               {"AllTheLeaks":"alltheleaks","MrCrayfish's Furniture Mod: Refurbished":"refurbished-furniture","Framework":"framework"}[label]+
                               "/files/"+str(fid)+" | attempts="+str(errors))
        embedded.append(path)
        manifest.append({"name":label,"version":str(fid),"category":
                         "performance" if label == "AllTheLeaks" else "dependency" if label == "Framework" else "gameplay",
                         "source":"CurseForge"})
    if sum(1 for x in manifest if x["category"]=="performance") != 10:
        raise RuntimeError("Incorrect optimization mod count")
    idx = {
        "formatVersion":1,"game":"minecraft","versionId":"1.0.0",
        "name":"Optimized Home & Security","summary":"10 performance mods, SecurityCraft, Farmer's Delight, Sophisticated Storage/Backpacks and Refurbished Furniture with More Apps.",
        "files":indexfiles,
        "dependencies":{"minecraft":MC,"neoforge":neoforge()},
    }
    with ZipFile(out / (BASE+".mrpack"), "w", ZIP_DEFLATED) as z:
        z.writestr("modrinth.index.json",json.dumps(idx, indent=2))
        for p in embedded:
            z.write(p, "overrides/mods/"+p.name)
    with ZipFile(out / (BASE+"-mods.zip"),"w",ZIP_DEFLATED) as z:
        for p in mods.glob("*.jar"):
            z.write(p,"mods/"+p.name)
    (out/"installed-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("BUILT:", BASE+".mrpack, "+BASE+"-mods.zip", flush=True)

if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print("BUILD FAILED:",str(exc), file=sys.stderr)
        sys.exit(1)
