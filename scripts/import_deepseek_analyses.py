#!/usr/bin/env python3
"""
Import DeepSeek analysis JSON files into SQLite database
Reads all JSON files from analyses/ directory and populates the database
"""

import json
import glob
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import BotDetectionDB

def import_json_files(analyses_dir: str = "analyses", db_path: str = "bot_detection.db"):
    """
    Import all JSON analysis files into database (optimized with batch commits)

    Args:
        analyses_dir: Directory containing JSON files
        db_path: Path to SQLite database
    """
    db = BotDetectionDB(db_path)
    db.connect()
    db.initialize_schema()

    # Find all JSON files
    json_files = glob.glob(f"{analyses_dir}/*.json")
    print(f"Found {len(json_files)} JSON files")

    total_users = 0
    total_analyses = 0

    # Use a single cursor with manual transaction control for speed
    cursor = db.connection.cursor()

    try:
        # Process each JSON file
        for idx, json_file in enumerate(json_files):
            print(f"Processing {idx+1}/{len(json_files)}: {os.path.basename(json_file)}")

            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                # Each file contains a list of user analyses
                for user_data in data:
                    handle = user_data.get('handle')
                    if not handle:
                        continue

                    # Insert user with batch mode
                    cursor.execute("""
                        INSERT OR REPLACE INTO users
                        (handle, last_updated)
                        VALUES (?, CURRENT_TIMESTAMP)
                    """, (handle,))
                    total_users += 1

                    # Insert each prompt analysis
                    for prompt_name in ['prompt1', 'prompt2', 'prompt3', 'prompt4']:
                        if prompt_name in user_data:
                            analysis = user_data[prompt_name]
                            cursor.execute("""
                                INSERT OR REPLACE INTO deepseek_analyses
                                (handle, prompt_name, assessment, confidence, reasoning, analyzed_at)
                                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            """, (
                                handle,
                                prompt_name,
                                analysis.get('assessment', 'unknown'),
                                analysis.get('confidence', 0),
                                analysis.get('reasoning', '')
                            ))
                            total_analyses += 1

            except Exception as e:
                print(f"Error processing {json_file}: {e}")
                continue

            # Commit every 10 files to save progress
            if (idx + 1) % 10 == 0:
                db.connection.commit()
                print(f"  Committed progress ({total_users} users, {total_analyses} analyses so far)")

        # Final commit
        db.connection.commit()
        cursor.close()

        print(f"\nImport complete!")
        print(f"Imported {total_users} user entries")
        print(f"Imported {total_analyses} DeepSeek analyses")

        # Show statistics
        stats = db.get_statistics()
        print(f"\nDatabase statistics:")
        print(f"  Unique users: {stats['total_users']}")
        print(f"  Total analyses: {stats['total_deepseek_analyses']}")

    finally:
        db.close()

if __name__ == "__main__":
    import_json_files()
