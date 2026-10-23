# Cave Horror Project 1 — FCL Android workaround

For Minecraft 1.20.1, Forge 47.4.23 and Fold Craft Launcher on Android.

The October 23 [crash log](https://mclo.gs/zQO1x4u) implicates Embeddium 0.3.31 Video Settings, where `FullscreenResolutionHelper` creates an invalid range for a slider. Resetting Embeddium's JSON options cannot fix the code-level problem.

## Fix

Use the supplied `tools/fix_pack.py` on the **original CurseForge export** to write a new importable ZIP:

```bash
python tools/fix_pack.py "Cave Horror Project 1.zip" "Cave-Horror-FCL-Android-FIXED.zip"
```

It removes these six CurseForge entries by project ID:

| Mod | Project ID | Reason |
| --- | --- | --- |
| Embeddium | 908741 | Crashes on FCL resolution slider |
| Oculus | 581495 | Shader stack requires compatible Embeddium renderer |
| Euphoria Patcher | 915902 | Shader add-on no longer useful without Oculus |
| BandwidthOptimizer | 1507336 | zstd native library fails on Android |
| Simple Voice Chat | 416089 | Audio native library fails on Android |
| ImmediatelyFast | 686911 | Log shows Minecraft 1.20.4 build in 1.20.1 instance |

Related configuration files are skipped while all other overrides are copied byte-for-byte. Preserves the original archive, gameplay mods and configs not implicated above.

## Existing FCL instance

Changing a manifest does **not uninstall JARs** already downloaded and installed.

Use `python tools/fix_pack.py --instance /path/to/instance` to rename matching JARs from `.jar` to `.jar.disabled`. It also backs up affected configuration files. You can also do those changes manually in Android's file manager. **Back up your worlds first.**

Caveats: shader support is disabled; a multiplayer server may require matching BandwidthOptimizer or voice-chat configurations. Android/FCL loading has not been tested in this repository, so a subsequent crash log may reveal additional incompatibilities.