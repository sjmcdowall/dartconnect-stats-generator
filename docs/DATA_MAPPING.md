# Data Mapping - DartConnect Exports to Reports

## Overview
This document maps the DartConnect export data fields to the required report outputs and explains how Quality Points (QPs) can be calculated.

---

## DartConnect Export Files

### File 1 (PRIMARY): `By_Leg_export.csv` ⭐ 
**This is the main file we'll use for report generation!**

Contains leg-by-leg detail for every leg played in the season. Each row = one leg.

**Critical Fields:**
- `PF` - **Player Format**: `S` (Singles) or `D` (Doubles)
- `Game Name` - Game type: `"501 SIDO"` or `"Cricket"`
- `Win` - Leg result: `W` (won) or `L` (lost)
- `Division` - Winston or Salem
- `Date` - When the leg was played
- `Set #`, `Game #` - Position within match
- `Hi Turn` - Highest score in one turn (for 501 QP calculation)
- `DO` - Dart Out / Checkout score (for 501 QP calculation)
- `Pts/Marks` - Points (501) or Marks (Cricket)
- `Report Link` - URL to throw-by-throw detail

**Game Type Identification:**
- `PF=S` + `Game Name=501 SIDO` = **Singles 501 (S01)**
- `PF=S` + `Game Name=Cricket` = **Singles Cricket (SC)**
- `PF=D` + `Game Name=501 SIDO` = **Doubles 501 (D01)**
- `PF=D` + `Game Name=Cricket` = **Doubles Cricket (DC)**

### File 2 (SUPPLEMENTARY): `all_01_leaderboard.csv` (501 Games)
Contains aggregated statistics for all 01/501 games played. Useful for validation and QP calculations.

### File 3 (SUPPLEMENTARY): `all_cricket_leaderboard.csv` (Cricket Games)  
Contains aggregated statistics for all Cricket games played. Useful for validation and QP calculations.

---

## Key Field Mapping

### Player Identification Fields
| DartConnect Field | Description | Used In Reports |
|-------------------|-------------|-----------------|
| `Last`, `First` | Player name | Both Overall & Individual |
| `Gender` | M/F | Individual (separating rankings) |
| `Team` | Team name | Overall (team grouping) |
| `Division` | Winston/Salem | Both (division separation) |

### Game Statistics Fields
| DartConnect Field | Description | Report Usage |
|-------------------|-------------|--------------|
| `Matches` | Number of games played | Overall: "Games Played" |
| `Legs` | Total legs played | Overall: "Legs Played" |
| `LWon` | Legs won | Calculate Win% |

### 501-Specific Fields (from `all_01_leaderboard.csv`)
| Field | Description | QP Calculation Usage |
|-------|-------------|----------------------|
| `HTurn` | High Turn (highest score in one turn) | **YES - Key for QP calculation** |
| `HDO` | High Checkout (highest out shot) | **YES - Key for QP calculation** |
| `180` | Count of 180s hit | QP tracking/special achievements |
| `140+` | Count of 140+ scores | QP tracking |
| `100+` | Count of 100+ scores | QP tracking |
| `T95_113` | Turns scoring 95-113 | **Direct QP match!** (1 QP) |
| `T14_32`, `T33_51`, `T52_70`, `T71_80` | Turn score ranges | **Direct QP matches!** |
| `3DA` | 3-dart average | Individual report rankings |
| `First 9` | First 9-dart average | Statistics |

### Cricket-Specific Fields (from `all_cricket_leaderboard.csv`)
| Field | Description | QP Calculation Usage |
|-------|-------------|----------------------|
| `5M+`, `7M+` | 5 marks+, 7 marks+ counts | **YES - QP calculation** |
| `5M`, `6M`, `7M`, `8M`, `9M` | Exact mark counts | **YES - QP calculation** |
| `3B`, `4B`, `5B`, `6B` | Bulls hit (3, 4, 5, 6) | **YES - QP calculation** |
| `MPR` | Marks Per Round | Individual report rankings |
| `HT` | High Turn (marks in one turn) | QP tracking |

---

## Quality Points (QP) Calculation Strategy

### 501 Game QPs - Direct Mapping Available!

The DartConnect export includes TURN-based columns that map directly to QP rules:

| QP Value | QP Rule | DartConnect Field | Calculation |
|----------|---------|-------------------|-------------|
| 1 QP | 95-115 in one turn | `T95_113` column | Direct count |
| 1 QP | 61-84 out | Need to derive from `HDO` | Check if HDO in range |
| 2 QP | 116-131 in one turn | `T14_32` column (114-132) | Close match! |
| 2 QP | 85-106 out | Derive from checkout data | Check range |
| 3 QP | 132-147 in one turn | `T33_51` column (133-151) | Close match! |
| 3 QP | 107-128 out | Derive from checkout data | Check range |
| 4 QP | 148-163 in one turn | `T52_70` column (152-170) | Overlaps |
| 4 QP | 129-150 out | Derive from checkout data | Check range |
| 5 QP | 164-180 in one turn | `T71_80` column (171-180) | Overlaps |
| 5 QP | 151-170 out | Derive from checkout data | Check range |
| 1 QP | 2 Bulls OUT | Special case | Needs special tracking |

**Strategy for 501 QPs:**
1. Use the `T95_113`, `T14_32`, `T33_51`, `T52_70`, `T71_80` columns directly (with slight range adjustments)
2. For checkout QPs, we need more detailed data OR we estimate based on `HDO` (High Checkout)
3. The `Ton Points` column might aggregate some of this

### Cricket Game QPs - Calculation Required

Cricket QPs require combining marks + bulls:

| QP Value | QP Rule | Calculation Strategy |
|----------|---------|---------------------|
| 1 QP | 5H | Use `5M` column |
| 1 QP | 3H+1B | Need to infer combinations |
| 1 QP | 2B+2H | Need to infer combinations |
| 2 QP | 6H | Use `6M` column |
| 2 QP | 3B | Use `3B` column |
| 2 QP | 1H+3B, 3H+2B, 4H+1B | Need to infer |
| 3 QP | 7H | Use `7M` column |
| 3 QP | 4B, 1H+4B, 2H+3B, 5H+2B | Need combinations |
| 4 QP | 8H | Use `8M` column |
| 4 QP | 5B, 2H+4B, 3H+3B, 6H+1B | Need combinations |
| 5 QP | 9H | Use `9M` column |
| 5 QP | 6B, 3H+4B, 6H+2B | Need combinations |

**Strategy for Cricket QPs:**
1. Start with pure marks: use `5M`, `6M`, `7M`, `8M`, `9M` columns for base QPs
2. Use `3B`, `4B`, `5B`, `6B` columns for bull-only QPs
3. For combinations (marks + bulls), we may need to estimate or use the `5M+` and `7M+` aggregates
4. The `HT` (High Turn) column might give us the maximum and help validate

---

## Report Generation Data Flow

### Overall Report Data Requirements

**For Each Player:**
```
FROM: Both CSV files (01 + Cricket)
CALCULATE:
- Legs Played = Sum(01.Legs + Cricket.Legs)
- Games Played = Sum(01.Matches + Cricket.Matches)
- Games To Qualify = 18 - Games Played
- Tournament Eligibility = IF Games Played >= 18 THEN "QUALIFIED" ELSE "INELIGIBLE"

FOR EACH GAME TYPE (S01, SC, D01, DC):
- W = Legs Won for that game type
- L = Legs - Legs Won for that game type
- (Need to separate Singles vs Doubles from export)

TOTALS:
- Total W = Sum all W across game types
- Total L = Sum all L across game types  
- Win % = (Total W / (Total W + Total L)) * 100

QUALITY POINTS:
- QPs = Calculate from turn statistics (see QP calculation above)
- QP% = (QPs / Legs Played) * 100

RATING:
- Rating = ((Total W × 2) / Total Games) + (QPs / Total Legs)
```

### Individual Report Data Requirements

**Separate by Gender and Game Type:**
- Singles - Women: Filter Gender='F', Singles games only
- Singles - Men: Filter Gender='M', Singles games only
- All Events - Women/Men: All game types combined
- Quality Points - Women/Men: QP totals

**Rankings:** Top 5 in each category, sorted by relevant metric

**Special QP Register:**
- Track 180s, high checkouts, 9-marks, bulls from export columns
- Format: "Achievement - Player Name(count)"

---

## Data Gaps & Challenges

### Known Gaps:
1. **Singles vs Doubles Separation**: The CSV doesn't explicitly separate singles from doubles games
   - May need separate exports OR derive from game patterns
   - Could use team composition to infer

2. **Exact Checkout QPs**: We have high checkout (`HDO`) but not all checkout achievements
   - May need separate detailed match data
   - Could estimate based on checkout percentage and high checkout

3. **Cricket Mark+Bull Combinations**: We have separate counts but not the specific combinations
   - May need to use aggregate columns (`5M+`, `7M+`)
   - Could be conservative and only award QPs for pure achievements

4. **Week-by-Week History**: Current exports show cumulative totals
   - Need to run export each week and calculate deltas
   - OR get match-by-match detail exports

### Recommendations:
1. **Start Simple**: Use the direct field mappings first (pure marks, pure turns)
2. **Estimate Complex QPs**: Use statistical methods for combinations
3. **Request Additional Exports**: If DartConnect can provide match-level detail, QP calculation becomes exact
4. **Manual QP Entry**: For edge cases, allow manual QP input to supplement automated calculation

---

## Game Winner Logic (CRITICAL)

Since the By_Leg export is leg-by-leg, we need to determine game winners:

### Winston Division (Best 2 out of 3)
- Group legs by: Player, Date, Opponent, Game Type (S01/SC/D01/DC)
- Use `Set #` and `Game #` to identify legs in same game
- **Game Winner**: First player to win 2 legs in that game
- Possible outcomes:
  - 2-0 (winner wins legs 1 & 2, no leg 3)
  - 2-1 (winner wins 2 of 3 legs)

### Salem Division (Best of 1)
- Each leg = one complete game
- **Game Winner**: Winner of that single leg
- Much simpler - just count W/L from each leg

### Algorithm:
```
FOR each unique match (by Date, Team, Opponent, Game Type):
  IF Division == "Winston":
    Group legs by Set# and Game#
    Count wins per player in that game
    Player with 2 wins = game winner
  ELSE IF Division == "Salem":
    Each leg with Win="W" = 1 game win
    Each leg with Win="L" = 1 game loss
```

---

## Data Processing Strategy

### Primary Source: By_Leg Export
This file gives us everything we need:
1. ✅ Singles vs Doubles separation (`PF` column)
2. ✅ Game type identification (`PF` + `Game Name`)
3. ✅ Leg-by-leg results for game winner calculation
4. ✅ Per-leg stats for QP calculation (`Hi Turn`, `DO`)
5. ✅ Week-by-week tracking (`Date` column)
6. ✅ Division info for applying correct game rules

### Supplementary: Leaderboard Files
Use for:
- Validation of aggregated statistics
- Cross-checking QP calculations
- Pre-calculated turn statistics (T95_113, etc.)

---

## Field Extraction from By_Leg Export

### For Overall Report (Per Player)

**From each leg record, extract:**
1. Player: `First Name` + `Last Name, FI` (or construct from both)
2. Team: `Team`
3. Division: `Division` (Winston or Salem)
4. Game Type: Derive from `PF` + `Game Name`
   - If `PF="S"` and `Game Name="501 SIDO"` → S01
   - If `PF="S"` and `Game Name="Cricket"` → SC  
   - If `PF="D"` and `Game Name="501 SIDO"` → D01
   - If `PF="D"` and `Game Name="Cricket"` → DC
5. Leg Result: `Win` (W or L)
6. Legs Played: Count rows for this player
7. Hi Turn: `Hi Turn` (for QP calculation)
8. Checkout: `DO` (for QP calculation)
9. Date: `Date` (for week filtering)

**Aggregate to calculate:**
- **Games Played**: Apply game winner logic, count games
- **S01 W/L**: Games won/lost in Singles 501
- **SC W/L**: Games won/lost in Singles Cricket
- **D01 W/L**: Games won/lost in Doubles 501
- **DC W/L**: Games won/lost in Doubles Cricket
- **Total W/L**: Sum of all game wins/losses
- **Win %**: (Total W / (Total W + Total L)) × 100
- **QPs**: Sum of quality points from leg data
- **QP%**: (QPs / Legs Played) × 100
- **Rating**: ((Total W × 2) / Games Played) + (QPs / Legs Played)

### For Individual Report (Rankings)

**Singles - Women:**
- Filter: `M/F="F"` AND `PF="S"`
- Count game wins/losses (applying division rules)
- Rank by Win%

**Singles - Men:**
- Filter: `M/F="M"` AND `PF="S"`  
- Count game wins/losses (applying division rules)
- Rank by Win%

**All Events:**
- No PF filter (include both Singles and Doubles)
- Count all game wins/losses
- Rank by Win%

**Quality Points:**
- Calculate QPs from `Hi Turn` and `DO` fields
- Rank by QP%

**Ratings:**
- Calculate using formula
- Rank by Rating value

**Special Achievements (QP Register):**
- Scan `Hi Turn` for 180s, high scores
- Scan `DO` for notable checkouts (122, 108, etc.)
- Count by player for display

---

## Next Steps

1. ✅ Map all fields from DartConnect to reports
2. ✅ Determine Singles vs Doubles separation - **SOLVED with PF column**
3. ✅ Match-level detail for exact QP calculation - **SOLVED with By_Leg export**
4. ✅ Week-by-week tracking - **SOLVED with Date field**
5. ⬜ Implement game winner logic (Winston 2/3 vs Salem 1/1)
6. ⬜ Build QP calculation engine from leg-level data
7. ⬜ Create data aggregation pipeline
8. ⬜ Generate test outputs with sample data
