# Backend Utilities

This directory contains utility scripts for managing the FINRA Compliance Analyzer.

## Scripts

### load_finra_rules.py

Unified loader for FINRA rules from JSON files. Handles both array and object JSON formats.

**Usage:**
```bash
# Run from inside the backend container
docker exec finra-backend python /app/utils/load_finra_rules.py [options]

# Or copy and run
docker cp backend/utils/load_finra_rules.py finra-backend:/app/utils/
docker exec finra-backend python /app/utils/load_finra_rules.py
```

**Options:**
- `--rule-set-id ID` - Rule set ID to load into (default: 5)
- `--batch-size N` - Number of rules to process before committing (default: 20)
- `--skip-preprocessing` - Skip GPT preprocessing for faster loading (recommended)
- `--verbose` - Show detailed progress

**Example:**
```bash
# Load all rules with larger batch size for faster processing
docker exec finra-backend python /app/utils/load_finra_rules.py --batch-size 50

# Load into a different rule set with verbose output
docker exec finra-backend python /app/utils/load_finra_rules.py --rule-set-id 6 --verbose
```

### cleanup_old_analyses.sql

SQL script to clean up old analyses with hallucinated/invalid rule numbers.

**Usage:**
```bash
# Copy to container and run
docker cp backend/utils/cleanup_old_analyses.sql finra-postgres:/tmp/
docker exec finra-postgres psql -U finra_user -d finra_compliance -f /tmp/cleanup_old_analyses.sql
```

## Data Location

FINRA rules JSON files should be located at:
- In container: `/app/data/dmp-finra/FinraRulesBook-set/`
- On host: `/home/nervous/finra-compliance/data/dmp-finra/FinraRulesBook-set/`

## Current Status

As of last run:
- **744 FINRA rules loaded** into rule set 5
- All files are in array format (containing multiple rule versions)
- Key rules present: 2010, 2111, 2210, 3150, 3160, 5210
- Missing: Some specialized rules like 4512, 4513 (may not exist in dataset)