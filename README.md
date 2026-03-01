# PrecastIQ  
### AI-Powered Cycle Time Optimization for Precast Yards  

PrecastIQ is a climate-adaptive, AI-driven multi-objective optimization system designed to reduce cycle time inefficiencies in precast yard operations.  

The system integrates nonlinear machine learning, constrained optimization, risk modeling, and sustainability analytics to recommend optimal production strategies under real-world environmental and budget constraints.

---

## Problem Statement

In precast construction, element cycle time — from casting to de-moulding and mold reset — directly impacts production throughput, yard capacity, cost-per-element, and project timelines.

Cycle time depends on multiple interdependent variables:

- Mix design (cement ratio, water-cement ratio)
- Curing method (normal vs steam)
- Automation level
- Ambient temperature & humidity
- Strength requirement constraints

Traditional scheduling relies on static curing tables and manual buffers, resulting in:

- 15–20% variance between planned and actual output
- Excess steam curing energy consumption
- Increased operational cost and carbon footprint
- Suboptimal mold utilization

PrecastIQ addresses this through predictive and prescriptive AI optimization.

---

## Solution Overview

PrecastIQ acts as a decision intelligence layer that:

1. Predicts cycle time using nonlinear regression (XGBoost)
2. Applies multi-objective constrained optimization
3. Filters strategies based on strength and budget limits
4. Performs sensitivity analysis
5. Conducts Monte Carlo risk simulations
6. Estimates CO₂ emissions
7. Provides executive-level dashboard visualization

---

## Core Technologies

- Python
- XGBoost (Regression Model)
- Pandas & NumPy
- Streamlit (Interactive Dashboard)
- Plotly (Visualization)

---

## System Architecture

Input Layer  
→ Environmental & Operational Parameters  
→ XGBoost Prediction Engine  
→ Multi-Objective Optimization  
→ Risk Simulation (Monte Carlo)  
→ Sustainability Estimation  
→ Interactive Dashboard  

The architecture is modular and API-ready for integration with ERP systems such as SAP and Primavera.

---

## Key Features

- Climate-aware cycle time prediction  
- Strength vs cost trade-off optimization  
- Scenario simulation & decision support  
- Sensitivity analysis (temperature impact)  
- Monte Carlo risk modeling  
- CO₂ emission estimation  
- Strategy comparison module  

---

## Performance Estimates

- R² > 0.99 (physics-informed dataset)
- 12–18% simulated cycle time reduction
- 8–10% cost-per-element reduction
- <5% deviation under risk stress testing

---

## SDG Alignment

PrecastIQ aligns with:

- SDG 9 – Industry, Innovation & Infrastructure
- SDG 12 – Responsible Consumption & Production
- SDG 13 – Climate Action

---

## Implementation Roadmap

Phase 1: Historical data calibration  
Phase 2: IoT-based real-time environmental monitoring  
Phase 3: Enterprise API integration & multi-yard deployment  

---

## Scalability

- Climate-adaptive modeling supports deployment across multiple regions.
- Cloud-ready architecture.
- Applicable to infrastructure and building precast operations.

---


---

## How to Run Locally

```bash
git clone https://github.com/1tach1271/precastiq.git
cd precastiq
pip install -r requirements.txt
streamlit run app.py
