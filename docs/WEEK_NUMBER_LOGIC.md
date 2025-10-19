# Week Number Calculation Logic

**Purpose**: Document how week numbers are calculated for Wix folder naming

## Summary
Week numbers are automatically calculated from match dates in the CSV data.
The first match date = Week 1, and weeks increment every 7 days.

## Implementation Location
**File**: `src/pdf_generator.py`
**Method**: `_calculate_week_number(data: Dict[str, Any]) -> int` (lines 551-582)

## Calculation Logic

```python
# 1. Extract all match dates from raw_data DataFrame
unique_dates = df['game_date'].dt.date.unique()

# 2. Sort dates to find first and most recent
sorted_dates = sorted(unique_dates)
first_match_date = sorted_dates[0]   # Season start (Week 1)
most_recent_date = sorted_dates[-1]  # Current week

# 3. Calculate days difference
days_diff = (most_recent_date - first_match_date).days

# 4. Convert to week number
week_number = (days_diff // 7) + 1  # +1 because first week is Week 1, not Week 0

return max(1, week_number)  # At least week 1
```

## Example
- First match: October 1, 2025
- Current match: October 15, 2025
- Days diff: 14 days
- Week calculation: (14 // 7) + 1 = 2 + 1 = **Week 3**

## Usage in PDFs

### PDF Headers
Week number appears in PDF headers (lines 105, 167):
```
"{season_number} Season - {season_name} - Week {week_number}"
```
Example: "74th Season - Fall/Winter 2025 - Week 8"

### PDF Filenames
Week number is NOT in filenames. Filenames use timestamps:
```
Individual-{MMDD_HHMMSS}.pdf  (e.g., Individual-1018_094513.pdf)
Overall-{MMDD_HHMMSS}.pdf     (e.g., Overall-1018_094512.pdf)
```

## For Wix Upload Automation

The Wix uploader will need to:
1. **Calculate week number** using the same logic (or extract from generated PDFs)
2. **Create folder** named "Week-{week_number:02d}" (e.g., "Week-09")
3. **Upload PDFs** (with timestamp filenames) into that folder

### Options for Getting Week Number

**Option A**: Re-use existing logic
- Import `_calculate_week_number` from `pdf_generator.py`
- Pass the same data structure

**Option B**: Extract from PDF metadata/content
- PDFs contain week number in header text
- Could extract via PDF parsing (more complex)

**Option C**: Parse from data directly in uploader
- Duplicate the simple calculation logic
- Just need access to raw_data with game_date column

**Recommendation**: Option A or C (simplest, most reliable)

## Config Reference
From `config.yaml`:
```yaml
season:
  number: '74th'
  name: 'Fall/Winter 2025'
  # Note: Week number is automatically calculated from match dates in the CSV
  # The first match date is considered Week 1
```
