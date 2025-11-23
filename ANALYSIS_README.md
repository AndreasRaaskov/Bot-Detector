# Bot Detection Analysis Pipeline

This document explains how to use the database and analysis scripts.

## Overview

The analysis pipeline processes Matt's DeepSeek JSON analyses and runs our bot detection system on all users, then provides comprehensive analysis and visualizations.

## Database Schema

The SQLite database (`bot_detection.db`) contains:

1. **users** - User profile metadata
   - `handle` (PRIMARY KEY)
   - `description`, `following`, `followers`, `ratio`
   - `replies_pct`, `reposts_pct`, `originals_pct`

2. **deepseek_analyses** - Matt's DeepSeek LLM analyses
   - `handle`, `prompt_name` (prompt1-4)
   - `assessment` (human/ai_bot)
   - `confidence` (0-100)
   - `reasoning`

3. **bot_detection_results** - Our bot detection results
   - `handle`, `overall_score`, `confidence`
   - Individual method scores (follow, pattern, text, llm)
   - `summary`, `recommendations`

## Step-by-Step Usage

### Step 1: Import DeepSeek Analyses (ALREADY DONE ✓)

```bash
python scripts/import_deepseek_analyses.py
```

This imports all JSON files from `analyses/` directory into the database.

**Status:** Already completed - 1,000 users with 3,988 analyses imported.

### Step 2: Run Bot Detection on All Users

```bash
python scripts/run_bot_detection.py
```

This runs the full bot detection analysis on all 1,000 users in the database.

**Note:** This will take a while as it:
- Fetches profile and posts from Bluesky for each user
- Runs 4 analysis methods (follow, pattern, text, LLM)
- May encounter rate limits or API errors

**Expected time:** ~10-30 minutes depending on API rate limits.

### Step 3: Analyze Results in Jupyter Notebook

```bash
jupyter notebook analysis_overview.ipynb
```

Or if using JupyterLab:
```bash
jupyter lab analysis_overview.ipynb
```

The notebook provides:
- **Score distributions** for each detection method
- **Correlation analysis** between methods
- **Top likely bots** ranked by score
- **DeepSeek prompt comparison** - how do the 4 prompts differ?
- **Method agreement** - how often do prompts agree?
- **Our detection vs DeepSeek** - correlation and comparison
- **Summary report** exported to text file

## Database Queries

You can also query the database directly:

```bash
sqlite3 bot_detection.db
```

### Useful Queries

```sql
-- Get top 10 bots
SELECT handle, overall_score, confidence
FROM bot_detection_results
ORDER BY overall_score DESC
LIMIT 10;

-- Count bot vs human by DeepSeek prompt
SELECT prompt_name, assessment, COUNT(*) as count
FROM deepseek_analyses
GROUP BY prompt_name, assessment;

-- Find accounts where DeepSeek disagrees with our detection
SELECT
    b.handle,
    b.overall_score,
    COUNT(CASE WHEN d.assessment = 'ai_bot' THEN 1 END) as deepseek_bot_votes
FROM bot_detection_results b
JOIN deepseek_analyses d ON b.handle = d.handle
GROUP BY b.handle
HAVING (b.overall_score > 0.6 AND deepseek_bot_votes < 2)
    OR (b.overall_score < 0.4 AND deepseek_bot_votes > 2);

-- Get user with all analysis data
SELECT
    u.handle,
    u.followers,
    u.following,
    b.overall_score,
    b.follow_analysis_score,
    b.posting_pattern_score,
    b.text_analysis_score,
    b.llm_analysis_score
FROM users u
JOIN bot_detection_results b ON u.handle = b.handle
LIMIT 10;
```

## Files Created

- `backend/database.py` - Database management class
- `scripts/import_deepseek_analyses.py` - Import JSON files
- `scripts/run_bot_detection.py` - Run bot detection on all users
- `analysis_overview.ipynb` - Comprehensive Jupyter notebook analysis
- `bot_detection.db` - SQLite database (created after import)
- `analysis_summary_report.txt` - Text summary (created by notebook)

## Requirements

Make sure you have these Python packages installed:

```bash
pip install pandas numpy matplotlib seaborn scipy jupyter
```

The backend packages (httpx, fastapi, etc.) should already be installed from requirements.txt.

## Troubleshooting

### "Database is locked" error
- Close any other connections to the database
- Make sure only one script is running at a time

### Rate limiting during bot detection
- The script will continue after errors
- You can restart it later - it uses INSERT OR REPLACE so won't duplicate

### Missing packages for notebook
```bash
pip install pandas matplotlib seaborn scipy jupyter
```

## Next Steps

After running the analysis:

1. Review the notebook visualizations
2. Check the summary report
3. Identify patterns and correlations
4. Refine detection weights based on findings
5. Investigate specific cases where methods disagree

## Questions?

Check the code comments in each script for detailed documentation of how things work.
