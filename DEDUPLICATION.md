# API Call Deduplication

## Overview

The bot detection system now includes comprehensive deduplication to prevent wasting API calls on users that have already been processed.

## Changes Made

### 1. Database Enhancement (`backend/database.py`)

**Added new method:**
```python
def get_unanalyzed_handles(self) -> List[str]:
    """
    Get list of user handles that haven't been analyzed yet
    Returns handles in users table that don't have bot_detection_results
    """
```

This method uses a LEFT JOIN to efficiently find users who need analysis.

### 2. Bot Detection Script (`run_bot_detection.py`)

**Default Behavior (Skip Analyzed Users):**
```bash
# Only analyzes users who haven't been analyzed yet
python run_bot_detection.py
```

**Force Re-analysis:**
```bash
# Re-analyze all users (including previously analyzed)
python run_bot_detection.py --force
```

**Other Options:**
```bash
# Custom batch size for progress logging
python run_bot_detection.py --batch-size 20

# Custom database path
python run_bot_detection.py --db-path my_database.db
```

**What Changed:**
- ✓ By default, only analyzes unanalyzed users
- ✓ Shows count of already-analyzed vs. unanalyzed users
- ✓ Exits early if all users are analyzed
- ✓ Added `--force` flag to re-analyze if needed
- ✓ Better logging and progress reporting

### 3. Bot Candidate Collection (`collect_bot_candidates.py`)

**Three Levels of Deduplication:**

1. **Session-level**: Tracks handles analyzed in current run
   ```python
   if handle in self.analyzed_handles:
       return None  # Skip, already checked this session
   ```

2. **Database-level**: Checks if user exists before API call
   ```python
   existing_user = self.db.get_user(handle)
   if existing_user:
       logger.debug(f"Skipping {handle} - already in database")
       return None  # Skip, no API call needed
   ```

3. **Initialization**: Loads existing users at startup
   ```python
   def _load_existing_from_database(self):
       # Pre-load all existing handles to avoid re-checking
       existing_handles = self.db.get_all_handles()
       self.candidates_found.update(existing_handles)
   ```

**Benefits:**
- ✓ No duplicate API calls to Bluesky
- ✓ Faster collection (skips known users)
- ✓ Resume safely from interruptions
- ✓ Clear logging of skipped users

## API Call Savings

### Before Deduplication
```
Run 1: Analyze 1000 users → 1000 API calls
Run 2: Analyze same 1000 users → 1000 API calls (wasted!)
Total: 2000 API calls
```

### After Deduplication
```
Run 1: Analyze 1000 users → 1000 API calls
Run 2: Skip 1000 analyzed users → 0 API calls
Total: 1000 API calls (50% savings!)
```

## Usage Examples

### Example 1: First Run
```bash
$ python run_bot_detection.py
INFO - Found 1000 unanalyzed users out of 1000 total
INFO - Analyzing 1/1000: user1.bsky.social
...
INFO - Analysis complete!
INFO - Successfully analyzed: 1000
```

### Example 2: Second Run (No New Users)
```bash
$ python run_bot_detection.py
INFO - Found 0 unanalyzed users out of 1000 total
INFO - All users have already been analyzed! Use --force to re-analyze.
```

### Example 3: Add New Users and Re-run
```bash
# First collect new users
$ python collect_bot_candidates.py --target 100
INFO - Loaded 1000 existing users from database (will skip these)
INFO - Processing seed account: bbc.bsky.social
INFO - Skipping user1.bsky.social - already in database
...
INFO - Found 100 new bot candidates

# Then analyze only the new ones
$ python run_bot_detection.py
INFO - Found 100 unanalyzed users out of 1100 total
INFO - Analyzing 1/100: newuser1.bsky.social
...
```

### Example 4: Force Re-analysis (Update Results)
```bash
# Re-analyze all users (maybe you improved the detection algorithm)
$ python run_bot_detection.py --force
INFO - Force mode: analyzing all 1100 users
INFO - Analyzing 1/1100: user1.bsky.social
...
```

## Database Schema

The deduplication relies on these tables:

```sql
-- All user profiles
CREATE TABLE users (
    handle TEXT PRIMARY KEY,
    description TEXT,
    following INTEGER,
    followers INTEGER,
    ...
);

-- Bot detection results (one per analyzed user)
CREATE TABLE bot_detection_results (
    handle TEXT PRIMARY KEY,
    overall_score REAL NOT NULL,
    confidence REAL NOT NULL,
    ...
    FOREIGN KEY (handle) REFERENCES users(handle)
);
```

**Finding unanalyzed users:**
```sql
SELECT u.handle
FROM users u
LEFT JOIN bot_detection_results b ON u.handle = b.handle
WHERE b.handle IS NULL  -- No results yet
```

## Performance Impact

### Bluesky API Rate Limits
- **Without deduplication**: Easy to hit rate limits by re-analyzing users
- **With deduplication**: Stays within limits by skipping known users

### Database Queries
- `get_user(handle)`: Very fast (indexed primary key lookup)
- `get_unanalyzed_handles()`: Fast (uses indexed LEFT JOIN)
- Minimal overhead, massive API savings

## Best Practices

1. **Always run without `--force` first** - Let the system skip analyzed users
2. **Only use `--force` when needed** - When you update detection algorithms
3. **Monitor logs** - Check how many users are being skipped
4. **Resume safely** - Both scripts support resuming from interruptions

## Troubleshooting

**Q: Script says "all users analyzed" but I want to check them again**
A: Use `--force` flag: `python run_bot_detection.py --force`

**Q: Collection script still seems slow**
A: Check logs - it should show "Skipping X - already in database" messages

**Q: How do I clear analysis results to start fresh?**
A: Delete the `bot_detection_results` table data:
```bash
sqlite3 bot_detection.db "DELETE FROM bot_detection_results;"
```

**Q: Can I re-analyze specific users?**
A: Yes, delete their results first:
```bash
sqlite3 bot_detection.db "DELETE FROM bot_detection_results WHERE handle = 'user.bsky.social';"
```

## Summary

✓ **No wasted API calls** - Users analyzed once stay analyzed
✓ **Smart skipping** - Checks database before making API calls
✓ **Resume support** - Safe to interrupt and restart
✓ **Clear logging** - See exactly what's being skipped
✓ **Flexible control** - Use `--force` when you need re-analysis
