#!/bin/bash
#
# Weekly Update Script - Complete DartConnect Stats Workflow
#
# Automates the entire weekly update process:
#   1. Download latest CSV export from DartConnect
#   2. Generate Individual and Overall PDF reports
#   3. Upload PDFs to Wix website (no 2FA!)
#
# Usage:
#   ./scripts/weekly-update.sh
#
# Requirements:
#   - .env file with credentials configured
#   - Python dependencies installed (pip install -r requirements.txt)
#

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory (works even if script is called from elsewhere)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo ""
echo "============================================================"
echo "  DartConnect Weekly Update Workflow"
echo "============================================================"
echo ""

# Step 0: Source .env file
echo -e "${BLUE}📝 Step 0: Loading environment variables...${NC}"
if [ -f "$PROJECT_ROOT/.env" ]; then
    # Source the .env file (which has export statements)
    source "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
else
    echo -e "${RED}❌ Error: .env file not found at $PROJECT_ROOT/.env${NC}"
    echo ""
    echo "Create .env file from .env.example:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your credentials"
    exit 1
fi
echo ""

# Step 1: Download latest CSV export
echo -e "${BLUE}📥 Step 1: Downloading latest CSV export from DartConnect...${NC}"
echo ""
cd "$PROJECT_ROOT"
if venv/bin/python scripts/fetch_exports.py --headless; then
    echo ""
    echo -e "${GREEN}✅ Step 1 Complete: CSV downloaded successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ Step 1 Failed: Could not download CSV export${NC}"
    echo ""
    echo "Possible issues:"
    echo "  - Check DARTCONNECT_EMAIL and DARTCONNECT_PASSWORD in .env"
    echo "  - Verify DartConnect credentials are correct"
    echo "  - Check internet connection"
    exit 1
fi
echo ""

# Step 2: Generate PDF reports
echo -e "${BLUE}📊 Step 2: Generating PDF reports (Individual + Overall)...${NC}"
echo ""
if venv/bin/python main_consolidated.py data/; then
    echo ""
    echo -e "${GREEN}✅ Step 2 Complete: PDFs generated successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ Step 2 Failed: Could not generate PDF reports${NC}"
    echo ""
    echo "Possible issues:"
    echo "  - Check that CSV was downloaded to data/ folder"
    echo "  - Verify Python dependencies are installed"
    echo "  - Check logs above for specific errors"
    exit 1
fi
echo ""

# Step 3: Upload to Wix
echo -e "${BLUE}🚀 Step 3: Uploading PDFs to Wix website (no 2FA required)...${NC}"
echo ""
if venv/bin/python scripts/wix_uploader.py --api-mode; then
    echo ""
    echo -e "${GREEN}✅ Step 3 Complete: PDFs uploaded and site published${NC}"
else
    echo ""
    echo -e "${RED}❌ Step 3 Failed: Could not upload PDFs to Wix${NC}"
    echo ""
    echo "Possible issues:"
    echo "  - Check WIX_API_KEY and WIX_SITE_ID in .env"
    echo "  - Verify API credentials are still valid"
    echo "  - Check internet connection"
    exit 1
fi
echo ""

# Success summary
echo "============================================================"
echo -e "${GREEN}✅ ALL STEPS COMPLETED SUCCESSFULLY!${NC}"
echo "============================================================"
echo ""
echo "Summary:"
echo "  ✓ Downloaded latest CSV from DartConnect"
echo "  ✓ Generated Individual and Overall PDF reports"
echo "  ✓ Uploaded PDFs to Wix and published site"
echo ""
echo "Your website is now live with the latest stats!"
echo ""
