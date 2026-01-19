"""
Pentagon Pizza Index - Robust Scraper POC
==========================================
Implements the "Project Manifesto" requirements for validation.
Targeting specific cluster of venues with anti-scraping measures.
"""

import time
import random
import sys
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import livepopulartimes
    import yfinance as yf
except ImportError:
    print("Error: Required libraries not found. Please run: pip install livepopulartimes yfinance")
    sys.exit(1)

# ============================================================================
# TARGET CONFIGURATION (The "Cluster")
# ============================================================================
TARGETS = [
    {
        "id": "A",
        "name": "Domino's Pizza (Eads St)",
        "address_query": "Domino's Pizza 1500 S Eads St Arlington VA 22202",
        "role": "Primary",
        "type": "pizza"
    },
    {
        "id": "B",
        "name": "Papa John's Pizza (Columbia Pike)",
        "address_query": "Papa John's Pizza 3405 Columbia Pike Arlington VA 22204",
        "role": "Secondary",
        "type": "pizza"
    },
    {
        "id": "C",
        "name": "Freddie's Beach Bar",
        "address_query": "Freddie's Beach Bar 555 23rd St S Arlington VA 22202",
        "role": "Inverse",
        "type": "bar"
    }
]

def get_delay():
    """Requirement 3: Random Delays (3-7 seconds)"""
    delay = random.uniform(3, 7)
    print(f"   [System] Waiting {delay:.1f}s to avoid detection...")
    time.sleep(delay)

def fetch_sensor_data(target: Dict[str, str]) -> Dict[str, Any]:
    """
    Requirement 2: Two-Step Discovery Logic
    Step A: Find by address
    Step B: Extract data
    """
    print(f"   [Connecting] Searching for '{target['name']}'...")
    
    try:
        # Step A & B combined: generic scrape by address
        # livepopulartimes returns the full object if found
        data = livepopulartimes.get_populartimes_by_address(target['address_query'])
        
        if not data:
            return {"status": "OFFLINE", "reason": "No data returned by Google"}
            
        place_id = data.get('place_id')
        name = data.get('name')
        current = data.get('current_popularity')
        rating = data.get('rating')
        
        # Calculate historical average for this hour
        now = datetime.now()
        day_idx = now.weekday()
        hour_idx = now.hour
        historical = 0
        
        populartimes = data.get('populartimes', [])
        if populartimes and len(populartimes) > day_idx:
            day_data = populartimes[day_idx].get('data', [])
            if len(day_data) > hour_idx:
                historical = day_data[hour_idx]
                
        # Determine signal
        signal = "NORMAL"
        percent_change = 0
        
        if current is not None and historical > 0:
            change = ((current - historical) / historical) * 100
            percent_change = change
            if change > 50:
                signal = f"SPIKE DETECTED (+{change:.0f}%)"
            elif change > 25:
                signal = f"ELEVATED (+{change:.0f}%)"
            elif change < -25:
                signal = f"LOW ACTION ({change:.0f}%)"
        elif current is None:
             # Handle closed/no-data case
             current = "N/A"
             signal = "NO LIVE SIGNAL"
        
        return {
            "status": "ONLINE",
            "place_id": place_id,
            "official_name": name,
            "live": current,
            "historical": historical,
            "signal": signal,
            "rating": rating
        }
        
    except Exception as e:
        return {"status": "ERROR", "reason": str(e)}

def fetch_market_data():
    """Fetch VIX and Gold"""
    print("   [Market] Fetching real-time assets...")
    try:
        # VIX
        vix = yf.Ticker("^VIX")
        vix_price = vix.info.get('regularMarketPrice') or vix.history(period='1d')['Close'].iloc[-1]
        
        # Gold
        gold = yf.Ticker("GC=F")
        gold_price = gold.info.get('regularMarketPrice') or gold.history(period='1d')['Close'].iloc[-1]
        
        return {"vix": round(vix_price, 2), "gold": round(gold_price, 2)}
    except Exception as e:
        return {"vix": "Error", "gold": "Error", "msg": str(e)}

def print_report(sensor_results, market_data):
    """Requirement 4: The Output Report"""
    print("\n" + "="*40)
    print("--- SENSOR REPORT ---")
    print("="*40)
    
    for i, res in enumerate(sensor_results):
        target = TARGETS[i]
        print(f"[{target['name']}]")
        
        if res['status'] == 'ONLINE':
            print(f"   > Status: ONLINE (ID: {res.get('place_id', 'Unknown')})")
            print(f"   > Live Busyness: {res['live']}")
            print(f"   > Historical Avg: {res['historical']}")
            print(f"   > Signal: {res['signal']}")
        else:
            print(f"   > Status: {res['status']} ({res.get('reason')})")
        print()
        
    print("[Market Context]")
    print(f"   > VIX: {market_data.get('vix')} | Gold: {market_data.get('gold')}")
    print("="*40 + "\n")

def main():
    print("Initializing Robust Scraper POC...")
    print("Targeting Pentagon Cluster...")
    print("-" * 30)
    
    results = []
    
    # Process Sensors
    for target in TARGETS:
        results.append(fetch_sensor_data(target))
        get_delay() # Anti-scraping delay
        
    # Process Market
    market = fetch_market_data()
    
    # Report
    print_report(results, market)

if __name__ == "__main__":
    main()
