import plotly.express as px

# Configuration constants for PrecastIQ
CHART_TEMPLATE = "plotly_white"
CHART_COLORS = px.colors.qualitative.Set2
BASELINE_CYCLE = 5
BASELINE_MIX = {"cement": 400, "water_ratio": 0.45}

# Region climate data
REGION_DATA = {
    "Chennai": {"temp": 34, "humidity": 75, "description": "Hot & Humid"},
    "Mumbai": {"temp": 32, "humidity": 80, "description": "Coastal Humid"},
    "Delhi": {"temp": 38, "humidity": 50, "description": "Hot & Dry"},
    "Ahmedabad": {"temp": 40, "humidity": 45, "description": "Very Hot & Dry"},
}

# Preset scenarios for quick actions
PRESET_SCENARIOS = {
    "Fast Track": {"target_strength": 30, "max_budget": 8000, "automation": 4},
    "Budget Optimized": {"target_strength": 25, "max_budget": 4000, "automation": 2},
    "High Strength": {"target_strength": 40, "max_budget": 10000, "automation": 3},
    "Balanced": {"target_strength": 28, "max_budget": 6000, "automation": 3},
}

# UI Colors
PRIMARY_COLOR = "#1f77b4"
SECONDARY_COLOR = "#ff7f0e"
SUCCESS_COLOR = "#2ca02c"
WARNING_COLOR = "#ff7f0e"
ERROR_COLOR = "#d62728"
