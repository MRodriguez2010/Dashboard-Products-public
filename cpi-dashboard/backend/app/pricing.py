"""Pricing analysis engine for competitive intelligence."""
import statistics
from typing import List, Dict, Any


def calculate_price_position(your_price: float, competitor_prices: List[float]) -> Dict[str, Any]:
    """Calculate where your price sits relative to competitors."""
    if not competitor_prices:
        return {"position": "unknown", "percentile": 0, "recommendation": "No competitor data"}
    
    all_prices = sorted(competitor_prices)
    below = sum(1 for p in all_prices if p < your_price)
    percentile = (below / len(all_prices)) * 100
    
    avg = statistics.mean(all_prices)
    median = statistics.median(all_prices)
    
    if percentile < 25:
        position = "budget"
        recommendation = "You're priced below most competitors. Consider raising price or emphasizing value."
    elif percentile < 50:
        position = "below_average"
        recommendation = "Slightly below market average. Good competitive position for value-seekers."
    elif percentile < 75:
        position = "above_average"
        recommendation = "Above market median. Ensure premium features justify the price."
    else:
        position = "premium"
        recommendation = "Premium pricing tier. Must deliver exceptional value to retain customers."
    
    return {
        "position": position,
        "percentile": round(percentile, 1),
        "avg_market_price": round(avg, 2),
        "median_market_price": round(median, 2),
        "min_price": round(min(all_prices), 2),
        "max_price": round(max(all_prices), 2),
        "price_spread": round(max(all_prices) - min(all_prices), 2),
        "your_vs_avg_pct": round(((your_price - avg) / avg) * 100, 1) if avg else 0,
        "recommendation": recommendation,
    }


def detect_price_changes(prices_history: List[Dict], threshold_pct: float = 5.0) -> List[Dict]:
    """Detect significant price changes from historical data."""
    alerts = []
    if len(prices_history) < 2:
        return alerts
    
    sorted_prices = sorted(prices_history, key=lambda x: x["recorded_at"])
    for i in range(1, len(sorted_prices)):
        old = sorted_prices[i-1]["price"]
        new = sorted_prices[i]["price"]
        if old == 0:
            continue
        change_pct = ((new - old) / old) * 100
        
        if abs(change_pct) >= threshold_pct:
            alert_type = "price_drop" if change_pct < 0 else "price_increase"
            alerts.append({
                "alert_type": alert_type,
                "old_price": old,
                "new_price": new,
                "change_pct": round(change_pct, 1),
                "date": sorted_prices[i]["recorded_at"],
                "product_id": sorted_prices[i].get("product_id"),
                "competitor_id": sorted_prices[i].get("competitor_id"),
            })
    return alerts


def calculate_elasticity_estimate(price_changes: List[Dict], volume_changes: List[float] = None) -> float:
    """Rough price elasticity estimate. Returns elasticity coefficient."""
    if not price_changes or len(price_changes) < 2:
        return -1.0  # default assumption: unit elastic
    
    avg_change = statistics.mean([abs(p["change_pct"]) for p in price_changes])
    # Without real volume data, estimate based on market sensitivity
    if avg_change > 20:
        return -2.5  # very elastic
    elif avg_change > 10:
        return -1.5  # elastic  
    elif avg_change > 5:
        return -1.0  # unit elastic
    else:
        return -0.5  # inelastic


def generate_pricing_recommendations(
    your_price: float,
    competitor_prices: List[float],
    category: str,
    tier: str = "mid-range"
) -> List[Dict[str, str]]:
    """Generate actionable pricing recommendations."""
    recs = []
    if not competitor_prices:
        return [{"type": "info", "title": "Insufficient Data", "detail": "Need competitor pricing data."}]
    
    avg = statistics.mean(competitor_prices)
    median = statistics.median(competitor_prices)
    
    # Price positioning
    diff_pct = ((your_price - avg) / avg) * 100 if avg else 0
    
    if diff_pct > 20:
        recs.append({
            "type": "warning",
            "title": "Significantly Above Market",
            "detail": f"Your price is {diff_pct:.0f}% above market average (${avg:.2f}). Risk losing price-sensitive customers. Consider a tiered pricing model."
        })
    elif diff_pct > 5:
        recs.append({
            "type": "info",
            "title": "Above Average Pricing",
            "detail": f"Your price is {diff_pct:.0f}% above average. Ensure premium features are well-communicated."
        })
    elif diff_pct < -20:
        recs.append({
            "type": "opportunity",
            "title": "Room to Increase Price",
            "detail": f"You're {abs(diff_pct):.0f}% below market average. Consider a 10-15% price increase to capture value."
        })
    elif diff_pct < -5:
        recs.append({
            "type": "opportunity",
            "title": "Competitive Value Position",
            "detail": f"Priced {abs(diff_pct):.0f}% below average — strong for acquisition. Monitor margins."
        })
    else:
        recs.append({
            "type": "success",
            "title": "Well-Positioned Pricing",
            "detail": f"Within 5% of market average (${avg:.2f}). Competitive and sustainable."
        })
    
    # Spread analysis
    spread = max(competitor_prices) - min(competitor_prices)
    if spread > avg * 0.8:
        recs.append({
            "type": "info",
            "title": "Fragmented Market",
            "detail": f"Wide price spread (${spread:.2f}). Opportunity for tiered product strategy."
        })
    
    # Undercutting opportunity
    lowest = min(competitor_prices)
    if your_price > lowest * 1.3:
        recs.append({
            "type": "warning",
            "title": "Budget Competitor Threat",
            "detail": f"Cheapest competitor at ${lowest:.2f} — {((your_price/lowest)-1)*100:.0f}% below you. Monitor for market share loss."
        })
    
    return recs
