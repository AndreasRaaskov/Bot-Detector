# Bot Candidate Collection Scripts

## collect_bot_candidates.py

This script crawls Bluesky to find accounts with high bot-probability characteristics and stores them in the database for analysis.

### Features

- **Smart Filtering**: Uses multiple indicators to identify potential bots:
  - High following/follower ratios (>10:1 with >500 following)
  - New accounts with suspiciously high post counts
  - Suspicious username patterns (e.g., user12345678)
  - Very high posting rates (>150 posts/day)
  - Missing profile information (no bio/avatar)
  - Zero followers despite many posts

- **Progress Tracking**: Saves progress to `collection_progress.json` so you can resume if interrupted

- **Rate Limiting**: Respects API limits with built-in delays

- **Logging**: Detailed logs saved to `bot_collection.log`

### Prerequisites

1. **Bluesky Account**: You need a Bluesky account to access the API

2. **Environment Variables**: Set your credentials in `.env` file or export them:
   ```bash
   export BLUESKY_USERNAME='your.handle.bsky.social'
   export BLUESKY_PASSWORD='your-password'
   ```

3. **Seed Accounts**: Edit `seed_accounts.json` to customize which high-profile accounts to crawl

### Usage

#### Basic Usage (collect 1000 candidates)
```bash
python scripts/collect_bot_candidates.py
```

#### Custom target count
```bash
python scripts/collect_bot_candidates.py --target 500
```

#### Resume from previous run
```bash
python scripts/collect_bot_candidates.py --resume
```

#### Use custom seed accounts file
```bash
python scripts/collect_bot_candidates.py --seeds my_seeds.json
```

### How It Works

1. **Loads seed accounts** from `seed_accounts.json` (high-profile accounts)
2. **Fetches followers** from each seed account (up to 100 per seed)
3. **Analyzes each follower** for bot-like characteristics
4. **Scores accounts** based on multiple indicators
5. **Stores bot candidates** (score ≥ 0.5) in the database
6. **Continues until target reached** or all seeds processed

### Output

- **Database**: Candidates stored in `bot_detection.db` in the `users` table
- **Progress File**: `collection_progress.json` tracks current state
- **Log File**: `bot_collection.log` contains detailed execution logs

### Bot Probability Scoring

The script calculates a bot probability score (0.0 to 1.0+) based on:

| Indicator | Score | Description |
|-----------|-------|-------------|
| High follow ratio (>10:1) + many following | +0.4 | Strong bot signal |
| New account (<30 days) with >500 posts | +0.4 | Suspicious activity |
| Suspicious username pattern | +0.3 | Bot-like naming |
| Very high posting rate (>150/day) | +0.3 | Likely automated |
| No bio or avatar | +0.2 | Minimal profile setup |
| Moderate follow ratio (5-10:1) | +0.2 | Moderate signal |
| Zero followers with many posts | +0.3 | Unusual pattern |

**Threshold**: Accounts with score ≥ 0.5 are considered bot candidates.

### Example Output

```
2025-11-23 10:30:15 - INFO - Starting collection. Target: 1000 candidates
2025-11-23 10:30:16 - INFO - Successfully authenticated with Bluesky
2025-11-23 10:30:17 - INFO - Loaded 23 seed accounts from scripts/seed_accounts.json
2025-11-23 10:30:20 - INFO - Processing seed account: bbc.bsky.social
2025-11-23 10:30:22 - INFO - Got 100 followers from bbc.bsky.social
2025-11-23 10:30:25 - INFO - ✓ Bot candidate: user12345678.bsky.social (score: 0.70)
2025-11-23 10:30:25 - INFO -   - High follow ratio (12.5:1) with 625 following
2025-11-23 10:30:25 - INFO -   - Suspicious username pattern: user12345678.bsky.social
2025-11-23 10:30:25 - INFO -   - No bio or avatar
2025-11-23 10:30:25 - INFO - Progress: 1/1000 candidates found
...
```

### Troubleshooting

**Authentication fails:**
- Check your credentials in `.env` file
- Ensure username includes `.bsky.social` suffix
- Verify password is correct

**No candidates found:**
- Seed accounts may not have bot followers
- Try adding different seed accounts (crypto/finance accounts often have more bots)
- Lower the threshold in `_calculate_bot_probability()` if needed

**Rate limiting errors:**
- Script has built-in delays, but you can increase them
- Wait a few minutes and resume with `--resume`

**Script interrupted:**
- Progress is saved automatically every 10 accounts and after each seed
- Resume with: `python scripts/collect_bot_candidates.py --resume`

### Customization

#### Adjust Bot Detection Criteria

Edit the `_calculate_bot_probability()` method in `collect_bot_candidates.py` to modify:
- Score thresholds
- Which indicators to check
- Weights for each indicator

#### Add More Seed Accounts

Edit `seed_accounts.json` and add handles to any category or create new categories.

#### Change Collection Strategy

Modify `process_seed_account()` to:
- Increase/decrease followers per seed (`followers_limit` parameter)
- Add additional analysis (e.g., fetch posts for each account)
- Filter by specific criteria
