import time
import os
import streamlit as st
from simulation.virtual_plant import VirtualPlant
from engineering.diagnostic_engine import DiagnosticEngine
from agents.diagnostic_agent import DiagnosticAgent
from agents.root_cause_agent import RootCauseAgent
from agents.troubleshooting_agent import TroubleshootingAgent
from ui.dashboard import DashboardUI
from utils.groq_client import get_groq_config

# Page Configuration
st.set_page_config(
    page_title="AI Instrumentation Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "plant" not in st.session_state:
    st.session_state.plant = VirtualPlant()
if "engine" not in st.session_state:
    st.session_state.engine = DiagnosticEngine()
if "ai_report" not in st.session_state:
    st.session_state.ai_report = None

plant: VirtualPlant = st.session_state.plant
engine: DiagnosticEngine = st.session_state.engine

# SIDEBAR CONTROL PANEL
st.sidebar.title("PROCESS CONTROL")

# Emergency Action Buttons
col_start, col_stop = st.sidebar.columns(2)
if col_start.button("▶️ START", use_container_width=True):
    plant.simulation_running = True
    plant.reset_e_stop()

if col_stop.button("⏹️ STOP", use_container_width=True):
    plant.simulation_running = False

if st.sidebar.button("🚨 EMERGENCY STOP", type="primary", use_container_width=True):
    plant.trigger_e_stop()
    st.sidebar.error("EMERGENCY STOP ENGAGED!")

st.sidebar.markdown("---")
st.sidebar.title("FAULT INJECTION")

fault_choice = st.sidebar.radio(
    "Select Abnormality to Inject:",
    [
        "No Fault",
        "PT-101 Drift",
        "4–20 mA Fault",
        "Stuck Transmitter",
        "Impulse Line Blockage",
        "Control Valve Fault",
        "Low Instrument Air",
        "Sensor Disagreement"
    ]
)

if st.sidebar.button("⚡ Inject Fault", use_container_width=True):
    plant.set_fault(fault_choice)
    st.sidebar.success(f"Injected: {fault_choice}")

# System Configuration Overview
api_key, model_name = get_groq_config()
st.sidebar.markdown("---")
st.sidebar.markdown("**Engine Mode:**")
if api_key:
    st.sidebar.success(f"🟢 GROQ API Active\n({model_name})")
else:
    st.sidebar.warning("🟡 DEMO MODE Active\n(Deterministic Rules Fallback)")

# MAIN APPLICATION DISPLAY
DashboardUI.render_header()
DashboardUI.render_safety_warning()

# Advance plant simulation step
if plant.simulation_running:
    current_sample = plant.step()
else:
    current_sample = plant.history[-1] if plant.history else plant.step()

# Run Engineering Calculation Engine
evidence_package = engine.evaluate_plant_health(current_sample)

# Display Dashboard Sections
DashboardUI.render_plant_overview(current_sample)
DashboardUI.render_instrument_health_table(evidence_package, current_sample)
DashboardUI.render_trend_graphs(plant.history)

# DIAGNOSTIC EXECUTION SECTION
st.markdown("---")
col_diag, _ = st.columns([2, 3])

with col_diag:
    run_diagnosis = st.button("🔍 RUN AI DIAGNOSIS", type="primary", use_container_width=True)

if run_diagnosis:
    with st.spinner("Orchestrating 3 AI Specialist Agents (Diagnostic -> Root Cause -> Troubleshooting)..."):
        # Agent 1: Diagnostic Specialist
        diag_agent = DiagnosticAgent()
        diag_res = diag_agent.run(evidence_package)

        # Agent 2: Root Cause Specialist
        rc_agent = RootCauseAgent()
        rc_res = rc_agent.run(evidence_package, diag_res)

        # Agent 3: Troubleshooting Specialist
        ts_agent = TroubleshootingAgent()
        ts_res = ts_agent.run(evidence_package, rc_res)

        st.session_state.ai_report = {
            "diagnostic": diag_res,
            "root_cause": rc_res,
            "troubleshooting": ts_res
        }

# RENDER AI DIAGNOSTIC REPORT
if st.session_state.ai_report:
    st.markdown("## 📋 Final Engineering AI Analysis Report")
    
    tab1, tab2, tab3 = st.tabs(["1. Diagnostic Summary", "2. Probable Root Causes", "3. Field Troubleshooting Procedure"])
    
    with tab1:
        st.markdown(st.session_state.ai_report["diagnostic"])
    with tab2:
        st.markdown(st.session_state.ai_report["root_cause"])
    with tab3:
        st.markdown(st.session_state.ai_report["troubleshooting"])

# Auto-rerun loop to drive live process simulation graphics
time.sleep(1.0)
st.rerun()
