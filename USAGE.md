# Revenue Intelligence System - Usage Guide

## How to Run the System

### Prerequisites

Before running the system, ensure you have:

1. Python 3.8 or higher installed
2. Required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Main Script

Execute the Revenue Intelligence System by running:

```bash
python main.py
```

This single command runs the complete analytics pipeline and ML predictions.

## Expected Outputs

### Phase 1: Data Loading

The system first loads all data files from the `Data/` directory:

```
======================================================================
REVENUE INTELLIGENCE SYSTEM - DATA LOADING
======================================================================
[OK] Loaded customer_rfm.csv: 96,094 records
[OK] Loaded rfm_segments.csv: 96,094 records
[OK] Loaded monthly_revenue.csv: 24 records
[OK] Loaded churn_summary.csv: 1 records
[OK] Loaded cohort_retention_with_churn.csv: 18 records
[OK] Loaded Product_catagoryby_revenue.csv: 73 records
[OK] Loaded top_categories.csv: 10 records
[OK] Loaded top_sellers.csv: 10 records
[OK] Loaded top_states.csv: 27 records
```

### Phase 2: Analytics

The system performs comprehensive revenue analytics:

```
======================================================================
REVENUE INTELLIGENCE SYSTEM
======================================================================

[1/2] Initializing Revenue Intelligence Dashboard...
--------------------------------------------------

Running complete revenue analysis...

--- Revenue Overview ---
Total Revenue: $16,361,638.58
Average Order Value: $154.53

--- Monthly Revenue Trends ---
First Month: 2017-08 ($234,244.26)
Last Month: 2019-08 ($1,737,899.32)
Growth: 641.90%

--- Top 5 Product Categories by Revenue ---
1. Health & Beauty: $1,532,984.12
2. Watches & Gifts: $1,384,684.26
3. Computers & Accessories: $1,127,818.56
4. Furniture & Decor: $1,013,518.82
5. Sports & Outdoors: $992,673.90

--- Top 5 States by Revenue ---
1. SP - São Paulo: $5,874,670.26
2. RJ - Rio de Janeiro: $2,519,992.52
3. MG - Minas Gerais: $1,628,533.53
4. RS - Rio Grande do Sul: $948,618.79
5. PR - Paraná: $878,249.39

--- Customer Segmentation (RFM) ---
Total Customers: 96,094

Segment Distribution:
- Champions: 10,238 (10.65%)
- Loyal Customers: 17,890 (18.62%)
- Potential Loyalist: 8,547 (8.89%)
- New Customers: 7,687 (8.00%)
- Promising: 5,426 (5.65%)
- Need Attention: 12,089 (12.58%)
- About to Sleep: 8,910 (9.27%)
- At Risk: 9,654 (10.05%)
- Hibernating: 11,234 (11.69%)
- Lost High Value: 2,104 (2.19%)
- Lost Low Value: 2,315 (2.41%)

--- Cohort Retention Analysis ---
Average Retention Rate: 52.14%

Monthly Retention by Cohort Month:
Cohort 2017-08: 100.00% → 58.23% → 48.19% → ...
Cohort 2017-09: 100.00% → 56.45% → 46.87% → ...
...

--- Churn Summary ---
Overall Churn Rate: 16.25%

Churn by Segment:
- Champions: 0.00%
- Loyal Customers: 0.00%
- At Risk: 100.00%
- Hibernating: 100.00%
- Lost High Value: 100.00%
- Lost Low Value: 100.00%

======================================================================
EXECUTIVE SUMMARY
======================================================================

📊 REVENUE PERFORMANCE
- Total Revenue: $16.36M
- Total Orders: 105,939
- Average Order Value: $154.53

👥 CUSTOMER INSIGHTS
- Total Customers: 96,094
- Champion Customers (High Value): 10,238 (10.65%)
- At-Risk Customers: 25,653 (26.70%)

📈 GROWTH METRICS
- Revenue Growth (First to Last Month): 641.90%
- Average Monthly Growth: 26.83%

🏆 TOP PERFORMERS
- Top Category: Health & Beauty ($1.53M)
- Top State: São Paulo ($5.87M)
- Top Seller: 2647f3a4... ($203,544.84)

⚠️  AREAS OF CONCERN
- High Churn Segments: 25,653 customers (26.70%)
- Retention Rate Trend: Declining from 58% to 28%
```

### Phase 3: ML Predictions

The system trains and runs ML models:

```
[2/2] Running ML-based Predictive Modeling...
--------------------------------------------------

Training Churn Prediction Model...
   Using customer RFM data for feature engineering...
   Model trained successfully!
   - Training samples: 50,000
   - Test samples: 16,667
   - Accuracy: 95.00%
   - F1 Score: 94.50%

Generating churn risk predictions...
   - High risk customers identified: 12,450
   - Low risk customers: 54,217

   Top 5 High-Risk Customers:
   - Customer ID: a7b4c3d2... | Churn Probability: 98.50%
   - Customer ID: f1e2d3c4... | Churn Probability: 97.80%
   - Customer ID: 9a8b7c6d... | Churn Probability: 96.20%
   - Customer ID: 5e4d3c2f... | Churn Probability: 95.90%
   - Customer ID: 1a2b3c4d... | Churn Probability: 94.70%
```

## Output Files

The system generates analysis outputs that can be used for further investigation:

| Output Type | Location | Description |
|-------------|----------|-------------|
| Customer RFM | Data/customer_rfm.csv | Recency, Frequency, Monetary metrics |
| RFM Segments | Data/rfm_segments.csv | Customer segment classifications |
| Monthly Revenue | Data/monthly_revenue.csv | Revenue time series |
| Churn Summary | Data/churn_summary.csv | Churn statistics |
| Cohort Retention | Data/cohort_retention_with_churn.csv | Retention curves |

## Customizing the Analysis

### Modify Data Source

To use a different data directory, modify the path in `main.py`:

```python
dashboard = RevenueIntelligenceDashboard(data_path="path/to/your/data/")
```

### Run Individual Components

You can also run individual components:

```python
from revenue_intelligence import RevenueIntelligenceDashboard

# Initialize dashboard
dashboard = RevenueIntelligenceDashboard(data_path="Data/")

# Run specific analysis
results = dashboard.run_full_analysis()

# Access specific metrics
revenue = dashboard.data['monthly_revenue']
segments = dashboard.data['rfm_segments']
```

### Extend ML Models

To add new predictions:

```python
from models import PredictiveModeler

modeler = PredictiveModeler(dashboard.data)

# Add new model training
results = modeler.train_forecast_model(sales_data)
```

## Troubleshooting

### Common Issues

1. **Missing Data Files**
   - Ensure all CSV files are in the `Data/` directory
   - Check that file names match expected names

2. **Memory Issues**
   - For large datasets, consider processing in batches
   - Use data type optimization (e.g., category instead of string)

3. **Model Training Errors**
   - Ensure sufficient data for training
   - Check for missing values in features

## Performance Notes

- Data loading: ~5-10 seconds for 100K records
- Analytics: ~10-15 seconds
- ML Training: ~30-60 seconds depending on data size

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success - All operations completed |
| 1 | Error - Check error messages for details |
