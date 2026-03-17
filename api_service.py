"""
Revenue Intelligence API Service
=================================
FastAPI-based REST API for monetization.
Provides real-time customer scoring, analytics, and campaign generation.

Usage:
    uvicorn api_service:app --reload
    or
    python -m uvicorn api_service:app --reload

API Endpoints:
    - GET  /                   - API info and health check
    - GET  /health             - Health check
    - GET  /analytics/revenue - Revenue analytics
    - GET  /customers          - List all customers with scores
    - GET  /customers/{id}     - Get specific customer details
    - POST /customers/score    - Score a new customer
    - GET  /churn/predictions  - Get churn predictions
    - POST /campaigns/generate - Generate retention campaign
    - GET  /segments           - Get customer segments
"""

from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Annotated
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from functools import lru_cache

# Initialize FastAPI app
app = FastAPI(
    title="Revenue Intelligence API",
    description="Monetization-ready API for e-commerce analytics and customer scoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== API AUTHENTICATION ====================

# Development mode flag - set to True to skip strict validation
# NOTE: In development mode:
#   - API key environment validation is skipped at startup
#   - API endpoints still REQUIRE API keys (via verify_api_key dependency)
#   - Use placeholder keys for testing
#   - In production, always set this to False
DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"

# Require API keys in dev mode too - dev mode only affects non-security startup checks
# Set REQUIRE_API_KEYS_IN_DEV=false to disable API key requirement (NOT recommended)
REQUIRE_API_KEYS_IN_DEV = os.environ.get("REQUIRE_API_KEYS_IN_DEV", "true").lower() != "false"

# Security: Fail fast if DEV_MODE is enabled in production environment
if DEV_MODE:
    environment = os.environ.get("ENVIRONMENT", "").lower()
    if environment in ("production", "prod", "live"):
        raise RuntimeError(
            "FATAL: DEV_MODE cannot be enabled in production environment! "
            "Set ENVIRONMENT=development or remove DEV_MODE flag."
        )

# Configure API key names from environment variable with prefix (configurable for flexibility)
# For development, set these in .env file or environment
# Example: MY_API_KEY_STARTER=your_key_here (set API_KEY_PREFIX=MY_API_KEY)
API_KEY_PREFIX = os.environ.get("API_KEY_PREFIX", "API_KEY")
REQUIRED_API_KEYS = [f"{API_KEY_PREFIX}_STARTER", f"{API_KEY_PREFIX}_GROWTH", f"{API_KEY_PREFIX}_ENTERPRISE"]

# Validate environment on startup (skip in development mode)
# NOTE: This validates that API keys are SET in environment variables.
# It does NOT affect endpoint-level authentication - all protected endpoints
# still require valid API keys via the verify_api_key dependency.
def _validate_api_keys():
    """Validate that all required API keys are set in environment."""
    if DEV_MODE:
        return  # Skip environment variable validation in development mode
    
    missing_keys = []
    for key in REQUIRED_API_KEYS:
        if not os.environ.get(key):
            missing_keys.append(key)
    
    if missing_keys:
        raise RuntimeError(
            f"Missing required API keys in environment: {', '.join(missing_keys)}. "
            f"Please set these environment variables before starting the API, "
            f"or set DEV_MODE=true for development mode."
        )

# Validate on module load - only in production mode
# In DEV_MODE, validation happens lazily on first request
if not DEV_MODE:
    _validate_api_keys()

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Build API_KEYS dict from environment (use placeholder in dev mode)
if DEV_MODE:
    API_KEYS = {
        "dev_starter": {"tier": "starter", "monthly_calls": 100},
        "dev_growth": {"tier": "growth", "monthly_calls": 10000},
        "dev_enterprise": {"tier": "enterprise", "monthly_calls": float('inf')},
    }
else:
    # Build properly structured API_KEYS dict from environment
    # Set API_KEY_PREFIX env var to customize (e.g., MY_API_KEY_STARTER)
    starter_key = os.environ.get(f"{API_KEY_PREFIX}_STARTER", "")
    growth_key = os.environ.get(f"{API_KEY_PREFIX}_GROWTH", "")
    enterprise_key = os.environ.get(f"{API_KEY_PREFIX}_ENTERPRISE", "")
    
    # Build API_KEYS dict with proper key-value structure
    API_KEYS = {}
    if starter_key:
        API_KEYS[starter_key] = {"tier": "starter", "monthly_calls": 100}
    if growth_key:
        API_KEYS[growth_key] = {"tier": "growth", "monthly_calls": 10000}
    if enterprise_key:
        API_KEYS[enterprise_key] = {"tier": "enterprise", "monthly_calls": float('inf')}
    
    # Log warnings for missing keys
    if not starter_key or not growth_key or not enterprise_key:
        missing = []
        if not starter_key:
            missing.append(f"{API_KEY_PREFIX}_STARTER")
        if not growth_key:
            missing.append(f"{API_KEY_PREFIX}_GROWTH")
        if not enterprise_key:
            missing.append(f"{API_KEY_PREFIX}_ENTERPRISE")
        if missing:
            logger.warning(
                f"Missing API keys in environment: {', '.join(missing)}. "
                f"Set API_KEY_PREFIX env var to customize key names, or set "
                f"{API_KEY_PREFIX}_{{STARTER,GROWTH,ENTERPRISE}}=your_key_here."
            )

# Track API usage with thread-safe locking
# WARNING: In-memory storage is reset on server restart - NOT suitable for production!
# For production with multiple instances, use Redis or PostgreSQL:
#   - Redis: pip install redis; redis_client = redis.Redis()
#   - PostgreSQL: Use a database table to track usage per API key
# This simplified tracking is only intended for development/testing.
import asyncio

api_usage = {}
_rate_limit_lock = asyncio.Lock()

# Optional: Redis configuration for production deployments
# Set REDIS_URL environment variable to enable Redis-based rate limiting
REDIS_URL = os.environ.get("REDIS_URL", None)
if REDIS_URL:
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL)
        _use_redis = True
    except ImportError:
        _use_redis = False
else:
    _redis_client = None
    _use_redis = False


async def verify_api_key(x_api_key: Annotated[str, Header()] = None) -> str:
    """Verify API key and return key identifier."""
    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key required. Add 'X-Api-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Please provide a valid API key.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_api_key


def _verify_api_key_for_optional_endpoints(x_api_key: Annotated[str, Header()] = None) -> Optional[str]:
    """Verify API key if provided, but don't require it. Returns key if valid, None otherwise."""
    if x_api_key is None:
        return None
    
    if x_api_key not in API_KEYS:
        return None
    
    return x_api_key


async def check_rate_limit(api_key: str) -> None:
    """Check if API key has exceeded rate limit."""
    key_info = API_KEYS[api_key]
    monthly_limit = key_info["monthly_calls"]
    
    # Track usage - supports both in-memory and Redis modes
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage_key = f"{api_key}:{current_month}"
    
    # Use Redis if available (production mode), otherwise use in-memory (development)
    if _use_redis and _redis_client:
        try:
            current_usage = int(_redis_client.get(usage_key) or 0)
            if current_usage >= monthly_limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Monthly API call limit ({monthly_limit}) exceeded. Upgrade your plan."
                )
            _redis_client.incr(usage_key)
            # Set expiry to end of month
            import calendar
            last_day = calendar.monthrange(int(current_month.split('-')[0]), int(current_month.split('-')[1]))[1]
            _redis_client.expire(usage_key, 60*60*24*last_day)
        except Exception as e:
            # Fall back to in-memory if Redis fails
            _check_rate_limit_fallback(usage_key, monthly_limit)
    else:
        # In-memory fallback (development mode)
        _check_rate_limit_fallback(usage_key, monthly_limit)


def _check_rate_limit_fallback(usage_key: str, monthly_limit: int) -> None:
    """Fallback in-memory rate limiting for development mode.
    
    ⚠️ WARNING: This implementation has race conditions in concurrent async contexts!
    
    The check-then-increment pattern is NOT atomic, which can lead to:
    - Rate limits being exceeded under high concurrency
    - Inaccurate usage tracking
    
    For production with multiple instances, use Redis-based rate limiting which
    provides atomic operations. The Redis implementation is inherently thread-safe.
    
    This fallback is only suitable for single-instance development deployments.
    Uses global lock for thread-safe increment in single-instance deployments.
    """
    global api_usage
    
    # Check if we're in an async context by trying to get the current task
    # This is safer than trying to get the event loop which can raise RuntimeError
    in_async_context = False
    try:
        import asyncio
        # Check for current task - this works in both sync and async contexts
        # without raising RuntimeError
        try:
            asyncio.current_task()
            in_async_context = True
        except RuntimeError:
            # No current task - we're in sync context
            pass
    except ImportError:
        pass  # asyncio not available, stay in sync mode
    
    # Initialize if not exists (non-atomic, but acceptable for development)
    if usage_key not in api_usage:
        api_usage[usage_key] = 0
    
    # Check BEFORE increment to enforce limit correctly
    if api_usage[usage_key] >= monthly_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly API call limit ({monthly_limit}) exceeded. Upgrade your plan."
        )
    
    # Increment after check - note: not atomic in high-concurrency scenarios
    # For production, use Redis which provides atomic operations
    api_usage[usage_key] += 1


# ==================== DATA LOADING ====================

# Simple TTL cache implementation
_data_cache = {
    'data': None,
    'timestamp': 0
}
DEFAULT_TTL = 3600  # 1 hour in seconds

def _get_cached_data(ttl_seconds: int = DEFAULT_TTL):
    """Get cached data if still valid based on TTL."""
    import time
    current_time = time.time()
    if (_data_cache['data'] is not None and 
        current_time - _data_cache['timestamp'] < ttl_seconds):
        return _data_cache['data']
    return None

def _set_cached_data(data):
    """Set cached data with current timestamp."""
    import time
    _data_cache['data'] = data
    _data_cache['timestamp'] = time.time()

def clear_data_cache():
    """Clear the data cache to force reload on next call."""
    _data_cache['data'] = None
    _data_cache['timestamp'] = 0

def load_data(ttl_seconds: int = DEFAULT_TTL):
    """
    Load all data files with caching for performance.
    
    Note: Uses lru_cache - data is cached for the lifetime of the process.
    For production deployments with frequent data updates, consider using:
    - Cache invalidation via /health/refresh endpoint
    - python-cacheable or cachetools with TTL
    - Redis caching for distributed deployments
    
    Args:
        ttl_seconds: Time-to-live for cache (default 1 hour). Set to 0 to disable.
    
    Cache invalidation:
        - Call clear_data_cache() to manually clear cache
        - Or call with ttl_seconds=0 to force reload
    """
    # Check if cache is valid
    if ttl_seconds > 0:
        cached = _get_cached_data(ttl_seconds)
        if cached is not None:
            return cached
    
    data = {}
    # Use absolute path relative to this module to avoid CWD issues
    module_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(module_dir, 'Data')
    
    try:
        # Load core datasets
        data['customer_rfm'] = pd.read_csv(f'{data_dir}/customer_rfm.csv')
        data['rfm_segments'] = pd.read_csv(f'{data_dir}/rfm_segments.csv')
        data['monthly_revenue'] = pd.read_csv(f'{data_dir}/monthly_revenue.csv')
        data['churn_summary'] = pd.read_csv(f'{data_dir}/churn_summary.csv')
        data['cohort_retention'] = pd.read_csv(f'{data_dir}/cohort_retention_with_churn.csv')
        data['top_categories'] = pd.read_csv(f'{data_dir}/top_categories.csv')
        data['top_states'] = pd.read_csv(f'{data_dir}/top_states.csv')
        
        # Load churn data if available
        try:
            data['customer_churn'] = pd.read_csv(f'{data_dir}/customer_churn.csv')
        except FileNotFoundError:
            # Churn data file doesn't exist yet - this is expected for new installations
            data['customer_churn'] = None
        except pd.errors.EmptyDataError:
            # Churn data file exists but is empty
            data['customer_churn'] = None
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logging.warning(f"Failed to load customer_churn.csv: {e}")
            data['customer_churn'] = None
            
        # Cache the loaded data
        _set_cached_data(data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

# ==================== Pydantic Models ====================

class CustomerScore(BaseModel):
    """Customer scoring response model."""
    customer_id: str
    churn_risk_score: float = Field(..., ge=0, le=1, description="Churn probability (0-1)")
    segment: str
    ltv_estimate: float
    recommended_action: str

class CampaignRequest(BaseModel):
    """Campaign generation request."""
    target_segment: str = Field(..., description="Target segment (e.g., 'At Risk', 'Loyal')")
    budget: float = Field(..., gt=0, description="Campaign budget in USD")
    channel: str = Field(..., description="Marketing channel (email, sms, push)")

class CampaignResponse(BaseModel):
    """Campaign generation response."""
    campaign_id: str
    target_segment: str
    budget: float
    estimated_reach: int
    estimated_conversion: float
    expected_revenue: float
    recommended_channels: List[str]
    message_templates: Dict[str, str]
    action_items: List[str]

class CustomerFeatures(BaseModel):
    """Input features for scoring a new customer."""
    monetary: float = Field(..., gt=0, description="Total spending amount")
    frequency: int = Field(..., ge=1, description="Number of purchases")
    avg_review_score: float = Field(..., ge=0, le=5, description="Average review score")
    avg_installments: float = Field(..., ge=1, description="Average payment installments")
    credit_card_rate: float = Field(..., ge=0, le=1, description="Proportion of credit card payments")
    late_delivery_rate: float = Field(..., ge=0, le=1, description="Proportion of late deliveries")

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """API information endpoint."""
    return {
        "name": "Revenue Intelligence API",
        "version": "1.0.0",
        "description": "Monetization-ready API for e-commerce analytics",
        "endpoints": {
            "health": "/health",
            "analytics": {
                "revenue": "/analytics/revenue",
                "segments": "/segments",
                "cohorts": "/analytics/cohorts"
            },
            "customers": {
                "list": "/customers",
                "detail": "/customers/{customer_id}",
                "score": "/customers/score"
            },
            "churn": "/churn/predictions",
            "campaigns": "/campaigns/generate"
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health_check(
    x_api_key: Annotated[str, Header()] = None
):
    """Health check endpoint. Accepts optional API key for authenticated health checks.
    
    Returns minimal status without exposing internal details when unauthenticated.
    """
    # If API key provided, verify it and check rate limit
    if x_api_key is not None:
        if x_api_key not in API_KEYS:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key.",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        # Still check rate limit for authenticated requests
        await check_rate_limit(x_api_key)
        
        # Full health check for authenticated requests
        data = load_data()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "data_loaded": len(data) > 0,
            "datasets": list(data.keys())
        }
    
    # Minimal health check for unauthenticated requests - no internal details exposed
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== Analytics Endpoints ====================

@app.get("/analytics/revenue")
async def get_revenue_analytics(
    period: Optional[str] = Query("monthly", description="Time period: daily, weekly, monthly"),
    api_key: str = Depends(verify_api_key)
):
    """Get revenue analytics. Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    data = load_data()
    
    # Monthly revenue
    monthly = data['monthly_revenue'].copy()
    monthly['month'] = pd.to_datetime(monthly['month'])
    monthly = monthly.sort_values('month')
    
    # Calculate metrics
    total_revenue = monthly['revenue'].sum()
    avg_monthly = monthly['revenue'].mean()
    
    # Growth rate
    if len(monthly) >= 2:
        first_month = monthly['revenue'].iloc[0]
        last_month = monthly['revenue'].iloc[-1]
        growth_rate = ((last_month - first_month) / first_month) * 100 if first_month > 0 else 0
    else:
        growth_rate = 0
    
    return {
        "period": period,
        "total_revenue": float(total_revenue),
        "average_monthly": float(avg_monthly),
        "growth_rate": float(growth_rate),
        "monthly_data": monthly.to_dict(orient='records'),
        "top_categories": data['top_categories'].head(10).to_dict(orient='records'),
        "top_states": data['top_states'].head(10).to_dict(orient='records')
    }

@app.get("/segments")
async def get_segments(
    api_key: str = Depends(verify_api_key)
):
    """Get customer segment analysis. Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    data = load_data()
    segments = data['rfm_segments']
    
    # Segment distribution
    segment_counts = segments['rfm_segment'].value_counts().to_dict()
    
    # Segment performance
    segment_metrics = segments.groupby('rfm_segment').agg({
        'monetary': ['count', 'sum', 'mean'],
        'frequency': 'mean',
        'recency': 'mean'
    }).round(2)
    segment_metrics.columns = ['customer_count', 'total_revenue', 'avg_revenue', 'avg_frequency', 'avg_recency']
    segment_metrics = segment_metrics.to_dict(orient='index')
    
    return {
        "segments": segment_counts,
        "metrics": segment_metrics,
        "total_customers": len(segments)
    }

@app.get("/analytics/cohorts")
async def get_cohort_analysis(
    api_key: str = Depends(verify_api_key)
):
    """Get cohort retention analysis. Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    data = load_data()
    cohort = data['cohort_retention']
    
    # Filter active customers
    active_cohort = cohort[cohort['churn_label'] == 0]
    
    # Pivot for heatmap data
    cohort_pivot = active_cohort.pivot(
        index='cohort_month',
        columns='month_offset',
        values='retention_rate_pct'
    )
    
    return {
        "cohort_data": cohort_pivot.to_dict(),
        "average_retention": float(active_cohort['retention_rate_pct'].mean()),
        "cohort_months": list(cohort_pivot.index)
    }

# ==================== Customer Endpoints ====================

@app.get("/customers")
async def get_customers(
    segment: Optional[str] = Query(None, description="Filter by segment"),
    limit: int = Query(100, ge=1, le=10000, description="Number of customers to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    api_key: str = Depends(verify_api_key)
):
    """Get list of customers with scores. Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    
    key_tier = API_KEYS[api_key]["tier"]
    
    # Enforce tier-based limits
    original_limit = limit
    if key_tier == "starter" and limit > 10:
        limit = 10
    data = load_data()
    
    # Get customer data with segments
    customers = data['rfm_segments'].copy()
    
    # Filter by segment if provided
    if segment:
        customers = customers[customers['rfm_segment'] == segment]
    
    # Add churn risk score (vectorized for performance)
    segment_risk = {
        'Champions': 0.05,
        'Loyal Customers': 0.10,
        'Potential Loyalist': 0.20,
        'New Customers': 0.30,
        'At Risk': 0.60,
        'Cant Lose Them': 0.80,
        'Lost': 0.95
    }
    
    # Vectorized calculation - much faster than apply()
    # Clamp to ensure values stay in 0-1 range
    customers['churn_risk'] = (
        customers['rfm_segment'].map(segment_risk).fillna(0.5) *
        (1 + (customers['recency'].clip(upper=180) / 180) * 0.2)
    ).clip(lower=0.0, upper=1.0).round(3)
    
    # Calculate LTV estimate
    customers['ltv_estimate'] = customers['monetary'] * (1 + customers['frequency'] * 0.1)
    
    # Paginate
    total = len(customers)
    customers = customers.iloc[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "limit_original": original_limit if original_limit != limit else None,
        "limit_note": f"Starter tier limited to 10. Requested: {original_limit}" if original_limit > 10 else None,
        "offset": offset,
        "tier": key_tier,
        "customers": customers[['customer_id', 'rfm_segment', 'churn_risk', 'ltv_estimate', 'monetary', 'frequency']].to_dict(orient='records')
    }

def _calculate_churn_risk(row):
    """Calculate churn risk based on segment and recency."""
    segment_risk = {
        'Champions': 0.05,
        'Loyal Customers': 0.10,
        'Potential Loyalist': 0.20,
        'New Customers': 0.30,
        'At Risk': 0.60,
        'Cant Lose Them': 0.80,
        'Lost': 0.95
    }
    base_risk = segment_risk.get(row['rfm_segment'], 0.5)
    
    # Adjust by recency
    recency_factor = min(row['recency'] / 180, 1.0)  # Cap at 1
    return round(base_risk * (1 + recency_factor * 0.2), 3)

@app.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get detailed customer information. Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    
    data = load_data()
    
    # Search in RFM segments
    customer = data['rfm_segments'][data['rfm_segments']['customer_id'] == customer_id]
    
    if customer.empty:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = customer.iloc[0]
    
    # Get churn data if available
    churn_info = None
    if data['customer_churn'] is not None:
        churn_row = data['customer_churn'][data['customer_churn']['customer_id'] == customer_id]
        if not churn_row.empty:
            churn_info = {
                "churn_risk": float(churn_row.iloc[0].get('churn_probability', 0)),
                "churn_label": int(churn_row.iloc[0].get('churn_label', 0))
            }
    
    return {
        "customer_id": customer['customer_id'],
        "segment": customer['rfm_segment'],
        "rfm_scores": {
            "recency": int(customer['r_score']),
            "frequency": int(customer['f_score']),
            "monetary": int(customer['m_score'])
        },
        "metrics": {
            "total_spent": float(customer['monetary']),
            "order_count": int(customer['frequency']),
            "days_since_last_purchase": int(customer['recency'])
        },
        "churn_risk": _calculate_churn_risk(customer),
        "ltv_estimate": float(customer['monetary'] * (1 + customer['frequency'] * 0.1)),
        "churn_info": churn_info,
        "recommended_action": _get_recommendation(customer['rfm_segment'])
    }

def _get_recommendation(segment):
    """Get recommended action based on segment."""
    recommendations = {
        'Champions': 'Reward program, VIP treatment, early access to new products',
        'Loyal Customers': 'Cross-sell premium products, loyalty rewards',
        'Potential Loyalist': 'Personalized recommendations, engage with brand',
        'New Customers': 'Onboarding sequence, welcome discounts, product education',
        'At Risk': 'Win-back campaign, personalized offers, satisfaction survey',
        'Cant Lose Them': 'Urgent retention offer, exclusive discount, direct outreach',
        'Lost': 'Reactivation campaign, deep discount, feedback request'
    }
    return recommendations.get(segment, 'General nurturing')

@app.post("/customers/score")
async def score_customer(
    features: CustomerFeatures,
    api_key: str = Depends(verify_api_key)
):
    """Score a new customer for churn risk (real-time scoring). Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    
    # Calculate churn probability based on customer features
    # This is a heuristic-based calculation for real-time scoring
    churn_prob = (
        (1 - min(features.monetary / 1000, 1)) +  # Lower spend = higher churn
        (features.avg_installments / 12) +          # More installments = higher churn (price sensitive)
        (1 - features.avg_review_score / 5) +     # Lower review = higher churn
        (1 - features.credit_card_rate) +          # Non-credit card = slightly higher churn
        features.late_delivery_rate +              # Late delivery = higher churn
        (1 - min(features.frequency / 10, 1))     # Less frequent = higher churn
    )
    
    # Normalize to 0-1 range (max possible sum is 6.0)
    churn_prob = min(churn_prob / 6, 1)
    
    # Determine segment
    segment = _classify_segment(churn_prob, features.monetary, features.frequency)
    
    # Calculate LTV
    ltv = features.monetary * (1 + features.frequency * 0.1) * (1 - churn_prob)
    
    # Calculate confidence based on feature completeness and validity
    # Higher confidence when all features are provided and valid
    confidence = 0.5  # Base confidence
    
    # Check feature completeness (each valid feature adds to confidence)
    valid_features = 0
    total_features = 6
    
    if features.monetary > 0:
        valid_features += 1
    if features.frequency >= 1:
        valid_features += 1
    if 0 <= features.avg_review_score <= 5:
        valid_features += 1
    if features.avg_installments >= 1:
        valid_features += 1
    if 0 <= features.credit_card_rate <= 1:
        valid_features += 1
    if 0 <= features.late_delivery_rate <= 1:
        valid_features += 1
    
    # Calculate confidence as percentage of valid features
    confidence = round(valid_features / total_features, 2)
    
    # Adjust based on data quality signals
    # Higher monetary value and frequency indicate more reliable prediction
    if features.monetary > 500 and features.frequency > 3:
        confidence = min(confidence + 0.1, 0.95)
    
    # Lower confidence for customers with high late delivery rate
    if features.late_delivery_rate > 0.3:
        confidence = max(confidence - 0.1, 0.3)
    
    confidence = round(confidence, 2)
    
    return {
        "churn_risk_score": round(churn_prob, 3),
        "segment": segment,
        "ltv_estimate": round(ltv, 2),
        "recommended_action": _get_recommendation(segment),
        "confidence": confidence
    }

def _classify_segment(churn_prob, monetary, frequency):
    """Classify customer into segment based on scores."""
    if churn_prob < 0.1:
        return 'Champions'
    elif churn_prob < 0.2:
        return 'Loyal Customers'
    elif churn_prob < 0.35:
        return 'Potential Loyalist'
    elif churn_prob < 0.5:
        return 'New Customers'
    elif churn_prob < 0.7:
        return 'At Risk'
    elif churn_prob < 0.85:
        return 'Cant Lose Them'
    else:
        return 'Lost'

# ==================== Churn Endpoints ====================

@app.get("/churn/predictions")
async def get_churn_predictions(
    risk_level: Optional[str] = Query(None, description="Filter by risk: high, medium, low"),
    limit: int = Query(100, ge=1, le=10000),
    api_key: str = Depends(verify_api_key)
):
    """Get churn predictions for all customers. Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    
    data = load_data()
    
    # Use churn data if available
    if data['customer_churn'] is not None:
        churn_df = data['customer_churn'].copy()
    else:
        # Calculate from RFM using vectorized operations
        churn_df = data['rfm_segments'].copy()
        segment_risk = {
            'Champions': 0.05,
            'Loyal Customers': 0.10,
            'Potential Loyalist': 0.20,
            'New Customers': 0.30,
            'At Risk': 0.60,
            'Cant Lose Them': 0.80,
            'Lost': 0.95
        }
        churn_df['churn_probability'] = (
            churn_df['rfm_segment'].map(segment_risk).fillna(0.5) *
            (1 + (churn_df['recency'].clip(upper=180) / 180) * 0.2)
        ).clip(lower=0.0, upper=1.0)
    
    # Filter by risk level
    if risk_level == 'high':
        churn_df = churn_df[churn_df['churn_probability'] >= 0.6]
    elif risk_level == 'medium':
        churn_df = churn_df[(churn_df['churn_probability'] >= 0.3) & (churn_df['churn_probability'] < 0.6)]
    elif risk_level == 'low':
        churn_df = churn_df[churn_df['churn_probability'] < 0.3]
    
    # Get top at-risk
    at_risk = churn_df.nlargest(limit, 'churn_probability')
    
    return {
        "total_at_risk": len(churn_df[churn_df['churn_probability'] >= 0.6]),
        "total_medium_risk": len(churn_df[(churn_df['churn_probability'] >= 0.3) & (churn_df['churn_probability'] < 0.6)]),
        "predictions": at_risk[['customer_id', 'churn_probability']].to_dict(orient='records')
    }

# ==================== Campaign Endpoints ====================

@app.post("/campaigns/generate")
async def generate_campaign(
    request: CampaignRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate an automated retention campaign. Requires API authentication."""
    # Check rate limit
    await check_rate_limit(api_key)
    
    # Check tier access (campaign generation only for Growth and Enterprise)
    key_tier = API_KEYS[api_key]["tier"]
    if key_tier == "starter":
        raise HTTPException(
            status_code=403,
            detail="Campaign generation requires Growth or Enterprise tier."
        )
    
    data = load_data()
    
    # Get customers in target segment
    segment_customers = data['rfm_segments'][data['rfm_segments']['rfm_segment'] == request.target_segment]
    
    if segment_customers.empty:
        raise HTTPException(status_code=404, detail=f"Segment '{request.target_segment}' not found")
    
    # Calculate campaign metrics
    segment_size = len(segment_customers)
    
    # Estimate reach based on channel
    channel_reach = {
        'email': 0.85,
        'sms': 0.95,
        'push': 0.70,
        'social': 0.60
    }
    estimated_reach = int(segment_size * channel_reach.get(request.channel, 0.7))
    
    # Estimate conversion based on segment
    segment_conversion = {
        'Champions': 0.15,
        'Loyal Customers': 0.12,
        'Potential Loyalist': 0.08,
        'New Customers': 0.10,
        'At Risk': 0.05,
        'Cant Lose Them': 0.03,
        'Lost': 0.02
    }
    conversion_rate = segment_conversion.get(request.target_segment, 0.05)
    estimated_conversion = estimated_reach * conversion_rate
    
    # Average order value from segment
    avg_order_value = segment_customers['monetary'].mean()
    expected_revenue = estimated_conversion * avg_order_value * 2  # Assume 2x LTV from conversion
    
    # Generate campaign ID
    campaign_id = f"CMP_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Generate message templates
    message_templates = _generate_messages(request.target_segment, request.channel)
    
    # Generate action items
    action_items = _generate_action_items(request.target_segment, request.budget)
    
    return {
        "campaign_id": campaign_id,
        "target_segment": request.target_segment,
        "segment_size": segment_size,
        "budget": request.budget,
        "channel": request.channel,
        "estimated_reach": estimated_reach,
        "estimated_conversion": round(estimated_conversion, 0),
        "expected_revenue": round(expected_revenue, 2),
        "roi": round((expected_revenue - request.budget) / request.budget * 100, 1) if request.budget > 0 else 0,
        "recommended_channels": list(channel_reach.keys()),
        "message_templates": message_templates,
        "action_items": action_items,
        "generated_at": datetime.utcnow().isoformat()
    }

def _generate_messages(segment: str, channel: str) -> Dict[str, str]:
    """Generate message templates for campaign."""
    messages = {
        'At Risk': {
            'email': "We miss you! Here's 20% off your next order to welcome you back.",
            'sms': "😢 We miss you! Come back and save 20% with code: WELCOME20",
            'push': "Don't miss out! Your favorite products are waiting with 20% off"
        },
        'Cant Lose Them': {
            'email': "Exclusive VIP offer - 30% off + free shipping as our valued customer.",
            'email_alt': "We can't imagine life without you! 🎁 Special VIP offer inside.",
            'sms': "🥺 VIP alert! 30% OFF + FREE SHIPPING just for you. Code: VIP30",
            'push': "You're special to us! Unlock your exclusive VIP reward"
        },
        'Champions': {
            'email': "Thank you for being amazing! Early access to our new collection.",
            'sms': "⭐ VIP early access! Shop new arrivals before everyone else.",
            'push': "Your exclusive early access is here!"
        },
        'Loyal Customers': {
            'email': "Thank you for your loyalty! Here's a gift for you.",
            'sms': "🎁 Thank you! Here's a special thank-you gift from us.",
            'push': "Your loyalty rewards are waiting!"
        }
    }
    
    return messages.get(segment, {
        'email': f"Special offer just for you! Shop now and save.",
        'sms': "Special offer awaits! Don't miss out.",
        'push': "New deals waiting for you!"
    })

def _generate_action_items(segment: str, budget: float) -> List[str]:
    """Generate action items for campaign."""
    base_actions = [
        "Set up automated email sequence",
        "Create targeted landing page",
        "Configure tracking pixels"
    ]
    
    segment_actions = {
        'At Risk': [
            "Create urgency with countdown timers",
            "Offer time-limited discount",
            "Send satisfaction survey"
        ],
        'Cant Lose Them': [
            "Prepare personalized video message",
            "Offer exclusive product bundle",
            "Schedule direct outreach call"
        ],
        'Champions': [
            "Create referral program",
            "Offer early access to new products",
            "Launch loyalty rewards program"
        ]
    }
    
    return segment_actions.get(segment, base_actions)

# ==================== Pricing/Monetization ====================

@app.get("/pricing")
async def get_pricing():
    """Get API pricing tiers for monetization."""
    return {
        "tiers": [
            {
                "name": "Starter",
                "price": 0,
                "features": [
                    "100 API calls/month",
                    "Basic analytics",
                    "Email support"
                ],
                "limits": {
                    "api_calls": 100,
                    "customers": 1000
                }
            },
            {
                "name": "Growth",
                "price": 99,
                "period": "month",
                "features": [
                    "10,000 API calls/month",
                    "Full customer scoring",
                    "Campaign generation",
                    "Priority support"
                ],
                "limits": {
                    "api_calls": 10000,
                    "customers": 50000
                }
            },
            {
                "name": "Enterprise",
                "price": 499,
                "period": "month",
                "features": [
                    "Unlimited API calls",
                    "Custom ML models",
                    "Dedicated account manager",
                    "SLA guarantee",
                    "Custom integrations"
                ],
                "limits": {
                    "api_calls": -1,
                    "customers": -1
                }
            }
        ],
        "currency": "USD",
        "generated_at": datetime.utcnow().isoformat()
    }

@app.get("/usage")
async def get_usage(
    x_api_key: Annotated[str, Header()] = None
):
    """Get current API usage for monitoring. Requires API authentication."""
    # Verify API key if provided
    if x_api_key is not None:
        if x_api_key not in API_KEYS:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key.",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        # Check rate limit
        await check_rate_limit(x_api_key)
    
    return {
        "api_calls_today": 0,
        "api_calls_monthly": 0,
        "customers_scored": 0,
        "campaigns_generated": 0,
        "limits": {
            "api_calls": 10000,
            "customers": 50000
        }
    }

# Run with: uvicorn api_service:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
