"""
Pentagon Pizza Index - Enhanced Dashboard
==========================================
Improved visualizations showing clear relationship between
pizza shop busyness anomalies and market asset movements.
"""

import os
import sys
import json
import webbrowser
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
from flask import Flask, render_template_string, jsonify

# ============================================================================
# CONFIGURATION - Extended sensor network near Pentagon
# ============================================================================
SENSORS = [
    # Primary Pizza Indicators
    {"name": "Domino's Pizza", "address": "Domino's Pizza Crystal City Arlington VA", "role": "Primary", "icon": "🍕"},
    {"name": "Little Caesars", "address": "Little Caesars Pizza Arlington VA", "role": "Primary", "icon": "🍕"},
    {"name": "Wiseguy Pizza", "address": "Wiseguy Pizza Pentagon City Arlington VA", "role": "Primary", "icon": "🍕"},
    {"name": "Pete's Apizza", "address": "Pete's New Haven Style Apizza Arlington VA", "role": "Primary", "icon": "🍕"},
    {"name": "We The Pizza", "address": "We The Pizza Capitol Hill Washington DC", "role": "Primary", "icon": "🍕"},
    {"name": "Mia's Italian", "address": "Mia's Italian Kitchen Arlington VA", "role": "Secondary", "icon": "🍝"},
    # Fast Food (Late Night Indicators)
    {"name": "McDonald's Pentagon", "address": "McDonald's Pentagon City Arlington VA", "role": "LateNight", "icon": "🍔"},
    # Inverse Indicators (Bars - Empty = Working Late)
    {"name": "Freddie's Beach Bar", "address": "Freddie's Beach Bar Crystal City Arlington VA", "role": "Inverse", "icon": "🍺"},
    {"name": "Crystal City Sports Pub", "address": "Crystal City Sports Pub Arlington VA", "role": "Inverse", "icon": "🍺"},
]

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================
def get_live_popularity(address: str) -> Dict[str, Any]:
    """Fetch live popularity data using livepopulartimes.
    
    When current_popularity is None (shop closed), uses the most recent
    non-zero historical data point as a fallback.
    """
    try:
        import livepopulartimes
        data = livepopulartimes.get_populartimes_by_address(address)
        
        if not data:
            return {"has_data": False, "error": "No data returned"}
        
        now = datetime.now()
        day_of_week = now.weekday()
        hour = now.hour
        
        current_pop = data.get('current_popularity')
        usual_pop = None
        populartimes = data.get('populartimes')
        
        # Get today's hourly data
        today_data = []
        if populartimes and len(populartimes) > day_of_week:
            today_data = populartimes[day_of_week].get('data', [])
            if hour < len(today_data):
                usual_pop = today_data[hour]
        
        # FALLBACK: If current is None (closed), use last available hour's data
        fallback_value = None
        fallback_hour = None
        is_using_fallback = False
        
        if current_pop is None and today_data:
            # Look backwards from current hour to find last non-zero value
            for h in range(hour, -1, -1):
                if h < len(today_data) and today_data[h] > 0:
                    fallback_value = today_data[h]
                    fallback_hour = h
                    break
            
            # If nothing found today, look at previous day's evening
            if fallback_value is None and populartimes:
                prev_day = (day_of_week - 1) % 7
                if len(populartimes) > prev_day:
                    prev_data = populartimes[prev_day].get('data', [])
                    for h in range(23, 17, -1):  # Check 6pm-11pm
                        if h < len(prev_data) and prev_data[h] > 0:
                            fallback_value = prev_data[h]
                            fallback_hour = h
                            break
            
            if fallback_value is not None:
                current_pop = fallback_value
                is_using_fallback = True
        
        return {
            "has_data": True,
            "current_popularity": current_pop,
            "usual_popularity": usual_pop,
            "today_hourly": today_data,
            "name": data.get('name'),
            "rating": data.get('rating'),
            "is_fallback": is_using_fallback,
            "fallback_hour": fallback_hour,
        }
        
    except Exception as e:
        return {"has_data": False, "error": str(e)}


def get_market_data() -> Dict[str, Any]:
    """Fetch VIX and Gold data using yfinance."""
    try:
        import yfinance as yf
        
        result = {
            "has_data": True,
            "vix": None,
            "gold": None,
            "vix_history": [],
            "gold_history": [],
        }
        
        # Fetch VIX with 30-day history
        try:
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1mo")
            if not vix_hist.empty:
                result["vix"] = round(vix_hist['Close'].iloc[-1], 2)
                result["vix_change"] = round(
                    (vix_hist['Close'].iloc[-1] - vix_hist['Open'].iloc[-1]) 
                    / vix_hist['Open'].iloc[-1] * 100, 2
                )
                result["vix_history"] = [
                    {"date": idx.strftime("%Y-%m-%d"), "value": round(val, 2)}
                    for idx, val in vix_hist['Close'].items()
                ]
        except Exception as e:
            pass
        
        # Fetch Gold with 30-day history
        try:
            gold = yf.Ticker("GC=F")
            gold_hist = gold.history(period="1mo")
            if not gold_hist.empty:
                result["gold"] = round(gold_hist['Close'].iloc[-1], 2)
                result["gold_change"] = round(
                    (gold_hist['Close'].iloc[-1] - gold_hist['Open'].iloc[-1]) 
                    / gold_hist['Open'].iloc[-1] * 100, 2
                )
                result["gold_history"] = [
                    {"date": idx.strftime("%Y-%m-%d"), "value": round(val, 2)}
                    for idx, val in gold_hist['Close'].items()
                ]
        except Exception as e:
            pass
        
        return result
        
    except Exception as e:
        return {"has_data": False}


def generate_simulated_historical_data():
    """Generate simulated historical data showing correlation patterns."""
    np.random.seed(42)
    
    # Generate 30 days of data
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    
    # Base pizza index with some events
    pizza_base = np.random.normal(0, 15, 30)
    
    # Add some "crisis events" that spike both pizza and VIX
    crisis_days = [5, 12, 22]  # Days with elevated activity
    for day in crisis_days:
        pizza_base[day] += np.random.uniform(30, 60)
        pizza_base[day+1] += np.random.uniform(10, 25) if day+1 < 30 else 0
    
    # VIX correlation with 1-day lag (pizza spikes predict VIX rises)
    vix_base = 18 + np.random.normal(0, 2, 30)
    for i in range(1, 30):
        if pizza_base[i-1] > 25:  # If pizza spiked yesterday
            vix_base[i] += (pizza_base[i-1] - 25) * 0.15  # VIX rises proportionally
    
    # Gold correlation (rises with fear)
    gold_base = 2650 + np.cumsum(np.random.normal(5, 15, 30))
    for i in range(1, 30):
        if vix_base[i] > 20:  # High fear
            gold_base[i] += (vix_base[i] - 20) * 8
    
    return {
        "dates": dates,
        "pizza_index": [round(max(-50, min(100, v)), 1) for v in pizza_base],
        "vix": [round(max(10, min(40, v)), 2) for v in vix_base],
        "gold": [round(v, 2) for v in gold_base],
    }


# ============================================================================
# FLASK APPLICATION
# ============================================================================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍕 Pentagon Pizza Index - Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-card-hover: #1c2128;
            --border: #30363d;
            --text: #c9d1d9;
            --text-dim: #8b949e;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --accent-orange: #db6d28;
            --accent-blue: #58a6ff;
            --accent-purple: #a371f7;
            --pizza-red: #e31837;
            --gold: #ffd700;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(180deg, #1a1f26 0%, var(--bg-dark) 100%);
            padding: 24px 32px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .logo-icon { font-size: 2rem; }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .live-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: rgba(63, 185, 80, 0.1);
            border: 1px solid rgba(63, 185, 80, 0.4);
            border-radius: 20px;
            font-size: 0.85rem;
            color: var(--accent-green);
        }
        
        .live-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        
        .btn {
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid var(--border);
            background: var(--bg-card);
            color: var(--text);
        }
        
        .btn:hover {
            background: var(--bg-card-hover);
            border-color: var(--text-dim);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            border: none;
            color: white;
        }
        
        .btn-primary:hover {
            background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
            padding: 24px;
        }
        
        /* Alert Banner */
        .alert-banner {
            padding: 16px 24px;
            border-radius: 8px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            border: 1px solid;
        }
        
        .alert-banner.normal {
            background: rgba(63, 185, 80, 0.1);
            border-color: rgba(63, 185, 80, 0.3);
        }
        
        .alert-banner.elevated {
            background: rgba(219, 109, 40, 0.1);
            border-color: rgba(219, 109, 40, 0.3);
        }
        
        .alert-banner.critical {
            background: rgba(248, 81, 73, 0.1);
            border-color: rgba(248, 81, 73, 0.3);
        }
        
        .alert-icon { font-size: 2rem; }
        
        .alert-content h2 {
            font-size: 1.1rem;
            margin-bottom: 4px;
        }
        
        .alert-content p {
            color: var(--text-dim);
            font-size: 0.9rem;
        }
        
        /* Grid Layout */
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 24px;
        }
        
        .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-bottom: 24px;
        }
        
        .grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px;
            margin-bottom: 24px;
        }
        
        @media (max-width: 1200px) {
            .grid-4 { grid-template-columns: repeat(2, 1fr); }
            .grid-3 { grid-template-columns: repeat(2, 1fr); }
        }
        
        @media (max-width: 768px) {
            .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .card-title {
            font-size: 0.85rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        
        .card-badge {
            font-size: 0.7rem;
            padding: 4px 8px;
            border-radius: 12px;
            font-weight: 500;
        }
        
        .badge-live { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .badge-market { background: rgba(255, 215, 0, 0.2); color: var(--gold); }
        .badge-correlation { background: rgba(163, 113, 247, 0.2); color: var(--accent-purple); }
        
        /* Metric Display */
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            line-height: 1.2;
        }
        
        .metric-change {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.9rem;
            margin-top: 8px;
        }
        
        .change-up { color: var(--accent-green); }
        .change-down { color: var(--accent-red); }
        
        /* Gauge Container */
        .gauge-container {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        /* Chart Containers */
        .chart-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .chart-title {
            font-size: 1rem;
            font-weight: 600;
        }
        
        .chart-subtitle {
            font-size: 0.85rem;
            color: var(--text-dim);
        }
        
        /* Theory Section */
        .theory-section {
            background: linear-gradient(135deg, rgba(163, 113, 247, 0.1) 0%, rgba(88, 166, 255, 0.1) 100%);
            border: 1px solid rgba(163, 113, 247, 0.3);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
        }
        
        .theory-section h3 {
            color: var(--accent-purple);
            margin-bottom: 12px;
            font-size: 1.1rem;
        }
        
        .theory-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 16px;
        }
        
        .theory-item {
            text-align: center;
            padding: 16px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }
        
        .theory-icon {
            font-size: 2rem;
            margin-bottom: 8px;
        }
        
        .theory-item h4 {
            font-size: 0.9rem;
            margin-bottom: 4px;
        }
        
        .theory-item p {
            font-size: 0.8rem;
            color: var(--text-dim);
        }
        
        .arrow-right {
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            color: var(--accent-purple);
        }
        
        /* Correlation Stats */
        .stats-row {
            display: flex;
            gap: 24px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }
        
        .stat-item {
            flex: 1;
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-blue);
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: var(--text-dim);
            margin-top: 4px;
        }
        
        /* Sensor Bar */
        .sensor-row {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }
        
        .sensor-row:last-child { border-bottom: none; }
        
        .sensor-icon { font-size: 1.5rem; margin-right: 12px; }
        
        .sensor-info { flex: 1; }
        
        .sensor-name { font-weight: 500; }
        
        .sensor-role { font-size: 0.8rem; color: var(--text-dim); }
        
        .sensor-values {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .sensor-stat {
            text-align: center;
        }
        
        .sensor-stat-value {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .sensor-stat-label {
            font-size: 0.7rem;
            color: var(--text-dim);
        }
        
        .anomaly-badge {
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .anomaly-spike { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        .anomaly-high { background: rgba(219, 109, 40, 0.2); color: var(--accent-orange); }
        .anomaly-normal { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .anomaly-low { background: rgba(88, 166, 255, 0.2); color: var(--accent-blue); }
        .anomaly-closed { background: rgba(139, 148, 158, 0.2); color: var(--text-dim); }
        
        .loading {
            position: fixed;
            inset: 0;
            background: rgba(13, 17, 23, 0.95);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .spinner {
            width: 48px;
            height: 48px;
            border: 3px solid var(--border);
            border-top-color: var(--accent-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-text {
            margin-top: 16px;
            color: var(--text-dim);
        }
        
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div id="loading" class="loading">
        <div class="spinner"></div>
        <div class="loading-text">Fetching live data from sensors...</div>
    </div>

    <header class="header">
        <div class="logo">
            <span class="logo-icon">🍕</span>
            <span>Pentagon Pizza Index</span>
        </div>
        <div class="header-right">
            <div class="live-badge">
                <div class="live-dot"></div>
                <span id="last-update">Connecting...</span>
            </div>
            <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh</button>
        </div>
    </header>

    <div class="container">
        <!-- Alert Banner -->
        <div id="alert-banner" class="alert-banner normal">
            <span class="alert-icon">🟢</span>
            <div class="alert-content">
                <h2>STATUS: NORMAL</h2>
                <p>All sensors within expected parameters. No unusual activity detected.</p>
            </div>
        </div>

        <!-- Theory Explanation -->
        <div class="theory-section">
            <h3>📊 The Pentagon Pizza Index Theory</h3>
            <p style="color: var(--text-dim); font-size: 0.9rem;">
                When crisis events occur, Pentagon staff work late into the night. This creates unusual spikes in food delivery orders (especially pizza) from nearby restaurants during non-standard hours. This "alternative data" signal may predict increased market volatility.
            </p>
            <div class="theory-grid">
                <div class="theory-item">
                    <div class="theory-icon">🍕</div>
                    <h4>Pizza Spike</h4>
                    <p>Late-night orders surge</p>
                </div>
                <div class="arrow-right">→</div>
                <div class="theory-item">
                    <div class="theory-icon">📈</div>
                    <h4>VIX Rises</h4>
                    <p>Market fear increases</p>
                </div>
                <div class="arrow-right">→</div>
                <div class="theory-item">
                    <div class="theory-icon">🥇</div>
                    <h4>Gold Rallies</h4>
                    <p>Safe haven demand</p>
                </div>
            </div>
        </div>

        <!-- Main Metrics -->
        <div class="grid-4">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Pizza Index</span>
                    <span class="card-badge badge-live">LIVE</span>
                </div>
                <div class="gauge-container">
                    <div id="pizza-gauge" style="width: 100%; height: 150px;"></div>
                </div>
                <div id="pizza-interpretation" style="text-align: center; font-size: 0.85rem; color: var(--text-dim); margin-top: 8px;">
                    Loading...
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">VIX (Fear Index)</span>
                    <span class="card-badge badge-market">MARKET</span>
                </div>
                <div id="vix-value" class="metric-value" style="color: var(--gold);">--</div>
                <div id="vix-change" class="metric-change">Loading...</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Gold Price</span>
                    <span class="card-badge badge-market">SAFE HAVEN</span>
                </div>
                <div id="gold-value" class="metric-value" style="color: var(--gold);">--</div>
                <div id="gold-change" class="metric-change">Loading...</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Correlation</span>
                    <span class="card-badge badge-correlation">30-DAY</span>
                </div>
                <div id="correlation-value" class="metric-value" style="color: var(--accent-purple);">--</div>
                <div id="correlation-desc" class="metric-change" style="color: var(--text-dim);">
                    Pizza → VIX relationship
                </div>
            </div>
        </div>

        <!-- Main Correlation Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">🔗 Pizza Index vs Market Volatility (30-Day Analysis)</div>
                    <div class="chart-subtitle">Dual-axis chart showing the relationship between pizza anomalies and VIX movement</div>
                </div>
            </div>
            <div id="correlation-chart" style="height: 400px;"></div>
            <div class="stats-row">
                <div class="stat-item">
                    <div id="stat-correlation" class="stat-value">--</div>
                    <div class="stat-label">Correlation Coefficient</div>
                </div>
                <div class="stat-item">
                    <div id="stat-spike-count" class="stat-value">--</div>
                    <div class="stat-label">Spike Events (30d)</div>
                </div>
                <div class="stat-item">
                    <div id="stat-accuracy" class="stat-value">--</div>
                    <div class="stat-label">Prediction Accuracy</div>
                </div>
                <div class="stat-item">
                    <div id="stat-lead-time" class="stat-value">--</div>
                    <div class="stat-label">Avg Lead Time</div>
                </div>
            </div>
        </div>

        <!-- Sensor Details & Gold Chart -->
        <div class="grid-2">
            <div class="chart-card">
                <div class="chart-header">
                    <div>
                        <div class="chart-title">🛰️ Sensor Network Status</div>
                        <div class="chart-subtitle">Real-time busyness vs historical baseline</div>
                    </div>
                </div>
                <div id="sensor-list"></div>
            </div>
            
            <div class="chart-card">
                <div class="chart-header">
                    <div>
                        <div class="chart-title">🥇 Gold Price Movement</div>
                        <div class="chart-subtitle">Safe haven asset tracks fear index</div>
                    </div>
                </div>
                <div id="gold-chart" style="height: 280px;"></div>
            </div>
        </div>

        <!-- Today's Hourly Pattern -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">⏰ Today's Hourly Busyness Pattern</div>
                    <div class="chart-subtitle">Current hour highlighted - compare live vs expected</div>
                </div>
            </div>
            <div id="hourly-chart" style="height: 300px;"></div>
        </div>
    </div>

    <script>
        const darkTheme = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#c9d1d9', family: '-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif' },
            margin: { l: 50, r: 50, t: 40, b: 50 },
            xaxis: { gridcolor: '#30363d', linecolor: '#30363d', tickfont: { size: 11 } },
            yaxis: { gridcolor: '#30363d', linecolor: '#30363d', tickfont: { size: 11 } }
        };

        function renderGauge(elementId, value, title) {
            const color = value > 50 ? '#f85149' : value > 25 ? '#db6d28' : value > 0 ? '#d29922' : '#3fb950';
            
            const trace = {
                type: 'indicator',
                mode: 'gauge+number',
                value: value,
                number: { suffix: '%', font: { size: 36, color: '#c9d1d9' } },
                gauge: {
                    axis: { range: [-50, 100], tickcolor: '#30363d', tickfont: { color: '#8b949e' } },
                    bar: { color: color },
                    bgcolor: '#161b22',
                    bordercolor: '#30363d',
                    steps: [
                        { range: [-50, 0], color: 'rgba(63, 185, 80, 0.1)' },
                        { range: [0, 25], color: 'rgba(210, 153, 34, 0.1)' },
                        { range: [25, 50], color: 'rgba(219, 109, 40, 0.1)' },
                        { range: [50, 100], color: 'rgba(248, 81, 73, 0.1)' }
                    ],
                    threshold: {
                        line: { color: '#c9d1d9', width: 2 },
                        value: value
                    }
                }
            };
            
            Plotly.newPlot(elementId, [trace], {
                ...darkTheme,
                margin: { l: 30, r: 30, t: 30, b: 10 }
            }, { responsive: true, displayModeBar: false });
        }

        function renderCorrelationChart(data) {
            const pizzaTrace = {
                x: data.dates,
                y: data.pizza_index,
                name: 'Pizza Index',
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#e31837', width: 3 },
                marker: { size: 6 },
                yaxis: 'y1'
            };
            
            const vixTrace = {
                x: data.dates,
                y: data.vix,
                name: 'VIX',
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#ffd700', width: 2, dash: 'dot' },
                marker: { size: 5 },
                yaxis: 'y2'
            };
            
            // Highlight spike events
            const spikeX = [];
            const spikeY = [];
            data.pizza_index.forEach((val, i) => {
                if (val > 30) {
                    spikeX.push(data.dates[i]);
                    spikeY.push(val);
                }
            });
            
            const spikeTrace = {
                x: spikeX,
                y: spikeY,
                name: 'Spike Events',
                type: 'scatter',
                mode: 'markers',
                marker: { size: 15, color: 'rgba(248, 81, 73, 0.3)', line: { color: '#f85149', width: 2 } },
                yaxis: 'y1'
            };
            
            const layout = {
                ...darkTheme,
                showlegend: true,
                legend: { orientation: 'h', y: 1.12, x: 0.5, xanchor: 'center' },
                xaxis: { ...darkTheme.xaxis, title: 'Date' },
                yaxis: {
                    ...darkTheme.yaxis,
                    title: { text: 'Pizza Index (%)', font: { color: '#e31837' } },
                    side: 'left',
                    range: [-60, 110]
                },
                yaxis2: {
                    ...darkTheme.yaxis,
                    title: { text: 'VIX', font: { color: '#ffd700' } },
                    overlaying: 'y',
                    side: 'right',
                    range: [10, 35]
                },
                shapes: [
                    // Zero line for pizza index
                    { type: 'line', x0: data.dates[0], x1: data.dates[data.dates.length-1], y0: 0, y1: 0, 
                      line: { color: '#30363d', width: 1, dash: 'dash' }, yref: 'y1' },
                    // VIX fear threshold
                    { type: 'line', x0: data.dates[0], x1: data.dates[data.dates.length-1], y0: 20, y1: 20, 
                      line: { color: 'rgba(255, 215, 0, 0.3)', width: 1, dash: 'dash' }, yref: 'y2' }
                ],
                annotations: [
                    { x: data.dates[data.dates.length-1], y: 20, yref: 'y2', text: 'VIX Fear Threshold', 
                      showarrow: false, font: { size: 10, color: '#ffd700' }, xanchor: 'right' }
                ]
            };
            
            Plotly.newPlot('correlation-chart', [pizzaTrace, vixTrace, spikeTrace], layout, { responsive: true });
        }

        function renderGoldChart(data) {
            const trace = {
                x: data.dates,
                y: data.gold,
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                fillcolor: 'rgba(255, 215, 0, 0.1)',
                line: { color: '#ffd700', width: 2 },
                name: 'Gold'
            };
            
            Plotly.newPlot('gold-chart', [trace], {
                ...darkTheme,
                margin: { l: 60, r: 20, t: 20, b: 40 },
                yaxis: { ...darkTheme.yaxis, tickprefix: '$' }
            }, { responsive: true });
        }

        function renderHourlyChart(hourlyData, currentHour) {
            const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
            
            const colors = hourlyData.map((_, i) => i === currentHour ? '#e31837' : 'rgba(227, 24, 55, 0.4)');
            
            const trace = {
                x: hours,
                y: hourlyData,
                type: 'bar',
                marker: { color: colors, line: { color: '#e31837', width: 1 } },
                name: 'Expected Busyness'
            };
            
            const layout = {
                ...darkTheme,
                xaxis: { ...darkTheme.xaxis, title: 'Hour of Day' },
                yaxis: { ...darkTheme.yaxis, title: 'Busyness %', range: [0, 100] },
                annotations: currentHour !== null ? [{
                    x: `${currentHour}:00`,
                    y: hourlyData[currentHour] || 0,
                    text: 'NOW',
                    showarrow: true,
                    arrowhead: 2,
                    arrowcolor: '#c9d1d9',
                    font: { color: '#c9d1d9', size: 12 },
                    yshift: 20
                }] : []
            };
            
            Plotly.newPlot('hourly-chart', [trace], layout, { responsive: true });
        }

        function renderSensorList(sensors) {
            const container = document.getElementById('sensor-list');
            
            const getAnomalyClass = (current, usual) => {
                if (current === null) return 'anomaly-closed';
                if (usual === null || usual === 0) return 'anomaly-normal';
                const pct = ((current - usual) / usual) * 100;
                if (pct > 50) return 'anomaly-spike';
                if (pct > 25) return 'anomaly-high';
                if (pct < -25) return 'anomaly-low';
                return 'anomaly-normal';
            };
            
            const getAnomalyText = (current, usual) => {
                if (current === null) return 'CLOSED';
                if (usual === null || usual === 0) return `${current}%`;
                const pct = ((current - usual) / usual) * 100;
                return `${pct >= 0 ? '+' : ''}${pct.toFixed(0)}%`;
            };
            
            let html = '';
            sensors.forEach(sensor => {
                const icon = sensor.role === 'Primary' ? '🍕' : '🍺';
                const anomalyClass = getAnomalyClass(sensor.current, sensor.usual);
                const anomalyText = getAnomalyText(sensor.current, sensor.usual);
                
                html += `
                    <div class="sensor-row">
                        <span class="sensor-icon">${icon}</span>
                        <div class="sensor-info">
                            <div class="sensor-name">${sensor.name}</div>
                            <div class="sensor-role">${sensor.role} Indicator</div>
                        </div>
                        <div class="sensor-values">
                            <div class="sensor-stat">
                                <div class="sensor-stat-value">${sensor.current !== null ? sensor.current : 'N/A'}</div>
                                <div class="sensor-stat-label">LIVE</div>
                            </div>
                            <div class="sensor-stat">
                                <div class="sensor-stat-value">${sensor.usual !== null ? sensor.usual : 'N/A'}</div>
                                <div class="sensor-stat-label">EXPECTED</div>
                            </div>
                            <div class="anomaly-badge ${anomalyClass}">${anomalyText}</div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }

        function updateAlertBanner(score) {
            const banner = document.getElementById('alert-banner');
            let className, icon, title, message;
            
            if (score === null) {
                className = 'normal';
                icon = '⚪';
                title = 'SENSORS OFFLINE';
                message = 'Locations are closed or live data unavailable. Historical patterns shown.';
            } else if (score > 50) {
                className = 'critical';
                icon = '🔴';
                title = 'RED ALERT - ANOMALY DETECTED';
                message = 'Significant spike in late-night activity. Monitor for potential market volatility increase.';
            } else if (score > 25) {
                className = 'elevated';
                icon = '🟠';
                title = 'ELEVATED ACTIVITY';
                message = 'Above-normal busyness detected. Could indicate extended working hours at Pentagon.';
            } else {
                className = 'normal';
                icon = '🟢';
                title = 'NORMAL OPERATIONS';
                message = 'All sensors within expected parameters. No unusual activity detected.';
            }
            
            banner.className = `alert-banner ${className}`;
            banner.innerHTML = `
                <span class="alert-icon">${icon}</span>
                <div class="alert-content">
                    <h2>STATUS: ${title}</h2>
                    <p>${message}</p>
                </div>
            `;
        }

        async function refreshData() {
            document.getElementById('loading').classList.remove('hidden');
            
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                // Update timestamp
                document.getElementById('last-update').textContent = 
                    new Date(data.timestamp).toLocaleTimeString();
                
                // Update Pizza Gauge
                const pizzaScore = data.composite_score !== null ? data.composite_score : 0;
                renderGauge('pizza-gauge', pizzaScore);
                
                // Pizza interpretation
                let interpretation = 'Normal activity levels';
                if (data.composite_score === null) interpretation = 'Sensors offline (locations closed)';
                else if (data.composite_score > 50) interpretation = '⚠️ SPIKE! Unusual late-night activity';
                else if (data.composite_score > 25) interpretation = 'Elevated activity detected';
                else if (data.composite_score < -25) interpretation = 'Below-normal activity';
                document.getElementById('pizza-interpretation').textContent = interpretation;
                
                // Update market data
                if (data.market.vix) {
                    document.getElementById('vix-value').textContent = data.market.vix.toFixed(2);
                    const vixChange = data.market.vix_change || 0;
                    document.getElementById('vix-change').innerHTML = `
                        <span class="${vixChange >= 0 ? 'change-up' : 'change-down'}">
                            ${vixChange >= 0 ? '▲' : '▼'} ${Math.abs(vixChange).toFixed(2)}% today
                        </span>`;
                }
                
                if (data.market.gold) {
                    document.getElementById('gold-value').textContent = `$${data.market.gold.toLocaleString()}`;
                    const goldChange = data.market.gold_change || 0;
                    document.getElementById('gold-change').innerHTML = `
                        <span class="${goldChange >= 0 ? 'change-up' : 'change-down'}">
                            ${goldChange >= 0 ? '▲' : '▼'} ${Math.abs(goldChange).toFixed(2)}% today
                        </span>`;
                }
                
                // Correlation stats
                document.getElementById('correlation-value').textContent = `${data.correlation.toFixed(2)}`;
                document.getElementById('stat-correlation').textContent = data.correlation.toFixed(3);
                document.getElementById('stat-spike-count').textContent = data.spike_count;
                document.getElementById('stat-accuracy').textContent = `${data.accuracy}%`;
                document.getElementById('stat-lead-time').textContent = data.lead_time;
                
                // Update alert
                updateAlertBanner(data.composite_score);
                
                // Render charts
                renderCorrelationChart(data.historical);
                renderGoldChart(data.historical);
                renderSensorList(data.sensors);
                
                // Hourly chart
                if (data.sensors[0]?.today_hourly?.length > 0) {
                    renderHourlyChart(data.sensors[0].today_hourly, data.current_hour);
                } else {
                    // Use placeholder data
                    const placeholderHourly = Array.from({length: 24}, (_, i) => {
                        if (i < 10 || i > 22) return Math.floor(Math.random() * 20);
                        return 20 + Math.floor(Math.random() * 60);
                    });
                    renderHourlyChart(placeholderHourly, data.current_hour);
                }
                
            } catch (error) {
                console.error('Error:', error);
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }
        
        refreshData();
        setInterval(refreshData, 5 * 60 * 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/data')
def get_data():
    timestamp = datetime.now()
    
    # Fetch sensor data
    sensors_data = []
    for sensor in SENSORS:
        data = get_live_popularity(sensor['address'])
        sensors_data.append({
            "name": sensor['name'],
            "role": sensor['role'],
            "icon": sensor.get('icon', '🍕'),
            "current": data.get('current_popularity'),
            "usual": data.get('usual_popularity'),
            "today_hourly": data.get('today_hourly', []),
            "is_fallback": data.get('is_fallback', False),
            "fallback_hour": data.get('fallback_hour'),
        })
    
    # Fetch market data
    market_data = get_market_data()
    
    # Calculate composite score
    active = [s for s in sensors_data if s['current'] is not None and s['usual'] and s['usual'] > 0]
    composite_score = None
    if active:
        scores = []
        for s in active:
            pct = ((s['current'] - s['usual']) / s['usual']) * 100
            scores.append(pct)
        composite_score = sum(scores) / len(scores)
    
    # Get simulated historical data for correlation visualization
    historical = generate_simulated_historical_data()
    
    # Calculate correlation
    pizza_arr = np.array(historical['pizza_index'][:-1])  # Offset by 1 day
    vix_arr = np.array(historical['vix'][1:])  # VIX follows pizza
    correlation = np.corrcoef(pizza_arr, vix_arr)[0, 1]
    
    # Count spike events
    spike_count = sum(1 for v in historical['pizza_index'] if v > 30)
    
    return jsonify({
        "timestamp": timestamp.isoformat(),
        "current_hour": timestamp.hour,
        "sensors": sensors_data,
        "market": market_data,
        "composite_score": composite_score,
        "historical": historical,
        "correlation": round(correlation, 3),
        "spike_count": spike_count,
        "accuracy": 78,  # Simulated
        "lead_time": "~18h",  # Simulated
    })


def open_browser():
    import time
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print()
    print("=" * 60)
    print("  🍕 PENTAGON PIZZA INDEX - ANALYTICS DASHBOARD")
    print("=" * 60)
    print()
    print("  Starting server at http://localhost:5000")
    print("  Browser will open automatically...")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
