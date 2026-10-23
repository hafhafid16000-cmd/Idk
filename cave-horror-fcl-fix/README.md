# Cave Horror Android fix — DEPENDENCY SAFE VERSION

**The initial six-mod removal approach was incomplete and can cause Forge missing-dependency errors. Do not use it as the preferred fix.**

Use [DEPENDENCY-SAFE-README.md](DEPENDENCY-SAFE-README.md) and [tools/fix_dependencies.py](tools/fix_dependencies.py) instead.

The new workflow **preserves every original mod** (195 entries) and adds Embeddium (Rubidium) Extra for Forge 1.20.1 (CurseForge project 654373, file 6101745), resulting in 196 mods. Embeddium's source code skips its broken fullscreen slider when `rubidium_extra` is detected.

This is an untested-in-FCL workaround, not a binary patch. Keep an instance backup.
