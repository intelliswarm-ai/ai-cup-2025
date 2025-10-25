"""
Script to download the fine-tuned model checkpoint from Google Drive
"""
import os
import sys
import gdown
from pathlib import Path

# Google Drive folder ID from the shared link
# https://drive.google.com/drive/folders/1U6bun6U2DgtNej0lc-Suw_sw4EqPLX6W?usp=sharing
FOLDER_ID = "1U6bun6U2DgtNej0lc-Suw_sw4EqPLX6W"
MODEL_DIR = Path("models")
CHECKPOINT_FILE = MODEL_DIR / "checkpoint.pt"

def download_checkpoint():
    """Download the checkpoint.pt file from Google Drive folder"""
    print(f"Checking for model checkpoint at {CHECKPOINT_FILE}...")

    if CHECKPOINT_FILE.exists():
        print(f"✓ Model checkpoint already exists at {CHECKPOINT_FILE}")
        return True

    print("Model checkpoint not found. Downloading from Google Drive...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Google Drive folder URL
        folder_url = f"https://drive.google.com/drive/folders/{FOLDER_ID}"

        print(f"Downloading from: {folder_url}")
        print(f"Target directory: {MODEL_DIR}")

        # Download all files from the folder
        gdown.download_folder(
            url=folder_url,
            output=str(MODEL_DIR),
            quiet=False,
            use_cookies=False
        )

        # Check if checkpoint.pt was downloaded
        if CHECKPOINT_FILE.exists():
            print(f"✓ Successfully downloaded checkpoint to {CHECKPOINT_FILE}")
            return True
        else:
            # Sometimes the file might be in a subdirectory
            checkpoint_files = list(MODEL_DIR.rglob("checkpoint.pt"))
            if checkpoint_files:
                # Move the first found checkpoint to the expected location
                print(f"Found checkpoint at {checkpoint_files[0]}, moving to {CHECKPOINT_FILE}")
                checkpoint_files[0].rename(CHECKPOINT_FILE)
                print(f"✓ Successfully moved checkpoint to {CHECKPOINT_FILE}")
                return True
            else:
                print("✗ Error: checkpoint.pt not found after download")
                return False

    except Exception as e:
        print(f"✗ Error downloading model: {e}")
        print("\nPlease manually download the checkpoint.pt file from:")
        print(f"  {folder_url}")
        print(f"And place it at: {CHECKPOINT_FILE}")
        return False

if __name__ == "__main__":
    success = download_checkpoint()
    sys.exit(0 if success else 1)
