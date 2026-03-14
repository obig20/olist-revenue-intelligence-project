"""
Prepare realistic churn data from Olist orders.
Defines churn based on actual purchase behavior (no purchase in 180 days).
"""
import pandas as pd
import numpy as np

# Load orders
print("Loading orders data...")
orders = pd.read_csv('Data/olist_orders_dataset.csv')
orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])

# Only use delivered orders
orders = orders[orders['order_status'] == 'delivered'].copy()
print(f"Delivered orders: {len(orders):,}")

# Load customers to get customer_unique_id
customers = pd.read_csv('Data/olist_customers_dataset.csv')
orders = orders.merge(customers[['customer_id', 'customer_unique_id']], on='customer_id', how='left')

# Define reference date and churn window
# Use data up to June 30, 2018 as reference, then predict churn in last 6 months
reference_date = pd.Timestamp('2018-06-30')
churn_window_days = 180

# Get customer order statistics
print("Calculating customer order patterns...")
customer_orders = orders.groupby('customer_unique_id').agg(
    first_order_date=('order_purchase_timestamp', 'min'),
    last_order_date=('order_purchase_timestamp', 'max'),
    total_orders=('order_id', 'count')
).reset_index()

# Calculate recency (days since last order from reference date)
customer_orders['recency_days'] = (reference_date - customer_orders['last_order_date']).dt.days

# Calculate frequency
customer_orders['frequency'] = customer_orders['total_orders']

# Calculate monetary (need to join with payments)
payments = pd.read_csv('Data/olist_order_payments_dataset.csv')
customer_monetary = orders.merge(payments[['order_id', 'payment_value']], on='order_id')
customer_monetary = customer_monetary.groupby('customer_unique_id')['payment_value'].sum().reset_index()
customer_monetary.columns = ['customer_unique_id', 'monetary']

customer_orders = customer_orders.merge(customer_monetary, on='customer_unique_id', how='left')
customer_orders['monetary'] = customer_orders['monetary'].fillna(0)

# Churn definition: no purchase in 180 days from reference date
# Churned = 1 if last order was more than 180 days ago
churn_cutoff = reference_date - pd.Timedelta(days=churn_window_days)
customer_orders['churn_label'] = (customer_orders['last_order_date'] < churn_cutoff).astype(int)

print(f"\n=== Churn Distribution (180-day window) ===")
print(f"Total customers: {len(customer_orders):,}")
print(f"Churned: {customer_orders.churn_label.sum():,} ({customer_orders.churn_label.mean()*100:.1f}%)")
print(f"Active: {(~customer_orders.churn_label.astype(bool)).sum():,} ({(1-customer_orders.churn_label.mean())*100:.1f}%)")

# Add features NOT used in RFM segmentation (to avoid leakage)
# 1. Average review score
print("Adding review scores...")
reviews = pd.read_csv('Data/olist_order_reviews_dataset.csv')
order_reviews = orders.merge(reviews[['order_id', 'review_score']], on='order_id')
avg_reviews = order_reviews.groupby('customer_unique_id')['review_score'].mean().reset_index()
avg_reviews.columns = ['customer_unique_id', 'avg_review_score']

# 2. Payment behavior - credit card usage rate
print("Adding payment behavior...")
# Need to join payments with orders to get customer_unique_id
orders_for_payments = orders[['order_id', 'customer_unique_id']].drop_duplicates()
payments_with_customer = payments.merge(orders_for_payments, on='order_id', how='left')
payment_behavior = payments_with_customer.groupby('customer_unique_id').agg({
    'payment_type': lambda x: (x == 'credit_card').mean(),
    'payment_installments': 'mean'
}).reset_index()
payment_behavior.columns = ['customer_unique_id', 'credit_card_rate', 'avg_installments']

# Merge all features
print("\nMerging features...")
churn_data = customer_orders.merge(avg_reviews, on='customer_unique_id', how='left')
churn_data = churn_data.merge(payment_behavior, on='customer_unique_id', how='left')

# Fill missing values
churn_data['avg_review_score'] = churn_data['avg_review_score'].fillna(churn_data['avg_review_score'].median())
churn_data['credit_card_rate'] = churn_data['credit_card_rate'].fillna(0)
churn_data['avg_installments'] = churn_data['avg_installments'].fillna(1)

# Late delivery rate - simpler calculation using orders data
late_delivery = orders[['customer_unique_id', 'order_id']].merge(
    orders[['order_id', 'order_estimated_delivery_date', 'order_delivered_customer_date']].drop_duplicates(),
    on='order_id'
)
late_delivery['order_estimated_delivery_date'] = pd.to_datetime(late_delivery['order_estimated_delivery_date'])
late_delivery['order_delivered_customer_date'] = pd.to_datetime(late_delivery['order_delivered_customer_date'])
late_delivery['is_late'] = late_delivery['order_delivered_customer_date'] > late_delivery['order_estimated_delivery_date']
late_rate = late_delivery.groupby('customer_unique_id')['is_late'].mean().reset_index()
late_rate.columns = ['customer_unique_id', 'late_delivery_rate']

churn_data = churn_data.merge(late_rate, on='customer_unique_id', how='left')
churn_data['late_delivery_rate'] = churn_data['late_delivery_rate'].fillna(0)

# Calculate customer tenure (days since first purchase)
churn_data['tenure_days'] = (reference_date - churn_data['first_order_date']).dt.days

# Select final columns
final_columns = [
    'customer_unique_id', 'churn_label',
    'recency_days', 'frequency', 'monetary', 'tenure_days',
    'avg_review_score', 'late_delivery_rate', 
    'credit_card_rate', 'avg_installments'
]
churn_data = churn_data[final_columns]

# Save
output_path = 'Data/customer_churn.csv'
churn_data.to_csv(output_path, index=False)
print(f"\nSaved churn data to {output_path}")
print(f"Shape: {churn_data.shape}")
print(f"\nFeature summary:")
print(churn_data.describe())
