"""
Revenue Intelligence System
============================
A comprehensive revenue analytics and intelligence platform
that processes customer data, generates insights, and provides
actionable recommendations for revenue growth.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# ============================================================================
# DATA LOADING MODULE
# ============================================================================

class RevenueDataLoader:
    """Handles loading and initial processing of revenue data."""
    
    def __init__(self, data_path: str = "Data/"):
        self.data_path = data_path
        self.data = {}
        
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load all available datasets."""
        print("=" * 70)
        print("REVENUE INTELLIGENCE SYSTEM - DATA LOADING")
        print("=" * 70)
        
        # Load RFM data
        try:
            self.data['customer_rfm'] = pd.read_csv(f"{self.data_path}customer_rfm.csv")
            print(f"[OK] Loaded customer_rfm.csv: {len(self.data['customer_rfm']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading customer_rfm: {e}")
            
        # Load RFM segments
        try:
            self.data['rfm_segments'] = pd.read_csv(f"{self.data_path}rfm_segments.csv")
            print(f"[OK] Loaded rfm_segments.csv: {len(self.data['rfm_segments']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading rfm_segments: {e}")
            
        # Load monthly revenue
        try:
            self.data['monthly_revenue'] = pd.read_csv(f"{self.data_path}monthly_revenue.csv")
            self.data['monthly_revenue']['month'] = pd.to_datetime(self.data['monthly_revenue']['month'])
            print(f"[OK] Loaded monthly_revenue.csv: {len(self.data['monthly_revenue']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading monthly_revenue: {e}")
            
        # Load churn data
        try:
            self.data['churn_summary'] = pd.read_csv(f"{self.data_path}churn_summary.csv")
            print(f"[OK] Loaded churn_summary.csv: {len(self.data['churn_summary']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading churn_summary: {e}")
            
        # Load cohort retention
        try:
            self.data['cohort_retention'] = pd.read_csv(f"{self.data_path}cohort_retention_with_churn.csv")
            self.data['cohort_retention']['cohort_month'] = pd.to_datetime(
                self.data['cohort_retention']['cohort_month']
            )
            print(f"[OK] Loaded cohort_retention_with_churn.csv: {len(self.data['cohort_retention']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading cohort_retention: {e}")
            
        # Load product category revenue
        try:
            self.data['product_revenue'] = pd.read_csv(f"{self.data_path}Product_catagoryby_revenue.csv")
            print(f"[OK] Loaded Product_catagoryby_revenue.csv: {len(self.data['product_revenue']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading product_revenue: {e}")
            
        # Load top categories
        try:
            self.data['top_categories'] = pd.read_csv(f"{self.data_path}top_categories.csv")
            print(f"[OK] Loaded top_categories.csv: {len(self.data['top_categories']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading top_categories: {e}")
            
        # Load top sellers
        try:
            self.data['top_sellers'] = pd.read_csv(f"{self.data_path}top_sellers.csv")
            print(f"[OK] Loaded top_sellers.csv: {len(self.data['top_sellers']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading top_sellers: {e}")
            
        # Load top states
        try:
            self.data['top_states'] = pd.read_csv(f"{self.data_path}top_states.csv")
            print(f"[OK] Loaded top_states.csv: {len(self.data['top_states']):,} records")
        except Exception as e:
            print(f"[ERROR] Error loading top_states: {e}")
            
        print(f"\n[OK] Total datasets loaded: {len(self.data)}")
        return self.data


# ============================================================================
# RFM ANALYTICS MODULE
# ============================================================================

class RFMAnalyzer:
    """Performs Recency, Frequency, Monetary analysis on customer data."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.rfm_df = data.get('customer_rfm', pd.DataFrame())
        self.segments_df = data.get('rfm_segments', pd.DataFrame())
        
    def get_segment_distribution(self) -> pd.DataFrame:
        """Analyze RFM segment distribution."""
        if self.rfm_df.empty:
            return pd.DataFrame()
            
        segment_dist = self.rfm_df['rfm_segment'].value_counts().reset_index()
        segment_dist.columns = ['Segment', 'Customer_Count']
        segment_dist['Percentage'] = (
            segment_dist['Customer_Count'] / segment_dist['Customer_Count'].sum() * 100
        ).round(2)
        
        # Calculate revenue by segment
        segment_revenue = self.rfm_df.groupby('rfm_segment')['monetary'].sum().reset_index()
        segment_revenue.columns = ['Segment', 'Total_Revenue']
        
        segment_dist = segment_dist.merge(segment_revenue, on='Segment')
        segment_dist['Avg_Revenue_Per_Customer'] = (
            segment_dist['Total_Revenue'] / segment_dist['Customer_Count']
        ).round(2)
        
        return segment_dist.sort_values('Total_Revenue', ascending=False)
    
    def get_rfm_scores_analysis(self) -> Dict:
        """Analyze RFM score distributions."""
        if self.rfm_df.empty:
            return {}
            
        return {
            'recency': {
                'mean': self.rfm_df['recency_days'].mean(),
                'median': self.rfm_df['recency_days'].median(),
                'min': self.rfm_df['recency_days'].min(),
                'max': self.rfm_df['recency_days'].max(),
                'std': self.rfm_df['recency_days'].std()
            },
            'frequency': {
                'mean': self.rfm_df['frequency'].mean(),
                'median': self.rfm_df['frequency'].median(),
                'max': self.rfm_df['frequency'].max(),
                'total_orders': self.rfm_df['frequency'].sum()
            },
            'monetary': {
                'mean': self.rfm_df['monetary'].mean(),
                'median': self.rfm_df['monetary'].median(),
                'min': self.rfm_df['monetary'].min(),
                'max': self.rfm_df['monetary'].max(),
                'total': self.rfm_df['monetary'].sum()
            }
        }
    
    def get_high_value_customers(self, top_pct: float = 0.1) -> pd.DataFrame:
        """Identify top high-value customers."""
        if self.rfm_df.empty:
            return pd.DataFrame()
            
        threshold = self.rfm_df['monetary'].quantile(1 - top_pct)
        high_value = self.rfm_df[self.rfm_df['monetary'] >= threshold].copy()
        return high_value.sort_values('monetary', ascending=False)
    
    def get_churn_risk_analysis(self) -> Dict:
        """Analyze churn risk based on RFM patterns."""
        if self.rfm_df.empty:
            return {}
            
        # High recency (haven't purchased in a while) + low frequency = high churn risk
        high_risk = self.rfm_df[
            (self.rfm_df['recency_days'] > self.rfm_df['recency_days'].quantile(0.75)) &
            (self.rfm_df['frequency'] == 1)
        ]
        
        return {
            'high_risk_count': len(high_risk),
            'high_risk_revenue': high_risk['monetary'].sum(),
            'risk_percentage': len(high_risk) / len(self.rfm_df) * 100
        }


# ============================================================================
# CUSTOMER SEGMENTATION MODULE
# ============================================================================

class CustomerSegmentor:
    """Advanced customer segmentation and lifecycle analysis."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.rfm_df = data.get('customer_rfm', pd.DataFrame())
        
    def get_segment_characteristics(self) -> Dict[str, Dict]:
        """Get detailed characteristics of each segment."""
        if self.rfm_df.empty:
            return {}
            
        segments = self.rfm_df['rfm_segment'].unique()
        characteristics = {}
        
        for segment in segments:
            seg_data = self.rfm_df[self.rfm_df['rfm_segment'] == segment]
            characteristics[segment] = {
                'customer_count': len(seg_data),
                'total_revenue': seg_data['monetary'].sum(),
                'avg_revenue': seg_data['monetary'].mean(),
                'avg_recency': seg_data['recency_days'].mean(),
                'avg_frequency': seg_data['frequency'].mean(),
                'revenue_share': seg_data['monetary'].sum() / self.rfm_df['monetary'].sum() * 100
            }
            
        return characteristics
    
    def segment_customers_for_marketing(self) -> Dict[str, List[str]]:
        """Create marketing-ready customer segments."""
        if self.rfm_df.empty:
            return {}
            
        segments = {
            'champions': [],
            'loyal_customers': [],
            'potential_loyalists': [],
            'new_customers': [],
            'need_attention': [],
            'at_risk': [],
            'hibernating': [],
            'lost': []
        }
        
        # Map RFM segments to marketing actions
        segment_mapping = {
            'Champions': 'champions',
            'Loyal Customers': 'loyal_customers',
            'Potential Loyalist': 'potential_loyalists',
            'New Customers': 'new_customers',
            'Need Attention': 'need_attention',
            'At Risk': 'at_risk',
            'Hibernating': 'hibernating',
            'Lost': 'lost',
            'Lost High Value': 'lost'
        }
        
        for orig_seg, market_seg in segment_mapping.items():
            if market_seg in segments:
                customers = self.rfm_df[
                    self.rfm_df['rfm_segment'] == orig_seg
                ]['customer_unique_id'].tolist()
                segments[market_seg].extend(customers)
        
        return {k: v for k, v in segments.items() if v}


# ============================================================================
# REVENUE ANALYTICS MODULE
# ============================================================================

class RevenueAnalytics:
    """Comprehensive revenue analysis and forecasting."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.monthly_revenue = data.get('monthly_revenue', pd.DataFrame())
        
    def get_revenue_summary(self) -> Dict:
        """Get overall revenue summary."""
        if self.monthly_revenue.empty:
            return {}
            
        return {
            'total_revenue': self.monthly_revenue['revenue'].sum(),
            'avg_monthly_revenue': self.monthly_revenue['revenue'].mean(),
            'max_monthly_revenue': self.monthly_revenue['revenue'].max(),
            'min_monthly_revenue': self.monthly_revenue['revenue'].min(),
            'growth_rate': self._calculate_growth_rate(),
            'months_of_data': len(self.monthly_revenue)
        }
    
    def _calculate_growth_rate(self) -> float:
        """Calculate growth rate using CAGR formula for more realistic metrics."""
        if len(self.monthly_revenue) < 2:
            return 0.0
            
        revenue = self.monthly_revenue['revenue'].values
        
        # Filter out months with very low revenue (< $10,000) as they represent data issues
        MIN_REVENUE_THRESHOLD = 10000
        
        # Find months with substantial revenue
        valid_indices = [i for i, r in enumerate(revenue) if r >= MIN_REVENUE_THRESHOLD]
        
        if len(valid_indices) < 2:
            return 0.0
        
        first_idx = valid_indices[0]
        last_idx = valid_indices[-1]
        
        first_value = revenue[first_idx]
        last_value = revenue[last_idx]
        periods = last_idx - first_idx
        
        if periods <= 0 or first_value <= 0:
            return 0.0
        
        # Calculate CAGR: ((End Value / Start Value) ^ (1/n)) - 1
        cagr = ((last_value / first_value) ** (1 / periods) - 1) * 100
        
        return round(cagr, 2)
    
    def get_revenue_trends(self) -> pd.DataFrame:
        """Get revenue trends with moving averages."""
        if self.monthly_revenue.empty:
            return pd.DataFrame()
            
        df = self.monthly_revenue.copy()
        df['month'] = pd.to_datetime(df['month'])
        df = df.sort_values('month')
        df['rolling_avg_3m'] = df['revenue'].rolling(window=3).mean()
        df['rolling_avg_6m'] = df['revenue'].rolling(window=6).mean()
        df['mom_growth'] = df['revenue'].pct_change() * 100
        
        return df
    
    def forecast_revenue(self, periods: int = 3) -> Dict:
        """Simple revenue forecasting using moving average."""
        if self.monthly_revenue.empty or len(self.monthly_revenue) < 3:
            return {}
            
        df = self.get_revenue_trends()
        last_date = df['month'].max()
        last_avg = df['rolling_avg_3m'].iloc[-1]
        
        forecasts = []
        for i in range(1, periods + 1):
            forecast_date = last_date + pd.DateOffset(months=i)
            # Simple forecast based on recent trend
            growth_factor = 1 + (df['mom_growth'].iloc[-3:].mean() / 100)
            forecast_value = last_avg * (growth_factor ** i)
            forecasts.append({
                'month': forecast_date,
                'forecasted_revenue': forecast_value
            })
            
        return {
            'forecasts': forecasts,
            'confidence': 'medium',
            'method': 'moving_average_with_growth'
        }
    
    def get_seasonality_analysis(self) -> Dict:
        """Analyze revenue seasonality."""
        if self.monthly_revenue.empty:
            return {}
            
        df = self.monthly_revenue.copy()
        df['month'] = pd.to_datetime(df['month'])
        df['month_num'] = df['month'].dt.month
        
        monthly_avg = df.groupby('month_num')['revenue'].mean()
        
        return {
            'best_month': monthly_avg.idxmax(),
            'best_month_revenue': monthly_avg.max(),
            'worst_month': monthly_avg.idxmin(),
            'worst_month_revenue': monthly_avg.min(),
            'seasonality_index': (monthly_avg / monthly_avg.mean()).to_dict()
        }


# ============================================================================
# COHORT ANALYSIS MODULE
# ============================================================================

class CohortAnalyzer:
    """Cohort and retention analysis."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.cohort_df = data.get('cohort_retention', pd.DataFrame())
        
    def get_retention_summary(self) -> Dict:
        """Get overall retention summary."""
        if self.cohort_df.empty:
            return {}
            
        active_retention = self.cohort_df[
            self.cohort_df['churn_label'] == 1
        ]
        
        return {
            'total_cohorts': self.cohort_df['cohort_month'].nunique(),
            'avg_retention_rate': active_retention['retention_rate_pct'].mean(),
            'max_retention_rate': active_retention['retention_rate_pct'].max(),
            'min_retention_rate': active_retention[active_retention['retention_rate_pct'] > 0]['retention_rate_pct'].min(),
            'months_of_data': active_retention['month_offset'].max()
        }
    
    def get_cohort_performance(self) -> pd.DataFrame:
        """Get performance metrics by cohort."""
        if self.cohort_df.empty:
            return pd.DataFrame()
            
        cohort_summary = self.cohort_df.groupby('cohort_month').agg({
            'active_customers': 'sum',
            'cohort_size': 'first'
        }).reset_index()
        
        cohort_summary['initial_to_current_ratio'] = (
            cohort_summary['active_customers'] / cohort_summary['cohort_size'] * 100
        ).round(2)
        
        return cohort_summary.sort_values('cohort_month', ascending=False)


# ============================================================================
# CHURN ANALYSIS MODULE
# ============================================================================

class ChurnAnalyzer:
    """Customer churn analysis and prediction insights."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.churn_df = data.get('churn_summary', pd.DataFrame())
        
    def get_churn_metrics(self) -> Dict:
        """Get key churn metrics."""
        if self.churn_df.empty:
            return {}
            
        total_customers = self.churn_df['count'].sum()
        churned = self.churn_df[self.churn_df['churn_label'] == 1]['count'].sum()
        active = self.churn_df[self.churn_df['churn_label'] == 0]['count'].sum()
        
        churned_revenue = self.churn_df[self.churn_df['churn_label'] == 1]['revenue'].sum()
        active_revenue = self.churn_df[self.churn_df['churn_label'] == 0]['revenue'].sum()
        
        return {
            'total_customers': total_customers,
            'churned_customers': churned,
            'active_customers': active,
            'churn_rate_pct': (churned / total_customers * 100),
            'retention_rate_pct': (active / total_customers * 100),
            'churned_revenue': churned_revenue,
            'active_revenue': active_revenue,
            'revenue_at_risk': churned_revenue,
            'avg_revenue_per_churned': churned_revenue / churned if churned > 0 else 0,
            'avg_revenue_per_active': active_revenue / active if active > 0 else 0
        }


# ============================================================================
# PRODUCT ANALYTICS MODULE
# ============================================================================

class ProductAnalytics:
    """Product category and seller performance analysis."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.product_df = data.get('product_revenue', pd.DataFrame())
        self.top_cat_df = data.get('top_categories', pd.DataFrame())
        self.top_sellers_df = data.get('top_sellers', pd.DataFrame())
        
    def get_top_categories(self, n: int = 10) -> pd.DataFrame:
        """Get top performing categories."""
        if self.top_cat_df.empty:
            return pd.DataFrame()
        return self.top_cat_df.head(n)
    
    def get_top_sellers(self, n: int = 10) -> pd.DataFrame:
        """Get top performing sellers."""
        if self.top_sellers_df.empty:
            return pd.DataFrame()
        return self.top_sellers_df.head(n)
    
    def get_category_insights(self) -> Dict:
        """Get strategic insights from category performance."""
        if self.top_cat_df.empty:
            return {}
            
        return {
            'total_categories': len(self.top_cat_df),
            'top_category': self.top_cat_df.iloc[0]['product_category_name_english'],
            'top_category_revenue': self.top_cat_df.iloc[0]['revenue'],
            'top_category_margin': self.top_cat_df.iloc[0]['margin_pct'],
            'avg_margin_all_categories': self.top_cat_df['margin_pct'].mean(),
            'high_margin_categories': self.top_cat_df[
                self.top_cat_df['margin_pct'] > self.top_cat_df['margin_pct'].quantile(0.75)
            ]['product_category_name_english'].tolist()[:5]
        }
    
    def get_seller_insights(self) -> Dict:
        """Get strategic insights from seller performance."""
        if self.top_sellers_df.empty:
            return {}
            
        return {
            'total_top_sellers': len(self.top_sellers_df),
            'top_seller': self.top_sellers_df.iloc[0]['seller_id'][:8] + '...',
            'top_seller_revenue': self.top_sellers_df.iloc[0]['revenue'],
            'avg_review_top_sellers': self.top_sellers_df['avg_review'].mean(),
            'top_state': self.top_sellers_df['seller_state'].mode().iloc[0] if not self.top_sellers_df.empty else 'N/A'
        }


# ============================================================================
# REVENUE INTELLIGENCE DASHBOARD
# ============================================================================

class RevenueIntelligenceDashboard:
    """Main dashboard that integrates all analytics modules."""
    
    def __init__(self, data_path: str = "Data/"):
        self.loader = RevenueDataLoader(data_path)
        self.data = self.loader.load_all_data()
        
        # Initialize all analyzers
        self.rfm = RFMAnalyzer(self.data)
        self.segmentor = CustomerSegmentor(self.data)
        self.revenue = RevenueAnalytics(self.data)
        self.cohort = CohortAnalyzer(self.data)
        self.churn = ChurnAnalyzer(self.data)
        self.product = ProductAnalytics(self.data)
        
    def generate_executive_summary(self) -> Dict:
        """Generate comprehensive executive summary."""
        print("\n" + "=" * 70)
        print("EXECUTIVE REVENUE INTELLIGENCE SUMMARY")
        print("=" * 70)
        
        # Revenue Summary
        rev_summary = self.revenue.get_revenue_summary()
        print(f"\n[REPORT] REVENUE OVERVIEW")
        print(f"   Total Revenue: ${rev_summary.get('total_revenue') or 0:,.2f}")
        print(f"   Avg Monthly Revenue: ${rev_summary.get('avg_monthly_revenue', 0):,.2f}")
        print(f"   Growth Rate: {rev_summary.get('growth_rate', 0):.2f}%")
        
        # Customer Summary
        seg_dist = self.rfm.get_segment_distribution()
        if not seg_dist.empty:
            print(f"\n[REPORT] CUSTOMER SEGMENTS")
            total_customers = seg_dist['Customer_Count'].sum()
            print(f"   Total Customers: {total_customers:,}")
            for _, row in seg_dist.head(5).iterrows():
                print(f"   - {row['Segment']}: {row['Customer_Count']:,} ({row['Percentage']:.1f}%)")
        
        # Churn Metrics
        churn_metrics = self.churn.get_churn_metrics()
        print(f"\n[REPORT] CHURN ANALYSIS")
        print(f"   Churn Rate: {churn_metrics.get('churn_rate_pct', 0):.2f}%")
        print(f"   Revenue at Risk: ${churn_metrics.get('revenue_at_risk', 0):,.2f}")
        print(f"   Active Customers: {churn_metrics.get('active_customers', 0):,}")
        
        # Retention
        retention = self.cohort.get_retention_summary()
        print(f"\n[REPORT] RETENTION METRICS")
        print(f"   Average Retention Rate: {retention.get('avg_retention_rate', 0):.2f}%")
        print(f"   Number of Cohorts: {retention.get('total_cohorts', 0)}")
        
        # Product Performance
        cat_insights = self.product.get_category_insights()
        print(f"\n[REPORT] TOP PERFORMING CATEGORY")
        print(f"   Category: {cat_insights.get('top_category', 'N/A')}")
        print(f"   Revenue: ${cat_insights.get('top_category_revenue', 0):,.2f}")
        print(f"   Margin: {cat_insights.get('top_category_margin', 0):.2f}%")
        
        return {
            'revenue': rev_summary,
            'churn': churn_metrics,
            'retention': retention,
            'categories': cat_insights
        }
    
    def generate_segment_report(self) -> pd.DataFrame:
        """Generate detailed segment performance report."""
        print("\n" + "=" * 70)
        print("CUSTOMER SEGMENT PERFORMANCE REPORT")
        print("=" * 70)
        
        seg_dist = self.rfm.get_segment_distribution()
        if seg_dist.empty:
            print("No segment data available")
            return pd.DataFrame()
            
        print(f"\n{'Segment':<25} {'Customers':>12} {'Revenue':>15} {'% Rev':>10} {'Avg Revenue':>15}")
        print("-" * 80)
        
        for _, row in seg_dist.iterrows():
            print(f"{row['Segment']:<25} {row['Customer_Count']:>12,} ${row['Total_Revenue']:>13,.2f} {row['Percentage']:>9.2f}% ${row['Avg_Revenue_Per_Customer']:>13,.2f}")
            
        return seg_dist
    
    def generate_revenue_forecast_report(self) -> Dict:
        """Generate revenue forecast report."""
        print("\n" + "=" * 70)
        print("REVENUE FORECAST")
        print("=" * 70)
        
        forecast = self.revenue.forecast_revenue(periods=3)
        if not forecast:
            print("Insufficient data for forecasting")
            return {}
            
        print("\nForecasted Revenue:")
        for f in forecast['forecasts']:
            print(f"   {f['month'].strftime('%Y-%m')}: ${f['forecasted_revenue']:,.2f}")
            
        return forecast
    
    def generate_marketing_recommendations(self) -> Dict:
        """Generate actionable marketing recommendations."""
        print("\n" + "=" * 70)
        print("MARKETING RECOMMENDATIONS")
        print("=" * 70)
        
        recommendations = []
        
        # Analyze segments for recommendations
        seg_dist = self.rfm.get_segment_distribution()
        churn_metrics = self.churn.get_churn_metrics()
        
        # Champions - Reward them
        champions = seg_dist[seg_dist['Segment'].str.contains('Champion', case=False, na=False)]
        if not champions.empty:
            recommendations.append({
                'segment': 'Champions',
                'action': 'VIP treatment - exclusive offers, early access to products',
                'priority': 'HIGH'
            })
        
        # At Risk - Win back
        at_risk = seg_dist[seg_dist['Segment'].str.contains('Risk', case=False, na=False)]
        if not at_risk.empty:
            recommendations.append({
                'segment': 'At Risk Customers',
                'action': 'Win-back campaigns with special discounts',
                'priority': 'HIGH'
            })
        
        # High Churn Risk
        if churn_metrics.get('churn_rate_pct', 0) > 50:
            recommendations.append({
                'segment': 'Churned Revenue',
                'action': 'Implement retention programs - loyalty rewards, personalized outreach',
                'priority': 'CRITICAL'
            })
        
        # New Customers
        new_cust = seg_dist[seg_dist['Segment'].str.contains('New', case=False, na=False)]
        if not new_cust.empty:
            recommendations.append({
                'segment': 'New Customers',
                'action': 'Onboarding sequences, first-purchase incentives',
                'priority': 'MEDIUM'
            })
        
        # Hibernating
        hibernating = seg_dist[seg_dist['Segment'].str.contains('Hibernat', case=False, na=False)]
        if not hibernating.empty:
            recommendations.append({
                'segment': 'Hibernating',
                'action': 'Re-engagement campaigns with time-limited offers',
                'priority': 'MEDIUM'
            })
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['priority']}] {rec['segment']}")
            print(f"   -> {rec['action']}")
            
        return {'recommendations': recommendations}
    
    def run_full_analysis(self) -> Dict:
        """Run complete revenue intelligence analysis."""
        print("\n" + "=" * 70)
        print("STARTING COMPREHENSIVE REVENUE INTELLIGENCE ANALYSIS")
        print("=" * 70)
        
        results = {
            'executive_summary': self.generate_executive_summary(),
            'segment_report': self.generate_segment_report().to_dict('records'),
            'forecast': self.generate_revenue_forecast_report(),
            'recommendations': self.generate_marketing_recommendations()
        }
        
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)
        
        return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Initialize and run the revenue intelligence system
    dashboard = RevenueIntelligenceDashboard(data_path="Data/")
    results = dashboard.run_full_analysis()
