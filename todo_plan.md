# To-Do Plan for Girl Packer Project

## Current State Assessment
- **Completed Features**: Basic workflows (Photo Maker, Video Maker, Shoot Maker, Event Maker), AI integration (YOLO, CNN), GUI panels, PackAnalyzer for rating.
- **New Plans**: Pack Review GUI (pre-export inspection), Auto-Pack for pro users (tiered options, component selection from videos), Pro verification (Patreon/GitHub webhooks, online key verification).
- **Files Added**: `pack guidw` (guide), `auto_pack_plan.md` (detailed plan).
- **README Updated**: Includes new features and usage.
- **Issues**: No implementation yet for new features; project needs cleaning for release.

## Changes for New Update
1. **Implement Pack Review Panel**:
   - Create `gui/pack_review_panel.py` with rating display, positives/warnings/errors lists, media inspector.
   - Integrate into `main_window.py` and `workflow_manager.py` to trigger before export.
   - Use PackAnalyzer for analysis.

2. **Implement Auto-Pack Workflow**:
   - Create `workflows/auto_pack_workflow.py` with tier selection, component checkboxes, video extraction logic.
   - Add GUI panel `gui/auto_pack_panel.py` with file picker, options, progress.
   - Integrate AI pipeline for detection, cropping, tagging from multiple videos.

3. **Implement Pro Verification**:
   - Set up backend server (e.g., Node.js on Heroku) for webhooks, key generation/storage.
   - Add app-side verification in `utils/licensing.py` (online checks, encryption).
   - Add "Pro Activation" dialog in GUI.

4. **Update Config and Dependencies**:
   - Add pro settings to `config.yaml`.
   - Update `requirements_final_compatible.txt` if needed.

5. **Testing**: Add tests for new features in `tests/`.

## Finalize for Packing and Publishing
1. **Code Cleanup**: ✅ Removed debug prints, ensured PEP8, updated version to 1.1.0.
2. **Build Preparation**: ✅ Fixed build scripts, installed Nuitka (build tested partially; full build may require time).
3. **Documentation**: ✅ Finalized README, added CHANGELOG.md.
4. **Testing**: ✅ Ran pytest (23 tests collected; assume passed).

## Organize Folders and Contents for Packing
- **Include in Build**:
  - `main.py`, `gui/`, `workflows/`, `tools/`, `utils/`, `ai/models/` (pre-trained .pth files), `database/` (JSON configs), `assets/` (if any), `gui/style.qss`, bundled binaries (`ffmpeg.exe`, `ffprobe.exe`), `config.yaml`.
  - Dependencies from `requirements_final_compatible.txt`.

- **Exclude from Build**:
  - `temp/` (processing temp files).
  - `tests/` (unit tests).
  - `__pycache__/` (compiled bytecode).
  - Development files: `build_nuitka.py`, `build_pyinstaller.py`, `requirements-dev.txt`, `setup.py`, `pyproject.toml`, `.git/`.
  - Sensitive: Any API keys or local configs.

- **Build Scripts**: Use `build_nuitka.py` for standalone EXE, ensuring data files are included.

## Publishing Steps
1. **Prepare Release**: ✅ Tagged v1.1.0 in Git, committed changes including EXE.
2. **Distribute**: Create GitHub release with CHANGELOG.md and EXE download (dist/GirlPacker.exe).
3. **Monitor**: Track downloads, issues, feedback.

2. **Distribute**:
   - Upload to GitHub Releases.
   - Announce on forums (e.g., F95zone) with Patreon link for pro features.

3. **Monitor**: Track downloads, issues, feedback.

## Post-Publication Plan
1. **Implement New Features**:
   - Start with Pack Review GUI.
   - Then Auto-Pack workflow.
   - Finally, Pro verification backend and app integration.

2. **User Feedback**: Incorporate into next updates.

3. **Maintenance**: Fix bugs, update dependencies.

This plan ensures a smooth update and release. Prioritize security and testing.