/* ============================================================
   DATA QUALITY CHECKS - DIGITAL PRODUCT TABLES
   ------------------------------------------------------------
   Run after 01 (and 02 / 02 v2) for the same month:
       vsql -v RUN_MNTH=202511 -f dq_checks.sql
   Returns one row per check (ACTUAL vs EXPECTED -> PASS / FAIL) and a summary row.
   Any FAIL = do not publish the month's report until it is explained.

   Checks
     A. Source -> target reconciliation  (revenue KPI and subscriber count vs the source tables)
     B. Keys                              (no duplicate subscriber per month)
     C. Completeness                      (every profile subscriber has a flag and a revenue row, no orphans)
     D. Nulls                             (segment fields filled)
     E. Month-over-month drift            (active base, revenue, digital share vs last month)
     F. Survival table                    (cohort size = profile, caller <= active)
        - using 02 v2: replace AUTO_LIFESTYLE_SUB_SEGMENT_SURVIVAL_ACTIVE_CALLER with the view ..._V in F1 / F2
   ============================================================ */


/* ============================================================
   0. RUN DATE
   ============================================================ */
DROP TABLE IF EXISTS TEMP_DQ_DATE;

CREATE LOCAL TEMP TABLE TEMP_DQ_DATE ON COMMIT PRESERVE ROWS AS
(
SELECT
	  GREG_MTH_ID AS MNTH_ID
	, MAX(GREG_DT_DT) AS MAX_RUN_DATE
	, CAST(TO_CHAR(ADD_MONTHS(TO_DATE(CAST(GREG_MTH_ID AS VARCHAR(6)), 'YYYYMM'), -1), 'YYYYMM') AS INT) AS PREV_MNTH_ID
FROM EDW.DTN_GEOG_CLDR
WHERE GREG_MTH_ID = :RUN_MNTH
GROUP BY 1
)
SEGMENTED BY HASH(MNTH_ID) ALL NODES
;


/* ============================================================
   1. SOURCE TOTALS (SAME RULES AS 01 STEP 2)
   ============================================================ */
DROP TABLE IF EXISTS TEMP_DQ_SOURCE;

CREATE LOCAL TEMP TABLE TEMP_DQ_SOURCE ON COMMIT PRESERVE ROWS AS
(
SELECT
	  SUM(REVN_AMNT)           AS SRC_REVN_AMNT
	, COUNT(DISTINCT PROD_KEY) AS SRC_REVN_NSUBR
FROM (
	-- Prepaid Revenue
	SELECT
		  PROD_KEY
		, NVL(CAST(TOT_MAIN_AMT AS NUMERIC(12,2)), 0)/1.07
		+ NVL(CAST(TOT_CASHBACK_AMT AS NUMERIC(12,2)), 0)
		+ CASE WHEN REV_CHNL IS NOT NULL THEN NVL(CAST(TOT_SRVC_RVN_AMT AS NUMERIC(12,2)),0)/1.07 ELSE NVL(CAST(TOT_TPPNG_CASH_AMT AS NUMERIC(12,2)), 0)/1.07 END AS REVN_AMNT
	FROM EDW.AGG_PREP_REV_SUBS_DAY
	WHERE CAST(TO_CHAR(VC_PAR_Key,'YYYYMM') AS INT) IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)
		AND RVN_IND = 1
		AND NVL(TEST_IND, 0) <> 1

	UNION ALL

	-- Postpaid Revenue
	SELECT
		  PROD_KEY
		, CAST(INVC_AMT AS DECIMAL(18, 6)) AS REVN_AMNT
	FROM EDW.FCT_INVC_PROD
	WHERE INVC_TYP = 'BILL'
		AND PROD_CTGRY = 'Postpay'
		AND PROD_TYP_NM = 'Mobile'
		AND AS_OF_MTH_KEY IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)
) S
)
;


/* ============================================================
   2. RUN ALL CHECKS
   ============================================================ */
DROP TABLE IF EXISTS TEMP_DQ_RESULT;

CREATE LOCAL TEMP TABLE TEMP_DQ_RESULT ON COMMIT PRESERVE ROWS AS
(
-- A1. revenue KPI: target total = source total (rounding tolerance 0.01%)
SELECT
	  'A1' AS CHECK_NO
	, 'Revenue total: target vs source' AS CHECK_NAME
	, T.REVN_AMNT AS ACTUAL
	, S.SRC_REVN_AMNT AS EXPECTED
	, CASE WHEN ABS(T.REVN_AMNT - S.SRC_REVN_AMNT) <= 0.0001 * ABS(S.SRC_REVN_AMNT) THEN 'PASS' ELSE 'FAIL' END AS STATUS
FROM (SELECT SUM(REVN_AMNT) AS REVN_AMNT FROM SANDBOX.AUTO_LIFESTYLE_SUB_AGG_REVENUE_MTH WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)) T
CROSS JOIN TEMP_DQ_SOURCE S

UNION ALL
-- A2. subscribers with revenue: target = source
SELECT
	  'A2', 'Subscribers with revenue: target vs source'
	, T.NSUBR, S.SRC_REVN_NSUBR
	, CASE WHEN T.NSUBR = S.SRC_REVN_NSUBR THEN 'PASS' ELSE 'FAIL' END
FROM (SELECT COUNT(DISTINCT PROD_KEY) AS NSUBR FROM SANDBOX.AUTO_LIFESTYLE_SUB_AGG_REVENUE_MTH WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)) T
CROSS JOIN TEMP_DQ_SOURCE S

UNION ALL
-- A3. active profile can not exceed the subscriber snapshot it was built from
SELECT
	  'A3', 'Profile subscribers <= source snapshot (A/E/D, Postpay+Prepay)'
	, T.NSUBR, S.NSUBR
	, CASE WHEN T.NSUBR > 0 AND T.NSUBR <= S.NSUBR THEN 'PASS' ELSE 'FAIL' END
FROM (SELECT COUNT(DISTINCT PROD_KEY) AS NSUBR FROM SANDBOX.AUTO_SUB_PROFILE_MTH WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)) T
CROSS JOIN (
	SELECT COUNT(DISTINCT PROD_KEY) AS NSUBR
	FROM EDW.DIM_PROD_MOL
	WHERE VC_PAR_KEY IN (SELECT MAX_RUN_DATE FROM TEMP_DQ_DATE)
		AND DWH_PROD_STAT IN ('A','E','D')
		AND PROD_CTGRY IN ('Postpay','Prepay')
) S

UNION ALL
-- B1. one row per subscriber per month in the flag segment
SELECT
	  'B1', 'Duplicate subscribers in flag segment'
	, COUNT(*), 0
	, CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (
	SELECT PROD_KEY FROM SANDBOX.AUTO_LIFESTYLE_SUB_FLAG_SEGMENT
	WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)
	GROUP BY PROD_KEY HAVING COUNT(*) > 1
) X

UNION ALL
-- B2. one row per subscriber per month in the revenue table
SELECT
	  'B2', 'Duplicate subscribers in revenue table'
	, COUNT(*), 0
	, CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (
	SELECT PROD_KEY FROM SANDBOX.AUTO_LIFESTYLE_SUB_AGG_REVENUE_MTH
	WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)
	GROUP BY PROD_KEY HAVING COUNT(*) > 1
) X

UNION ALL
-- C1. every profile subscriber has a flag row
SELECT
	  'C1', 'Profile subscribers missing in flag segment'
	, COUNT(*), 0
	, CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM SANDBOX.AUTO_SUB_PROFILE_MTH P
LEFT JOIN SANDBOX.AUTO_LIFESTYLE_SUB_FLAG_SEGMENT F
	ON P.MNTH_ID = F.MNTH_ID
	AND P.PROD_KEY = F.PROD_KEY
WHERE P.MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)
	AND F.PROD_KEY IS NULL

UNION ALL
-- C2. no flag rows for subscribers outside the profile (orphans)
SELECT
	  'C2', 'Flag rows with no profile subscriber'
	, COUNT(*), 0
	, CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM SANDBOX.AUTO_LIFESTYLE_SUB_FLAG_SEGMENT F
LEFT JOIN SANDBOX.AUTO_SUB_PROFILE_MTH P
	ON P.MNTH_ID = F.MNTH_ID
	AND P.PROD_KEY = F.PROD_KEY
WHERE F.MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)
	AND P.PROD_KEY IS NULL

UNION ALL
-- C3. share of profile subscribers with no revenue row (expected small: new / suspended lines)
SELECT
	  'C3', '% profile subscribers with no revenue row (<= 5%)'
	, ROUND(100.0 * SUM(CASE WHEN R.PROD_KEY IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2), 5
	, CASE WHEN 100.0 * SUM(CASE WHEN R.PROD_KEY IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) <= 5 THEN 'PASS' ELSE 'FAIL' END
FROM (SELECT DISTINCT MNTH_ID, PROD_KEY FROM SANDBOX.AUTO_SUB_PROFILE_MTH WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)) P
LEFT JOIN SANDBOX.AUTO_LIFESTYLE_SUB_AGG_REVENUE_MTH R
	ON P.MNTH_ID = R.MNTH_ID
	AND P.PROD_KEY = R.PROD_KEY

UNION ALL
-- D1. segment fields filled (SIM type, tenure)
SELECT
	  'D1', '% flag rows with NULL SIM_TYPE or AOU (<= 1%)'
	, ROUND(100.0 * SUM(CASE WHEN SIM_TYPE IS NULL OR AOU IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2), 1
	, CASE WHEN 100.0 * SUM(CASE WHEN SIM_TYPE IS NULL OR AOU IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) <= 1 THEN 'PASS' ELSE 'FAIL' END
FROM SANDBOX.AUTO_LIFESTYLE_SUB_FLAG_SEGMENT
WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)

UNION ALL
-- E1. active base vs last month (within +/-10%)
SELECT
	  'E1', 'Active subscribers: % change vs last month (+/-10%)'
	, ROUND(100.0 * (C.N - P.N) / NULLIF(P.N, 0), 2), 10
	, CASE WHEN P.N > 0 AND ABS(100.0 * (C.N - P.N) / P.N) <= 10 THEN 'PASS' ELSE 'FAIL' END
FROM       (SELECT COUNT(DISTINCT PROD_KEY) AS N FROM SANDBOX.AUTO_SUB_PROFILE_MTH WHERE MNTH_ID IN (SELECT MNTH_ID      FROM TEMP_DQ_DATE)) C
CROSS JOIN (SELECT COUNT(DISTINCT PROD_KEY) AS N FROM SANDBOX.AUTO_SUB_PROFILE_MTH WHERE MNTH_ID IN (SELECT PREV_MNTH_ID FROM TEMP_DQ_DATE)) P

UNION ALL
-- E2. revenue vs last month (within +/-15%)
SELECT
	  'E2', 'Revenue: % change vs last month (+/-15%)'
	, ROUND(100.0 * (C.R - P.R) / NULLIF(P.R, 0), 2), 15
	, CASE WHEN P.R > 0 AND ABS(100.0 * (C.R - P.R) / P.R) <= 15 THEN 'PASS' ELSE 'FAIL' END
FROM       (SELECT SUM(REVN_AMNT) AS R FROM SANDBOX.AUTO_LIFESTYLE_SUB_AGG_REVENUE_MTH WHERE MNTH_ID IN (SELECT MNTH_ID      FROM TEMP_DQ_DATE)) C
CROSS JOIN (SELECT SUM(REVN_AMNT) AS R FROM SANDBOX.AUTO_LIFESTYLE_SUB_AGG_REVENUE_MTH WHERE MNTH_ID IN (SELECT PREV_MNTH_ID FROM TEMP_DQ_DATE)) P

UNION ALL
-- E3. digital share vs last month (within +/-2pp)
SELECT
	  'E3', 'Digital user share: change vs last month in pp (+/-2)'
	, ROUND(C.PCT - P.PCT, 2), 2
	, CASE WHEN ABS(C.PCT - P.PCT) <= 2 THEN 'PASS' ELSE 'FAIL' END
FROM       (SELECT 100.0 * SUM(TOTAL_DIGIT) / NULLIF(COUNT(*), 0) AS PCT FROM SANDBOX.AUTO_LIFESTYLE_SUB_FLAG_SEGMENT WHERE MNTH_ID IN (SELECT MNTH_ID      FROM TEMP_DQ_DATE)) C
CROSS JOIN (SELECT 100.0 * SUM(TOTAL_DIGIT) / NULLIF(COUNT(*), 0) AS PCT FROM SANDBOX.AUTO_LIFESTYLE_SUB_FLAG_SEGMENT WHERE MNTH_ID IN (SELECT PREV_MNTH_ID FROM TEMP_DQ_DATE)) P

UNION ALL
-- F1. new cohort size in the survival table = profile subscribers of the month
SELECT
	  'F1', 'Survival cohort (M01) size = profile subscribers'
	, S.N, P.N
	, CASE WHEN S.N = P.N THEN 'PASS' ELSE 'FAIL' END
FROM       (SELECT COUNT(DISTINCT PROD_KEY) AS N FROM SANDBOX.AUTO_LIFESTYLE_SUB_SEGMENT_SURVIVAL_ACTIVE_CALLER WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)) S
CROSS JOIN (SELECT COUNT(DISTINCT PROD_KEY) AS N FROM SANDBOX.AUTO_SUB_PROFILE_MTH                         WHERE MNTH_ID IN (SELECT MNTH_ID FROM TEMP_DQ_DATE)) P

UNION ALL
-- F2. an active caller must be active (any month number of the last 12 cohorts)
SELECT
	  'F2', 'Survival rows with ACTIVE_CALLER = 1 but ACTIVE = 0'
	, COUNT(*), 0
	, CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM SANDBOX.AUTO_LIFESTYLE_SUB_SEGMENT_SURVIVAL_ACTIVE_CALLER
WHERE MNTH_ID BETWEEN CAST(TO_CHAR(ADD_MONTHS(TO_DATE(CAST(:RUN_MNTH AS VARCHAR(6)), 'YYYYMM'), -11), 'YYYYMM') AS INT) AND :RUN_MNTH
	AND (   (ACTIVE_CALLER_M01 = 1 AND ACTIVE_M01 = 0)
	     OR (ACTIVE_CALLER_M06 = 1 AND ACTIVE_M06 = 0)
	     OR (ACTIVE_CALLER_M12 = 1 AND ACTIVE_M12 = 0))
)
;


/* ============================================================
   3. RESULT
   ============================================================ */
SELECT * FROM TEMP_DQ_RESULT ORDER BY CHECK_NO;

SELECT
	  (SELECT MNTH_ID FROM TEMP_DQ_DATE) AS MNTH_ID
	, COUNT(*) AS CHECKS
	, SUM(CASE WHEN STATUS = 'FAIL' THEN 1 ELSE 0 END) AS FAILED
	, CASE WHEN SUM(CASE WHEN STATUS = 'FAIL' THEN 1 ELSE 0 END) = 0 THEN 'OK TO PUBLISH' ELSE 'HOLD - CHECK FAILED ROWS' END AS RESULT
FROM TEMP_DQ_RESULT
;
