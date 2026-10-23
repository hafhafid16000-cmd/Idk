# Cave Horror FCL — dependency-safe fix (recommended)

**Minecraft 1.20.1 · Forge 47.4.23 · FCL Android**

## Why the earlier fix was incomplete

The first workaround removed Embeddium, Oculus, Euphoria Patcher, BandwidthOptimizer, Simple Voice Chat and ImmediatelyFast. That can break dependencies and change expected gameplay features. Do **not** use that version when Forge reports missing mods.

The identified crash is a bad fullscreen-resolution slider range inside `Embeddium 0.3.31` when the Android launcher exposes no useful resolution modes.

**Key upstream evidence:** `FullscreenResolutionHelper.isFullscreenResAlreadyAdded()` returns true when Forge loads `rubidium_extra` or `embeddium_extra`; `EmbeddiumGameOptionPages` only creates its own fullscreen slider if that function returns false.

Source: [Embeddium FullscreenResolutionHelper.java](https://github.com/FiniteReality/embeddium/blob/aa6657df4eaea8bdfa6243233c893207f5b7f8b4/src/main/java/org/embeddedt/embeddium/impl/gui/options/FullscreenResolutionHelper.java).

## Minimal workaround with no removed mods

Keep all **195** existing mods and add:

- **Embeddium (Rubidium) Extra** `rubidium-extra-0.5.4.4+mc1.20.1-build.131.jar`
- CurseForge project ID **654373**, file ID **6101745**: https://www.curseforge.com/minecraft/mc-mods/rubidium-extra/files/6101745

This mod itself **requires Embeddium**, which the original pack already contains. It is compatible with Forge 1.20.1 according to the CurseForge file listing.

To generate a fresh **196-entry CurseForge export** from the original archive:

```bash
python cave-horror-fcl-fix/tools/fix_dependencies.py "Cave Horror Project 1.zip" "Cave-Horror-FCL-Dependency-Safe-FIX.zip"
```

No files in `overrides/` are removed or changed. Only the manifest changes.

## FCL already has Minecraft installed?

1. **Back up your world and instance.**
2. If you used the earlier removal workaround, re-enable the disabled Embeddium, Oculus and any other original mods (remove `.disabled` from their original JAR filenames). Restore config backups as needed.
3. Download the **Forge 1.20.1** Rubidium Extra JAR linked above and place it into that exact instance's `mods/` folder.
4. Launch and test the Video Settings menu, then test loading a world.
5. If missing-mod or crash messages remain, share the **new** `latest.log`. Check the **exact mod ID and version range** mentioned before making another change.

## Limitations

This is a targeted workaround derived from Embeddium's code, **not a patched Embeddium binary**. Rubidium Extra might introduce its own issue on FCL or show its own resolution settings. The modpack hasn't been launched on the target Samsung device. Native audio/JNI warnings from BandwidthOptimizer and Simple Voice Chat are not resolved by this fix and can require separate, dependency-aware troubleshooting. The importable CurseForge ZIP references downloaded mod files and does not include their actual JARs.

Previous destructive workaround and script are retained under `tools/fix_pack.py` only for historical reference; **use `tools/fix_dependencies.py` instead**.
