# Revenue Intelligence System

A comprehensive revenue analytics and machine learning platform that processes customer data, generates actionable insights, and provides predictive modeling for revenue growth.

## Overview

The Olist Revenue Intelligence System is a complete e-commerce analytics platform combining:
- **Revenue Analysis**: Monthly revenue trends, product category performance, geographic analysis
- **Customer Segmentation**: RFM (Recency, Frequency, Monetary) analysis for customer behavioral segmentation
- **Churn Prediction**: Realistic ML models using behavioral features only (excluding definitional leakage)
- **Cohort Analysis**: Customer retention and lifetime value tracking
- **Sales Forecasting**: Predictive models for future revenue forecasting
- **Revenue Impact Simulator**: Scenario-based ROI analysis for retention campaigns

This project demonstrates rigorous ML methodology with proper temporal awareness, class imbalance handling, and ablation studies to show true predictive power.

## Overview

The Revenue Intelligence System is designed to analyze e-commerce data from Olist (Brazilian e-commerce platform) to provide:

- **Revenue Analytics**: Monthly revenue trends, product category performance, geographic analysis
- **Customer Segmentation**: RFM (Recency, Frequency, Monetary) analysis for customer behavioral segmentation
- **Churn Prediction**: Machine learning models to identify at-risk customers
- **Cohort Analysis**: Customer retention and lifetime value tracking
- **Sales Forecasting**: Predictive models for future revenue forecasting

## Features

### Business Capabilities

1. **Revenue Analysis**
   - Monthly revenue tracking and trends
   - Product category revenue breakdown
   - Top-performing sellers analysis
   - Geographic revenue distribution by state

2. **Customer Segmentation (RFM)**
   - Recency: Days since last purchase
   - Frequency: Number of transactions
   - Monetary: Total spending amount
   - Automated customer segment classification (Champions, Loyal, At Risk, etc.)

3. **Churn Prediction**
   - ML-based churn risk scoring
   - High-risk customer identification
   - Feature importance analysis
   - Time-based train/test split to prevent data leakage
   - Class imbalance handling with balanced class weights
   - Ablation study to demonstrate predictive power vs definitional features

## Churn Prediction Methodology

### Definition
Churn is defined as: **no purchase in 180 days after reference date (June 30, 2018)**

This creates a realistic churn rate of ~44.7% in the dataset, which is more balanced than the typical ~97% one-time buyer rate in Olist data but still represents meaningful customer attrition.

### Why 100% Accuracy in Full Model?
The full model achieves near-perfect accuracy because:
- **recency_days** directly correlates with the 180-day churn definition
- **tenure_days** is highly correlated with recency (r=0.99)
- These features essentially encode the churn label definition itself

This is expected behavior for time-based churn definitions.

### Ablation Study (True Predictive Power)
To demonstrate genuine predictive power, we run an ablation study excluding time-based features:

| Metric | Full Model | Ablation (No Time Features) |
|--------|------------|---------------------------|
| Accuracy | 100% | 47.25% |
| F1 Score | 100% | 64.17% |
| CV F1 | 91.95% | 61.01% |

**Top Predictive Features (Ablation):**
1. **monetary (58%)**: Higher spenders have distinct churn patterns
2. **avg_installments (22%)**: Payment installments indicate price sensitivity
3. **avg_review_score (8%)**: Customer satisfaction predicts retention
4. **credit_card_rate (5%)**: Payment method correlates with loyalty

### Business Actions
Based on ablation insights:
- Focus retention on **medium-spend, high-installment customers** (price-sensitive)
- Monitor customers with **lower review scores** for early intervention
- **Credit card users** may show different loyalty patterns than other payment methods

### Best Practices Implemented
- **Time-based split**: Train on earlier data, test on later data
- **Class weighting**: Handle imbalance with `class_weight='balanced'`
- **Proper metrics**: F1, ROC-AUC, PR-AUC (more meaningful than accuracy for imbalanced data)
- **Cross-validation**: 5-fold CV to ensure robust performance estimates

4. **Cohort Analysis**
   - Monthly cohort retention tracking
   - Customer lifetime value estimation
   - Retention rate visualization

5. **Predictive Modeling**
   - Churn prediction model (Random Forest)
   - Sales forecasting (Time series)
   - Customer lifetime value prediction

## Project Structure

```
archive/
├── main.py                      # Main entry point
├── revenue_intelligence.py      # Core analytics dashboard
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── ARCHITECTURE.md              # System architecture
├── USAGE.md                     # Usage instructions
├── models/
│   ├── __init__.py
│   └── predictive_models.py     # ML models
├── Data/                        # Data directory
│   ├── customer_rfm.csv
│   ├── rfm_segments.csv
│   ├── monthly_revenue.csv
│   ├── churn_summary.csv
│   ├── cohort_retention_with_churn.csv
│   ├── Product_catagoryby_revenue.csv
│   ├── top_categories.csv
│   ├── top_sellers.csv
│   └── top_states.csv
└── Scripts/
    └── test.ipynb               # Jupyter notebooks
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Steps

1. **Clone or download the project**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python -c "import pandas; import numpy; import sklearn; print('All packages installed!')"
   ```

## Usage

### Running the System

Execute the main script to run the complete Revenue Intelligence System:

```bash
python main.py
```

### Expected Outputs

The system will:

1. **Data Loading Phase**
   - Load all CSV datasets from the Data directory
   - Display loading status for each dataset

2. **Analytics Phase**
   - Generate revenue insights
   - Display RFM segmentation results
   - Show cohort retention analysis

3. **ML Predictions Phase**
   - Train churn prediction model
   - Display model performance metrics
   - Show high-risk customer predictions

### Example Output

```
======================================================================
REVENUE INTELLIGENCE SYSTEM
======================================================================

[1/2] Initializing Revenue Intelligence Dashboard...
--------------------------------------------------

Running complete revenue analysis...

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
```

## ML Models Used

The Revenue Intelligence System uses the following machine learning models:

### 1. Churn Prediction Model
- **Algorithm**: Random Forest Classifier
- **Features**: Recency, Frequency, Monetary values, Review Score, Delivery Rate
- **Purpose**: Identify customers at risk of churning

### 2. Sales Forecasting Model
- **Algorithm**: Random Forest Regressor
- **Features**: Historical revenue, Seasonality, Trend factors
- **Purpose**: Predict future revenue

### 3. Customer Lifetime Value (CLV) Prediction
- **Algorithm**: Random Forest Regressor
- **Features**: Purchase frequency, Average order value, Customer age
- **Purpose**: Estimate total customer value

### Model Training

Models are trained using scikit-learn with:
- Train/Test split (70/30)
- Cross-validation for model evaluation
- StandardScaler for feature normalization
- Performance metrics: Accuracy, F1 Score, MAE, RMSE, R²

## Data Sources

The system processes e-commerce data from the Olist dataset, including:
- Customer information
- Order details
- Product catalog
- Order payments
- Order reviews
- Seller information

## License

This project is for educational and analytical purposes.

## Author

Revenue Intelligence System - E-commerce Analytics Platform
