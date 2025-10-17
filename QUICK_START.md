# Quick Start Guide
## DartConnect Stats Generator

### Generate PDF Report

```bash
python3 test_overall_with_real_data.py
```

This will:
1. Process `data/season74/by_leg_export.csv`
2. Fetch and cache turn-by-turn data from DartConnect URLs
3. Calculate all statistics (W/L, QPs, Ratings)
4. Generate PDF in `output/Overall-[timestamp].pdf`
5. Automatically open the PDF

---

## What's Calculated

### Games Played
- Counts unique `(Report Link, Set #)` combinations
- Each Set/Game is best of 3 or 5 legs

### Wins/Losses
- Determined by who won majority of legs in each Set
- Calculated separately for S01, SC, D01, DC
- Total W/L = sum across all game types

### 501 QPs
From CSV columns for each leg:
- **Hi Turn** (95-180): 1-5 QPs based on range
- **DO/Checkout** (61-170): 1-5 QPs based on range
- **Additive**: Both can apply to same leg!

### Cricket QPs
From cached turn-by-turn data:
- Parse each turn's marks and bulls
- Award 1-5 QPs based on best single turn
- Rules: 5H=1QP, 6H=2QP, 7H=3QP, 8H=4QP, 9H=5QP
- Bulls and combinations also count

### Rating
```
Rating = ((Wins × 2) / Games) + (QPs / Legs)
```
- Win component: 0-2.0
- QP component: typically 0.5-2.0
- Top players: 3.0+

---

## File Locations

### Input Data
- **Primary**: `data/season74/by_leg_export.csv`
- **Cache**: `cache/dartconnect_urls/[match_id].json` (auto-generated)

### Output
- **PDF**: `output/Overall-[timestamp].pdf`
- **Logs**: Terminal output shows processing status

### Documentation
- **Session Notes**: `SESSION_2025_10_11_FIXES.md`
- **Data Info**: `DATA_SOURCE_NOTE.md`
- **This File**: `QUICK_START.md`

---

## Key Concepts

**Leg** = Single scoring unit (501 or Cricket round)  
**Game/Set** = Best of 3 or 5 legs  
**Match** = Multiple games (typically 4-5)

**Wins/Losses** = Counted at GAME level (not leg!)  
**QPs** = Earned at LEG level (summed across all legs)  
**Rating** = Combines win rate + QP rate

---

## Troubleshooting

### "No data found"
- Check CSV file path is correct
- Verify CSV has proper columns (Win, Set #, Game Name, etc.)

### "QPs seem wrong"
- 501 QPs: Check Hi Turn and DO columns have values
- Cricket QPs: Requires URL fetcher to work (needs internet)

### "Games played is 0"
- Check CSV has 'Report Link' and 'Set #' columns
- Verify data isn't empty

### "URL fetching fails"
- Check internet connection
- Verify DartConnect URLs are accessible
- Cache will be used if available from previous runs

---

## Current Status

✅ **All systems operational**
- W/L calculation: Fixed ✓
- 501 QPs: Fixed ✓
- Cricket QPs: Fixed ✓
- Rating formula: Verified ✓
- PDF generation: Working ✓

**Last verified**: October 11, 2025  
**Test data**: Fall/Winter 2025 season (1/3 complete)  
**Commit**: a020cc9
