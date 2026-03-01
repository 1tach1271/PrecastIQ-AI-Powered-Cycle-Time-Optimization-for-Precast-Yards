import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from optimizer import recommend_for_project, evaluate_single_config, simulate_scenario

# Chart theme
CHART_TEMPLATE = "plotly_white"
CHART_COLORS = px.colors.qualitative.Set2
BASELINE_CYCLE = 5
BASELINE_MIX = {"cement": 400, "water_ratio": 0.45}

st.set_page_config(page_title="AI Strategy Recommender", layout="wide")

st.title("AI Strategy Recommender Dashboard")
st.markdown("*PrecastIQ — AI-Driven Mix Design & Curing Strategy Recommendations*")

st.sidebar.header("Input")

region = st.sidebar.selectbox(
    "Region",
    ["Custom", "Chennai", "Mumbai", "Delhi", "Ahmedabad"],
    help="Climate affects curing and strength gain",
)
region_data = {
    "Chennai": (34, 75),
    "Mumbai": (32, 80),
    "Delhi": (38, 50),
    "Ahmedabad": (40, 45),
}
if region != "Custom":
    temperature, humidity = region_data[region]
else:
    temperature = st.sidebar.slider("Temperature (°C)", 10, 45, 30)
    humidity = st.sidebar.slider("Humidity (%)", 30, 95, 65)

project_type = st.sidebar.selectbox(
    "Project Type",
    ["Infra", "Building"],
    help="Infra typically requires higher strength",
)
target_strength = st.sidebar.slider("Target Strength (MPa)", 15, 45, 25)
max_budget = st.sidebar.slider("Budget Constraint (₹)", 2000, 12000, 6000)
automation_level = st.sidebar.selectbox(
    "Automation Level",
    [1, 2, 3, 4],
    help="1=manual, 4=full automation",
)

# Store results in session state to persist across interactions
if 'results' not in st.session_state:
    st.session_state.results = None

if st.button("Get Recommendation"):
    st.session_state.results = recommend_for_project(
        temperature=temperature,
        humidity=humidity,
        project_type=project_type,
        target_strength=target_strength,
        max_budget=max_budget,
        automation_level=automation_level,
    )

# Display results if they exist
if st.session_state.results is not None:
    results = st.session_state.results
    
    if len(results) == 0:
        st.error("No feasible solutions under given constraints.")
    else:
        df = pd.DataFrame(results)
        df = df.sort_values("score")
        best = df.iloc[0]

        # ——— Output Section ———
        st.header("Output")

        # Mix design tweak
        cement_diff = best["cement_ratio"] - BASELINE_MIX["cement"]
        water_diff = best["water_ratio"] - BASELINE_MIX["water_ratio"]
        cement_tweak = f"+{cement_diff:.0f} kg/m³" if cement_diff >= 0 else f"{cement_diff:.0f} kg/m³"
        water_tweak = f"+{water_diff:.2f}" if water_diff >= 0 else f"{water_diff:.2f}"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Recommended Mix Design Tweak")
            st.markdown(
                f"- **Cement:** {best['cement_ratio']:.0f} kg/m³ ({cement_tweak} vs baseline 400)\n"
                f"- **Water–Cement Ratio:** {best['water_ratio']:.2f} ({water_tweak} vs 0.45)"
            )
        with col2:
            st.subheader("Curing Strategy")
            st.markdown(
                f"**{best['curing'].capitalize()} Curing** — "
                + ("Steam accelerates strength gain for faster demoulding." if best["curing"] == "steam" else "Ambient curing — lower cost, suitable for longer schedules.")
            )
        with col3:
            st.subheader("Predicted Cycle Time")
            st.metric("Cycle Time", f"{best['cycle_time']:.2f} days", help="Estimated time to target strength")

        st.divider()

        # Cost, efficiency, CO2
        efficiency_gain = ((BASELINE_CYCLE - best["cycle_time"]) / BASELINE_CYCLE) * 100
        co2_estimate = best["cement_ratio"] * 0.9 * (1.5 if best["curing"] == "steam" else 1.0)

        out1, out2, out3 = st.columns(3)
        out1.metric("Cost Implication", f"₹{best['cost']:.0f}", "per element")
        out2.metric("Efficiency Gain", f"{efficiency_gain:.1f}%", f"vs {BASELINE_CYCLE} day baseline")
        out3.metric("CO₂ Impact", f"{co2_estimate:.1f} kg", "per element (optional)")

        st.divider()

        # ——— Scenario Simulator (decision-support) ———
        st.subheader("Scenario Simulator")
        st.caption("*Test what-if scenarios to support investment decisions.*")

        sim_col1, sim_col2 = st.columns([2, 1])
        with sim_col1:
            scenario_type = st.selectbox(
                "What if we…",
                [
                    "Increase steam curing temperature by 5%",
                    "Increase steam curing temperature by 10%",
                    "Increase steam curing temperature by 15%",
                    "Increase ambient temperature by 10%",
                    "Increase cement content by 10%",
                    "Increase humidity by 10%",
                ],
                key="scenario_select",
            )
        with sim_col2:
            value_per_day = st.number_input(
                "Value of 1 day saved (₹)",
                min_value=100,
                max_value=2000,
                value=500,
                step=50,
                help="For ROI: revenue/margin per element-day",
            )

        # Add button to run simulation
        if st.button("Run Scenario Simulation", key="run_sim"):
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
                st.info("Steam curing scenarios apply only when using steam. Your recommendation uses normal curing.")
                sim_result = {"cycle_time": best["cycle_time"], "cost": best["cost"], "cycle_delta": 0, "cost_delta": 0}
            else:
                sim_result = simulate_scenario(best, stype, spct, temperature, humidity)

            # Output: new cycle time, cost delta, ROI
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric(
                    "New Cycle Time",
                    f"{sim_result['cycle_time']:.2f} days",
                    f"{sim_result['cycle_delta']:+.2f} vs baseline",
                )
            with s2:
                st.metric(
                    "Cost Delta",
                    f"₹{sim_result['cost_delta']:+.0f}",
                    f"Total: ₹{sim_result['cost']:.0f}",
                )
            with s3:
                cycle_saved = best["cycle_time"] - sim_result["cycle_time"]
                if cycle_saved > 0 and sim_result["cost_delta"] > 0:
                    if value_per_day > 0:
                        roi_elements = sim_result["cost_delta"] / (cycle_saved * value_per_day)
                        roi_months = roi_elements / 120  # ~120 elements/month for typical yard
                        st.metric(
                            "ROI Period",
                            f"{roi_elements:.0f} elements",
                            f"~{max(0.1, roi_months):.1f} months at 120/mo",
                        )
                    else:
                        st.metric("ROI Period", "—", "Value per day set to 0")
                elif cycle_saved > 0 and sim_result["cost_delta"] <= 0:
                    st.metric("ROI Period", "Immediate", "Faster & cheaper")
                elif cycle_saved <= 0 and sim_result["cost_delta"] > 0:
                    st.metric("ROI Period", "—", "Slower & costlier")
                else:
                    st.metric("ROI Period", "—", "No cycle gain")
        else:
            # Show initial state when button hasn't been clicked
            st.info("Select a scenario and click 'Run Scenario Simulation' to see results.")

        st.divider()

        # Supporting analysis
        st.subheader("Solution Space Exploration")

        df_plot = df.copy()

        fig = px.scatter(
            df_plot,
            x="cycle_time",
            y="cost",
            color="curing",
            hover_data=["cement_ratio", "water_ratio", "score"],
            template=CHART_TEMPLATE,
            color_discrete_sequence=CHART_COLORS,
            title="Cost vs Cycle Time Tradeoff",
        )

        # Highlight best point with larger marker
        best_trace = go.Scatter(
            x=[best["cycle_time"]],
            y=[best["cost"]],
            mode="markers+text",
            marker=dict(symbol="star", size=24, color="gold", line=dict(width=2, color="darkorange")),
            text=["★ Best"],
            textposition="top center",
            showlegend=False,
        )
        fig.add_trace(best_trace)

        fig.update_layout(
            xaxis_title="Cycle Time (days)",
            yaxis_title="Cost (₹)",
            legend_title="Curing",
            hovermode="closest",
            height=450,
        )
        fig.update_traces(marker=dict(line=dict(width=1, color="white")), selector=dict(mode="markers"))

        st.plotly_chart(fig, use_container_width=True)

        # Quick insight
        with st.expander("📊 Insight", expanded=False):
            ct_range = df["cycle_time"].max() - df["cycle_time"].min()
            cost_range = df["cost"].max() - df["cost"].min()
            st.markdown(
                f"**Solution space:** {len(df)} feasible configurations at automation level {automation_level}. "
                f"Cycle time varies by {ct_range:.2f} days; cost spread is ₹{cost_range:.0f}. "
                f"Steam curing typically yields faster cycle times at higher cost."
            )

        st.divider()


        st.subheader("Top 5 Recommended Configurations")

        top5 = df.head(5)
        top5_display = top5[["cement_ratio", "water_ratio", "automation", "curing", "cycle_time", "cost", "score"]].copy()
        top5_display.columns = ["Cement", "Water Ratio", "Auto", "Curing", "Cycle (days)", "Cost (₹)", "Score"]
        top5_display = top5_display.round({"Cement": 0, "Water Ratio": 3, "Cycle (days)": 2, "Cost (₹)": 0, "Score": 2})
        st.dataframe(top5_display, use_container_width=True, hide_index=True)

        st.subheader("Strategy Comparison")

        if len(df) > 1:
            compare_option = df.iloc[1]

            comp_col1, comp_col2 = st.columns(2)

            with comp_col1:
                comp_data = pd.DataFrame({
                    "Metric": ["Cycle Time (days)", "Cost (₹)"],
                    "Best": [round(best["cycle_time"], 2), round(best["cost"], 0)],
                    "Second Best": [round(compare_option["cycle_time"], 2), round(compare_option["cost"], 0)],
                })
                st.dataframe(comp_data, use_container_width=True, hide_index=True)

            with comp_col2:
                fig_comp = go.Figure()
                fig_comp.add_trace(go.Bar(x=["Best", "2nd"], y=[best["cycle_time"], compare_option["cycle_time"]],
                    marker_color=[CHART_COLORS[0], CHART_COLORS[1]], text=[f"{best['cycle_time']:.2f} days", f"{compare_option['cycle_time']:.2f} days"], textposition="outside"))
                fig_comp.update_layout(
                    title="Cycle Time",
                    template=CHART_TEMPLATE,
                    height=280,
                    xaxis_title="",
                    yaxis_title="Days",
                    margin=dict(t=60, b=40),
                    showlegend=False,
                )
                st.plotly_chart(fig_comp, use_container_width=True)

            ct_save = compare_option["cycle_time"] - best["cycle_time"]
            cost_save = compare_option["cost"] - best["cost"]
            parts = []
            if ct_save > 0:
                parts.append(f"{ct_save:.2f} days faster cycle")
            if cost_save > 0:
                parts.append(f"₹{cost_save:.0f} lower cost")
            st.caption("Best vs 2nd: " + " and ".join(parts) + "." if parts else "Best and 2nd are close.")

        with st.expander("Projected Operational Impact", expanded=False):
            col4, col5 = st.columns(2)
            col4.metric("Cycle Reduction (%)", f"{round(efficiency_gain, 1)}%")
            col5.metric("Est. Annual Impact (₹ Lakhs)", round(efficiency_gain * 8, 1))
        st.subheader("Risk Simulation (Monte Carlo)")

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

        mc_col1, mc_col2, mc_col3, mc_col4 = st.columns(4)
        mc_col1.metric("Mean", f"{mc_mean:.2f} days", help="Average across 500 simulations")
        mc_col2.metric("Std Dev", f"{mc_std:.2f}", help="Variability in cycle time")
        mc_col3.metric("P10–P90 Range", f"{mc_p10:.2f} – {mc_p90:.2f} days", help="80% of outcomes fall here")
        mc_col4.metric("Median", f"{mc_p50:.2f} days", help="Typical outcome")

        fig_mc = go.Figure()
        fig_mc.add_trace(go.Histogram(x=sim_cycles, nbinsx=30, name="Cycle Time", marker_color=CHART_COLORS[0], opacity=0.8))
        fig_mc.add_vline(x=mc_mean, line_dash="dash", line_color="darkgreen", annotation_text=f"Mean: {mc_mean:.2f}")
        fig_mc.add_vline(x=best["cycle_time"], line_dash="dot", line_color="orange", annotation_text="Baseline")
        fig_mc.update_layout(
            title="Distribution of Cycle Time (500 simulations with temp ±2°C, humidity ±5%)",
            xaxis_title="Cycle Time (days)",
            yaxis_title="Frequency",
            template=CHART_TEMPLATE,
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig_mc, use_container_width=True)
        st.subheader("Sensitivity Analysis")

        temps = list(range(15, 46, 2))
        cycle_vs_temp = []
        for t in temps:
            ct, _ = evaluate_single_config(
                best["cement_ratio"], best["water_ratio"], best["automation"],
                best["curing"], t, humidity
            )
            cycle_vs_temp.append(ct)

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
            fig_temp.add_trace(go.Scatter(x=temps, y=cycle_vs_temp, mode="lines+markers",
                line=dict(color=CHART_COLORS[0], width=3), marker=dict(size=8),
                name="Cycle Time", hovertemplate="%{x}°C → %{y:.2f} days<extra></extra>"))
            fig_temp.add_vline(x=temperature, line_dash="dash", line_color="gray",
                annotation_text=f"Current: {temperature}°C")
            fig_temp.update_layout(
                title="Temperature Impact",
                xaxis_title="Temperature (°C)",
                yaxis_title="Cycle Time (days)",
                template=CHART_TEMPLATE,
                height=320,
                margin=dict(t=50, b=50),
            )
            st.plotly_chart(fig_temp, use_container_width=True)

        with sens_col2:
            fig_hum = go.Figure()
            fig_hum.add_trace(go.Scatter(x=humidities, y=cycle_vs_hum, mode="lines+markers",
                line=dict(color=CHART_COLORS[1], width=3), marker=dict(size=8),
                name="Cycle Time", hovertemplate="%{x}% → %{y:.2f} days<extra></extra>"))
            fig_hum.add_vline(x=humidity, line_dash="dash", line_color="gray",
                annotation_text=f"Current: {humidity}%")
            fig_hum.update_layout(
                title="Humidity Impact",
                xaxis_title="Humidity (%)",
                yaxis_title="Cycle Time (days)",
                template=CHART_TEMPLATE,
                height=320,
                margin=dict(t=50, b=50),
            )
            st.plotly_chart(fig_hum, use_container_width=True)

        # Sensitivity insight
        temp_sens = (max(cycle_vs_temp) - min(cycle_vs_temp)) / (max(temps) - min(temps)) if max(temps) != min(temps) else 0
        hum_sens = (max(cycle_vs_hum) - min(cycle_vs_hum)) / (max(humidities) - min(humidities)) if max(humidities) != min(humidities) else 0
        stronger = "Temperature" if temp_sens > hum_sens else "Humidity"
        st.caption(f"**Sensitivity:** {stronger} has a stronger impact on cycle time under the current configuration.")