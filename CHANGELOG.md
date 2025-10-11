# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-11

### Added
- **Sample-Matched PDF Reports**: PDF generators now produce reports that exactly match the provided sample formats
- **Professional Report Naming**: Reports now use `Overall-MMDD_HHMMSS.pdf` and `Individual-MMDD_HHMMSS.pdf` naming convention
- **Division-Based Layout**: Overall report features Winston Division (green header) and Salem Division (blue header)
- **Team-Based Organization**: Individual report organizes players by team with comprehensive statistics
- **Enhanced Visual Formatting**: Colors, borders, and styling match official league report samples

### Changed
- **PDF Generator Complete Rewrite**: `src/pdf_generator.py` updated to match sample PDF layouts exactly
- **Method Names Updated**: `generate_report1/2()` renamed to `generate_overall_report()` and `generate_individual_report()`
- **Report Structure**: Complete restructure to match Overall-14.pdf and Individual-14.pdf sample formats
- **Documentation Updates**: README, OUTPUT_SPECIFICATION updated to reflect new formats

### Fixed
- **JSON Serialization Error**: Fixed MultiIndex DataFrame tuple key serialization issue in `main_consolidated.py`
- **Cache Performance**: Improved error handling for edge cases in data structure serialization

### Technical Details
- Overall Report Features:
  - Centered league title with season/week information
  - Three-column layout per division (Singles, All Events, Quality Points)
  - Separate Women/Men sections within each division
  - Player ratings and special achievements sections
  - Footer with calculation explanations

- Individual Report Features:
  - Week-based title structure
  - Division and team organization
  - Tournament eligibility tracking (QUALIFIED/INELIGIBLE)
  - Weekly game results in tabular format
  - Comprehensive player statistics (Win%, QPs, Ratings)
  - Proper rookie designation markers

## [1.0.0] - 2025-10-04

### Initial Release
- Basic PDF report generation from DartConnect exports
- URL fetching and caching system for enhanced data
- Quality Point calculations for Cricket and 501 games
- Multi-strategy data processing (by_leg, leaderboards)
- Comprehensive caching system with 5-month expiry
- Command-line interface with auto-detection
- Documentation and setup guides

---

### Migration Notes

**For users upgrading from v1.0.0:**

1. **PDF File Names Changed**: Reports are now named `Overall-MMDD_HHMMSS.pdf` and `Individual-MMDD_HHMMSS.pdf` instead of the previous `league_statistics_*.pdf` and `player_performance_*.pdf`

2. **Report Content Updated**: The PDF content and layout have been completely restructured to match official league formats. If you have existing scripts that process the PDFs, you may need to update them.

3. **Method Names**: If you're using the library programmatically, update calls from `generate_report1()` to `generate_overall_report()` and `generate_report2()` to `generate_individual_report()`

4. **No Data Migration Needed**: All existing cache files, data files, and configurations remain compatible.

**Backward Compatibility**: The old method names and report formats have been completely replaced. If you need the old format, please use version 1.0.0.