-- Script to clean up old analyses with hallucinated rule numbers
-- These are rules that don't exist in our database but were hallucinated by the LLM

-- First, let's see what rule numbers are in compliance issues but not in rules table
WITH invalid_rules AS (
    SELECT DISTINCT ci.rule_number
    FROM compliance_issues ci
    WHERE NOT EXISTS (
        SELECT 1 FROM rules r 
        WHERE r.rule_number = ci.rule_number
    )
)
SELECT 
    rule_number as "Invalid Rule Number",
    COUNT(*) as "Number of Issues"
FROM compliance_issues
WHERE rule_number IN (SELECT rule_number FROM invalid_rules)
GROUP BY rule_number
ORDER BY rule_number;

-- To delete these invalid issues (uncomment to run):
-- DELETE FROM compliance_issues 
-- WHERE rule_number NOT IN (SELECT rule_number FROM rules);

-- To delete all old analyses and start fresh (uncomment to run):
-- TRUNCATE TABLE compliance_issues CASCADE;
-- TRUNCATE TABLE document_paragraphs CASCADE;
-- TRUNCATE TABLE document_analyses CASCADE;
-- TRUNCATE TABLE analysis_cache CASCADE;