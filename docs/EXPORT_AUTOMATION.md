# DartConnect Export Automation

Automated retrieval of CSV exports from DartConnect without manual downloads.

## Quick Start

### 1. Set Your Credentials (One-Time Setup)

Create a `.env` file in the project root with your DartConnect credentials:

```bash
cp .env.example .env
# Edit .env and add your credentials:
# DARTCONNECT_EMAIL=your.email@example.com
# DARTCONNECT_PASSWORD=your-password
```

**Security Note**: The `.env` file is in `.gitignore` and will **never** be committed to git.

### 2. Verify Credentials Are Set

```bash
python3 scripts/fetch_exports.py --check-creds
```

Output:
```
✅ DartConnect credentials are configured
   Email: you...com
```

### 3. Download Exports

**Standalone (recommended for testing):**
```bash
python3 scripts/fetch_exports.py
```

**With custom output directory:**
```bash
python3 scripts/fetch_exports.py --output-dir data/season74
```

**With verbose logging:**
```bash
python3 scripts/fetch_exports.py --verbose
```

**Integrated with main processing:**
```bash
python3 main_consolidated.py --download-first
```

## Setup Methods

### Method 1: .env File (Recommended for Local Development)

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```
DARTCONNECT_EMAIL=your.email@example.com
DARTCONNECT_PASSWORD=your-password
```

Then load credentials before running:
```bash
# In your shell session
source .env
python3 scripts/fetch_exports.py
```

Or use a tool like `python-dotenv` (can be added to requirements).

### Method 2: Shell Environment Variables

```bash
export DARTCONNECT_EMAIL="your.email@example.com"
export DARTCONNECT_PASSWORD="your-password"
python3 scripts/fetch_exports.py
```

### Method 3: Inline (Less Secure - Use Carefully)

```bash
DARTCONNECT_EMAIL="your.email@example.com" DARTCONNECT_PASSWORD="your-password" python3 scripts/fetch_exports.py
```

## Automation Workflows

### Weekly Report Generation with Download

```bash
#!/bin/bash
# Weekly report script

# Load credentials
export DARTCONNECT_EMAIL="your.email@example.com"
export DARTCONNECT_PASSWORD="your-password"

# Download latest exports
python3 scripts/fetch_exports.py --output-dir data/season74

# Process exports and generate reports
python3 main_consolidated.py data/season74
```

### Cron Job Setup (macOS/Linux)

Edit crontab:
```bash
crontab -e
```

Add a weekly job:
```cron
# Run every Sunday at 8 AM
0 8 * * 0 cd /path/to/dartconnect-stats-generator && source .env && python3 scripts/fetch_exports.py && python3 main_consolidated.py data
```

### Scheduled Task Setup (Windows)

Use Task Scheduler to run:
```batch
cd C:\path\to\dartconnect-stats-generator
set DARTCONNECT_EMAIL=your.email@example.com
set DARTCONNECT_PASSWORD=your-password
python3 scripts/fetch_exports.py
python3 main_consolidated.py data
```

## Usage Examples

### Example 1: One-Time Export Download

```bash
# Set credentials
export DARTCONNECT_EMAIL="john@example.com"
export DARTCONNECT_PASSWORD="mypassword123"

# Download to default location (data/)
python3 scripts/fetch_exports.py

# Output:
# 🚀 Starting DartConnect export downloader
# ✅ Successfully downloaded 3 file(s):
#   • by_leg: data/Fall_Winter_2025_By_Leg_export.csv
#   • cricket_leaderboard: data/WinSSNDL_Fall_Winter_2025_all_cricket_leaderboard.csv
#   • 501_leaderboard: data/WinSSNDL_Fall_Winter_2025_all_01_leaderboard.csv
```

### Example 2: Download and Process in One Command

```bash
# Using integrated flag (when implemented)
python3 main_consolidated.py --download-first data
```

This will:
1. Check for credentials
2. Download latest exports
3. Process the data
4. Generate PDF reports

### Example 3: Automated Weekly Reports

Create `weekly_report.sh`:
```bash
#!/bin/bash
set -e  # Exit on error

PROJECT_DIR="/Users/stevemcdowall/play/projects/dartconnect-stats-generator"
cd "$PROJECT_DIR"

# Source credentials from .env
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Download exports
echo "📥 Downloading exports..."
python3 scripts/fetch_exports.py --output-dir data/season74

# Generate reports
echo "📊 Generating reports..."
python3 main_consolidated.py data/season74

echo "✅ Weekly reports ready!"
```

Make it executable:
```bash
chmod +x weekly_report.sh
./weekly_report.sh
```

## File Structure

After running `fetch_exports.py`:

```
data/
├── Fall_Winter_2025_By_Leg_export.csv
├── WinSSNDL_Fall_Winter_2025_all_cricket_leaderboard.csv
└── WinSSNDL_Fall_Winter_2025_all_01_leaderboard.csv

output/
├── Overall-1017_143000.pdf
├── Individual-1017_143000.pdf
└── processed_results.json
```

## Troubleshooting

### "DartConnect credentials not found"

**Error**:
```
❌ Configuration Error:
   DartConnect credentials not found in environment variables.
   Please set:
     export DARTCONNECT_EMAIL='your.email@example.com'
     export DARTCONNECT_PASSWORD='your-password'
```

**Solution**: Set credentials before running:
```bash
export DARTCONNECT_EMAIL="your.email@example.com"
export DARTCONNECT_PASSWORD="your-password"
python3 scripts/fetch_exports.py
```

Or use `.env` file:
```bash
cp .env.example .env
# Edit .env with your credentials
source .env
python3 scripts/fetch_exports.py
```

### "Login failed - check credentials"

**Possible causes**:
- Incorrect email or password
- DartConnect server is down
- Account is locked after too many attempts

**Solution**:
1. Verify credentials are correct
2. Log in manually to dartconnect.com to test
3. Wait 15 minutes if account was locked
4. Check if DartConnect site is accessible

### "No export links found on the page"

**Cause**: The site structure may have changed or the navigation path is different

**Solution**: 
1. Log in manually to see current page structure
2. Report issue with fresh screenshots
3. Update `_find_export_links()` in `src/export_downloader.py`

### Connection timeout

**Cause**: Network issues or DartConnect servers slow

**Solution**:
- Increase timeout: (Not yet implemented in CLI)
- Try again later
- Check internet connection

## Security Best Practices

### Do ✅

- Use `.env` file for local development
- Use environment variables for CI/CD
- Use secure credential management for production
- Rotate passwords periodically
- Use separate DartConnect account if possible

### Don't ❌

- Store credentials in code files
- Commit `.env` to git
- Share credentials over email or chat
- Use personal passwords in shared scripts
- Log credentials in output or error messages

## Implementation Status

### Current ✅
- [x] Secure credential handling via environment variables
- [x] Basic login framework
- [x] File download infrastructure
- [x] CLI tool (scripts/fetch_exports.py)
- [x] Documentation

### Pending (Next Steps) ⏳
- [ ] Page structure analysis (awaiting screenshots)
- [ ] Find export links implementation
- [ ] Download mechanism refinement
- [ ] Integration with main_consolidated.py
- [ ] Testing with real DartConnect site
- [ ] Error handling refinement

## Architecture

```
User sets credentials in .env or environment variables
                    ↓
        scripts/fetch_exports.py
                    ↓
        src/export_downloader.py (DartConnectExporter)
                    ↓
        1. Load credentials from environment
        2. Create secure session
        3. Login to DartConnect
        4. Navigate to exports page
        5. Find download links
        6. Download CSV files
        7. Save to data directory
                    ↓
        Files ready for main_consolidated.py
```

## Next Steps

1. ✅ You: Provide screenshot of post-login page
2. ✅ You: Show export menu structure
3. ✅ You: Show download confirmation
4. Developer: Update `_find_export_links()` with actual URLs
5. Developer: Test with real DartConnect site
6. You: Verify downloads work correctly
7. Developer: Integrate `--download-first` flag into main_consolidated.py

---

**Ready for screenshots of the export flow!** 📸
