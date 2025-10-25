#!/usr/bin/env python3
"""
Download script to fetch the fine-tuned model checkpoint from Google Drive
"""
import os
import sys
import subprocess
from pathlib import Path

# Google Drive folder link
FOLDER_URL = "https://drive.google.com/drive/folders/1U6bun6U2DgtNej0lc-Suw_sw4EqPLX6W?usp=sharing"
FOLDER_ID = "1U6bun6U2DgtNej0lc-Suw_sw4EqPLX6W"
MODEL_DIR = Path("models")
CHECKPOINT_FILE = MODEL_DIR / "checkpoint.pt"

def download_with_gdown():
    """Download using gdown library"""
    try:
        import gdown

        print(f"Checking for model checkpoint at {CHECKPOINT_FILE}...")

        if CHECKPOINT_FILE.exists():
            print(f"✓ Model checkpoint already exists at {CHECKPOINT_FILE}")
            file_size = CHECKPOINT_FILE.stat().st_size / (1024 * 1024)  # MB
            print(f"  File size: {file_size:.2f} MB")
            return True

        print("Model checkpoint not found. Downloading from Google Drive...")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        print(f"Downloading from: {FOLDER_URL}")
        print(f"Target directory: {MODEL_DIR}")

        # Download the entire folder
        gdown.download_folder(
            url=FOLDER_URL,
            output=str(MODEL_DIR),
            quiet=False,
            use_cookies=False,
            remaining_ok=True
        )

        # Check if checkpoint.pt was downloaded
        if CHECKPOINT_FILE.exists():
            file_size = CHECKPOINT_FILE.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ Successfully downloaded checkpoint to {CHECKPOINT_FILE}")
            print(f"  File size: {file_size:.2f} MB")
            return True
        else:
            # Sometimes the file might be in a subdirectory
            checkpoint_files = list(MODEL_DIR.rglob("*.pt"))
            if checkpoint_files:
                # Move the first found checkpoint to the expected location
                source_file = checkpoint_files[0]
                print(f"Found checkpoint at {source_file}, moving to {CHECKPOINT_FILE}")
                source_file.rename(CHECKPOINT_FILE)
                file_size = CHECKPOINT_FILE.stat().st_size / (1024 * 1024)  # MB
                print(f"✓ Successfully moved checkpoint to {CHECKPOINT_FILE}")
                print(f"  File size: {file_size:.2f} MB")
                return True
            else:
                print("✗ Error: checkpoint.pt not found after download")
                return False

    except Exception as e:
        print(f"✗ Error downloading with gdown: {e}")
        return False

def download_with_wget():
    """Alternative download using wget (if available)"""
    try:
        print("Attempting download using wget...")

        # Try direct file download if we know the file ID
        # This is a fallback method
        download_url = f"https://drive.google.com/uc?export=download&id={FOLDER_ID}"

        cmd = [
            "wget",
            "--no-check-certificate",
            "--load-cookies", "/tmp/cookies.txt",
            f"https://docs.google.com/uc?export=download&confirm=1&id={FOLDER_ID}",
            "-O", str(CHECKPOINT_FILE)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and CHECKPOINT_FILE.exists():
            file_size = CHECKPOINT_FILE.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ Successfully downloaded checkpoint using wget")
            print(f"  File size: {file_size:.2f} MB")
            return True
        else:
            print(f"✗ wget download failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ Error downloading with wget: {e}")
        return False

def main():
    print("=" * 60)
    print("Fine-tuned Model Checkpoint Downloader")
    print("=" * 60)

    # Try gdown first
    if download_with_gdown():
        print("\n✓ Download successful!")
        return 0

    print("\n⚠ gdown failed, manual download required")
    print("\nPlease manually download the checkpoint.pt file from:")
    print(f"  {FOLDER_URL}")
    print(f"\nAnd place it at: {CHECKPOINT_FILE.absolute()}")
    print("\nAlternatively, you can:")
    print("  1. Open the Google Drive link in your browser")
    print("  2. Download the checkpoint.pt file")
    print("  3. Copy it to the models/ directory")

    return 1

if __name__ == "__main__":
    sys.exit(main())
