# Data Source Information

## Valid Input Dataset

**IMPORTANT**: The only valid input dataset currently being used for testing and development is:

```
docs/samples/dartconnect/Fall_Winter*.csv
```

This is the official DartConnect export file that contains the complete league data with all necessary columns including:
- Player names (First Name, Last Name, FI)
- Game information (Game Name, Set #, Game #)
- Match results (Win column: W/L values)
- Match metadata (Date, Report Link, Event Link)
- Performance statistics (3DA, Pts/Marks, Darts, Hi Turn, DO, DI, etc.)
- Team information (Team, Division, Season)

### Key Facts About the Data Structure

1. **Leg-level data**: Each row represents one leg (the smallest scoring unit)
2. **Games (Sets)**: Multiple legs make up one game, identified by unique (Report Link, Set #) combinations
3. **Match**: Multiple games/sets make up one match, identified by Report Link
4. **Win/Loss Calculation**: To determine game wins/losses, we must:
   - Group legs by (Report Link, Set #)
   - Count legs won vs lost in each Set
   - The player who won the majority of legs in a Set wins that game

### Example: Marc Bopp's Statistics

From the Fall_Winter_2025_By_Leg_export.csv:
- **34 legs played** (rows in CSV)
- **21 legs won, 13 legs lost** (individual leg results)
- **15 unique games (Sets)** played
- **9 games won, 6 games lost** (determined by who won majority of legs in each Set)
  - 501 SIDO: 6W - 1L
  - Cricket: 3W - 5L
- **60.00% win rate** at the game level

## Other Data Files

- `data/sample_data.csv` - This is a simplified test file with different structure, NOT the primary data source
- Cache files under `cache/dartconnect_urls/` - These are fetched match details in JSON format

## Usage in Tests

When writing tests or running the PDF generator, always reference the Fall_Winter CSV file:

```python
data_file = "docs/samples/dartconnect/Fall_Winter_2024-25_Players_Singles.csv"
```
