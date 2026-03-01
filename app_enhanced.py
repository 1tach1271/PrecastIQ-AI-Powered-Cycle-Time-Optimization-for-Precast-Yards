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
from ui_components import (
    create_metric_card, create_comparison_chart, create_sensitivity_chart,
    create_solution_space_chart, show_loading_animation, create_info_alert
)

# Page configuration
st.set_page_config(
    page_title="PrecastIQ - AI Strategy Recommender",
    layout="wide",
    page_icon="🏗️",
    initial_sidebar_state="expanded"
)

# Initialize session state FIRST
if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_preset' not in st.session_state:
    st.session_state.current_preset = None
if 'run_simulation' not in st.session_state:
    st.session_state.run_simulation = False

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .preset-button {
        background: linear-gradient(45deg, #1f77b4, #17a2b8);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .preset-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🏗️ PrecastIQ</h1>
    <h3>AI-Driven Mix Design & Curing Strategy Recommendations</h3>
    <p>Optimize your precast concrete production with intelligent recommendations</p>
</div>
""", unsafe_allow_html=True)

# Main content area with enhanced UI
st.sidebar.header("📊 Project Configuration")

# Quick preset selection
st.sidebar.subheader("⚡ Quick Start")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🚀 Fast Track", help="Optimized for speed"):
        st.session_state.current_preset = "Fast Track"
        preset = PRESET_SCENARIOS["Fast Track"]
        st.session_state.preset_values = preset
with col2:
    if st.button("💰 Budget", help="Optimized for cost"):
        st.session_state.current_preset = "Budget Optimized"
        preset = PRESET_SCENARIOS["Budget Optimized"]
        st.session_state.preset_values = preset

col3, col4 = st.sidebar.columns(2)
with col3:
    if st.button("💪 High Strength", help="Maximum strength"):
        st.session_state.current_preset = "High Strength"
        preset = PRESET_SCENARIOS["High Strength"]
        st.session_state.preset_values = preset
with col4:
    if st.button("⚖️ Balanced", help="Balanced approach"):
        st.session_state.current_preset = "Balanced"
        preset = PRESET_SCENARIOS["Balanced"]
        st.session_state.preset_values = preset

# Show current preset if selected
if st.session_state.get('current_preset'):
    create_info_alert(f"📋 Preset Applied: {st.session_state.current_preset}", "success")

st.sidebar.divider()

# Region selection with enhanced info
st.sidebar.subheader("🌍 Environmental Conditions")
region = st.sidebar.selectbox(
    "Region",
    ["Custom"] + list(REGION_DATA.keys()),
    help="Climate affects curing and strength gain",
    format_func=lambda x: f"{x} - {REGION_DATA.get(x, {}).get('description', '')}" if x != "Custom" else x
)

if region != "Custom":
    region_info = REGION_DATA[region]
    temperature, humidity = region_info["temp"], region_info["humidity"]
    st.sidebar.markdown(f"*{region_info['description']}*: {temperature}°C, {humidity}% humidity")
else:
    temperature = st.sidebar.slider("Temperature (°C)", 10, 45, 30)
    humidity = st.sidebar.slider("Humidity (%)", 30, 95, 65)

# Project parameters
st.sidebar.subheader("🏗️ Project Requirements")
project_type = st.sidebar.selectbox(
    "Project Type",
    ["Infra", "Building"],
    help="Infrastructure projects typically require higher strength"
)

# Use preset values if available
if st.session_state.get('preset_values'):
    preset = st.session_state.preset_values
    st.sidebar.write(f"🔍 Debug: Preset = {preset}")
    
    target_strength = st.sidebar.slider("Target Strength (MPa)", 15, 45, preset["target_strength"])
    max_budget = st.sidebar.slider("Budget Constraint (₹)", 2000, 12000, preset["max_budget"])
    automation_level = st.sidebar.selectbox(
        "Automation Level",
        [1, 2, 3, 4],
        index=preset["automation"] - 1,
        help="1=Manual, 4=Full automation"
    )
    # Update the actual variables with preset values
    target_strength = preset["target_strength"]
    max_budget = preset["max_budget"]
    automation_level = preset["automation"]
    
    st.sidebar.write(f"🔍 Debug: Variables after preset - Strength: {target_strength}, Budget: {max_budget}, Auto: {automation_level}")
else:
    target_strength = st.sidebar.slider("Target Strength (MPa)", 15, 45, 25)
    max_budget = st.sidebar.slider("Budget Constraint (₹)", 2000, 12000, 6000)
    automation_level = st.sidebar.selectbox(
        "Automation Level",
        [1, 2, 3, 4],
        help="1=Manual, 4=Full automation"
    )
    st.sidebar.write(f"🔍 Debug: Variables (default) - Strength: {target_strength}, Budget: {max_budget}, Auto: {automation_level}")

# Main content area
if st.button("🎯 Get AI Recommendations", type="primary", use_container_width=True):
    st.write("🔍 Debug: Button clicked!")
    
    with st.spinner("AI is analyzing your requirements..."):
        try:
            st.write("🔍 Debug: Calling recommend_for_project...")
            results = recommend_for_project(
                temperature=temperature,
                humidity=humidity,
                project_type=project_type,
                target_strength=target_strength,
                max_budget=max_budget,
                automation_level=automation_level,
            )
            
            st.write("🔍 Debug: Got results:", len(results) if results else "None")
            st.session_state.results = results
            st.session_state.analysis_complete = True
            
            st.success(f"✅ Found {len(results)} solutions!")
            # Remove st.rerun() to prevent infinite loop
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.write("Traceback:", traceback.format_exc())

# Results section
if st.session_state.results is not None:
    results = st.session_state.results
    
    if len(results) == 0:
        create_info_alert("❌ No feasible solutions found under given constraints. Try adjusting your parameters.", "error")
    else:
        df = pd.DataFrame(results)
        df = df.sort_values("score")
        best = df.iloc[0]
        
        # Success message
        create_info_alert(f"✅ Found {len(df)} optimal configurations for your project!", "success")
        
        # Key Metrics Dashboard
        st.header("📈 Key Performance Indicators")
        
        # Calculate metrics
        cement_diff = best["cement_ratio"] - BASELINE_MIX["cement"]
        water_diff = best["water_ratio"] - BASELINE_MIX["water_ratio"]
        efficiency_gain = ((BASELINE_CYCLE - best["cycle_time"]) / BASELINE_CYCLE) * 100
        co2_estimate = best["cement_ratio"] * 0.9 * (1.5 if best["curing"] == "steam" else 1.0)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card(
                "⏱️ Cycle Time",
                f"{best['cycle_time']:.2f} days",
                f"-{efficiency_gain:.1f}% vs baseline",
                color="success"
            )
        
        with col2:
            create_metric_card(
                "💰 Cost per Element",
                f"₹{best['cost']:.0f}",
                help_text="Including materials, curing, and automation"
            )
        
        with col3:
            create_metric_card(
                "🏗️ Cement Content",
                f"{best['cement_ratio']:.0f} kg/m³",
                f"{cement_diff:+.0f} vs baseline"
            )
        
        with col4:
            create_metric_card(
                "🌱 CO₂ Impact",
                f"{co2_estimate:.1f} kg",
                help_text="Estimated CO₂ per element"
            )
        
        # Detailed Recommendations
        st.header("🎯 Recommended Strategy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🧪 Mix Design")
            st.markdown(f"""
            - **Cement:** {best['cement_ratio']:.0f} kg/m³ ({cement_diff:+.0f} vs baseline)
            - **Water-Cement Ratio:** {best['water_ratio']:.3f} ({water_diff:+.3f} vs 0.45)
            - **Automation Level:** {best['automation']}/4
            """)
        
        with col2:
            st.markdown("### 🌡️ Curing Strategy")
            curing_type = best['curing'].capitalize()
            curing_desc = "Steam curing for accelerated strength gain" if best["curing"] == "steam" else "Ambient curing for cost efficiency"
            st.markdown(f"""
            - **Method:** {curing_type} Curing
            - **Description:** {curing_desc}
            - **Cycle Time:** {best['cycle_time']:.2f} days to target strength
            """)
        
        # Interactive tabs for different analyses
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Solution Space", "🔬 Scenario Simulator", "📈 Sensitivity Analysis", "🎲 Risk Assessment", "📋 Detailed Results"])
        
        with tab1:
            st.subheader("Solution Space Exploration")
            fig = create_solution_space_chart(df, best)
            st.plotly_chart(fig, use_container_width=True)
            
            # Top solutions table
            st.subheader("🏆 Top 5 Configurations")
            top5 = df.head(5)
            display_df = top5[["cement_ratio", "water_ratio", "automation", "curing", "cycle_time", "cost", "score"]].copy()
            display_df.columns = ["Cement (kg/m³)", "W/C Ratio", "Automation", "Curing", "Cycle (days)", "Cost (₹)", "Score"]
            display_df = display_df.round({"Cement (kg/m³)": 0, "W/C Ratio": 3, "Cycle (days)": 2, "Cost (₹)": 0, "Score": 2})
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        with tab2:
            st.subheader("🔬 What-If Scenario Simulator")
            st.caption("Test different scenarios to support investment decisions")
            
            sim_col1, sim_col2, sim_col3 = st.columns([2, 1, 1])
            
            with sim_col1:
                scenario_type = st.selectbox(
                    "Select Scenario:",
                    [
                        "🔥 Increase steam curing temperature by 5%",
                        "🔥 Increase steam curing temperature by 10%", 
                        "🔥 Increase steam curing temperature by 15%",
                        "🌡️ Increase ambient temperature by 10%",
                        "🏗️ Increase cement content by 10%",
                        "💧 Increase humidity by 10%",
                    ],
                    key="scenario_select_enhanced",
                )
            
            with sim_col2:
                value_per_day = st.number_input(
                    "Value of 1 day saved (₹)",
                    min_value=100,
                    max_value=5000,
                    value=500,
                    step=50,
                    help="For ROI: revenue/margin per element-day"
                )
            
            with sim_col3:
                if st.button("🚀 Run Simulation", type="secondary"):
                    st.session_state.run_simulation = True
            
            if st.session_state.get('run_simulation', False):
                # Parse scenario
                scenario_map = {
                    "🔥 Increase steam curing temperature by 5%": ("steam_temp", 5),
                    "🔥 Increase steam curing temperature by 10%": ("steam_temp", 10),
                    "🔥 Increase steam curing temperature by 15%": ("steam_temp", 15),
                    "🌡️ Increase ambient temperature by 10%": ("ambient_temp", 10),
                    "🏗️ Increase cement content by 10%": ("cement", 10),
                    "💧 Increase humidity by 10%": ("humidity", 10),
                }
                stype, spct = scenario_map[scenario_type]
                
                if stype == "steam_temp" and best["curing"] == "normal":
                    create_info_alert("Steam curing scenarios apply only when using steam. Your recommendation uses normal curing.", "warning")
                    sim_result = {"cycle_time": best["cycle_time"], "cost": best["cost"], "cycle_delta": 0, "cost_delta": 0}
                else:
                    with st.spinner("Running simulation..."):
                        sim_result = simulate_scenario(best, stype, spct, temperature, humidity)
                
                # Store simulation result in session state
                st.session_state.sim_result = sim_result
                
                # Results
                st.markdown("### 📊 Simulation Results")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                
                with res_col1:
                    delta_color = "success" if sim_result['cycle_delta'] < 0 else "error"
                    create_metric_card(
                        "New Cycle Time",
                        f"{sim_result['cycle_time']:.2f} days",
                        f"{sim_result['cycle_delta']:+.2f} days",
                        color=delta_color
                    )
                
                with res_col2:
                    delta_color = "success" if sim_result['cost_delta'] <= 0 else "warning"
                    create_metric_card(
                        "Cost Impact",
                        f"₹{sim_result['cost_delta']:+.0f}",
                        f"Total: ₹{sim_result['cost']:.0f}",
                        color=delta_color
                    )
                
                with res_col3:
                    cycle_saved = best["cycle_time"] - sim_result["cycle_time"]
                    if cycle_saved > 0 and sim_result["cost_delta"] > 0 and value_per_day > 0:
                        roi_elements = sim_result["cost_delta"] / (cycle_saved * value_per_day)
                        roi_months = roi_elements / 120
                        create_metric_card(
                            "ROI Period",
                            f"{roi_elements:.0f} elements",
                            f"~{max(0.1, roi_months):.1f} months"
                        )
                    elif cycle_saved > 0 and sim_result["cost_delta"] <= 0:
                        create_metric_card("ROI Period", "Immediate", "Faster & Cheaper", "success")
                    else:
                        create_metric_card("ROI Period", "—", "No clear benefit")
        
        # ROI recalculation when value_per_day changes (if simulation results exist)
        if 'sim_result' in st.session_state:
            sim_result = st.session_state.sim_result
            st.markdown("### 💰 ROI Calculator")
            st.caption("Adjust the value per day to see how it affects ROI")
            
            roi_col1, roi_col2, roi_col3 = st.columns(3)
            
            with roi_col1:
                st.metric("Value per Day", f"₹{value_per_day}")
            
            with roi_col2:
                cycle_saved = best["cycle_time"] - sim_result["cycle_time"]
                if cycle_saved > 0:
                    daily_value = cycle_saved * value_per_day
                    st.metric("Daily Value Created", f"₹{daily_value:.0f}")
                else:
                    st.metric("Daily Value Created", "₹0", "No time saved")
            
            with roi_col3:
                if cycle_saved > 0 and sim_result["cost_delta"] > 0 and value_per_day > 0:
                    roi_elements = sim_result["cost_delta"] / (cycle_saved * value_per_day)
                    roi_months = roi_elements / 120
                    st.metric("ROI Period", f"{roi_elements:.0f} elements", f"~{roi_months:.1f} months")
                elif cycle_saved > 0 and sim_result["cost_delta"] <= 0:
                    st.metric("ROI Period", "Immediate", "Faster & Cheaper")
                else:
                    st.metric("ROI Period", "—", "No benefit")
        
        with tab3:
            st.subheader("📈 Sensitivity Analysis")
            
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
                fig_temp = create_sensitivity_chart(temps, cycle_vs_temp, temperature, "🌡️ Temperature Impact")
                st.plotly_chart(fig_temp, use_container_width=True)
            
            with sens_col2:
                fig_hum = create_sensitivity_chart(humidities, cycle_vs_hum, humidity, "💧 Humidity Impact")
                st.plotly_chart(fig_hum, use_container_width=True)
            
            # Sensitivity insights
            temp_sens = (max(cycle_vs_temp) - min(cycle_vs_temp)) / (max(temps) - min(temps)) if max(temps) != min(temps) else 0
            hum_sens = (max(cycle_vs_hum) - min(cycle_vs_hum)) / (max(humidities) - min(humidities)) if max(humidities) != min(humidities) else 0
            stronger = "Temperature" if temp_sens > hum_sens else "Humidity"
            
            create_info_alert(f"🔍 **Key Insight:** {stronger} has a stronger impact on cycle time under current configuration", "info")
        
        with tab4:
            st.subheader("🎲 Monte Carlo Risk Assessment")
            
            with st.spinner("Running 500 simulations..."):
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
            
            # Risk metrics
            risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)
            
            with risk_col1:
                create_metric_card("Mean", f"{mc_mean:.2f} days", "Average outcome")
            with risk_col2:
                create_metric_card("Std Dev", f"{mc_std:.2f}", "Variability")
            with risk_col3:
                create_metric_card("P10–P90", f"{mc_p10:.2f}–{mc_p90:.2f}", "80% range")
            with risk_col4:
                create_metric_card("Median", f"{mc_p50:.2f} days", "Typical outcome")
            
            # Distribution chart
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Histogram(
                x=sim_cycles, 
                nbinsx=30, 
                name="Cycle Time Distribution",
                marker_color=CHART_COLORS[0], 
                opacity=0.8
            ))
            fig_mc.add_vline(
                x=mc_mean, 
                line_dash="dash", 
                line_color="green", 
                annotation_text=f"Mean: {mc_mean:.2f}"
            )
            fig_mc.add_vline(
                x=best["cycle_time"], 
                line_dash="dot", 
                line_color="orange", 
                annotation_text="Baseline"
            )
            
            fig_mc.update_layout(
                title="Cycle Time Distribution (500 simulations with ±2°C temp, ±5% humidity)",
                xaxis_title="Cycle Time (days)",
                yaxis_title="Frequency",
                template=CHART_TEMPLATE,
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_mc, use_container_width=True)
        
        with tab5:
            st.subheader("📋 Detailed Analysis Results")
            
            # Strategy comparison if available
            if len(df) > 1:
                st.markdown("### 🏆 Best vs Second Best Comparison")
                compare_option = df.iloc[1]
                
                comp_col1, comp_col2 = st.columns(2)
                
                with comp_col1:
                    comp_data = pd.DataFrame({
                        "Metric": ["Cycle Time (days)", "Cost (₹)", "Cement (kg/m³)", "Automation"],
                        "Best": [round(best["cycle_time"], 2), round(best["cost"], 0), round(best["cement_ratio"], 0), best["automation"]],
                        "Second Best": [round(compare_option["cycle_time"], 2), round(compare_option["cost"], 0), round(compare_option["cement_ratio"], 0), compare_option["automation"]],
                    })
                    st.dataframe(comp_data, use_container_width=True, hide_index=True)
                
                with comp_col2:
                    fig_comp = create_comparison_chart(best, compare_option)
                    st.plotly_chart(fig_comp, use_container_width=True)
            
            # Export functionality
            st.markdown("### 📤 Export Results")
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                # Create CSV for download
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="precastiq_results.csv">📊 Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with col_export2:
                # Summary report
                if st.button("📄 Generate Summary Report"):
                    st.markdown("### 📋 Executive Summary")
                    st.markdown(f"""
                    **Project:** {project_type} | **Region:** {region}
                    
                    **Recommended Configuration:**
                    - Cycle Time: {best['cycle_time']:.2f} days ({efficiency_gain:.1f}% improvement)
                    - Cost: ₹{best['cost']:.0f} per element
                    - Mix Design: {best['cement_ratio']:.0f} kg/m³ cement, {best['water_ratio']:.3f} w/c ratio
                    - Curing: {best['curing'].capitalize()} method
                    - Automation: Level {best['automation']}/4
                    
                    **Key Benefits:**
                    - {efficiency_gain:.1f}% faster cycle time vs baseline
                    - CO₂ impact: {co2_estimate:.1f} kg per element
                    - {len(df)} feasible configurations analyzed
                    
                    **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏗️ PrecastIQ - AI-Powered Precast Concrete Optimization</p>
    <p>© 2024 | Built with Streamlit & Machine Learning</p>
</div>
""", unsafe_allow_html=True)
