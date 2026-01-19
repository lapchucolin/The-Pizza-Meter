"""
Pentagon Pizza Index - Live Scraper Test
==========================================
Tests the scraping of live busyness data from Google Maps and
correlates with market volatility indicators.

Sensors:
1. Domino's Pizza (Crystal City) - Primary Pizza Indicator
2. Freddie's Beach Bar (Crystal City) - Inverse Indicator
3. Papa John's Pizza - Secondary (NEEDS MANUAL PLACE ID)
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# ============================================================================
# SENSOR CONFIGURATION - Place IDs discovered from find_places.py
# ============================================================================
SENSORS = [
    {
        "name": "Domino's Pizza (Crystal City)",
        "place_id": "ChIJiRsMcTKxt4kRb9rj3ZyTt-M",
        "address": "Domino's Pizza Crystal City Arlington VA",
        "role": "Primary",
        "indicator_type": "pizza_spike",  # Higher = more activity
    },
    {
        "name": "Freddie's Beach Bar",
        "place_id": "ChIJlxXYvim3t4kR4MCE7Wn3AqI",
        "address": "Freddie's Beach Bar Crystal City Arlington VA",
        "role": "Inverse",
        "indicator_type": "inverse",  # Lower = Pentagon working late
    },
    # Uncomment when you have the Place ID:
    # {
    #     "name": "Papa John's Pizza",
    #     "place_id": "REPLACE_WITH_PLACE_ID",
    #     "address": "Papa John's Pizza Columbia Pike Arlington VA",
    #     "role": "Secondary",
    #     "indicator_type": "pizza_spike",
    # },
]


def get_live_popularity(place_id: str, address: str = None) -> Dict[str, Any]:
    """
    Fetch live popularity data for a place using livepopulartimes.
    
    Note: get_populartimes_by_place_id requires a Google API key, so we use
    get_populartimes_by_address instead which scrapes directly from Google Maps.
    
    Returns:
        dict with keys: current_popularity, usual_popularity, has_data, error
    """
    try:
        import livepopulartimes
        
        # Use address-based lookup (doesn't require API key)
        # If no address provided, we'll construct a search query
        if address:
            data = livepopulartimes.get_populartimes_by_address(address)
        else:
            # Fallback: this won't work well without an address
            return {"has_data": False, "error": "No address provided and API key required for Place ID lookup"}
        
        if not data:
            return {
                "has_data": False,
                "error": "No data returned from API"
            }
        
        # Get current hour to look up usual popularity
        now = datetime.now()
        day_of_week = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        
        # Get the current live popularity (may be None if place is closed)
        current_pop = data.get('current_popularity')
        
        # Get usual popularity for this day/hour from populartimes
        usual_pop = None
        populartimes = data.get('populartimes')
        if populartimes and len(populartimes) > day_of_week:
            day_data = populartimes[day_of_week].get('data', [])
            if hour < len(day_data):
                usual_pop = day_data[hour]
        
        return {
            "has_data": True,
            "current_popularity": current_pop,
            "usual_popularity": usual_pop,
            "name": data.get('name'),
            "address": data.get('address'),
            "rating": data.get('rating'),
            "day": populartimes[day_of_week]['name'] if populartimes else None,
            "hour": hour,
        }
        
    except ImportError:
        return {"has_data": False, "error": "livepopulartimes not installed"}
    except Exception as e:
        return {"has_data": False, "error": str(e)}


def get_market_data() -> Dict[str, Any]:
    """
    Fetch current VIX and Gold prices using yfinance.
    """
    try:
        import yfinance as yf
        
        result = {
            "has_data": True,
            "vix": None,
            "gold": None,
            "errors": []
        }
        
        # Fetch VIX
        try:
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1d")
            if not vix_hist.empty:
                result["vix"] = round(vix_hist['Close'].iloc[-1], 2)
                result["vix_change"] = round(
                    (vix_hist['Close'].iloc[-1] - vix_hist['Open'].iloc[0]) 
                    / vix_hist['Open'].iloc[0] * 100, 2
                )
        except Exception as e:
            result["errors"].append(f"VIX: {str(e)}")
        
        # Fetch Gold
        try:
            gold = yf.Ticker("GC=F")
            gold_hist = gold.history(period="1d")
            if not gold_hist.empty:
                result["gold"] = round(gold_hist['Close'].iloc[-1], 2)
                result["gold_change"] = round(
                    (gold_hist['Close'].iloc[-1] - gold_hist['Open'].iloc[0]) 
                    / gold_hist['Open'].iloc[0] * 100, 2
                )
        except Exception as e:
            result["errors"].append(f"Gold: {str(e)}")
        
        return result
        
    except ImportError:
        return {"has_data": False, "error": "yfinance not installed"}
    except Exception as e:
        return {"has_data": False, "error": str(e)}


def calculate_trend(current: Optional[int], usual: Optional[int]) -> str:
    """
    Calculate the trend percentage and return a formatted string.
    """
    if current is None:
        return "CLOSED/NO DATA"
    if usual is None or usual == 0:
        return f"Live: {current} (no baseline)"
    
    pct_change = ((current - usual) / usual) * 100
    
    if pct_change > 50:
        trend = f"+{pct_change:.0f}% (🔴 SPIKE!)"
    elif pct_change > 25:
        trend = f"+{pct_change:.0f}% (⚠️ ELEVATED)"
    elif pct_change > 10:
        trend = f"+{pct_change:.0f}% (📈 Above Normal)"
    elif pct_change < -25:
        trend = f"{pct_change:.0f}% (📉 Very Low)"
    elif pct_change < -10:
        trend = f"{pct_change:.0f}% (↓ Below Normal)"
    else:
        trend = f"{pct_change:+.0f}% (Normal)"
    
    return trend


def generate_report():
    """Generate the consolidated Pentagon Pizza Index report."""
    
    now = datetime.now()
    
    print()
    print("═" * 70)
    print("  🍕 PENTAGON PIZZA INDEX - LIVE ANALYSIS REPORT 🍕")
    print("═" * 70)
    print(f"  Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')} (Local)")
    print(f"  Day: {now.strftime('%A')}, Hour: {now.hour}:00")
    print("═" * 70)
    print()
    
    # =========================================================================
    # SECTION 1: ALTERNATIVE DATA SENSORS
    # =========================================================================
    print("┌─ ALTERNATIVE DATA SENSORS ────────────────────────────────────────┐")
    print()
    
    sensor_results = []
    
    for sensor in SENSORS:
        print(f"  [Fetching] {sensor['name']}...", end=" ", flush=True)
        
        data = get_live_popularity(sensor['place_id'], sensor.get('address'))
        
        if data.get('has_data'):
            current = data.get('current_popularity')
            usual = data.get('usual_popularity')
            trend = calculate_trend(current, usual)
            
            print("✓")
            print(f"  │")
            print(f"  ├─ [{sensor['role'].upper()}] {data.get('name', sensor['name'])}")
            print(f"  │    Live: {current if current is not None else 'N/A'} | "
                  f"Usual: {usual if usual is not None else 'N/A'} | "
                  f"Trend: {trend}")
            print(f"  │    📍 {data.get('address', 'Address not available')}")
            
            sensor_results.append({
                "sensor": sensor['name'],
                "role": sensor['role'],
                "current": current,
                "usual": usual,
                "indicator_type": sensor['indicator_type'],
            })
        else:
            print("✗")
            print(f"  ├─ [{sensor['role'].upper()}] {sensor['name']}")
            print(f"  │    ⚠️ ERROR: {data.get('error', 'Unknown error')}")
            sensor_results.append({
                "sensor": sensor['name'],
                "role": sensor['role'],
                "error": data.get('error'),
            })
        
        print(f"  │")
    
    print("└────────────────────────────────────────────────────────────────────┘")
    print()
    
    # =========================================================================
    # SECTION 2: MARKET DATA
    # =========================================================================
    print("┌─ MARKET VOLATILITY INDICATORS ──────────────────────────────────────┐")
    print()
    
    print("  [Fetching] VIX & Gold...", end=" ", flush=True)
    market = get_market_data()
    
    if market.get('has_data'):
        print("✓")
        print(f"  │")
        if market.get('vix'):
            vix_emoji = "🔴" if market['vix'] > 25 else ("⚠️" if market['vix'] > 20 else "🟢")
            print(f"  ├─ [VIX] {market['vix']} {vix_emoji} "
                  f"({market.get('vix_change', 0):+.2f}% today)")
        else:
            print(f"  ├─ [VIX] N/A (market may be closed)")
            
        if market.get('gold'):
            print(f"  ├─ [GOLD] ${market['gold']:,.2f} "
                  f"({market.get('gold_change', 0):+.2f}% today)")
        else:
            print(f"  ├─ [GOLD] N/A (market may be closed)")
        
        if market.get('errors'):
            for err in market['errors']:
                print(f"  │    ⚠️ {err}")
    else:
        print("✗")
        print(f"  │    ⚠️ ERROR: {market.get('error', 'Unknown error')}")
    
    print(f"  │")
    print("└────────────────────────────────────────────────────────────────────┘")
    print()
    
    # =========================================================================
    # SECTION 3: COMPOSITE INDEX
    # =========================================================================
    print("┌─ PENTAGON PIZZA INDEX (COMPOSITE) ─────────────────────────────────┐")
    print()
    
    # Calculate composite score
    active_sensors = [s for s in sensor_results if s.get('current') is not None]
    
    if active_sensors:
        pizza_anomaly_scores = []
        
        for s in active_sensors:
            if s.get('usual') and s['usual'] > 0:
                pct = ((s['current'] - s['usual']) / s['usual']) * 100
                
                # Invert for inverse indicators
                if s.get('indicator_type') == 'inverse':
                    pct = -pct  # Empty bar = high activity
                
                pizza_anomaly_scores.append(pct)
        
        if pizza_anomaly_scores:
            avg_anomaly = sum(pizza_anomaly_scores) / len(pizza_anomaly_scores)
            
            if avg_anomaly > 50:
                alert = "🔴 RED ALERT"
                interpretation = "Unusual late-night activity detected. Possible crisis mode."
            elif avg_anomaly > 25:
                alert = "🟠 ELEVATED"
                interpretation = "Above-normal activity. Monitor for developments."
            elif avg_anomaly > 10:
                alert = "🟡 WATCH"
                interpretation = "Slightly elevated. Normal variation possible."
            elif avg_anomaly < -25:
                alert = "🔵 QUIET"
                interpretation = "Below-normal activity. Routine operations."
            else:
                alert = "🟢 NORMAL"
                interpretation = "Activity within expected range."
            
            print(f"  │  COMPOSITE ANOMALY SCORE: {avg_anomaly:+.1f}%")
            print(f"  │  STATUS: {alert}")
            print(f"  │")
            print(f"  │  Interpretation: {interpretation}")
        else:
            print(f"  │  ⚠️ Cannot calculate: No baseline data available")
    else:
        print(f"  │  ⚠️ Cannot calculate: No live data from sensors")
        print(f"  │     This may be due to:")
        print(f"  │     - Locations being closed")
        print(f"  │     - Google not providing live data")
        print(f"  │     - Anti-scraping measures")
    
    print(f"  │")
    print("└────────────────────────────────────────────────────────────────────┘")
    print()
    
    print("═" * 70)
    print("  End of Report")
    print("═" * 70)
    print()
    
    # Save raw data for analysis
    output = {
        "timestamp": now.isoformat(),
        "sensors": sensor_results,
        "market": market,
    }
    
    with open("latest_reading.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print("[DATA SAVED] latest_reading.json")
    
    return 0


def main():
    try:
        return generate_report()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] User cancelled.")
        return 1
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
