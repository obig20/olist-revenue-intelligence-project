"""
Predictive Models Module
========================
Machine learning models for Revenue Intelligence System including:
- Churn Prediction Model
- Sales Forecasting Model  
- Customer Lifetime Value (CLV) Prediction

Author: Revenue Intelligence System
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

# Scikit-learn imports
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score
)


class PredictiveModeler:
    """
    Main class for ML-based predictive modeling in Revenue Intelligence.
    
    Provides methods for churn prediction, sales forecasting, and 
    customer lifetime value prediction using historical data.
    
    Attributes:
        churn_model: Trained churn prediction model
        forecast_model: Trained sales forecasting model
        clv_model: Trained CLV prediction model
        scaler: Feature scaler for preprocessing
    """
    
    def __init__(self, data: Optional[Dict[str, pd.DataFrame]] = None, random_state: int = 42):
        """
        Initialize the PredictiveModeler.
        
        Args:
            data: Dictionary of DataFrames from RevenueIntelligenceDashboard
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.data = data if data is not None else {}
        self.churn_model = None
        self.forecast_model = None
        self.clv_model = None
        self.scaler = StandardScaler()
        self.is_churn_trained = False
        self.is_forecast_trained = False
        self.is_clv_trained = False
        
        # Model performance metrics
        self.churn_metrics = {}
        self.forecast_metrics = {}
        self.clv_metrics = {}
    
    # =========================================================================
    # CHURN PREDICTION MODEL
    # =========================================================================
    
    def train_churn_model(
        self, 
        customer_data: Optional[pd.DataFrame] = None,
        target_col: str = 'churn_label',
        test_size: float = 0.2
    ) -> Dict:
        """
        Train a churn prediction model using customer features.
        
        Uses Random Forest classifier for churn prediction with features:
        - recency_days: Days since last purchase
        - frequency: Number of orders
        - monetary: Total revenue
        - avg_review_score: Average review score
        - late_delivery_rate: Rate of late deliveries
        
        Args:
            customer_data: DataFrame with customer features and churn labels.
                          If None, uses self.data['cohort_retention'] if available.
            target_col: Name of the target column (churn_label)
            test_size: Proportion of data for testing
            
        Returns:
            Dict with training metrics and model performance
        """
        # Use stored data if none provided
        if customer_data is None:
            if 'cohort_retention' in self.data:
                customer_data = self.data['cohort_retention']
            elif 'customer_rfm' in self.data:
                customer_data = self.data['customer_rfm']
            else:
                raise ValueError("No customer data available. Provide customer_data or set data in constructor.")
        required_features = [
            'recency_days', 'frequency', 'monetary', 
            'avg_review_score', 'late_delivery_rate'
        ]
        
        # Validate required columns
        missing_cols = [col for col in required_features if col not in customer_data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        if target_col not in customer_data.columns:
            raise ValueError(f"Target column '{target_col}' not found in data")
        
        # Prepare features and target
        X = customer_data[required_features].copy()
        y = customer_data[target_col].copy()
        
        # Handle missing values
        X = X.fillna(X.median())
        y = y.fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=self.random_state, 
            stratify=y if len(y.unique()) > 1 else None
        )
        
        # Train Random Forest model
        self.churn_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.churn_model.fit(X_train, y_train)
        
        # Predictions
        y_pred = self.churn_model.predict(X_test)
        y_pred_proba = self.churn_model.predict_proba(X_test)[:, 1] if len(self.churn_model.classes_) > 1 else None
        
        # Calculate metrics
        self.churn_metrics = {
            'accuracy': accuracy_score(y_test, y_pred) if len(y.unique()) > 1 else 1.0,
            'precision': precision_score(y_test, y_pred, zero_division=0) if len(y.unique()) > 1 else 1.0,
            'recall': recall_score(y_test, y_pred, zero_division=0) if len(y.unique()) > 1 else 1.0,
            'f1_score': f1_score(y_test, y_pred, zero_division=0) if len(y.unique()) > 1 else 1.0,
            'features': required_features,
            'feature_importances': dict(zip(required_features, self.churn_model.feature_importances_))
        }
        
        # Cross-validation
        if len(y.unique()) > 1:
            cv_scores = cross_val_score(self.churn_model, X_scaled, y, cv=5, scoring='f1')
            self.churn_metrics['cv_f1_mean'] = cv_scores.mean()
            self.churn_metrics['cv_f1_std'] = cv_scores.std()
        
        self.is_churn_trained = True
        
        return self.churn_metrics
    
    def predict_churn_risk(
        self, 
        customer_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Predict churn risk for customers.
        
        Args:
            customer_data: DataFrame with customer features
            
        Returns:
            DataFrame with customer IDs and churn predictions (0/1)
        """
        if not self.is_churn_trained:
            raise RuntimeError("Churn model not trained. Call train_churn_model() first.")
        
        required_features = [
            'recency_days', 'frequency', 'monetary', 
            'avg_review_score', 'late_delivery_rate'
        ]
        
        X = customer_data[required_features].copy()
        X = X.fillna(X.median())
        X_scaled = self.scaler.transform(X)
        
        predictions = self.churn_model.predict(X_scaled)
        
        result = customer_data[['customer_id']].copy() if 'customer_id' in customer_data.columns else pd.DataFrame()
        result['churn_prediction'] = predictions
        
        return result
    
    def get_churn_probability(
        self, 
        customer_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Get churn probability scores for customers.
        
        Args:
            customer_data: DataFrame with customer features
            
        Returns:
            DataFrame with customer IDs and churn probability (0-1)
        """
        if not self.is_churn_trained:
            raise RuntimeError("Churn model not trained. Call train_churn_model() first.")
        
        required_features = [
            'recency_days', 'frequency', 'monetary', 
            'avg_review_score', 'late_delivery_rate'
        ]
        
        X = customer_data[required_features].copy()
        X = X.fillna(X.median())
        X_scaled = self.scaler.transform(X)
        
        probabilities = self.churn_model.predict_proba(X_scaled)
        
        # Get probability of positive class (churn)
        churn_class_idx = list(self.churn_model.classes_).index(1) if 1 in self.churn_model.classes_ else 0
        churn_prob = probabilities[:, churn_class_idx]
        
        result = customer_data[['customer_id']].copy() if 'customer_id' in customer_data.columns else pd.DataFrame()
        result['churn_probability'] = churn_prob
        
        # Add risk level categorization
        result['risk_level'] = pd.cut(
            churn_prob, 
            bins=[-0.1, 0.2, 0.4, 0.6, 1.0],
            labels=['Low', 'Medium', 'High', 'Critical']
        )
        
        return result
    
    # =========================================================================
    # SALES FORECASTING MODEL
    # =========================================================================
    
    def train_forecast_model(
        self, 
        revenue_data: pd.DataFrame,
        date_col: str = 'month',
        revenue_col: str = 'revenue',
        test_size: float = 0.2
    ) -> Dict:
        """
        Train a sales forecasting model using historical revenue data.
        
        Uses Random Forest regressor for time-series forecasting with features:
        - historical monthly revenue
        - trend (lagged values)
        - seasonality indicators
        
        Args:
            revenue_data: DataFrame with monthly revenue data
            date_col: Name of the date column
            revenue_col: Name of the revenue column
            test_size: Proportion of data for testing
            
        Returns:
            Dict with training metrics and model performance
        """
        # Prepare data
        df = revenue_data.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)
        
        # Create features
        df = self._create_forecast_features(df, revenue_col)
        
        feature_cols = ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_3', 'rolling_mean_6', 
                       'month_sin', 'month_cos', 'trend']
        
        X = df[feature_cols].fillna(0)
        y = df[revenue_col].fillna(0)
        
        # Split data (respect time order)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Train model
        self.forecast_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=3,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.forecast_model.fit(X_train, y_train)
        
        # Predictions
        y_pred = self.forecast_model.predict(X_test)
        
        # Metrics
        self.forecast_metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mape': np.mean(np.abs((y_test - y_pred) / y_test.replace(0, np.nan))) * 100,
            'r2': r2_score(y_test, y_pred),
            'feature_importances': dict(zip(feature_cols, self.forecast_model.feature_importances_))
        }
        
        # Store last known values for forecasting
        self.last_known_values = df[feature_cols].iloc[-1:].copy()
        self.last_revenue = df[revenue_col].iloc[-1]
        self.feature_cols = feature_cols
        
        self.is_forecast_trained = True
        
        return self.forecast_metrics
    
    def _create_forecast_features(
        self, 
        df: pd.DataFrame, 
        revenue_col: str
    ) -> pd.DataFrame:
        """Create time-series features for forecasting."""
        # Lag features
        for lag in [1, 2, 3, 6]:
            df[f'lag_{lag}'] = df[revenue_col].shift(lag)
        
        # Rolling statistics
        df['rolling_mean_3'] = df[revenue_col].rolling(window=3).mean()
        df['rolling_mean_6'] = df[revenue_col].rolling(window=6).mean()
        df['rolling_std_3'] = df[revenue_col].rolling(window=3).std()
        
        # Seasonality features
        df['month_num'] = df.index.month if hasattr(df.index, 'month') else pd.DatetimeIndex(df.iloc[:, 0]).month
        df['month_sin'] = np.sin(2 * np.pi * df['month_num'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month_num'] / 12)
        
        # Trend feature
        df['trend'] = np.arange(len(df))
        
        return df
    
    def forecast_sales(
        self, 
        months_ahead: int = 6
    ) -> pd.DataFrame:
        """
        Forecast sales for future months.
        
        Args:
            months_ahead: Number of months to forecast
            
        Returns:
            DataFrame with forecasted revenue by month
        """
        if not self.is_forecast_trained:
            raise RuntimeError("Forecast model not trained. Call train_forecast_model() first.")
        
        forecasts = []
        current_features = self.last_known_values.copy()
        
        for i in range(1, months_ahead + 1):
            # Predict
            prediction = self.forecast_model.predict(current_features)[0]
            
            # Create forecast record
            forecast_date = datetime.now() + timedelta(days=30 * i)
            forecasts.append({
                'month': forecast_date.strftime('%Y-%m'),
                'forecasted_revenue': prediction,
                'forecast_horizon': i
            })
            
            # Update features for next prediction
            current_features = self._update_features_for_next_forecast(
                current_features, prediction, i
            )
        
        return pd.DataFrame(forecasts)
    
    def _update_features_for_next_forecast(
        self, 
        current_features: pd.DataFrame, 
        new_value: float,
        month_num: int
    ) -> pd.DataFrame:
        """Update lag features for next forecast iteration."""
        updated = current_features.copy()
        
        # Shift lags
        updated['lag_3'] = updated['lag_2']
        updated['lag_2'] = updated['lag_1']
        updated['lag_1'] = self.last_revenue
        
        # Update rolling means (simplified)
        updated['rolling_mean_3'] = (updated['lag_1'] + updated['lag_2'] + new_value) / 3
        updated['rolling_mean_6'] = (updated['rolling_mean_3'] + updated['lag_2'] + updated['lag_3']) / 3
        
        # Update seasonality
        updated['month_sin'] = np.sin(2 * np.pi * (month_num + 1) / 12)
        updated['month_cos'] = np.cos(2 * np.pi * (month_num + 1) / 12)
        
        # Update trend
        updated['trend'] = updated['trend'] + 1
        
        self.last_revenue = new_value
        
        return updated
    
    # =========================================================================
    # CUSTOMER LIFETIME VALUE (CLV) PREDICTION
    # =========================================================================
    
    def train_clv_model(
        self,
        customer_data: pd.DataFrame,
        target_col: str = 'total_revenue',
        test_size: float = 0.2
    ) -> Dict:
        """
        Train a CLV prediction model.
        
        Predicts future revenue potential per customer using:
        - purchase frequency
        - average order value
        - customer tenure
        - product category preferences
        
        Args:
            customer_data: DataFrame with customer features and revenue
            target_col: Name of the target column (total revenue)
            test_size: Proportion of data for testing
            
        Returns:
            Dict with training metrics and model performance
        """
        # Define features for CLV
        feature_cols = [
            'frequency', 'monetary', 'avg_order_value', 
            'customer_tenure_days', 'total_orders'
        ]
        
        # Check available columns
        available_features = [col for col in feature_cols if col in customer_data.columns]
        
        if len(available_features) < 3:
            # Use fallback features if needed
            available_features = ['frequency', 'monetary']
        
        if target_col not in customer_data.columns:
            raise ValueError(f"Target column '{target_col}' not found in data")
        
        X = customer_data[available_features].copy()
        y = customer_data[target_col].copy()
        
        # Handle missing values
        X = X.fillna(X.median())
        y = y.fillna(y.median())
        
        # Remove outliers
        y = y[y < y.quantile(0.99)]
        X = X.loc[y.index]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=self.random_state
        )
        
        # Train model
        self.clv_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            min_samples_split=5,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.clv_model.fit(X_train, y_train)
        
        # Predictions
        y_pred = self.clv_model.predict(X_test)
        
        # Metrics
        self.clv_metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'features': available_features,
            'feature_importances': dict(zip(available_features, self.clv_model.feature_importances_))
        }
        
        self.is_clv_trained = True
        
        return self.clv_metrics
    
    def predict_customer_ltv(
        self,
        customer_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Predict Customer Lifetime Value for customers.
        
        Args:
            customer_data: DataFrame with customer features
            
        Returns:
            DataFrame with customer IDs and predicted LTV
        """
        if not self.is_clv_trained:
            raise RuntimeError("CLV model not trained. Call train_clv_model() first.")
        
        feature_cols = self.clv_metrics.get('features', ['frequency', 'monetary'])
        
        # Use available features
        available = [col for col in feature_cols if col in customer_data.columns]
        if len(available) < 2:
            available = ['frequency', 'monetary']
        
        X = customer_data[available].copy()
        X = X.fillna(X.median())
        X_scaled = self.scaler.transform(X)
        
        predictions = self.clv_model.predict(X_scaled)
        
        result = customer_data[['customer_id']].copy() if 'customer_id' in customer_data.columns else pd.DataFrame()
        result['predicted_ltv'] = predictions
        
        # Add LTV segment
        result['ltv_segment'] = pd.cut(
            predictions,
            bins=[-np.inf, 100, 500, 1000, np.inf],
            labels=['Low', 'Medium', 'High', 'Premium']
        )
        
        return result
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_model_status(self) -> Dict:
        """Get status of all models."""
        return {
            'churn_model_trained': self.is_churn_trained,
            'forecast_model_trained': self.is_forecast_trained,
            'clv_model_trained': self.is_clv_trained,
            'churn_metrics': self.churn_metrics if self.is_churn_trained else None,
            'forecast_metrics': self.forecast_metrics if self.is_forecast_trained else None,
            'clv_metrics': self.clv_metrics if self.is_clv_trained else None
        }
    
    def get_feature_importance(self, model_type: str = 'churn') -> Optional[Dict]:
        """
        Get feature importance for a specific model.
        
        Args:
            model_type: Type of model ('churn', 'forecast', or 'clv')
            
        Returns:
            Dict of feature importances or None if not trained
        """
        if model_type == 'churn' and self.is_churn_trained:
            return self.churn_metrics.get('feature_importances')
        elif model_type == 'forecast' and self.is_forecast_trained:
            return self.forecast_metrics.get('feature_importances')
        elif model_type == 'clv' and self.is_clv_trained:
            return self.clv_metrics.get('feature_importances')
        return None
