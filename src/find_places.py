"""
Pentagon Pizza Index - Enhanced Place ID Discovery
===================================================
Discovers more pizza shops and restaurants near the Pentagon area.
"""

import sys
import json
from datetime import datetime

# Extended list of pizza shops and food venues near Pentagon
SEARCH_LOCATIONS = [
    # Pizza Chains
    {"name": "Domino's Pizza Crystal City", "query": "Domino's Pizza Crystal City Arlington VA"},
    {"name": "Domino's Pizza Pentagon City", "query": "Domino's Pizza Pentagon City Arlington VA"},
    {"name": "Papa John's Columbia Pike", "query": "Papa John's Pizza Columbia Pike Arlington VA"},
    {"name": "Papa John's Pentagon City", "query": "Papa John's Pentagon City Arlington VA"},
    {"name": "Pizza Hut Arlington", "query": "Pizza Hut Arlington VA Pentagon"},
    {"name": "Little Caesars Arlington", "query": "Little Caesars Pizza Arlington VA"},
    
    # Local Pizza Shops
    {"name": "Wiseguy Pizza Pentagon", "query": "Wiseguy Pizza Pentagon City Arlington VA"},
    {"name": "Pete's New Haven Pizza", "query": "Pete's New Haven Style Apizza Arlington VA"},
    {"name": "Mia's Italian Kitchen", "query": "Mia's Italian Kitchen Arlington VA"},
    {"name": "Pupatella Pentagon", "query": "Pupatella Neapolitan Pizza Arlington VA"},
    {"name": "We The Pizza Capitol Hill", "query": "We The Pizza Capitol Hill Washington DC"},
    
    # Late Night Food Options
    {"name": "McDonald's Pentagon City", "query": "McDonald's Pentagon City Arlington VA"},
    {"name": "Taco Bell Crystal City", "query": "Taco Bell Crystal City Arlington VA"},
    {"name": "Five Guys Pentagon", "query": "Five Guys Pentagon City Arlington VA"},
    
    # Bars (Inverse Indicators)
    {"name": "Freddie's Beach Bar", "query": "Freddie's Beach Bar Crystal City Arlington VA"},
    {"name": "Crystal City Sports Pub", "query": "Crystal City Sports Pub Arlington VA"},
]


def search_place(query: str) -> dict:
    """Search for a place using livepopulartimes."""
    try:
        import livepopulartimes
        data = livepopulartimes.get_populartimes_by_address(query)
        
        if data and data.get('name') and data.get('populartimes'):
            return {
                "success": True,
                "name": data.get('name'),
                "address": data.get('address'),
                "rating": data.get('rating'),
                "has_populartimes": True,
            }
        elif data and data.get('name'):
            return {
                "success": True,
                "name": data.get('name'),
                "address": data.get('address'),
                "rating": data.get('rating'),
                "has_populartimes": False,
            }
        return {"success": False, "error": "No data"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    print("=" * 70)
    print("PENTAGON PIZZA INDEX - EXTENDED SENSOR DISCOVERY")
    print("=" * 70)
    print()
    
    discovered = []
    
    for location in SEARCH_LOCATIONS:
        print(f"Searching: {location['name']}...", end=" ", flush=True)
        result = search_place(location['query'])
        
        if result.get('success'):
            status = "✓" if result.get('has_populartimes') else "⚠️ (no timing data)"
            print(f"{status}")
            print(f"   Found: {result.get('name')}")
            print(f"   Address: {result.get('address')}")
            
            discovered.append({
                "search_name": location['name'],
                "query": location['query'],
                "found_name": result.get('name'),
                "address": result.get('address'),
                "rating": result.get('rating'),
                "has_populartimes": result.get('has_populartimes', False),
            })
        else:
            print(f"✗ ({result.get('error', 'Not found')})")
    
    # Filter to only those with popular times data
    valid_sensors = [d for d in discovered if d.get('has_populartimes')]
    
    print()
    print("=" * 70)
    print(f"DISCOVERY COMPLETE: {len(valid_sensors)}/{len(discovered)} locations have timing data")
    print("=" * 70)
    print()
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_searched": len(SEARCH_LOCATIONS),
        "total_found": len(discovered),
        "valid_sensors": len(valid_sensors),
        "locations": discovered,
    }
    
    with open("extended_sensors.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("[SAVED] extended_sensors.json")
    print()
    
    # Print sensor config for dashboard
    print("SENSOR CONFIGURATION FOR DASHBOARD:")
    print("-" * 40)
    for d in valid_sensors[:10]:  # Top 10
        print(f'    {{"name": "{d["found_name"]}", "address": "{d["query"]}", "role": "Primary"}},')
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
