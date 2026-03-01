import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import CHART_TEMPLATE, CHART_COLORS, PRIMARY_COLOR, SUCCESS_COLOR, WARNING_COLOR

def create_metric_card(title, value, delta=None, help_text=None, color="blue"):
    """Create a styled metric card"""
    if color == "success":
        st.markdown(f"""
        <div style="background-color: #d4edda; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #28a745;">
            <div style="font-size: 0.9rem; color: #155724; font-weight: 600;">{title}</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #155724;">{value}</div>
            {f'<div style="font-size: 0.8rem; color: #155724;">{delta}</div>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)
    elif color == "warning":
        st.markdown(f"""
        <div style="background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107;">
            <div style="font-size: 0.9rem; color: #856404; font-weight: 600;">{title}</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #856404;">{value}</div>
            {f'<div style="font-size: 0.8rem; color: #856404;">{delta}</div>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.metric(title, value, delta, help=help_text)

def create_comparison_chart(best, second_best):
    """Create side-by-side comparison chart"""
    fig = go.Figure()
    
    metrics = ["Cycle Time (days)", "Cost (₹)"]
    best_values = [best["cycle_time"], best["cost"]]
    second_values = [second_best["cycle_time"], second_best["cost"]]
    
    fig.add_trace(go.Bar(
        name='Best', 
        x=metrics, 
        y=best_values,
        marker_color=CHART_COLORS[0],
        text=[f"{v:.2f}" if i == 0 else f"₹{v:.0f}" for i, v in enumerate(best_values)],
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        name='Second Best', 
        x=metrics, 
        y=second_values,
        marker_color=CHART_COLORS[1],
        text=[f"{v:.2f}" if i == 0 else f"₹{v:.0f}" for i, v in enumerate(second_values)],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Strategy Comparison",
        template=CHART_TEMPLATE,
        height=400,
        barmode='group',
        showlegend=True
    )
    
    return fig

def create_sensitivity_chart(temps, cycle_vs_temp, current_temp, title="Temperature Impact"):
    """Create sensitivity analysis chart"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=temps, 
        y=cycle_vs_temp, 
        mode="lines+markers",
        line=dict(color=CHART_COLORS[0], width=3), 
        marker=dict(size=8),
        name="Cycle Time", 
        hovertemplate="%{x}°C → %{y:.2f} days<extra></extra>"
    ))
    
    fig.add_vline(
        x=current_temp, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Current: {current_temp}°C"
    )
    
    fig.update_layout(
        title=title,
        xaxis_title="Temperature (°C)",
        yaxis_title="Cycle Time (days)",
        template=CHART_TEMPLATE,
        height=350,
        margin=dict(t=50, b=50),
    )
    
    return fig

def create_solution_space_chart(df, best):
    """Create enhanced solution space visualization"""
    fig = px.scatter(
        df,
        x="cycle_time",
        y="cost",
        color="curing",
        size="score",
        hover_data=["cement_ratio", "water_ratio", "automation"],
        template=CHART_TEMPLATE,
        color_discrete_sequence=CHART_COLORS,
        title="Cost vs Cycle Time Tradeoff (Bubble size = Score)",
        labels={
            "cycle_time": "Cycle Time (days)",
            "cost": "Cost (₹)",
            "curing": "Curing Method",
            "cement_ratio": "Cement (kg/m³)",
            "water_ratio": "Water-Cement Ratio",
            "automation": "Automation Level"
        }
    )
    
    # Highlight best solution
    fig.add_trace(go.Scatter(
        x=[best["cycle_time"]],
        y=[best["cost"]],
        mode="markers+text",
        marker=dict(
            symbol="star", 
            size=20, 
            color="gold", 
            line=dict(width=2, color="darkorange")
        ),
        text=["★ BEST"],
        textposition="top center",
        showlegend=False,
        name="Recommended"
    ))
    
    # Add Pareto frontier line
    pareto_df = df.sort_values('cycle_time')
    pareto_costs = []
    min_cost = float('inf')
    
    for _, row in pareto_df.iterrows():
        if row['cost'] < min_cost:
            min_cost = row['cost']
            pareto_costs.append(row)
    
    if len(pareto_costs) > 1:
        pareto_df = pd.DataFrame(pareto_costs)
        fig.add_trace(go.Scatter(
            x=pareto_df['cycle_time'],
            y=pareto_df['cost'],
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name='Pareto Frontier',
            showlegend=True
        ))
    
    fig.update_layout(
        height=500,
        hovermode='closest'
    )
    
    return fig

def show_loading_animation(message="Processing..."):
    """Show loading animation"""
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem;">
        <div style="border: 4px solid #f3f3f3; border-top: 4px solid {PRIMARY_COLOR}; 
                    border-radius: 50%; width: 40px; height: 40px; 
                    animation: spin 1s linear infinite; margin: 0 auto;"></div>
        <p style="margin-top: 1rem; color: #666;">{message}</p>
    </div>
    <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """, unsafe_allow_html=True)

def create_info_alert(message, alert_type="info"):
    """Create styled alert messages"""
    if alert_type == "success":
        color = "#d4edda"
        border = "#28a745"
        text = "#155724"
    elif alert_type == "warning":
        color = "#fff3cd"
        border = "#ffc107"
        text = "#856404"
    elif alert_type == "error":
        color = "#f8d7da"
        border = "#dc3545"
        text = "#721c24"
    else:
        color = "#d1ecf1"
        border = "#17a2b8"
        text = "#0c5460"
    
    st.markdown(f"""
    <div style="background-color: {color}; padding: 1rem; border-radius: 0.5rem; 
                border-left: 4px solid {border}; margin: 1rem 0;">
        <div style="color: {text};">{message}</div>
    </div>
    """, unsafe_allow_html=True)
