# Output Specification - PDF Reports

## Overview
This document specifies the exact output requirements for the two PDF reports generated from DartConnect league data.

**Report Naming Convention:**
- Overall Report: `Overall-{MMDD_HHMMSS}.pdf` (e.g., `Overall-1011_162943.pdf`)
- Individual Report: `Individual-{MMDD_HHMMSS}.pdf` (e.g., `Individual-1011_162943.pdf`)

Where `{MMDD_HHMMSS}` represents the month/day and hour/minute/second when the report was generated.

---

## Report 1: Overall Report (Team Standings & Player Details)

### Purpose
Team-by-team breakdown showing each player's cumulative performance statistics for the season.

### Document Structure

#### Header
- Title: "WEEK {week_number}" (centered, top of page)
- League name and season information

#### Organization
- Grouped by **DIVISION** (Winston Division, Salem Division)
- Within each division: Listed by **TEAM**

### Team Section Layout

**For Each Team:**

#### 1. Team Header
- Team name (bold, larger font)
- Examples: "DARK HORSE", "KBTN", "IS IT IN?", etc.

#### 2. Player Data Table

Each player row contains these columns (left to right):

| Column | Description | Data Type | Notes |
|--------|-------------|-----------|-------|
| **Player Name** | Player's name with rookie indicator | Text | `®` = 1st season, `®®` = 2nd season |
| **Legs Played** | Total legs played this season | Number | Sum of all legs across all game types |
| **Games Played** | Total games played | Number | Must play 18 to qualify |
| **Games To Qualify** | Games remaining to reach 18 | Number | `18 - Games Played`, 0 if qualified |
| **Tournament Eligibility** | Qualification status | Text | "QUALIFIED" (green) or "INELIGIBLE" (red) |
| **S01 - W** | Singles 501 Wins | Number | Cumulative season wins |
| **S01 - L** | Singles 501 Losses | Number | Cumulative season losses |
| **SC - W** | Singles Cricket Wins | Number | Cumulative season wins |
| **SC - L** | Singles Cricket Losses | Number | Cumulative season losses |
| **D01 - W** | Doubles 501 Wins | Number | Cumulative season wins |
| **D01 - L** | Doubles 501 Losses | Number | Cumulative season losses |
| **DC - W** | Doubles Cricket Wins | Number | Cumulative season wins |
| **DC - L** | Doubles Cricket Losses | Number | Cumulative season losses |
| **W** | Total Wins | Number | Sum of all W columns |
| **L** | Total Losses | Number | Sum of all L columns |
| **Win %** | Win Percentage | Decimal | `(W / (W + L)) × 100`, 2 decimals |
| **QPs** | Quality Points | Number | Calculated from achievements |
| **QP%** | Quality Point Percentage | Decimal | `(QPs / Legs Played) × 100`, 2 decimals |
| **Rating** | Player Rating | Decimal | `((W × 2) / Games Played) + (QPs / Legs Played)`, 4 decimals |

**END OF COLUMNS** - Any columns beyond Rating in sample are not needed.

#### 3. Team Summary Rows

After player rows, include these special rows:

- **Sub** rows (2): For substitute players (usually zeros)
- **Forfeit** row: Count of forfeited matches
- **Default** row: Count of defaulted matches

#### 4. Team Footer
- `® first season rookie` indicator
- `®® second season rookie` indicator

#### 5. Team Totals
- Aggregate statistics showing team-level sums/averages
- Right side: Small summary box with key team stats

### Visual Formatting

**Colors & Styling:**
- **QUALIFIED**: Green text
- **INELIGIBLE**: Red text
- **Rookie indicators**: `®` and `®®` symbols before name
- **Division headers**: Colored background (Green for Winston, Blue for Salem)
- **Team names**: Bold, larger font
- **Alternating row shading**: Subtle for readability

**Layout:**
- Page size: Letter (8.5" × 11")
- Orientation: Landscape (to fit all columns)
- Margins: 0.5" all sides
- Font: Helvetica or similar sans-serif
- Font sizes: 10-12pt for data, 14pt for headers

---

## Report 2: Individual Report (Player Rankings & Special Achievements)

### Purpose
Rankings and leaderboards showing top performers across various categories.

### Document Header
- **Title**: "Winston-Salem Sunday Night Dart League"
- **Subtitle**: "73rd Season - Spring 2025 - Week {week_number}"

### Document Structure

The report is divided by **DIVISION** with identical sections for each:

---

### Division Sections

Each division (Winston, Salem) contains:

#### 1. Singles - Women
**Top 5 Rankings**

| Column | Description | Format |
|--------|-------------|--------|
| Name | Player name | Text |
| W | Singles wins | Number |
| L | Singles losses | Number |
| Win% | Win percentage | `XX.XX%` |

**Sort by:** Win% descending

#### 2. All Events - Women
**Top 5 Rankings**

| Column | Description | Format |
|--------|-------------|--------|
| Name | Player name | Text |
| W | Total wins (all events) | Number |
| L | Total losses (all events) | Number (may show `#` in some cases) |
| Win% | Overall win percentage | `XX.XX%` |

**Sort by:** Win% descending

#### 3. Quality Points - Women
**Top 5 Rankings**

| Column | Description | Format |
|--------|-------------|--------|
| Name | Player name | Text |
| Qp's | Total quality points | Number |
| QP% | Quality point percentage | `XX.XX%` |

**Sort by:** QP% descending

#### 4. Ratings - Women
**Top 5 Rankings**

| Column | Description | Format |
|--------|-------------|--------|
| Name | Player name | Text |
| Rating | Calculated rating value | `X.XXXX` (4 decimals) |

**Sort by:** Rating descending

---

#### 5. Singles - Men
*(Same structure as Singles - Women)*

#### 6. All Events - Men
*(Same structure as All Events - Women)*

#### 7. Quality Points - Men
*(Same structure as Quality Points - Women)*

#### 8. Ratings - Men
*(Same structure as Ratings - Women)*

---

### Special Quality Point Register

**Center box between divisions showing weekly achievements:**

Format: `Achievement Type - Player Name(s) [count if multiple]`

**Tracked Achievements:**
- **180** - Perfect score (3 × triple 20)
- **122 Out**, **108 Out** - Specific checkout achievements
- **6B** - Six bulls
- **9H** - Nine marks/hits (Cricket)
- Other notable achievements

**Example:**
```
180 - Steve B, Scott W, David S(2), Eric H(2), KC, Stefano
122 Out - Matt D
6B - Eric H
9H - Mike T(3), Megan(2), Ryan Mc, Mike R, Aaron
```

### Visual Formatting

**Colors & Styling:**
- **Division headers**: 
  - Winston Division: Green background bar
  - Salem Division: Blue/cyan background bar
- **Table headers**: Colored backgrounds for readability
- **Special QP Register**: Center box with border/highlight
- **Clean table layout**: Professional formatting with borders

**Layout:**
- Page size: Letter (8.5" × 11")
- Orientation: Portrait
- Margins: 0.5" all sides
- Font: Helvetica or similar sans-serif
- Multiple columns per page for space efficiency

### Footer Notes

At bottom of report:
- "Rating is calculated by adding Total Wins x 2 divided by Total Games plus QPs divided by Total Legs"
- "QP percentage is calculated # of QP's divided by the number of games played."

---

## Data Validation Rules

### Eligibility
- Minimum 18 games to be "QUALIFIED"
- Players with < 18 games show as "INELIGIBLE"

### Win Percentage
- Calculate as: `(Wins / (Wins + Losses)) × 100`
- Display with 2 decimal places
- Handle 0/0 case as 0.00%

### Quality Point Percentage
- Calculate as: `(Total QPs / Legs Played) × 100`
- Display with 2 decimal places

### Rating
- Formula: `((Total Wins × 2) / Total Games) + (QPs / Total Legs)`
- Display with 4 decimal places
- Never show negative ratings

### Rankings
- Show top 5 only in each category
- Ties: Use secondary sort (e.g., total games played, name alphabetically)

---

## Edge Cases to Handle

1. **New players mid-season**: Show as INELIGIBLE with Games To Qualify count
2. **Substitute players**: Usually have zero stats, still list in team
3. **Multiple QP achievements**: Show count in parentheses (e.g., "David S(2)")
4. **Players with no singles games**: May show 0-0 record or be excluded from Singles rankings
5. **Division symbol (`#`)**: May appear in loss column - meaning TBD (needs clarification)

---

## Open Questions / Refinements Needed

1. ✅ Columns after Rating in Overall report - **Confirmed: Not needed**
2. ❓ Singles vs Doubles separation - How to distinguish in source data?
3. ❓ Week-by-week vs cumulative - Export strategy?
4. ❓ Meaning of `#` symbol in some loss columns
5. ❓ Special QP achievements tracking - From exports or manual entry?

---

## Version History

- **v0.1** - Initial specification from sample PDFs (Week 14)
- **v0.2** - Clarified Overall report ends at Rating column

---

## Notes for Developers

- See `DATA_MAPPING.md` for field mappings from DartConnect exports
- See `docs/samples/` for reference PDFs showing exact desired output
- PDF generation should match layout precisely including colors and formatting
- Team order within division may follow standings or alphabetical (TBD)
