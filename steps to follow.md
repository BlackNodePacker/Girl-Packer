# Steps to follow for release 0.2

Summary (from README):
- PySide6 GUI tool to process images/videos into Ren'Py game content.
- Core features: Photo Maker, Video Maker, Shoot Maker, Event Maker, AI Training, Pack Review, Auto-Pack (pro).
- AI stack: YOLO (detection) + CNN (classification).
- Workflows run in threads; temp/ and game/ output structure; configs in `config.yaml`.

Release goal (0.2):
- Replace the existing "Buy Me Coffee" donation button with Patreon + GitHub Sponsor icons that open donation links.
- Add a Settings panel with persistent user settings.
- Add a Theme Manager with multiple themes and the ability to add more themes later.
- Add an in-app "Report Bug / Report Error" flow that collects logs, optional user message, and uploads (or saves) a report.
- Improve GUI controls to expose useful settings for users (e.g., model thresholds, frame extraction interval, output paths).
- Update README and changelog for the release; add tests where practical.

Detailed Steps

1) Audit repository and README
- Read `README.md` and confirm architecture and features.
- Locate GUI entry points: `main.py`, `gui/main_window.py`, and panel files in `gui/`.
- Status: DONE (README inspected)

2) Branch & version
- Ensure branch `release/0.2` is created and checked out.
- Decide versioning bump location (e.g., `pyproject.toml`, `setup.py`, or a `__version__` constant).
- Status: DONE (branch created)

3) Locate donation UI element(s)
- Search `gui/` for labels/buttons that reference Buy Me Coffee, `buyme`, or similar strings.
- Identify the file(s) and widgets to change (likely `main_window.py` or a toolbar/footer panel).
- Status: TODO

4) Design donation icons & links
- Create small PNG/SVG icons for Patreon and GitHub Sponsors (or use embedded Qt resources).
- Define URLs:
  - Patreon: https://patreon.com/girlpacker
  - GitHub Sponsors: https://github.com/sponsors/your-username (replace with real handle)
- Status: TODO

5) Implement Settings panel
- Add new `gui/settings_panel.py` (or extend an existing panel) with controls:
  - App theme selector
  - Model thresholds (YOLO/CNN)
  - Frame extraction defaults (interval, blur)
  - Paths (temp, output)
  - Pro Activation (license key)
- Persist settings in `config.yaml` or `~/.girlpacker/config.yaml` (use `utils/config_loader.py` to save/load).
- Status: TODO

6) Implement Theme Manager
- Add theme loader (read `.qss` or JSON theme files in `gui/themes/`).
- Provide at least 3 themes: `light`, `dark`, `classic`.
- Integrate theme selection into Settings panel and apply at runtime.
- Status: TODO

7) Add Report Bug / Report Error feature
- Add a dialog `gui/report_bug_dialog.py` to collect a short user message and attach logs.
- Collect `logs/` latest files and optionally compress into `.zip`.
- Provide a local save and an optional upload endpoint (for now: save to `reports/` and open folder; later: integrate with GitHub Issues API or a server).
- Status: TODO

8) GUI improvements & user controls
- Expose common workflow settings in panels (`photo_maker_panel.py`, `vids_maker_panel.py`).
- Add tooltips and validation.
- Ensure heavy tasks still run in threads and UI remains responsive.
- Status: TODO

9) Tests & logging
- Add/extend tests in `tests/` for new Settings persistence and theme loading.
- Improve logging around the new features (use `tools/logger.py`).
- Status: TODO

10) Replace donation button and integrate icons
- Remove `Buy Me Coffee` references and widgets.
- Add clickable icon buttons to main toolbar or footer linking to Patreon and GitHub Sponsors.
- Status: TODO

11) Docs & release
- Update `README.md` with new features and screenshots.
- Update `CHANGELOG.md` (or `CHANGELOG` section) with 0.2 notes.
- Create PR from `release/0.2` when changes are ready.
- Status: TODO

Progress tracking
- This file will be updated after each completed step. Use the TODO list for machine-tracked statuses.

Notes / Next actions
- I will search the `gui/` folder for any donation button references and list the files next.

---
Generated on: 2025-12-29
