import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime
import joblib
import base64

from optimizer import recommend_for_project, evaluate_single_config, simulate_scenario
from config import (
    CHART_TEMPLATE, CHART_COLORS, BASELINE_CYCLE, BASELINE_MIX, 
    REGION_DATA, PRESET_SCENARIOS, PRIMARY_COLOR, SUCCESS_COLOR
)

# Professional page configuration
st.set_page_config(
    page_title="PrecastIQ - Concrete Production Optimization",
    layout="wide",
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_preset' not in st.session_state:
    st.session_state.current_preset = None
if 'run_simulation' not in st.session_state:
    st.session_state.run_simulation = False

# Professional CSS styling
st.markdown("""
<style>
    .professional-header {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .professional-header h1 {
        font-size: 2.5rem;
        font-weight: 300;
        margin-bottom: 0.5rem;
    }
    .professional-header h3 {
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 1rem;
        opacity: 0.9;
    }
    .professional-header p {
        font-size: 1rem;
        opacity: 0.8;
        margin: 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #3498db;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    .preset-button {
        background: #3498db;
        color: white;
        border: none;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
        width: 100%;
    }
    .preset-button:hover {
        background: #2980b9;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .stButton > button {
        background: #27ae60;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: #229954;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .stSelectbox > div > div {
        background: white;
        border-radius: 6px;
    }
    .stSlider > div > div > div {
        background: #3498db;
    }
    .section-header {
        color: #2c3e50;
        font-weight: 600;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Professional header
st.markdown("""
<div class="professional-header">
    <h1>PrecastIQ</h1>
    <h3>Advanced Concrete Production Optimization System</h3>
    <p>Data-driven recommendations for precast concrete manufacturing efficiency</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with professional styling
st.sidebar.markdown("### Project Configuration")
st.sidebar.markdown("---")

# Quick preset selection
st.sidebar.markdown("#### Configuration Presets")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Fast Track", help="Optimized for rapid production"):
        st.session_state.current_preset = "Fast Track"
        preset = PRESET_SCENARIOS["Fast Track"]
        st.session_state.preset_values = preset
with col2:
    if st.button("Cost Optimized", help="Optimized for budget efficiency"):
        st.session_state.current_preset = "Budget Optimized"
        preset = PRESET_SCENARIOS["Budget Optimized"]
        st.session_state.preset_values = preset

col3, col4 = st.sidebar.columns(2)
with col3:
    if st.button("High Performance", help="Maximum strength requirements"):
        st.session_state.current_preset = "High Strength"
        preset = PRESET_SCENARIOS["High Strength"]
        st.session_state.preset_values = preset
with col4:
    if st.button("Balanced", help="Optimized balance of parameters"):
        st.session_state.current_preset = "Balanced"
        preset = PRESET_SCENARIOS["Balanced"]
        st.session_state.preset_values = preset

# Show current preset if selected
if st.session_state.get('current_preset'):
    st.sidebar.success(f"Preset Applied: {st.session_state.current_preset}")

st.sidebar.markdown("---")

# Region selection
st.sidebar.markdown("#### Environmental Conditions")
region = st.sidebar.selectbox(
    "Climate Region",
    ["Custom"] + list(REGION_DATA.keys()),
    help="Environmental factors affecting curing and strength development",
    format_func=lambda x: f"{x} - {REGION_DATA.get(x, {}).get('description', '')}" if x != "Custom" else x
)

if region != "Custom":
    region_info = REGION_DATA[region]
    temperature, humidity = region_info["temp"], region_info["humidity"]
    st.sidebar.info(f"{region_info['description']}: {temperature}°C, {humidity}% humidity")
else:
    temperature = st.sidebar.slider("Ambient Temperature (°C)", 10, 45, 30)
    humidity = st.sidebar.slider("Relative Humidity (%)", 30, 95, 65)

# Project parameters
st.sidebar.markdown("#### Project Specifications")
project_type = st.sidebar.selectbox(
    "Project Type",
    ["Infrastructure", "Building"],
    help="Infrastructure projects require higher structural performance"
)

# Use preset values if available
if st.session_state.get('preset_values'):
    preset = st.session_state.preset_values
    st.sidebar.write(f"Active Preset: {preset}")
    
    target_strength = st.sidebar.slider("Target Compressive Strength (MPa)", 15, 45, preset["target_strength"])
    max_budget = st.sidebar.slider("Budget Constraint (₹/element)", 2000, 12000, preset["max_budget"])
    automation_level = st.sidebar.selectbox(
        "Automation Level",
        [1, 2, 3, 4],
        index=preset["automation"] - 1,
        help="1: Manual, 2: Semi-Automated, 3: Automated, 4: Fully Automated"
    )
    # Update the actual variables with preset values
    target_strength = preset["target_strength"]
    max_budget = preset["max_budget"]
    automation_level = preset["automation"]
else:
    target_strength = st.sidebar.slider("Target Compressive Strength (MPa)", 15, 45, 25)
    max_budget = st.sidebar.slider("Budget Constraint (₹/element)", 2000, 12000, 6000)
    automation_level = st.sidebar.selectbox(
        "Automation Level",
        [1, 2, 3, 4],
        help="1: Manual, 2: Semi-Automated, 3: Automated, 4: Fully Automated"
    )

# Main content area
st.markdown("---")

if st.button("Generate Optimization Recommendations", use_container_width=True):
    with st.spinner("Analyzing project parameters..."):
        try:
            results = recommend_for_project(
                temperature=temperature,
                humidity=humidity,
                project_type=project_type,
                target_strength=target_strength,
                max_budget=max_budget,
                automation_level=automation_level,
            )
            
            st.session_state.results = results
            st.session_state.analysis_complete = True
            
            st.success(f"Analysis Complete: {len(results)} optimal configurations identified")
            
        except Exception as e:
            st.error(f"Analysis Error: {str(e)}")
            import traceback
            st.write("Technical Details:", traceback.format_exc())

# Results section
if st.session_state.results is not None:
    results = st.session_state.results
    
    if len(results) == 0:
        st.warning("No feasible solutions found under current constraints. Consider adjusting project parameters.")
    else:
        df = pd.DataFrame(results)
        df = df.sort_values("score")
        best = df.iloc[0]
        
        # Executive Summary
        st.markdown("## Executive Summary")
        st.markdown("---")
        
        # Calculate key metrics
        cement_diff = best["cement_ratio"] - BASELINE_MIX["cement"]
        water_diff = best["water_ratio"] - BASELINE_MIX["water_ratio"]
        efficiency_gain = ((BASELINE_CYCLE - best["cycle_time"]) / BASELINE_CYCLE) * 100
        co2_estimate = best["cement_ratio"] * 0.9 * (1.5 if best["curing"] == "steam" else 1.0)
        
        # Key Performance Indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #2c3e50;">Production Cycle Time</h4>
                <h2 style="margin: 0.5rem 0; color: #27ae60;">{:.2f} days</h2>
                <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">{:.1f}% efficiency improvement</p>
            </div>
            """.format(best['cycle_time'], efficiency_gain), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #2c3e50;">Cost per Element</h4>
                <h2 style="margin: 0.5rem 0; color: #3498db;">₹{:.0f}</h2>
                <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Including materials and processing</p>
            </div>
            """.format(best['cost']), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #2c3e50;">Cement Content</h4>
                <h2 style="margin: 0.5rem 0; color: #e74c3c;">{:.0f} kg/m³</h2>
                <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">{:+.0f} kg/m³ vs baseline</p>
            </div>
            """.format(best['cement_ratio'], cement_diff), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #2c3e50;">Environmental Impact</h4>
                <h2 style="margin: 0.5rem 0; color: #16a085;">{:.1f} kg CO₂</h2>
                <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Estimated per element</p>
            </div>
            """.format(co2_estimate), unsafe_allow_html=True)
        
        # Detailed Recommendations
        st.markdown("## Recommended Configuration")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Mix Design Specifications")
            st.markdown(f"""
            **Material Composition:**
            - **Cement Content:** {best['cement_ratio']:.0f} kg/m³ ({cement_diff:+.0f} kg/m³ adjustment)
            - **Water-Cement Ratio:** {best['water_ratio']:.3f} ({water_diff:+.3f} vs standard 0.45)
            - **Automation Level:** Level {best['automation']}/4
            """)
        
        with col2:
            st.markdown("### Curing Strategy")
            curing_method = "Steam Curing" if best['curing'] == "steam" else "Ambient Curing"
            curing_benefit = "Accelerated strength development for reduced cycle time" if best["curing"] == "steam" else "Cost-effective curing for standard production cycles"
            st.markdown(f"""
            **Processing Method:**
            - **Curing Type:** {curing_method}
            - **Cycle Time:** {best['cycle_time']:.2f} days to target strength
            - **Benefits:** {curing_benefit}
            """)
        
        # Interactive analysis tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Solution Analysis", "Scenario Modeling", "Parameter Sensitivity", "Risk Assessment", "Detailed Results"])
        
        with tab1:
            st.markdown("### Solution Space Analysis")
            
            # Enhanced solution space visualization
            fig = go.Figure()
            
            # Add all solutions
            fig.add_trace(go.Scatter(
                x=df["cycle_time"],
                y=df["cost"],
                mode="markers",
                marker=dict(
                    size=df["score"] * 50,
                    color=df["cost"],
                    colorscale="Blues",
                    showscale=True,
                    colorbar=dict(title="Cost (₹)")
                ),
                text=[f"Cement: {row['cement_ratio']:.0f}<br>W/C: {row['water_ratio']:.3f}<br>Auto: {row['automation']}" 
                      for _, row in df.iterrows()],
                hovertemplate="<b>%{text}</b><br>Cycle: %{x:.2f} days<br>Cost: ₹%{y:.0f}<extra></extra>",
                name="Feasible Solutions"
            ))
            
            # Highlight optimal solution
            fig.add_trace(go.Scatter(
                x=[best["cycle_time"]],
                y=[best["cost"]],
                mode="markers",
                marker=dict(
                    symbol="diamond",
                    size=20,
                    color="red",
                    line=dict(width=2, color="darkred")
                ),
                text=["OPTIMAL SOLUTION"],
                hovertemplate="<b>%{text}</b><br>Cycle: %{x:.2f} days<br>Cost: ₹%{y:.0f}<extra></extra>",
                name="Recommended"
            ))
            
            fig.update_layout(
                title="Cost-Cycle Time Optimization Landscape",
                xaxis_title="Production Cycle Time (days)",
                yaxis_title="Cost per Element (₹)",
                template="plotly_white",
                height=500,
                hovermode="closest"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Top configurations table
            st.markdown("### Top 5 Optimal Configurations")
            top5 = df.head(5)
            display_df = top5[["cement_ratio", "water_ratio", "automation", "curing", "cycle_time", "cost", "score"]].copy()
            display_df.columns = ["Cement (kg/m³)", "W/C Ratio", "Automation", "Curing", "Cycle (days)", "Cost (₹)", "Optimization Score"]
            display_df = display_df.round({"Cement (kg/m³)": 0, "W/C Ratio": 3, "Cycle (days)": 2, "Cost (₹)": 0, "Optimization Score": 3})
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        with tab2:
            st.markdown("### Scenario Analysis")
            st.caption("Evaluate alternative production strategies")
            
            sim_col1, sim_col2, sim_col3 = st.columns([2, 1, 1])
            
            with sim_col1:
                scenario_type = st.selectbox(
                    "Select Scenario for Analysis:",
                    [
                        "Increase steam curing temperature by 5%",
                        "Increase steam curing temperature by 10%", 
                        "Increase steam curing temperature by 15%",
                        "Increase ambient temperature by 10%",
                        "Increase cement content by 10%",
                        "Increase humidity by 10%",
                    ],
                    key="scenario_select_professional",
                )
            
            with sim_col2:
                value_per_day = st.number_input(
                    "Daily Production Value (₹)",
                    min_value=100,
                    max_value=5000,
                    value=500,
                    step=50,
                    help="Economic value of one production day"
                )
            
            with sim_col3:
                if st.button("Run Analysis", type="secondary"):
                    st.session_state.run_simulation = True
            
            if st.session_state.get('run_simulation', False):
                # Parse scenario
                scenario_map = {
                    "Increase steam curing temperature by 5%": ("steam_temp", 5),
                    "Increase steam curing temperature by 10%": ("steam_temp", 10),
                    "Increase steam curing temperature by 15%": ("steam_temp", 15),
                    "Increase ambient temperature by 10%": ("ambient_temp", 10),
                    "Increase cement content by 10%": ("cement", 10),
                    "Increase humidity by 10%": ("humidity", 10),
                }
                stype, spct = scenario_map[scenario_type]
                
                if stype == "steam_temp" and best["curing"] == "normal":
                    st.warning("Steam temperature scenarios require steam curing methodology. Current recommendation uses ambient curing.")
                    sim_result = {"cycle_time": best["cycle_time"], "cost": best["cost"], "cycle_delta": 0, "cost_delta": 0}
                else:
                    with st.spinner("Running scenario analysis..."):
                        sim_result = simulate_scenario(best, stype, spct, temperature, humidity)
                
                # Store simulation result
                st.session_state.sim_result = sim_result
                
                # Results display
                st.markdown("### Scenario Analysis Results")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                
                with res_col1:
                    delta_color = "green" if sim_result['cycle_delta'] < 0 else "red"
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="margin: 0; color: #2c3e50;">Revised Cycle Time</h4>
                        <h2 style="margin: 0.5rem 0; color: {delta_color};">{sim_result['cycle_time']:.2f} days</h2>
                        <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">{sim_result['cycle_delta']:+.2f} days change</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with res_col2:
                    delta_color = "green" if sim_result['cost_delta'] <= 0 else "orange"
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="margin: 0; color: #2c3e50;">Cost Impact</h4>
                        <h2 style="margin: 0.5rem 0; color: {delta_color};">₹{sim_result['cost_delta']:+.0f}</h2>
                        <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Total: ₹{sim_result['cost']:.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with res_col3:
                    cycle_saved = best["cycle_time"] - sim_result["cycle_time"]
                    if cycle_saved > 0 and sim_result["cost_delta"] > 0 and value_per_day > 0:
                        roi_elements = sim_result["cost_delta"] / (cycle_saved * value_per_day)
                        roi_months = roi_elements / 120
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="margin: 0; color: #2c3e50;">Return on Investment</h4>
                            <h2 style="margin: 0.5rem 0; color: #3498db;">{roi_elements:.0f} units</h2>
                            <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">~{roi_months:.1f} months at 120 units/month</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif cycle_saved > 0 and sim_result["cost_delta"] <= 0:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="margin: 0; color: #2c3e50;">Return on Investment</h4>
                            <h2 style="margin: 0.5rem 0; color: #27ae60;">Immediate</h2>
                            <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Faster production, lower cost</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="margin: 0; color: #2c3e50;">Return on Investment</h4>
                            <h2 style="margin: 0.5rem 0; color: #95a5a6;">Not Viable</h2>
                            <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">No clear economic benefit</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        with tab3:
            st.markdown("### Parameter Sensitivity Analysis")
            
            # Temperature sensitivity
            temps = list(range(15, 46, 2))
            cycle_vs_temp = []
            for t in temps:
                ct, _ = evaluate_single_config(
                    best["cement_ratio"], best["water_ratio"], best["automation"],
                    best["curing"], t, humidity
                )
                cycle_vs_temp.append(ct)
            
            # Humidity sensitivity
            humidities = list(range(35, 96, 4))
            cycle_vs_hum = []
            for h in humidities:
                ct, _ = evaluate_single_config(
                    best["cement_ratio"], best["water_ratio"], best["automation"],
                    best["curing"], temperature, h
                )
                cycle_vs_hum.append(ct)
            
            sens_col1, sens_col2 = st.columns(2)
            
            with sens_col1:
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=temps, 
                    y=cycle_vs_temp, 
                    mode="lines+markers",
                    line=dict(color="#3498db", width=3), 
                    marker=dict(size=8),
                    name="Cycle Time",
                    hovertemplate="Temperature: %{x}°C<br>Cycle Time: %{y:.2f} days<extra></extra>"
                ))
                
                fig_temp.add_vline(
                    x=temperature, 
                    line_dash="dash", 
                    line_color="#e74c3c",
                    annotation_text=f"Current: {temperature}°C"
                )
                
                fig_temp.update_layout(
                    title="Temperature Sensitivity Analysis",
                    xaxis_title="Ambient Temperature (°C)",
                    yaxis_title="Production Cycle Time (days)",
                    template="plotly_white",
                    height=400,
                    margin=dict(t=50, b=50),
                )
                st.plotly_chart(fig_temp, use_container_width=True)
            
            with sens_col2:
                fig_hum = go.Figure()
                fig_hum.add_trace(go.Scatter(
                    x=humidities, 
                    y=cycle_vs_hum, 
                    mode="lines+markers",
                    line=dict(color="#2ecc71", width=3), 
                    marker=dict(size=8),
                    name="Cycle Time",
                    hovertemplate="Humidity: %{x}%<br>Cycle Time: %{y:.2f} days<extra></extra>"
                ))
                
                fig_hum.add_vline(
                    x=humidity, 
                    line_dash="dash", 
                    line_color="#e74c3c",
                    annotation_text=f"Current: {humidity}%"
                )
                
                fig_hum.update_layout(
                    title="Humidity Sensitivity Analysis",
                    xaxis_title="Relative Humidity (%)",
                    yaxis_title="Production Cycle Time (days)",
                    template="plotly_white",
                    height=400,
                    margin=dict(t=50, b=50),
                )
                st.plotly_chart(fig_hum, use_container_width=True)
            
            # Sensitivity insights
            temp_sens = (max(cycle_vs_temp) - min(cycle_vs_temp)) / (max(temps) - min(temps)) if max(temps) != min(temps) else 0
            hum_sens = (max(cycle_vs_hum) - min(cycle_vs_hum)) / (max(humidities) - min(humidities)) if max(humidities) != min(humidities) else 0
            stronger = "Temperature" if temp_sens > hum_sens else "Humidity"
            
            st.info(f"**Key Finding:** {stronger} demonstrates greater impact on production cycle time under current configuration")
        
        with tab4:
            st.markdown("### Production Risk Assessment")
            st.caption("Monte Carlo simulation for production variability analysis")
            
            with st.spinner("Running 500 production simulations..."):
                np.random.seed(42)
                sim_cycles = []
                
                for _ in range(500):
                    temp_noise = temperature + np.random.normal(0, 2)
                    hum_noise = humidity + np.random.normal(0, 5)
                    
                    ct, _ = evaluate_single_config(
                        best["cement_ratio"],
                        best["water_ratio"],
                        best["automation"],
                        best["curing"],
                        temp_noise,
                        hum_noise
                    )
                    sim_cycles.append(ct)
                
                sim_array = np.array(sim_cycles)
                mc_mean, mc_std = sim_array.mean(), sim_array.std()
                mc_p10, mc_p50, mc_p90 = np.percentile(sim_array, [10, 50, 90])
            
            # Risk metrics display
            risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)
            
            with risk_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #2c3e50;">Expected Cycle Time</h4>
                    <h2 style="margin: 0.5rem 0; color: #3498db;">{mc_mean:.2f} days</h2>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Mean projection</p>
                </div>
                """, unsafe_allow_html=True)
            
            with risk_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #2c3e50;">Variability Index</h4>
                    <h2 style="margin: 0.5rem 0; color: #e74c3c;">±{mc_std:.2f}</h2>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Standard deviation</p>
                </div>
                """, unsafe_allow_html=True)
            
            with risk_col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #2c3e50;">Confidence Range</h4>
                    <h2 style="margin: 0.5rem 0; color: #f39c12;">{mc_p10:.2f}-{mc_p90:.2f}</h2>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">80% probability range</p>
                </div>
                """, unsafe_allow_html=True)
            
            with risk_col4:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #2c3e50;">Most Likely Outcome</h4>
                    <h2 style="margin: 0.5rem 0; color: #27ae60;">{mc_p50:.2f} days</h2>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Median projection</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Distribution visualization
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Histogram(
                x=sim_cycles, 
                nbinsx=30, 
                name="Cycle Time Distribution",
                marker_color="#3498db", 
                opacity=0.8
            ))
            fig_mc.add_vline(
                x=mc_mean, 
                line_dash="dash", 
                line_color="#27ae60", 
                annotation_text=f"Mean: {mc_mean:.2f}"
            )
            fig_mc.add_vline(
                x=best["cycle_time"], 
                line_dash="dot", 
                line_color="#e74c3c", 
                annotation_text="Baseline"
            )
            
            fig_mc.update_layout(
                title="Production Cycle Time Distribution (500 simulations with ±2°C temperature, ±5% humidity variations)",
                xaxis_title="Cycle Time (days)",
                yaxis_title="Frequency",
                template="plotly_white",
                height=450,
                showlegend=False
            )
            
            st.plotly_chart(fig_mc, use_container_width=True)
        
        with tab5:
            st.markdown("### Comprehensive Analysis Results")
            
            # Strategy comparison if available
            if len(df) > 1:
                st.markdown("#### Optimal vs Alternative Configuration Comparison")
                compare_option = df.iloc[1]
                
                comp_col1, comp_col2 = st.columns(2)
                
                with comp_col1:
                    comp_data = pd.DataFrame({
                        "Performance Metric": ["Cycle Time (days)", "Cost (₹)", "Cement (kg/m³)", "Automation Level"],
                        "Optimal Configuration": [round(best["cycle_time"], 2), round(best["cost"], 0), round(best["cement_ratio"], 0), best["automation"]],
                        "Alternative Configuration": [round(compare_option["cycle_time"], 2), round(compare_option["cost"], 0), round(compare_option["cement_ratio"], 0), compare_option["automation"]],
                    })
                    st.dataframe(comp_data, use_container_width=True, hide_index=True)
                
                with comp_col2:
                    fig_comp = go.Figure()
                    fig_comp.add_trace(go.Bar(
                        x=["Optimal", "Alternative"], 
                        y=[best["cycle_time"], compare_option["cycle_time"]],
                        marker_color=["#27ae60", "#3498db"],
                        text=[f"{best['cycle_time']:.2f} days", f"{compare_option['cycle_time']:.2f} days"], 
                        textposition="auto"
                    ))
                    fig_comp.update_layout(
                        title="Cycle Time Comparison",
                        template="plotly_white",
                        height=350,
                        xaxis_title="Configuration",
                        yaxis_title="Days",
                        showlegend=False
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
            
            # Export functionality
            st.markdown("#### Export Analysis Results")
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                # Create CSV for download
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="precastiq_analysis_results.csv" style="text-decoration: none; color: #3498db; font-weight: 600;">📊 Download Analysis Data (CSV)</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with col_export2:
                if st.button("Generate Executive Report"):
                    st.markdown("#### Executive Summary Report")
                    st.markdown(f"""
                    **Project Analysis Report**
                    
                    **Project Parameters:**
                    - Type: {project_type}
                    - Region: {region}
                    - Target Strength: {target_strength} MPa
                    - Budget Constraint: ₹{max_budget}/element
                    - Automation Level: {automation_level}/4
                    
                    **Recommended Configuration:**
                    - Production Cycle Time: {best['cycle_time']:.2f} days ({efficiency_gain:.1f}% improvement)
                    - Unit Cost: ₹{best['cost']:.0f} per element
                    - Mix Design: {best['cement_ratio']:.0f} kg/m³ cement, {best['water_ratio']:.3f} water-cement ratio
                    - Curing Method: {best['curing'].capitalize()}
                    - Automation: Level {best['automation']}/4
                    
                    **Performance Benefits:**
                    - {efficiency_gain:.1f}% reduction in production cycle time
                    - Environmental Impact: {co2_estimate:.1f} kg CO₂ per element
                    - Analysis Scope: {len(df)} feasible configurations evaluated
                    
                    **Risk Assessment:**
                    - Expected cycle time: {mc_mean:.2f} days (±{mc_std:.2f})
                    - 80% confidence interval: {mc_p10:.2f} - {mc_p90:.2f} days
                    
                    **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """)

# Professional footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 2rem; border-top: 1px solid #ecf0f1;'>
    <p><strong>PrecastIQ</strong> - Advanced Concrete Production Optimization</p>
    <p style='font-size: 0.9rem;'>© 2024 | Enterprise Manufacturing Intelligence Platform</p>
</div>
""", unsafe_allow_html=True)
