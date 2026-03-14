-- =============================================================================
-- PHASE 1: DIMENSION TABLES (customers, products, geolocation)
-- =============================================================================

-- 1. CUSTOMERS
DROP TABLE IF EXISTS customers CASCADE;
CREATE TABLE customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state VARCHAR(5)
);
CREATE INDEX idx_customers_unique_id ON customers (customer_unique_id);

-- Validation (run after import)
SELECT 
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(DISTINCT customer_unique_id) AS total_unique_customers
FROM customers;

-- 4. PRODUCTS
DROP TABLE IF EXISTS products CASCADE;
CREATE TABLE products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER
);

-- Check missing
SELECT
    COUNT(*) FILTER (WHERE product_category_name IS NULL) AS missing_category,
    COUNT(*) FILTER (WHERE product_weight_g IS NULL) AS missing_weight
FROM products;

UPDATE products
SET product_category_name = 'Unknown'
WHERE product_category_name IS NULL;

DROP TABLE IF EXISTS products_clean;
CREATE TABLE products_clean AS
SELECT
    product_id,
    product_category_name,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
FROM products;

-- 8. GEOLOCATION
DROP TABLE IF EXISTS geolocation CASCADE;
CREATE TABLE geolocation (
    geolocation_zip_code_prefix VARCHAR(10),
    geolocation_lat NUMERIC,
    geolocation_lng NUMERIC,
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(5)
);

-- Standardize São Paulo
UPDATE geolocation
SET geolocation_city = LOWER(TRIM(REPLACE(geolocation_city, 'ã', 'a')))
WHERE geolocation_city ILIKE '%sao paulo%' OR geolocation_city ILIKE '%são paulo%';

SELECT geolocation_city, COUNT(*) AS count
FROM geolocation
WHERE geolocation_city ILIKE '%sao paulo%'
GROUP BY geolocation_city
LIMIT 10;

-- =============================================================================
-- PHASE 2: FACT TABLES (orders, reviews, payments)
-- =============================================================================

-- 2. ORDERS_RAW
DROP TABLE IF EXISTS orders_raw CASCADE;
CREATE TABLE orders_raw (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    order_status VARCHAR(20),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE INDEX idx_orders_purchase_ts ON orders_raw (order_purchase_timestamp);
CREATE INDEX idx_orders_status ON orders_raw (order_status);

-- Add FK after import - orders_raw
ALTER TABLE orders_raw DROP CONSTRAINT IF EXISTS orders_raw_customer_id_fkey;
ALTER TABLE orders_raw
ADD CONSTRAINT orders_raw_customer_id_fkey
FOREIGN KEY (customer_id) REFERENCES customers(customer_id);

-- Add FK to orders_clean (subset of orders_raw - only delivered orders)
ALTER TABLE orders_clean DROP CONSTRAINT IF EXISTS orders_clean_customer_id_fkey;
ALTER TABLE orders_clean
ADD CONSTRAINT orders_clean_customer_id_fkey
FOREIGN KEY (customer_id) REFERENCES customers(customer_id);

-- 3. ORDERS_CLEAN
DROP TABLE IF EXISTS orders_clean;
CREATE TABLE orders_clean AS
SELECT *
FROM orders_raw
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;

-- Ensure order_approved_at has valid timestamp (NULL check with explicit validation)
UPDATE orders_clean
SET order_approved_at = COALESCE(order_approved_at, order_purchase_timestamp + INTERVAL '1 day')
WHERE order_purchase_timestamp IS NOT NULL
  AND (order_approved_at IS NULL OR order_approved_at < order_purchase_timestamp);

-- Order status distribution
SELECT
    order_status,
    COUNT(*) AS total_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM orders_raw
GROUP BY order_status
ORDER BY total_orders DESC;

-- 6. ORDER_REVIEWS
DROP TABLE IF EXISTS order_reviews CASCADE;
CREATE TABLE order_reviews (
    review_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    review_score INTEGER CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

ALTER TABLE order_reviews
ADD CONSTRAINT order_reviews_order_id_fkey
FOREIGN KEY (order_id) REFERENCES orders_raw(order_id);

-- Check missing
SELECT
    COUNT(*) FILTER (WHERE review_score IS NULL) AS missing_score,
    COUNT(*) FILTER (WHERE review_comment_message IS NULL) AS missing_comment
FROM order_reviews;

DROP TABLE IF EXISTS order_reviews_clean;
CREATE TABLE order_reviews_clean AS
SELECT * FROM order_reviews WHERE review_score IS NOT NULL;

-- 7. ORDER_PAYMENTS (missing in your code - add this)
DROP TABLE IF EXISTS order_payments;
CREATE TABLE order_payments (
    order_id VARCHAR(32),
    payment_sequential INTEGER,
    payment_type VARCHAR(20),
    payment_installments INTEGER,
    payment_value NUMERIC
);

-- Add FK
ALTER TABLE order_payments
ADD CONSTRAINT order_payments_order_id_fkey
FOREIGN KEY (order_id) REFERENCES orders_raw(order_id);

-- =============================================================================
-- PHASE 3: AGGREGATIONS & CUSTOMER LEVEL TABLE
-- =============================================================================

-- 9. ORDER_REVENUE (pre-aggregate payments)
DROP TABLE IF EXISTS order_revenue;
CREATE TABLE order_revenue AS
SELECT
    order_id,
    SUM(payment_value) AS total_order_payment
FROM order_payments
GROUP BY order_id;

CREATE INDEX idx_order_revenue_order_id ON order_revenue (order_id);

-- Validation
SELECT
    (SELECT SUM(payment_value) FROM order_payments) AS raw_total_payments,
    (SELECT SUM(total_order_payment) FROM order_revenue) AS aggregated_revenue;

-- 10. ORDER_REVIEW_AGG
DROP TABLE IF EXISTS order_review_agg;
CREATE TABLE order_review_agg AS
SELECT
    order_id,
    AVG(review_score) AS avg_review_score_per_order,
    COUNT(*) AS review_count_per_order,
    MAX(review_creation_date) AS latest_review_date
FROM order_reviews_clean
GROUP BY order_id;

CREATE INDEX idx_order_review_agg_order_id ON order_review_agg (order_id);

-- 11. CUSTOMER_RETENTION_BASE
DROP TABLE IF EXISTS customer_retention_base;
CREATE TABLE customer_retention_base AS
SELECT
    c.customer_unique_id,
    MIN(o.order_purchase_timestamp) AS first_order_date,
    MAX(o.order_purchase_timestamp) AS last_order_date,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(orev.total_order_payment), 0) AS total_revenue,
    AVG(orev.total_order_payment) AS avg_order_value,
    AVG(orev_agg.avg_review_score_per_order) AS avg_review_score,
    AVG(EXTRACT(DAY FROM (o.order_delivered_customer_date - o.order_estimated_delivery_date))) AS avg_delivery_difference_days,
    AVG(CASE WHEN o.order_delivered_customer_date::date > o.order_estimated_delivery_date::date THEN 1.0 ELSE 0.0 END) AS late_delivery_rate
FROM customers c
INNER JOIN orders_clean o ON c.customer_id = o.customer_id
LEFT JOIN order_revenue orev ON o.order_id = orev.order_id
LEFT JOIN order_review_agg orev_agg ON o.order_id = orev_agg.order_id
GROUP BY c.customer_unique_id;

CREATE INDEX idx_customer_retention_unique_id ON customer_retention_base (customer_unique_id);

-- 12. ADD CHURN & RECENCY (dynamic)
DO $$
DECLARE v_last_date DATE;
BEGIN
    SELECT MAX(order_purchase_timestamp)::date INTO v_last_date FROM orders_clean;
    
    ALTER TABLE customer_retention_base
    DROP COLUMN IF EXISTS recency_days,
    DROP COLUMN IF EXISTS churn_label;

    ALTER TABLE customer_retention_base
    ADD COLUMN recency_days INTEGER,
    ADD COLUMN churn_label INTEGER;

    UPDATE customer_retention_base
    SET 
        recency_days = (v_last_date - last_order_date::date),
        churn_label = CASE 
            WHEN last_order_date + INTERVAL '90 days' < v_last_date THEN 1 
            ELSE 0 
        END;
END $$;

-- =============================================================================
-- PHASE 4: RFM & SEGMENTATION (your current working version)
-- =============================================================================

DROP TABLE IF EXISTS customer_rfm;
CREATE TABLE customer_rfm AS
SELECT
    customer_unique_id,
    recency_days,
    total_orders AS frequency,
    total_revenue AS monetary,
    NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
    NTILE(5) OVER (ORDER BY total_orders ASC) AS f_score,
    NTILE(5) OVER (ORDER BY total_revenue ASC) AS m_score
FROM customer_retention_base
WHERE total_revenue > 0;

ALTER TABLE customer_rfm ADD COLUMN rfm_segment VARCHAR(50);

UPDATE customer_rfm
SET rfm_segment = CASE
    WHEN r_score = 5 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 3 THEN 'Loyal Customers'
    WHEN r_score = 5 AND f_score <= 2 THEN 'New Customers'
    WHEN r_score >= 4 AND f_score >= 3 THEN 'Potential Loyalists'
    WHEN r_score = 3 AND f_score >= 3 THEN 'Need Attention'
    WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'Lost High Value'
    WHEN r_score <= 2 THEN 'Hibernating'
    ELSE 'Others'
END;

-- RFM validation
SELECT
    rfm_segment,
    COUNT(*) AS customers,
    ROUND(AVG(recency_days),1) AS avg_recency
FROM customer_rfm
GROUP BY rfm_segment
ORDER BY avg_recency ASC;

-- Churn rate per segment
SELECT
    r.rfm_segment,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN ret.churn_label = 1 THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(100.0 * SUM(CASE WHEN ret.churn_label = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM customer_rfm r
JOIN customer_retention_base ret ON r.customer_unique_id = ret.customer_unique_id
GROUP BY r.rfm_segment
ORDER BY churn_rate_pct DESC;

-- =============================================================================
-- PHASE 5: COHORT RETENTION (corrected month_offset using age)
-- =============================================================================

DROP TABLE IF EXISTS customer_cohorts;
CREATE TABLE customer_cohorts AS
SELECT
    c.customer_unique_id,
    DATE_TRUNC('month', MIN(o.order_purchase_timestamp))::date AS cohort_month
FROM customers c
JOIN orders_clean o ON c.customer_id = o.customer_id
GROUP BY c.customer_unique_id;

DROP VIEW IF EXISTS monthly_activity;
CREATE VIEW monthly_activity AS
SELECT DISTINCT
    coh.customer_unique_id,
    coh.cohort_month,
    DATE_TRUNC('month', o.order_purchase_timestamp)::date AS activity_month
FROM customer_cohorts coh
JOIN customers c ON coh.customer_unique_id = c.customer_unique_id
JOIN orders_clean o ON c.customer_id = o.customer_id;

DROP TABLE IF EXISTS cohort_retention;
CREATE TABLE cohort_retention AS
WITH cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
),
retention_raw AS (
    SELECT
        coh.cohort_month,
        ma.activity_month,
        EXTRACT(YEAR FROM age(ma.activity_month, coh.cohort_month))*12 +
        EXTRACT(MONTH FROM age(ma.activity_month, coh.cohort_month)) AS month_offset,
        COUNT(DISTINCT ma.customer_unique_id) AS active_customers
    FROM monthly_activity ma
    JOIN customer_cohorts coh ON ma.customer_unique_id = coh.customer_unique_id
    GROUP BY coh.cohort_month, ma.activity_month
)
SELECT
    r.cohort_month,
    r.month_offset,
    r.active_customers,
    cs.cohort_size,
    ROUND(100.0 * r.active_customers::numeric / cs.cohort_size, 2) AS retention_rate_pct
FROM retention_raw r
JOIN cohort_sizes cs ON r.cohort_month = cs.cohort_month
WHERE r.month_offset >= 0
ORDER BY r.cohort_month, r.month_offset;

-- Cohort pivot (for Tableau)
SELECT
    cohort_month,
    MAX(CASE WHEN month_offset = 0 THEN retention_rate_pct END) AS "Month 0",
    MAX(CASE WHEN month_offset = 1 THEN retention_rate_pct END) AS "Month 1",
    MAX(CASE WHEN month_offset = 2 THEN retention_rate_pct END) AS "Month 2",
    MAX(CASE WHEN month_offset = 3 THEN retention_rate_pct END) AS "Month 3",
    MAX(CASE WHEN month_offset = 4 THEN retention_rate_pct END) AS "Month 4",
    MAX(CASE WHEN month_offset = 5 THEN retention_rate_pct END) AS "Month 5"
FROM cohort_retention
WHERE cohort_month >= '2017-01-01'
GROUP BY cohort_month
ORDER BY cohort_month;

-- Average retention by month offset
SELECT
    month_offset,
    ROUND(AVG(retention_rate_pct),2) AS avg_retention_pct
FROM cohort_retention
WHERE month_offset <= 6
GROUP BY month_offset
ORDER BY month_offset;

-- =============================================================================
-- PHASE 6: EXPORTS FOR TABLEAU
-- =============================================================================
COPY (SELECT * FROM customer_retention_base) 
TO 'Data/customer_retention_base.csv' WITH CSV HEADER;

-- RFM
COPY (SELECT * FROM customer_rfm) 
TO 'Data/rfm_segments.csv' WITH CSV HEADER;

-- Cohort retention
COPY (SELECT * FROM cohort_retention) 
TO 'Data/cohort_retention.csv' WITH CSV HEADER;

-- Churn summary
COPY (
    SELECT 
        churn_label,
        COUNT(*) AS count,
        SUM(total_revenue) AS revenue
    FROM customer_retention_base
    GROUP BY churn_label
) TO 'Data/churn_summary.csv' WITH CSV HEADER;

-- Monthly revenue (create table first if missing)
DROP TABLE IF EXISTS monthly_revenue;
CREATE TABLE monthly_revenue AS
SELECT 
    DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
    SUM(orev.total_order_payment) AS revenue
FROM orders_clean o
JOIN order_revenue orev ON o.order_id = orev.order_id
GROUP BY month
ORDER BY month;

COPY (SELECT month, revenue FROM monthly_revenue ORDER BY month) 
TO 'Data/monthly_revenue.csv' WITH CSV HEADER;

-- One-time buyer percentage
SELECT
    COUNT(*) FILTER (WHERE total_orders = 1) * 100.0 / COUNT(*) AS one_time_pct
FROM customer_retention_base;

