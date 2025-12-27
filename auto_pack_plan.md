# Auto-Pack Creation Plan for Pro Users

## Overview
This plan outlines a new "Auto-Pack" feature for advanced users (pro mode) in Girl Packer. It automates the entire process of creating a girl pack from raw source media (images and videos), reducing manual effort while leveraging AI models for detection, classification, and processing. The feature will be accessible via a new "Auto-Pack" button in the main GUI, requiring a pro license or advanced settings toggle.

## Target Users
- Pro users: Those familiar with the tool who want to batch-process multiple packs or handle large datasets.
- Prerequisites: Source media folder with organized subfolders (e.g., body_images_raw, fullbody_raw, vids_raw), pre-trained AI models loaded.

## Pro User Verification and Subscription
To access the Auto-Pack feature, users must verify pro status through an automated subscription-based system. This ensures fair compensation, protects against unauthorized use, and maintains user privacy.

### Subscription Flow
- **Platforms**: Users subscribe via Patreon (e.g., patreon.com/girlpacker) or GitHub Sponsors at the repository.
- **Automation**: Upon successful subscription, webhooks from Patreon/GitHub trigger the backend server to generate and email a unique license key automatically. No manual intervention required.
- **Activation**: Users paste the key into the app's "Pro Activation" dialog and click "Activate". The app verifies online; no accounts or logins needed.
- **Requirements**: Internet connection for verification; keys are tied to subscriptions and expire accordingly.

### Backend Implementation
- **Server**: A secure backend (e.g., Node.js on AWS Lambda or Heroku) listens for webhooks from Patreon and GitHub Sponsors APIs.
- **Webhook Handling**:
  - On subscription creation/update: Generate a unique, random license key (e.g., UUID-based), store it in an encrypted database with subscription ID, status (active/canceled/expired), and optional hashed machine fingerprint.
  - On cancellation: Mark key as revoked; prevent future verifications.
- **Key Management**: Keys are stored securely (encrypted at rest); no user personal data (emails, names) is retained beyond what's necessary for webhook processing.
- **Revocation**: Admin can revoke keys via server dashboard if needed (e.g., abuse).

### App-Side Verification
- **Online-Only**: App sends encrypted requests to the server with the license key and optional hashed machine fingerprint (e.g., using CPU ID or OS info, hashed for privacy).
- **Checks**: Server responds with status (valid, invalid, expired, revoked). App caches status briefly but requires re-verification periodically.
- **Integrity**: Requests are signed/encrypted; app checks its own integrity (e.g., via code hashing) to detect tampering.
- **No Offline Mode**: Verification fails without internet; prevents cracking.

### Security and Privacy
- **Anti-Cracking**: Obfuscated code (PyArmor), rate-limited requests, encrypted communications (HTTPS/TLS), server-side validation.
- **Privacy**: No storage of personal data; hashed fingerprints are optional and non-identifying.
- **Maintenance**: Realistic setup using existing APIs; monitor for abuse and update endpoints as needed.
- **Ease of Use**: Simple paste-and-activate; automated key delivery.

### Implementation Notes
- Add a "Pro Activation" button in the GUI that opens a dialog for key entry.
- On successful verification, enable pro features; display status in settings.

## Auto Workflow Steps
1. **Input Setup**:
   - User selects a source folder containing raw media.
   - Subfolders: `body_images_raw/` (close-ups), `fullbody_raw/` (full-body shots), `vids_raw/` (video clips), `config_template.json` (optional base config).
   - Auto-detect character name from folder name or prompt user.

2. **AI-Powered Processing**:
   - **Body Images**: Use YOLO for body part detection (face, boobs, etc.), crop and resize to required dimensions, apply background removal for transparent backgrounds.
   - **Fullbody Images**: Classify outfits (bare, clothed, etc.) using CNN, resize and trim.
   - **Videos**: Extract frames, detect actions/scenes, tag videos automatically based on AI classification, generate thumbnails.
   - **Config Generation**: Auto-fill girl_config.json with detected traits (hair color, body size via AI), sensitivity defaults.

3. **Quality Checks and Adjustments**:
   - Run PackAnalyzer for rating and suggestions.
   - Allow user overrides for tags/traits if AI misclassifies.
   - Batch processing with progress bar and error logging.

4. **Output**:
   - Generate complete pack folder with all processed media and configs.
   - Optional: Auto-export to Ren'Py format or zip.

## Three Auto-Pack Options by Pack Type
Users can choose from three tiers based on the pack guide (Min, Mid, Top). Each option allows selection of components to extract from long videos or raw media. For videos, users can specify multiple long videos and check/select what to extract (bodyparts, clothing, events, photoshoots from frames, video shoots from split clips, fullbody pics).

### Option 1: Min Rated Pack (0-49 points)
- **Components**: Basic essentials only.
- **Selections**:
  - Bodyparts: Check to extract close-ups (face, boobs, pussy, ass, legs) from long videos.
  - Fullbody Pics: Check to extract full-body images from frames.
  - Videos: Check to split into basic clips (main tags like fuck_pussy, blowjob).
- **Auto-Processing**: Minimal AI usage; focus on detection and cropping.
- **Output**: 1-5 body images per type, 5-10 fullbody, 20-50 videos.

### Option 2: Mid Rated Pack (50-79 points)
- **Components**: Moderate variety with some advanced elements.
- **Selections**:
  - Bodyparts: Check for extraction.
  - Clothing: Check to generate custom clothing images from detected outfits.
  - Fullbody Pics: Check.
  - Photoshoots: Check to create from extracted frames (3-5 shoots, 10-20 photos each).
  - Video Shoots: Check to split clips into shoots (2-3 shoots, 5-10 videos each).
  - Events: Optional check for basic event generation.
- **Auto-Processing**: Use AI for classification, tagging, and config.
- **Output**: 5-10 body images per type, 10-20 fullbody, 50-100 videos, partial clothing/events.

### Option 3: Top Rated Pack (80-100 points)
- **Components**: Comprehensive with all features.
- **Selections**:
  - Bodyparts: Check.
  - Clothing: Check for full sets.
  - Fullbody Pics: Check.
  - Photoshoots: Check (6-10 shoots, 20-30 photos each).
  - Video Shoots: Check (4-6 shoots, 10-20 videos each).
  - Events: Check for 2-5 custom events.
- **Auto-Processing**: Full AI pipeline, including advanced tagging and script generation.
- **Output**: 10-15 body images per type, 20-30 fullbody, 100-200 videos, full clothing/events.

## Technical Implementation
- **New Module**: `workflows/auto_pack_workflow.py` – Inherits from base workflow, integrates with AI pipeline.
- **GUI Integration**: Add "Auto-Pack" tab/panel in main window, with file picker, tier selection, and checkboxes for components (bodyparts, clothing, events, photoshoots, video shoots, fullbody pics). Allow selection of multiple long videos for extraction.
- **Video Extraction**: Support multiple long videos; user checks what to extract from each (e.g., bodyparts from video 1, shoots from video 2).
- **Dependencies**: Ensure AI models are loaded; add fallback for manual mode.
- **Testing**: Unit tests for each step, integration tests with sample data.

## Benefits
- Saves time for large packs.
- Ensures consistency via AI.
- Pro feature to differentiate from basic usage.

## Risks and Mitigations
- AI inaccuracies: Allow manual review/override.
- Performance: Run in background threads.
- File size: Warn on large outputs.