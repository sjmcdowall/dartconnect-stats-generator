# DartConnect Cache Optimization

## Overview

The DartConnect Statistics Generator now includes intelligent caching for URL data fetching, providing dramatic performance improvements for repeated runs - especially important for weekly report generation.

## Performance Benefits

### Before Caching
- **First Run**: 20+ seconds to fetch 173 URLs
- **Every Subsequent Run**: 20+ seconds (re-fetching all URLs)
- **Network Load**: High impact on DartConnect servers
- **Reliability**: Dependent on network availability

### After Caching
- **First Run**: 20+ seconds (builds cache)
- **Subsequent Runs**: ~1 second (100% cache hits)
- **Performance Improvement**: **20x faster**
- **Network Load**: Minimal (only new games)
- **Reliability**: Works offline for cached data

## Cache Configuration

### Current Settings
- **Cache Expiry**: 150 days (~5 months)
- **Storage Location**: `cache/dartconnect_urls/`
- **File Format**: JSON with readable match ID filenames
- **Automatic Cleanup**: Expired files removed automatically

### Why 5 Months?
- Dart seasons typically last 5 months
- DartConnect game data is immutable once matches complete
- Balances performance with storage space
- Ensures data freshness for new seasons

## Cache Statistics

Based on sample data analysis:
- **Average File Size**: ~0.05 MB per match
- **173 Matches**: ~8.12 MB total
- **Weekly Growth**: ~0.9 MB (assuming 20 new games/week)
- **Season Total**: ~18 MB for full season cache

## Cache Management

Use the included `cache_manager.py` utility:

```bash
# View cache information
python3 cache_manager.py info

# Clear expired cache files
python3 cache_manager.py clear-expired

# Clear all cache files (use with caution)
python3 cache_manager.py clear-all
```

### Example Cache Info Output
```
🗂️  DartConnect Cache Information
========================================
📁 Total Files: 173
💾 Total Size: 8.12 MB
⏰ Cache Expiry: 150 days (~5.0 months)
🕰️  Oldest File: 68aba095f978cb217a4c5457.json (0 days old)
🆕 Newest File: 68d09ae77fb34ee7ab6f72d7.json (0 days old)

📊 Statistics:
   Average file size: 0.05 MB
   Estimated weekly growth: ~0.9 MB (assuming 20 new games/week)
```

## Cache File Structure

Each cached file contains:
```json
{
  "url": "https://recap.dartconnect.com/games/68aba095f978cb217a4c5457",
  "cached_at": "2025-10-11T15:55:01.901879",
  "game_data": {
    // Complete DartConnect game data...
  }
}
```

## Benefits for Weekly Workflow

### Week 1 (Cold Cache)
- Initial run processes all historical data
- Cache built for all existing matches
- Takes normal time (~20+ seconds)

### Week 2+ (Warm Cache)
- Existing matches loaded instantly from cache
- Only new games fetched from web
- Dramatic speed improvement
- Reliable offline processing

### Season Transitions
- Cache automatically expires after 150 days
- New season data fetched fresh
- No manual intervention required

## Error Handling

The cache system includes robust error handling:
- **Cache corruption**: Automatic fallback to web fetch
- **Network failures**: Uses cache when available
- **Expired cache**: Automatic cleanup and refresh
- **Storage issues**: Graceful degradation with logging

## Maintenance

### Automatic Maintenance
- Expired files removed automatically during runs
- Cache statistics tracked and reported
- File corruption detected and handled

### Manual Maintenance
- Use `cache_manager.py` for manual inspection
- Monitor disk usage if running for multiple seasons
- Consider clearing cache between major DartConnect updates

## Technical Implementation

### Cache Hit Process
1. URL requested for game data
2. Generate cache filename from match ID
3. Check if cache file exists and is not expired
4. Return cached data if valid
5. Update cache statistics

### Cache Miss Process
1. Cache file missing or expired
2. Fetch data from DartConnect web API
3. Parse and validate response
4. Store data in cache with metadata
5. Return fresh data and update statistics

### Storage Optimization
- Files named by match ID for readability
- JSON format for human inspection
- Automatic compression considered for future versions
- Directory organization by season (future enhancement)

## Future Enhancements

Potential improvements for future versions:
- **Compression**: Reduce storage requirements
- **Season Organization**: Separate cache directories per season
- **Parallel Fetching**: Faster initial cache building
- **Cache Prewarming**: Proactive cache building
- **Statistics Dashboard**: Web interface for cache monitoring