# Revenue Intelligence - Monetization Guide

This guide explains how to monetize your Revenue Intelligence System.

## Table of Contents
1. [Quick Start](#quick-start)
2. [API Service](#api-service)
3. [Report Export](#report-export)
4. [Campaign Generation](#campaign-generation)
5. [Pricing Tiers](#pricing-tiers)
6. [Business Models](#business-models)

---

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Dashboard
```bash
streamlit run streamlit_app.py
```

### Start the API Server
```bash
uvicorn api_service:app --reload
```

### Generate Reports
```bash
python report_exporter.py
```

---

## API Service

The API service provides programmatic access to all analytics features.

### Running the API
```bash
uvicorn api_service:app --host 0.0.0.0 --port 8000
```

### API Documentation
Once running, visit: `http://localhost:8000/docs`

### Example API Calls

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Get Revenue Analytics
```bash
curl http://localhost:8000/analytics/revenue
```

#### Get All Customers with Scores
```bash
curl "http://localhost:8000/customers?limit=10"
```

#### Score a New Customer (Real-time)
```bash
curl -X POST http://localhost:8000/customers/score \
  -H "Content-Type: application/json" \
  -d '{
    "monetary": 500.00,
    "frequency": 5,
    "avg_review_score": 4.5,
    "avg_installments": 3.0,
    "credit_card_rate": 0.8,
    "late_delivery_rate": 0.1
  }'
```

#### Get Churn Predictions
```bash
curl "http://localhost:8000/churn/predictions?risk_level=high&limit=100"
```

#### Generate Retention Campaign
```bash
curl -X POST http://localhost:8000/campaigns/generate \
  -H "Content-Type: application/json" \
  -d '{
    "target_segment": "At Risk",
    "budget": 1000.00,
    "channel": "email"
  }'
```

#### Get Pricing Tiers
```bash
curl http://localhost:8000/pricing
```

---

## Report Export

### Python API
```python
from report_exporter import generate_excel_report, generate_pdf_report

# Generate Excel
generate_excel_report("revenue_report.xlsx")

# Generate PDF
generate_pdf_report("revenue_report.pdf", title="Monthly Report")
```

### From Command Line
```bash
python report_exporter.py
```

### Supported Formats
- **Excel**: Multi-sheet workbook with formatted tables
- **PDF**: Professional report with charts placeholders and insights

---

## Campaign Generation

The campaign generator creates automated retention campaigns based on customer segments.

### Supported Segments
- Champions
- Loyal Customers
- Potential Loyalist
- New Customers
- At Risk
- Cant Lose Them
- Lost

### Supported Channels
- Email (85% reach)
- SMS (95% reach)
- Push Notification (70% reach)
- Social Media (60% reach)

### Campaign Metrics
The API returns:
- Estimated reach
- Expected conversions
- Expected revenue
- ROI percentage
- Message templates
- Action items

---

## Pricing Tiers

### Starter (Free)
- 100 API calls/month
- Basic analytics
- Email support

### Growth ($99/month)
- 10,000 API calls/month
- Full customer scoring
- Campaign generation
- Priority support

### Enterprise ($499/month)
- Unlimited API calls
- Custom ML models
- Dedicated account manager
- SLA guarantee
- Custom integrations

---

## Business Models

### 1. SaaS Platform
Host the API and charge subscription fees for access.

**Revenue Streams:**
- Monthly/annual subscriptions
- Usage overages
- Premium features
- Custom reports

### 2. White-Label Solution
Customize for specific clients and charge implementation fees.

**Revenue Streams:**
- Setup fees
- Monthly licensing
- Support contracts
- Custom development

### 3. Consulting Services
Use the analytics to provide consulting services.

**Revenue Streams:**
- Analysis projects
- Strategy workshops
- Implementation support
- Training

### 4. Data Products
Create derived data products for other businesses.

**Revenue Streams:**
- Industry benchmarks
- Trend reports
- Customer lists
- Integration feeds

### 5. API Marketplace
List on API marketplaces for broader reach.

**Revenue Streams:**
- Per-call pricing
- Tiered plans
- Enterprise deals

---

## Implementation Checklist

- [ ] Deploy API to cloud (AWS/GCP/Azure)
- [ ] Set up authentication (API keys, OAuth)
- [ ] Implement usage tracking
- [ ] Create billing system
- [ ] Build documentation portal
- [ ] Set up monitoring/alerting
- [ ] Create support system
- [ ] Implement rate limiting

---

## Tech Stack Recommendations

| Component | Recommended |
|-----------|-------------|
| API Hosting | AWS Lambda + API Gateway, or Railway, Render |
| Authentication | Auth0, Firebase Auth |
| Billing | Stripe, Paddle |
| Monitoring | Datadog, New Relic |
| Support | Intercom, Zendesk |
| CDN | Cloudflare |

---

## Contact

For questions about monetization strategies, consult with the development team.
