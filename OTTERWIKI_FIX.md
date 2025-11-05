# OtterWiki Case Sensitivity Fix - Documentation

## Problem
OtterWiki by default converts all page names to lowercase when looking them up. Our wiki pages were generated with capitalized names (e.g., `Meeting.md`, `Access-Control.md`), causing 404 errors when accessing pages.

## Solution
Added `RETAIN_PAGE_NAME_CASE = True` to OtterWiki's settings.cfg file to preserve the original case of page names.

## How the Fix is Automatically Applied

The fix is **permanently implemented** in `scripts/otterwiki-auto-init.sh`:

```bash
# Lines 14-19
# Always ensure RETAIN_PAGE_NAME_CASE setting is present
echo "⚙️  Ensuring OtterWiki settings are correct..."
if ! grep -q "RETAIN_PAGE_NAME_CASE" /app-data/settings.cfg 2>/dev/null; then
    echo "RETAIN_PAGE_NAME_CASE = True" >> /app-data/settings.cfg
    echo "✓ Added RETAIN_PAGE_NAME_CASE setting"
fi
```

This script:
- Runs automatically on **every startup** via the `otterwiki-init` container
- Checks if the setting exists in `/app-data/settings.cfg`
- Adds it if missing
- Runs **before** checking if pages exist, so it works for both fresh installs and existing setups

## Scenarios Where Fix is Guaranteed to Work

### ✅ Tested and Confirmed Scenarios:

1. **Normal Container Restart**
   ```bash
   docker-compose restart otterwiki
   ```
   - Settings file persists in volume
   - Fix remains in place

2. **Container Recreation**
   ```bash
   docker-compose down
   docker-compose up -d
   ```
   - Settings file persists in volume
   - Fix remains in place

3. **Complete Volume Deletion**
   ```bash
   docker-compose down
   docker volume rm ai-cup-2025_otterwiki_data
   docker-compose up -d otterwiki otterwiki-init
   ```
   - **NEW VOLUME CREATED**
   - Script automatically adds the setting
   - 537 wiki pages work immediately after initialization

4. **Fresh Install**
   - Clone repository
   - Run `docker-compose up -d`
   - Script automatically adds setting during first run

5. **Settings File Deleted**
   - If someone manually deletes `/app-data/settings.cfg`
   - OtterWiki recreates it on startup
   - `otterwiki-init` container adds the fix on next run

## File Locations

- **Fix Implementation**: `scripts/otterwiki-auto-init.sh` (lines 14-19)
- **Docker Compose**: `docker-compose.yml` (line 122 mounts the script)
- **Runtime Settings**: `/app-data/settings.cfg` inside container (persisted in `otterwiki_data` volume)

## Verification Commands

### Check if setting is present:
```bash
docker exec mailbox-otterwiki cat /app-data/settings.cfg | grep RETAIN_PAGE_NAME_CASE
```

Expected output:
```
RETAIN_PAGE_NAME_CASE = True
```

### Test wiki pages:
```bash
curl -s "http://localhost:9000/Meeting" | grep -c "Meeting Confirmation Process"
```

Expected output: `3` (or higher)

### Check total pages:
```bash
docker exec -u www-data mailbox-otterwiki sh -c 'cd /app-data/repository && git ls-files "*.md" | wc -l'
```

Expected output: `537`

## Current Status

- ✅ Fix verified working after complete volume deletion
- ✅ All 537 wiki pages accessible
- ✅ Homepage accessible at http://localhost:9000/
- ✅ Script committed to repository (permanent)

## URLs to Test

- Homepage: http://localhost:9000/
- Meeting: http://localhost:9000/Meeting
- Access Control: http://localhost:9000/Access-Control
- Training Session: http://localhost:9000/Training-Session
- Project Status: http://localhost:9000/Project-Status

All pages should display full content with multiple sections and comprehensive information.
