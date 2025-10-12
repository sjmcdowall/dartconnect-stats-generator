# Session Notes - October 12, 2025

## Individual PDF Report - Major Improvements

### Overview
Completed full implementation of Individual PDF report matching the sample format with dynamic data extraction, proper gender filtering, automatic week calculation, and real-time achievement tracking.

---

## Key Features Implemented

### 1. **Page Break Between Divisions**
- Added `PageBreak()` between Winston and Salem divisions
- Each division now appears on its own page for better readability

### 2. **Gender-Based Filtering**
- Fixed player statistics to properly filter by gender using `M/F` column
- Women stats show only female players (M/F = 'F')
- Men stats show only male players (M/F = 'M')
- Handles empty/null gender values gracefully

### 3. **Season Configuration**
Updated `config.yaml` with season metadata:
```yaml
season:
  number: '74th'
  name: 'Fall/Winter 2025'
```
- Easy to update for new seasons
- No need to edit code

### 4. **Automatic Week Number Calculation**
- Automatically detects season start from first match date in CSV
- Calculates current week: `(days_between_first_and_last / 7) + 1`
- No manual configuration needed
- Works with the processed `game_date` column (datetime format)

**Example:**
- First match: August 24, 2025 → Week 1
- Last match: September 21, 2025 → Week 5
- Calculation: 28 days ÷ 7 + 1 = Week 5

### 5. **Dynamic Special Quality Point Register**
Extracts real achievements from data:

**501 Achievements:**
- **180s** - Perfect turn (Hi Turn = 180)
- **Highest Out** - Highest double-out per division (DO column)

**Cricket Achievements (from enhanced data):**
- **6B** - 6 or more bulls in one turn
- **9H** - 9 or more marks in one turn

**Format:**
- Player names shown as first name only
- Count shown if multiple: e.g., "Mike(3)" means Mike had 3 of that achievement
- Alphabetically sorted

**Implementation:**
- `_extract_special_achievements()` - Scans raw data and enhanced Cricket data
- `_format_name()` - Formats names with counts
- `_format_name_simple()` - First name only for single achievements

---

## Code Changes

### `src/pdf_generator.py`

#### Modified Methods:
1. **`generate_individual_report()`**
   - Added season config reading
   - Added automatic week calculation
   - Added page break between divisions
   - Stores both enhanced_data and raw_data for achievement extraction

2. **`_extract_player_stats()`**
   - Fixed gender filtering using 'M/F' column
   - Properly separates male and female players

3. **`_calculate_week_number()`**
   - Completely rewritten to auto-detect season start
   - Uses `game_date` column (datetime format)
   - Calculates from first to last match date
   - Returns week number based on 7-day intervals

4. **`_create_special_qp_register()`**
   - Replaced hardcoded data with dynamic extraction
   - Calls `_extract_special_achievements()`
   - Formats achievements with player names and counts

#### New Methods:
1. **`_extract_special_achievements(division)`**
   - Extracts 180s from 501 games (Hi Turn column)
   - Finds highest out per division (DO column)
   - Scans Cricket enhanced data for 6B and 9H
   - Returns dict with all achievements

2. **`_format_name(full_name, count)`**
   - Formats player name with count: "Mike(3)"
   - Used for achievements with multiple occurrences

3. **`_format_name_simple(full_name)`**
   - Returns first name only
   - Used for single achievements like highest out

### `config.yaml`
```yaml
season:
  number: '74th'
  name: 'Fall/Winter 2025'
  # Note: Week number is automatically calculated from match dates
```

### `test_individual_with_real_data.py`
New test script for Individual PDF generation with real CSV data.

---

## Data Flow for Achievements

### 180s and Highest Outs (from CSV):
1. Filter raw_data by division
2. Filter 501 games: `game_name == '501 SIDO'`
3. Find 180s: `Hi Turn == 180`
4. Find highest out: `max(DO)` where DO > 0

### 6 Bulls and 9 Hits (from Enhanced Data):
1. Access `enhanced_data['cricket_qp_data']`
2. For each game, iterate through players
3. For each player's turns in `turn_data`:
   - Check `bulls >= 6` for 6B
   - Check `marks >= 9` for 9H
4. Cross-reference with division using raw_data

---

## Current Season Info
- **Season:** 74th Season - Fall/Winter 2025
- **Data Range:** Week 5 (August 24 - September 21, 2025)
- **Divisions:** Winston, Salem
- **Players:** 109 total

---

## Known Data Issues

### Bryan Windham Gender Classification
- CSV shows M/F = 'F' but player is actually male
- Likely fixed in DartConnect after export
- System correctly displays what CSV contains
- Will be resolved with fresh export

---

## Testing

### Test Script: `test_individual_with_real_data.py`
```bash
python3 test_individual_with_real_data.py
```

**Output:**
- Processes CSV data
- Generates Individual PDF in `output/` directory
- Automatically opens PDF for review

---

## Next Steps

1. **Get Fresh Export** - Download new CSV from DartConnect with corrected gender data
2. **Verify Achievements** - Review Special QP Register matches actual achievements
3. **Test with New Data** - Run test script with updated export
4. **Production Ready** - System is ready for regular season reporting

---

## Technical Notes

### Column Names After Processing:
- CSV `Date` column → `game_date` (datetime64[ns])
- CSV `M/F` column → `M/F` (unchanged)
- Player name in `player_name` column

### Achievement Thresholds:
- **180:** Exactly 180 in Hi Turn
- **High Out:** Any DO > 0, take max
- **6B:** Bulls >= 6 in single turn
- **9H:** Marks >= 9 in single turn

### Performance:
- Processes ~1600 rows in < 2 seconds
- Generates PDF with all calculations in < 1 second
- Total execution time: ~3 seconds
