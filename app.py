import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import dblquad
import time

# ==========================================
# 1. GLOBAL BRANDING & UI STYLING
# ==========================================
st.set_page_config(page_title="Thermal Flux Engine", layout="wide")

# Google-standard Material Design Theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    .metric-container { background: #1a1c24; padding: 20px; border-radius: 10px; border-top: 4px solid #4285F4; }
    .theory-box { background: #0e1117; border-left: 5px solid #34a853; padding: 15px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. VECTOR CALCULUS PHYSICS CORE
# ==========================================

def temperature_model(y, x, t, sources):
    """Calculates the Scalar Field T(x, y) at time t."""
    temp = 25.0  # Ambient
    for (sx, sy, pwr) in sources:
        # Physics: Spread (sigma) increases with time
        sigma = 0.6 + (0.3 * np.sqrt(t))
        dist_sq = (x - sx)**2 + (y - sy)**2
        # Amplitude decreases as heat dissipates
        amplitude = pwr / (1 + 0.15 * t)
        temp += amplitude * np.exp(-dist_sq / (2 * sigma**2))
    return temp

# ==========================================
# 3. INTERACTIVE DASHBOARD LAYOUT
# ==========================================

# Header section
st.title("🛰️ Thermal Stress Simulator v3.0")
st.markdown("### High-Fidelity Vector Calculus Analysis for Hardware Design")

# Sidebar for precise control
with st.sidebar:
    st.header("🎮 Mission Control")
    # State management for simulation
    if 'running' not in st.session_state:
        st.session_state.running = False

    def toggle_power():
        st.session_state.running = not st.session_state.running

    st.button("🚀 INITIALIZE SYSTEM" if not st.session_state.running else "🛑 EMERGENCY SHUTDOWN", 
              on_click=toggle_power, use_container_width=True, type="primary")
    
    st.divider()
    st.subheader("Compute Parameters")
    core_a = st.slider("Core A Load (W)", 50, 400, 200)
    core_b = st.slider("Core B Load (W)", 50, 400, 150)
    
    st.divider()
    st.subheader("Visual Overlay")
    show_gradient = st.toggle("Show Flux Vectors (∇T)", value=True)
    mesh_fidelity = st.select_slider("Mesh Density", options=[30, 45, 60], value=45)

# Main metrics display
m1, m2, m3 = st.columns(3)
peak_ui = m1.empty()
energy_ui = m2.empty()
status_ui = m3.empty()

# Main visualizer container
plot_ui = st.empty()

# ==========================================
# 4. HOW TO READ THE DATA (The "User Retention" Section)
# ==========================================
st.divider()
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Operational Intelligence")
    st.markdown("""
    <div class="theory-box">
    <b>The Scalar Field (The Heat Map):</b> 
    The 3D surface height and color (Purple to Yellow) represent the temperature magnitude at every point. 
    A peak indicates a thermal hotspot.
    </div>
    """, unsafe_allow_html=True)
    
    

    st.markdown("""
    <div class="theory-box">
    <b>The Gradient Field (The Arrows):</b> 
    Derived from ∇T. In vector calculus, heat flows from hot to cold areas. 
    The blue cones show the <b>direction and magnitude</b> of heat flux as it dissipates.
    </div>
    """, unsafe_allow_html=True)
    
    

with col_right:
    st.subheader("📐 Calculus Integration")
    st.markdown("""
    <div class="theory-box">
    <b>Double Integration (∬):</b> 
    While a single reading only tells us temperature at one point, we use a <b>double integral</b> 
    over a 2D region to find the <b>Total Thermal Energy (Joules)</b> accumulated in that area.
    </div>
    """, unsafe_allow_html=True)
    
    st.latex(r"E_{total} = \iint_R T(x, y) \,dx \,dy")
    
    

# ==========================================
# 5. SIMULATION EXECUTION
# ==========================================

if st.session_state.running:
    # Setup coordinates and sources
    x_lin = np.linspace(-6, 6, mesh_fidelity)
    y_lin = np.linspace(-6, 6, mesh_fidelity)
    X, Y = np.meshgrid(x_lin, y_lin)
    sources = [(-2, -1, core_a), (2, 2, core_b)]
    
    # Simulation loop
    for t in np.arange(0, 15, 0.2):
        if not st.session_state.running:
            break
            
        # 1. Update Scalar Field
        Z = np.array([[temperature_model(yi, xi, t, sources) for xi in x_lin] for yi in y_lin])
        
        # 2. Update Double Integral (Total Heat Accumulation)
        # Limits [-2, 2] define the critical monitoring region
        energy_val, _ = dblquad(temperature_model, -2, 2, lambda x: -2, lambda x: 2, args=(t, sources))
        
        # 3. Render 3D Interface
        fig = go.Figure()
        
        # Surface Trace (The Scalar Map)
        fig.add_trace(go.Surface(
            z=Z, x=X, y=Y, colorscale='Viridis',
            cmin=25, cmax=350, colorbar=dict(title="Temp (°C)", x=1.0)
        ))

        # Vector Trace (The Gradient)
        if show_gradient:
            dy, dx = np.gradient(Z)
            step = 4
            fig.add_trace(go.Cone(
                x=X[::step, ::step].flatten(), y=Y[::step, ::step].flatten(), z=Z[::step, ::step].flatten(),
                u=-dx[::step, ::step].flatten(), v=-dy[::step, ::step].flatten(), w=np.zeros_like(dx[::step, ::step].flatten()),
                colorscale='Blues', sizemode="absolute", sizeref=1.5, anchor="tail", showscale=False
            ))

        fig.update_layout(
            template="plotly_dark", height=700, margin=dict(l=0,r=0,b=0,t=0),
            scene=dict(
                xaxis_title="Board X (mm)", yaxis_title="Board Y (mm)", zaxis_title="Temp (°C)",
                zaxis=dict(range=[20, 350]),
                camera=dict(eye=dict(x=1.7, y=1.7, z=1.0))
            )
        )

        # 4. Push updates to UI placeholders (Prevents Blinking)
        plot_ui.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        peak_ui.metric("Peak Core Temperature", f"{np.max(Z):.1f} °C")
        energy_ui.metric("Energy Accumulated (∬)", f"{energy_val:.2f} J")
        status_ui.metric("Simulation State", "STRESSING", delta=f"{t:.1f}s")
        
        time.sleep(0.01) # Frame rate control

else:
    st.info("System is currently in **STANDBY**. Click 'INITIALIZE SYSTEM' to run the vector thermal simulation.")
