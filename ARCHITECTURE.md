# Revenue Intelligence System - Architecture

## System Overview

The Revenue Intelligence System is a modular analytics platform designed to process e-commerce data and generate actionable business insights through statistical analysis and machine learning.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REVENUE INTELLIGENCE SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        PRESENTATION LAYER                          │    │
│  │                                                                     │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │    │
│  │   │  main.py    │    │  README.md  │    │   USAGE.md          │   │    │
│  │   └─────────────┘    └─────────────┘    └─────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                        │
│                                      ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        BUSINESS LOGIC LAYER                         │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │              RevenueIntelligenceDashboard                     │  │    │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │  │    │
│  │  │  │RevenueAnalytics │  │RFMSegmentation │  │CohortAnalysis│  │  │    │
│  │  │  └─────────────────┘  └─────────────────┘  └──────────────┘  │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │                   PredictiveModeler                           │  │    │
│  │  │  ┌──────────────┐  ┌───────────────┐  ┌───────────────────┐  │  │    │
│  │  │  │Churn Model  │  │ Sales Forecast│  │   CLV Model      │  │  │    │
│  │  │  └──────────────┘  └───────────────┘  └───────────────────┘  │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                        │
│                                      ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          DATA LAYER                                │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │                  RevenueDataLoader                           │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │                        Data Files                           │  │    │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │  │    │
│  │  │  │ customer_  │ │   rfm_     │ │  monthly_  │ │  churn_  │  │  │    │
│  │  │  │ rfm.csv    │ │ segments.csv│ │ revenue.csv│ │ summary  │  │  │    │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘  │  │    │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │  │    │
│  │  │  │  cohort_   │ │  product_  │ │   top_    │ │   top_   │  │  │    │
│  │  │  │ retention │ │  revenue   │ │ categories│ │ sellers  │  │  │    │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘  │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   Raw Data   │────▶│  Data Loader      │────▶│  In-Memory Data  │
│   (CSV)      │     │  (Pandas)         │     │  (DataFrames)    │
└──────────────┘     └───────────────────┘     └──────────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────┐
                        │                               │                   │
                        ▼                               ▼                   ▼
              ┌─────────────────┐          ┌──────────────────┐    ┌────────────────┐
              │   Analytics    │          │  Segmentation    │    │    ML Models   │
              │   Engine       │          │  Engine          │    │    Training    │
              └─────────────────┘          └──────────────────┘    └────────────────┘
                        │                               │                   │
                        └───────────────────────────────┼───────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────────┐
                                              │   Insights &        │
                                              │   Predictions      │
                                              └─────────────────────┘
```

## Component Descriptions

### 1. Presentation Layer

| Component | Description |
|-----------|-------------|
| [`main.py`](main.py) | Entry point script that orchestrates the entire system |
| [`README.md`](README.md) | Project documentation and user guide |
| [`USAGE.md`](USAGE.md) | Detailed usage instructions |

### 2. Business Logic Layer

#### RevenueIntelligenceDashboard

The main analytics class providing:

- **RevenueAnalytics**: Calculates revenue metrics, trends, and breakdowns
- **RFMSegmentation**: Performs RFM analysis and customer segmentation
- **CohortAnalysis**: Tracks customer retention by cohort
- **ChurnAnalysis**: Analyzes customer churn patterns

#### PredictiveModeler

Machine learning module providing:

- **ChurnModel**: Random Forest classifier for churn prediction
- **ForecastModel**: Sales forecasting using regression
- **CLVModel**: Customer Lifetime Value prediction

### 3. Data Layer

#### RevenueDataLoader

- Loads CSV files from the Data directory
- Handles data preprocessing and type conversion
- Provides data validation

#### Data Files

| File | Description |
|------|-------------|
| `customer_rfm.csv` | Customer RFM metrics |
| `rfm_segments.csv` | Customer segment classifications |
| `monthly_revenue.csv` | Monthly revenue data |
| `churn_summary.csv` | Churn statistics |
| `cohort_retention_with_churn.csv` | Cohort retention analysis |
| `Product_catagoryby_revenue.csv` | Revenue by product category |
| `top_categories.csv` | Top performing categories |
| `top_sellers.csv` | Top performing sellers |
| `top_states.csv` | Revenue by state |

## Technology Stack

### Programming Language
- **Python 3.8+**: Core programming language

### Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| pandas | >=1.3.0 | Data manipulation and analysis |
| numpy | >=1.20.0 | Numerical computing |
| scikit-learn | >=0.24.0 | Machine learning algorithms |

### ML Algorithms

| Model | Algorithm | Use Case |
|-------|-----------|----------|
| Churn Prediction | Random Forest Classifier | Binary classification (churn/not churn) |
| Sales Forecasting | Random Forest Regressor | Regression for revenue prediction |
| CLV Prediction | Random Forest Regressor | Customer value estimation |

### Data Processing Pipeline

1. **Data Ingestion**: CSV files loaded via pandas
2. **Data Cleaning**: Handle missing values, type conversions
3. **Feature Engineering**: Create RFM features, aggregations
4. **Model Training**: Train/test split, cross-validation
5. **Prediction**: Generate insights and forecasts

## Module Dependencies

```
main.py
├── revenue_intelligence.py
│   ├── pandas
│   ├── numpy
│   └── datetime
└── models
    └── predictive_models.py
        ├── pandas
        ├── numpy
        └── scikit-learn
```

## Scalability Considerations

The system is designed with modularity in mind:

- **Data Layer**: Can be extended to use databases (SQL, NoSQL)
- **Analytics**: New metrics can be added to the dashboard
- **ML Models**: Easy to swap algorithms or add new models
- **Presentation**: Can be extended to web dashboards or APIs
