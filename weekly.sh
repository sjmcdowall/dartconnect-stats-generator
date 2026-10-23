#!/bin/bash
# Weekly Statistics Update Script - Season 76 (Fall/Winter 2026)
#
# Usage:
#   ./weekly.sh           # Full workflow: download + reports + upload to Wix
#   ./weekly.sh --reports # Reports only (skip download)
#   ./weekly.sh --download # Download only (skip reports & upload)
#   ./weekly.sh --no-upload # Download + reports, skip Wix upload

set -o pipefail

# Season 76 directories
DATA_DIR="data/season76"
OUTPUT_DIR="output/season76"

# Use venv python if available
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Season 76 Weekly Update - Fall/Winter 2026"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Parse arguments
DOWNLOAD=true
REPORTS=true
UPLOAD=true

if [[ "$1" == "--reports" ]]; then
    DOWNLOAD=false
    UPLOAD=true
elif [[ "$1" == "--download" ]]; then
    REPORTS=false
    UPLOAD=false
elif [[ "$1" == "--no-upload" ]]; then
    UPLOAD=false
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    source .env
fi

# Step 1: Download latest data
if $DOWNLOAD; then
    echo -e "\n${BLUE}📥 Step 1: Downloading latest DartConnect export...${NC}"
    $PYTHON scripts/fetch_exports.py --headless -o "$DATA_DIR"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Download failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Download complete${NC}"
fi

# Step 2: Generate reports
if $REPORTS; then
    echo -e "\n${BLUE}📊 Step 2: Generating reports...${NC}"
    $PYTHON main_consolidated.py "$DATA_DIR" -o "$OUTPUT_DIR"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Report generation failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Reports generated${NC}"
fi

# Step 3: Upload to Wix
if $UPLOAD; then
    echo -e "\n${BLUE}🚀 Step 3: Uploading PDFs to Wix...${NC}"
    $PYTHON scripts/wix_uploader.py --api-mode --pdf-dir "$OUTPUT_DIR" --data-dir "$DATA_DIR"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Wix upload failed${NC}"
        echo -e "${YELLOW}Reports are still available locally in $OUTPUT_DIR${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Uploaded to Wix${NC}"
fi

# Summary
echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Weekly update complete!${NC}"
echo "   Data:    $DATA_DIR"
echo "   Reports: $OUTPUT_DIR"
if $UPLOAD; then
    echo "   Website: Published to Wix"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
