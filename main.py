"""
Revenue Intelligence System - Main Entry Point
=================================================
This script demonstrates how to use the Revenue Intelligence System
for analytics and predictive modeling.

Usage:
    python main.py
"""

from revenue_intelligence import RevenueIntelligenceDashboard
from models import PredictiveModeler


def main():
    """Main function to run the Revenue Intelligence System."""
    
    print("=" * 70)
    print("REVENUE INTELLIGENCE SYSTEM")
    print("=" * 70)
    
    # ==========================================================================
    # PART 1: Run Analytics
    # ==========================================================================
    print("\n[1/2] Initializing Revenue Intelligence Dashboard...")
    print("-" * 50)
    
    # Initialize dashboard with data path
    dashboard = RevenueIntelligenceDashboard(data_path="Data/")
    
    # Run full analysis
    print("\nRunning complete revenue analysis...")
    results = dashboard.run_full_analysis()
    
    # Generate executive summary
    dashboard.generate_executive_summary()
    
    # ==========================================================================
    # PART 2: Run ML Predictions
    # ==========================================================================
    print("\n\n[2/2] Running ML-based Predictive Modeling...")
    print("-" * 50)
    
    # Initialize modeler with dashboard data
    modeler = PredictiveModeler(dashboard.data)
    
    # Train churn model using available customer RFM data
    print("\nTraining Churn Prediction Model...")
    print("   Using customer RFM data for feature engineering...")
    
    # Prepare customer data from available datasets
    # The model will use recency_days, frequency, monetary as features
    # and create synthetic churn labels based on RFM segments
    if 'customer_rfm' in dashboard.data:
        customer_data = dashboard.data['customer_rfm'].copy()
        
        # Create synthetic churn label based on RFM segment
        # Customers in 'Hibernating', 'Lost High Value', 'Lost Low Value' 
        # are considered at-risk (churned)
        churn_segments = ['Hibernating', 'Lost High Value', 'Lost Low Value']
        customer_data['churn_label'] = customer_data['rfm_segment'].isin(churn_segments).astype(int)
        
        # Add dummy features for avg_review_score and late_delivery_rate
        # (In production, these would come from actual order/delivery data)
        customer_data['avg_review_score'] = 4.0
        customer_data['late_delivery_rate'] = 0.1
        
        # Train the model
        try:
            train_results = modeler.train_churn_model(
                customer_data=customer_data,
                target_col='churn_label'
            )
            
            print(f"   Model trained successfully!")
            print(f"   - Training samples: {train_results.get('train_samples', 'N/A')}")
            print(f"   - Test samples: {train_results.get('test_samples', 'N/A')}")
            
            if 'accuracy' in train_results:
                print(f"   - Accuracy: {train_results['accuracy']:.2%}")
            if 'f1_score' in train_results:
                print(f"   - F1 Score: {train_results['f1_score']:.2%}")
            
            # Get churn predictions
            print("\nGenerating churn risk predictions...")
            churn_predictions = modeler.get_churn_probability(customer_data)
            
            if churn_predictions is not None and len(churn_predictions) > 0:
                if 'churn_probability' not in churn_predictions.columns:
                    print("   Warning: Model did not return probability predictions.")
                else:
                    high_risk_count = (churn_predictions['churn_probability'] > 0.5).sum()
                    print(f"   - High risk customers identified: {high_risk_count:,}")
                    print(f"   - Low risk customers: {len(churn_predictions) - high_risk_count:,}")
                    
                    # Show top 5 high-risk customers
                    print("\n   Top 5 High-Risk Customers:")
                    high_risk = churn_predictions.nlargest(5, 'churn_probability')
                    customer_id_col = 'customer_id' if 'customer_id' in high_risk.columns else high_risk.index.name
                    for idx, row in high_risk.iterrows():
                        cust_id = str(idx) if customer_id_col is None else row.get(customer_id_col, str(idx))
                        print(f"      - {cust_id[:20]}... Risk: {row['churn_probability']:.1%}")
            
        except Exception as e:
            print(f"   Warning: Could not complete churn prediction: {e}")
            print("   This is expected if the data doesn't meet model requirements.")
    
    # ==========================================================================
    # PART 3: Model Status
    # ==========================================================================
    print("\n\n" + "=" * 70)
    print("MODEL STATUS")
    print("=" * 70)
    
    status = modeler.get_model_status()
    for model_name, model_info in status.items():
        # status contains booleans and metrics, handle both cases
        if isinstance(model_info, bool):
            if model_info:
                print(f"   [{model_name}] - Trained")
            else:
                print(f"   [{model_name}] - Not trained")
        elif isinstance(model_info, dict) and model_info:
            print(f"   [{model_name}] - Trained (metrics available)")
        else:
            print(f"   [{model_name}] - Not trained")
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nThe Revenue Intelligence System has completed all analyses.")
    print("Check the Data/ directory for exported CSV files.")
    
    return results


if __name__ == "__main__":
    main()
