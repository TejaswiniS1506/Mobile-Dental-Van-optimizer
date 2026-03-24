import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import datetime
import requests
from math import radians, sin, cos, sqrt, atan2, floor, ceil

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Mobile Dental Clinic Van Schedule Optimization Model", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. THE ABSOLUTE CONTRAST CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    label, .st-emotion-cache-16idsys p, .st-emotion-cache-1pxm7c, [data-testid="stWidgetLabel"] p, [data-testid="stText"] {
        color: #2D2D2D !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #F2F2F2 !important;
        border-right: 2px solid #800000;
    }
    .sidebar-heading {
        color: #800000 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 700;
        font-size: 16px;
        margin-top: 20px;
        border-bottom: 2px solid #800000;
        padding-bottom: 5px;
        display: block;
    }
    .main-title { color: #800000 !important; font-size: 26px; font-weight: 800; text-transform: uppercase; }
    .sub-title { color: #800000 !important; font-size: 18px; font-weight: 600; margin-top: 5px; }
    h1, h2, h3, h4 { color: #800000 !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #4D4D4D !important; font-weight: 500 !important; }
    [data-testid="stMetricValue"] { color: #800000 !important; font-weight: 800 !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .cal-table { width: 100%; border-collapse: collapse; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; }
    .cal-table th { background-color: #800000; color: white; padding: 10px 8px; text-align: center; font-weight: 700; border: 1px solid #ddd; }
    .cal-table td { padding: 8px 6px; text-align: center; border: 1px solid #ddd; vertical-align: top; min-height: 60px; }
    .cal-table tr:nth-child(even) { background-color: #FDF5F5; }
    .cal-table tr:nth-child(odd) { background-color: #FFFFFF; }
    .cal-deploy { background-color: #800000 !important; color: white !important; font-weight: 700; border-radius: 4px; padding: 4px 6px; display: inline-block; margin: 2px 0; font-size: 12px; }
    .cal-off { color: #AAAAAA; font-style: italic; font-size: 11px; }
    .cal-week { font-weight: 700; color: #800000; font-size: 12px; }
    .cal-patients { font-size: 11px; color: #555; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---
@st.cache_data
def get_current_gas_price():
    API_KEY = "sYG29W5ZQaQdUd71zEA7qKGLK1jqwQfz8YWUSIrX"
    url = (f"https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={API_KEY}"
           f"&frequency=weekly&data[0]=value&facets[series][]=EMM_EPMR_PTE_YORD_DPG"
           f"&sort[0][column]=period&sort[0][direction]=desc&length=1")
    try:
        r = requests.get(url, timeout=3).json()
        return float(r['response']['data'][0]['value'])
    except:
        return 3.50

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3958.8
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return R * (2 * atan2(sqrt(a), sqrt(1 - a)))

def clean_uploaded_data(raw_df):
    df = raw_df.copy()
    df.columns = df.columns.str.strip()

    if 'SITE NAME' in df.columns and 'Name' not in df.columns:
        df = df.rename(columns={'SITE NAME': 'Name'})
    if 'seniors_y_coordinates' in df.columns and 'Latitude' not in df.columns:
        df = df.rename(columns={'seniors_y_coordinates': 'Latitude'})
    if 'seniors_x_coordinates' in df.columns and 'Longitude' not in df.columns:
        df = df.rename(columns={'seniors_x_coordinates': 'Longitude'})
    if 'Parking name' in df.columns and 'Parking_Name' not in df.columns:
        df = df.rename(columns={'Parking name': 'Parking_Name'})
    if 'Parking_Name' not in df.columns:
        df['Parking_Name'] = 'N/A'
    if 'ADDRESS' in df.columns and 'Address' not in df.columns:
        df = df.rename(columns={'ADDRESS': 'Address'})
    if 'Address' not in df.columns:
        df['Address'] = 'N/A'
    if 'Senior_Pop' not in df.columns:
        df['Senior_Pop'] = 200
    if 'Parking_Distance_Meters' not in df.columns:
        df['Parking_Distance_Meters'] = 0
    if 'distance_from_hospital' in df.columns and 'Dist_Closest_UCM' not in df.columns:
        df = df.rename(columns={'distance_from_hospital': 'Dist_Closest_UCM'})
    if 'Dist_Closest_UCM' not in df.columns:
        df['Dist_Closest_UCM'] = np.nan
    if 'hospital_name' in df.columns and 'Closest_UCM_Facility' not in df.columns:
        df = df.rename(columns={'hospital_name': 'Closest_UCM_Facility'})
    if 'Closest_UCM_Facility' not in df.columns:
        df['Closest_UCM_Facility'] = 'N/A'

    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    df['Senior_Pop'] = pd.to_numeric(df['Senior_Pop'], errors='coerce').fillna(200).astype(int)
    df['Parking_Distance_Meters'] = pd.to_numeric(df['Parking_Distance_Meters'], errors='coerce').fillna(0)
    df['Dist_Closest_UCM'] = pd.to_numeric(df['Dist_Closest_UCM'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])
    return df

def generate_deployment_schedule(final_output, start_date, num_weeks, deploy_days):
    """
    Rolling deployment planner. Each deployment day: pick the site with the
    highest remaining patient demand, serve up to Daily_Capacity, subtract, repeat.
    """
    sites = final_output[['Name', 'Volume', 'Daily_Capacity', 'Parking_Name', 'CPA']].copy()
    sites = sites.rename(columns={'Volume': 'Remaining'})
    
    schedule = []
    current = start_date
    while current.weekday() not in deploy_days:
        current += datetime.timedelta(days=1)
    
    end_date = start_date + datetime.timedelta(weeks=num_weeks)
    
    while current < end_date:
        if current.weekday() in deploy_days:
            active = sites[sites['Remaining'] > 0]
            if len(active) > 0:
                best_idx = active['Remaining'].idxmax()
                best = sites.loc[best_idx]
                served = min(int(best['Daily_Capacity']), int(best['Remaining']))
                sites.loc[best_idx, 'Remaining'] -= served
                schedule.append({
                    'Date': current, 'Day': current.strftime('%A'),
                    'Site': best['Name'], 'Patients_Served': served,
                    'Remaining_At_Site': int(sites.loc[best_idx, 'Remaining']),
                    'Parking': best['Parking_Name'],
                })
            else:
                schedule.append({
                    'Date': current, 'Day': current.strftime('%A'),
                    'Site': 'All Demand Met', 'Patients_Served': 0,
                    'Remaining_At_Site': 0, 'Parking': '-',
                })
        current += datetime.timedelta(days=1)
    
    return pd.DataFrame(schedule), sites

# --- 4. HEADER ---
st.markdown("""
    <div style="border-bottom: 3px solid #800000; padding-bottom: 10px; margin-bottom: 25px;">
        <div class="main-title">Mobile Dental Clinic Van Schedule Optimization Model</div>
        <div class="sub-title">University of Chicago | Center for Health and Social Sciences</div>
        <div style="color:#555555; font-size:12px; font-weight:500;">Policy Lab - Dental Team 2026</div>
    </div>
""", unsafe_allow_html=True)

logo_cols = st.columns([1, 1, 3])
if os.path.exists("ucm_logo.png"):
    with logo_cols[0]: st.image("ucm_logo.png", width=180)
if os.path.exists("lab_logo.png"):
    with logo_cols[1]: st.image("lab_logo.png", width=180)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown('<span class="sidebar-heading">Economic Parameters</span>', unsafe_allow_html=True)
    live_price = get_current_gas_price()
    gas_price = st.number_input("Fuel Price (USD per Gallon)", value=live_price, step=0.50)
    hourly_wage = st.number_input("Staff Hourly Wage (Combined USD)", value=155.0, step=5.0)
    fixed_daily_cost = st.number_input("Daily Fixed Overhead (Rent, Admin, etc.)", value=200.0, step=10.0)
    variable_patient_cost = st.number_input("Variable Cost Per Patient (Supplies)", value=20.0, step=10.0)
    
    st.markdown('<span class="sidebar-heading">Operational Capacity</span>', unsafe_allow_html=True)
    chairs = st.slider("Total Number of Dental Chairs", 1, 4, 2)
    shift_hours = st.slider("Daily Operational Shift (Hours)", 4, 12, 8)
    avg_speed = st.number_input("Average Transit Speed (MPH)", value=18)

    st.markdown('<span class="sidebar-heading">Optimization Strategy</span>', unsafe_allow_html=True)
    capture_rate = st.slider("Expected Patient Capture Rate", 0.1, 1.0, 0.4)
    weight_volume = st.slider("Weighting: Reach vs. Cost", 0.0, 1.0, 0.7)
    weight_cost = round(1.0 - weight_volume, 2)
    st.markdown(f"<p style='color:#800000; font-weight:bold; font-size:14px; margin-top:10px;'>Current Cost Efficiency Weight: {weight_cost}</p>", unsafe_allow_html=True)

    st.markdown('<span class="sidebar-heading">Deployment Planner</span>', unsafe_allow_html=True)
    plan_weeks = st.slider("Schedule Horizon (Weeks)", 4, 52, 12)
    plan_start = st.date_input("Schedule Start Date", value=datetime.date.today() + datetime.timedelta(days=(1 - datetime.date.today().weekday()) % 7))
    deploy_day_options = st.multiselect(
        "Deployment Days (Low Hospital Traffic)",
        options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        default=["Tuesday", "Friday"]
    )
    day_name_to_num = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
    deploy_day_nums = [day_name_to_num[d] for d in deploy_day_options]

# --- 6. MAIN CONTENT ---
uploaded_file = st.file_uploader("Upload Site Location Data (CSV Format Only)", type="csv")

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file)
    df = clean_uploaded_data(raw_df)
    BASE_LAT, BASE_LON = 41.7896, -87.5996
    
    def run_simulation(w_wage, w_fixed, w_var):
        temp_results = []
        for _, row in df.iterrows():
            dist = haversine_distance(BASE_LAT, BASE_LON, row['Latitude'], row['Longitude'])
            t_avail = (shift_hours * 60) - 60 - ((dist * 2 / avg_speed) * 60) - (40 + (row.get('Parking_Distance_Meters', 0)/100)*4)
            cap = floor(max(0, t_avail) / 60) * chairs
            demand = int(row['Senior_Pop'] * capture_rate)
            days = ceil(demand / cap) if cap > 0 else 999
            d_cost = w_fixed + (shift_hours * w_wage) + (dist * 2 / 10 * gas_price)
            p_cost = (days * d_cost) + (demand * w_var)
            temp_results.append({
                "Name": row['Name'],
                "Address": row.get('Address', 'N/A'),
                "Parking_Name": row.get('Parking_Name', 'N/A'),
                "Closest_UCM_Facility": row.get('Closest_UCM_Facility', 'N/A'),
                "Dist_Closest_UCM": round(row.get('Dist_Closest_UCM', 0), 2) if pd.notna(row.get('Dist_Closest_UCM')) else 'N/A',
                "lat": row['Latitude'],
                "lon": row['Longitude'],
                "Distance_From_Base_Miles": round(dist, 2),
                "Volume": demand,
                "Daily_Capacity": cap,
                "Days_Required": days,
                "CPA": p_cost / demand if demand > 0 else 9999,
            })
        return pd.DataFrame(temp_results)

    analysis_df = run_simulation(hourly_wage, fixed_daily_cost, variable_patient_cost)
    analysis_df['Score'] = (weight_volume * (analysis_df['Volume'] / analysis_df['Volume'].max())) - (weight_cost * (analysis_df['CPA'] / analysis_df['CPA'].max()))
    final_output = analysis_df.sort_values("Score", ascending=False).reset_index(drop=True)
    final_output.insert(0, 'Rank', range(1, len(final_output) + 1))

    # ==========================================
    # EXECUTIVE SUMMARY
    # ==========================================
    st.markdown('<h3 style="color:#800000;">Executive Summary</h3>', unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Priority Site", final_output['Name'].iloc[0])
    m2.metric("Total Patient Reach", f"{final_output['Volume'].sum():,}")
    m3.metric("Top Site CPA", f"${final_output['CPA'].iloc[0]:.2f}")
    m4.metric("Mean CPA", f"${final_output['CPA'].mean():.2f}")

    m5, m6, m7 = st.columns(3)
    m5.metric("Priority Site Parking", final_output['Parking_Name'].iloc[0])
    top_ucm_dist = final_output['Dist_Closest_UCM'].iloc[0]
    m6.metric("Dist. to Closest UCM Facility", f"{top_ucm_dist} mi" if top_ucm_dist != 'N/A' else "N/A")
    m7.metric("Sites Analyzed", f"{len(final_output)}")

    # Full-width UCM facility name so it never truncates
    st.markdown(f"""
        <div style="background-color:#FDF5F5; border-left:4px solid #800000; padding:10px 15px; margin:5px 0 15px 0; border-radius:0 4px 4px 0;">
            <span style="color:#4D4D4D; font-size:13px; font-weight:500;">Closest UCM Facility to Priority Site</span><br>
            <span style="color:#800000; font-size:18px; font-weight:700;">{final_output['Closest_UCM_Facility'].iloc[0]}</span>
        </div>
    """, unsafe_allow_html=True)

    # --- Volume / Patient Reach Methodology ---
    with st.expander("How is Total Patient Reach & Volume Calculated?"):
        nearby_cap = floor(((shift_hours * 60) - 60 - ((2 * 2 / avg_speed) * 60) - 40) / 60) * chairs
        st.markdown(f"""
**Patient Reach** is calculated per site using the formula:

> **Volume = Senior Population at Site × Capture Rate**

- **Senior Population**: Currently set to **{df['Senior_Pop'].iloc[0]}** per site (default estimate; replace with actual census data for better accuracy).
- **Capture Rate**: The expected proportion of the senior population that will seek dental care = **{capture_rate:.0%}** (adjustable in sidebar).
- **Total Patient Reach**: The sum of Volume across all **{len(final_output)}** sites = **{final_output['Volume'].sum():,}** patients.

**Daily Capacity** per site depends on travel time, setup, and chairs:

> **Available Minutes = (Shift Hours × 60) − 60 min setup − Round-trip Travel Time − Parking Overhead**
> **Daily Capacity = floor(Available Minutes / 60) × Number of Chairs**

With **{chairs} chairs** and an **{shift_hours}-hour shift**, a nearby site (~2 mi) yields ~**{nearby_cap}** patients/day, while a distant site (~15 mi) yields far fewer due to transit time eating into clinical hours.

**Days Required** = ceil(Volume / Daily Capacity) — how many deployment days needed to serve all projected patients at that site.
        """)

    # ==========================================
    # HOSPITAL TRAFFIC ANALYSIS
    # ==========================================
    st.markdown('<h3 style="color:#800000; margin-top:20px;">Hospital Traffic Analysis</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:#2D2D2D; font-size:14px;">EPIC appointment data reveals which days have lowest hospital dental clinic volume — optimal windows for mobile van deployment without disrupting fixed-site operations.</p>', unsafe_allow_html=True)

    traffic_data = pd.DataFrame({
        'Day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'Appointments': [794, 227, 972, 920, 194, 0, 0]
    })
    daily_avg = traffic_data['Appointments'].mean()

    colors = []
    for d in traffic_data['Day']:
        if d in deploy_day_options:
            colors.append('#800000')
        elif d == 'Wednesday':
            colors.append('#08519C')
        else:
            colors.append('#6BAED6')

    fig_traffic = go.Figure()
    fig_traffic.add_trace(go.Bar(
        x=traffic_data['Day'], y=traffic_data['Appointments'],
        marker_color=colors, text=traffic_data['Appointments'],
        textposition='outside', textfont=dict(size=13, color='#2D2D2D', family='Arial Black')
    ))
    fig_traffic.add_hline(y=daily_avg, line_dash="dash", line_color="#B22222", line_width=2,
                          annotation_text=f"Avg: {daily_avg:.0f}", annotation_position="right",
                          annotation_font=dict(color="#B22222", size=13, family="Arial Black"))
    fig_traffic.update_layout(
        plot_bgcolor='white', yaxis_title="Number of Appointments", xaxis_title="Day of Week",
        height=380, margin=dict(t=30, b=40),
        yaxis=dict(showgrid=True, gridcolor='#F0F0F0'), xaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_traffic, use_container_width=True)

    deploy_days_str = " and ".join(deploy_day_options) if deploy_day_options else "None selected"
    st.markdown(f"""
        <div style="background-color:#FDF5F5; border-left:4px solid #800000; padding:12px 15px; margin:0 0 20px 0; border-radius:0 4px 4px 0;">
            <span style="color:#800000; font-weight:700; font-size:14px;">Recommendation:</span>
            <span style="color:#2D2D2D; font-size:14px;"> Deploy the mobile van on <b>{deploy_days_str}</b> when hospital volume is lowest.
            Staff can be reassigned to the van on these days with minimal impact on fixed-site operations.
            Maroon bars above indicate your selected deployment days.</span>
        </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # SENSITIVITY ANALYSIS
    # ==========================================
    st.markdown('<h3 style="color:#800000; margin-top:20px;">Financial Sensitivity Analysis</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:#2D2D2D; font-size:14px;">Projected impact on Mean CPA across primary cost drivers (50% to 150% of current values).</p>', unsafe_allow_html=True)
    
    steps = np.linspace(0.5, 1.5, 11)
    sens_results = []
    for s in steps:
        sens_results.append({"Variable": "Hourly Wage", "Multiplier": s, "Mean CPA": run_simulation(hourly_wage * s, fixed_daily_cost, variable_patient_cost)['CPA'].mean()})
        sens_results.append({"Variable": "Fixed Daily Cost", "Multiplier": s, "Mean CPA": run_simulation(hourly_wage, fixed_daily_cost * s, variable_patient_cost)['CPA'].mean()})
        sens_results.append({"Variable": "Variable Cost (Supplies)", "Multiplier": s, "Mean CPA": run_simulation(hourly_wage, fixed_daily_cost, variable_patient_cost * s)['CPA'].mean()})
    
    fig_sens = px.line(pd.DataFrame(sens_results), x="Multiplier", y="Mean CPA", color="Variable",
                       color_discrete_sequence=["#800000", "#4D4D4D", "#A9A9A9"], markers=True)
    fig_sens.update_layout(plot_bgcolor='white', xaxis_tickformat='%', xaxis_title="Variance from Baseline", yaxis_title="Mean CPA ($)", legend_title="")
    fig_sens.update_xaxes(showgrid=True, gridcolor='#F0F0F0')
    fig_sens.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
    st.plotly_chart(fig_sens, use_container_width=True)

    # ==========================================
    # GEOGRAPHIC & TABLE
    # ==========================================
    st.markdown('<h3 style="color:#800000; margin-top:20px;">Geographic and Analytical Priority</h3>', unsafe_allow_html=True)
    col_map, col_chart = st.columns([1.5, 1])
    with col_map:
        fig_map = px.scatter_mapbox(final_output, lat="lat", lon="lon", hover_name="Name",
                                    hover_data={"Parking_Name": True, "Closest_UCM_Facility": True, "Dist_Closest_UCM": True, "CPA": ':.2f', "Distance_From_Base_Miles": True, "lat": False, "lon": False},
                                    color="Rank", size="Volume", color_continuous_scale=["#800000", "#D3D3D3"], zoom=10.5, height=450)
        fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    with col_chart:
        fig_bar = px.bar(final_output.head(10), x='Score', y='Name', orientation='h', color_discrete_sequence=['#800000'])
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}, xaxis={'title': 'Optimization Score'}, plot_bgcolor='rgba(0,0,0,0)', margin={"t":10,"b":10})
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown('<h3 style="color:#800000;">Detailed Analytical Results</h3>', unsafe_allow_html=True)
    display_cols = ['Rank', 'Name', 'Address', 'Parking_Name', 'Closest_UCM_Facility', 'Dist_Closest_UCM',
                    'Distance_From_Base_Miles', 'Volume', 'Daily_Capacity', 'Days_Required', 'CPA', 'Score']
    st.dataframe(final_output[display_cols], use_container_width=True)

    # ==========================================
    # DEPLOYMENT PLANNER / CALENDAR
    # ==========================================
    st.markdown('<h3 style="color:#800000; margin-top:30px;">Mobile Van Deployment Planner</h3>', unsafe_allow_html=True)
    st.markdown(f"""<p style="color:#2D2D2D; font-size:14px;">
        Rolling {plan_weeks}-week schedule starting {plan_start.strftime('%B %d, %Y')}. 
        Each deployment day, the van is assigned to the site with the <b>highest remaining patient demand</b>. 
        After each visit, served patients are subtracted and the next day re-evaluates priorities dynamically.
        Deployment days: <b>{deploy_days_str}</b>.
    </p>""", unsafe_allow_html=True)

    if len(deploy_day_nums) > 0:
        schedule_df, sites_after = generate_deployment_schedule(final_output, plan_start, plan_weeks, deploy_day_nums)

        # --- Build calendar HTML ---
        week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        date_lookup = {}
        for _, row in schedule_df.iterrows():
            date_lookup[row['Date']] = row
        
        all_weeks = []
        w_start = plan_start - datetime.timedelta(days=plan_start.weekday())
        w_end = plan_start + datetime.timedelta(weeks=plan_weeks)
        while w_start < w_end:
            all_weeks.append(w_start)
            w_start += datetime.timedelta(weeks=1)
        
        cal_html = '<table class="cal-table"><thead><tr><th>Week</th>'
        for day in week_days:
            cal_html += f'<th>{day}</th>'
        cal_html += '</tr></thead><tbody>'
        
        for week_monday in all_weeks:
            week_label = week_monday.strftime('%b %d')
            cal_html += f'<tr><td class="cal-week">{week_label}</td>'
            for i, day_name in enumerate(week_days):
                this_date = week_monday + datetime.timedelta(days=i)
                if this_date in date_lookup:
                    entry = date_lookup[this_date]
                    if entry['Site'] == 'All Demand Met':
                        cal_html += f'<td><span class="cal-off">All demand met</span></td>'
                    else:
                        cal_html += f'<td><span class="cal-deploy">{entry["Site"]}</span><div class="cal-patients">{entry["Patients_Served"]} patients<br>Parking: {entry["Parking"]}</div></td>'
                elif i in deploy_day_nums:
                    if this_date < plan_start:
                        cal_html += '<td><span class="cal-off">—</span></td>'
                    else:
                        cal_html += '<td><span class="cal-off">All demand met</span></td>'
                else:
                    cal_html += '<td><span class="cal-off">Hospital day</span></td>'
            cal_html += '</tr>'
        
        cal_html += '</tbody></table>'
        st.markdown(cal_html, unsafe_allow_html=True)

        # --- Summary stats ---
        st.markdown('<h4 style="color:#800000; margin-top:20px;">Deployment Summary</h4>', unsafe_allow_html=True)

        total_deployed = len(schedule_df[schedule_df['Site'] != 'All Demand Met'])
        total_served = schedule_df['Patients_Served'].sum()
        unique_sites = schedule_df[schedule_df['Site'] != 'All Demand Met']['Site'].nunique()
        
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Deployment Days", total_deployed)
        s2.metric("Total Patients Served", f"{total_served:,}")
        s3.metric("Unique Sites Visited", unique_sites)
        remaining_demand = sites_after['Remaining'].sum()
        s4.metric("Remaining Unmet Demand", f"{int(remaining_demand):,}")

        if remaining_demand > 0:
            st.markdown('<p style="color:#2D2D2D; font-size:13px; margin-top:10px;"><b>Sites with remaining unmet demand after scheduled horizon:</b></p>', unsafe_allow_html=True)
            unmet = sites_after[sites_after['Remaining'] > 0][['Name', 'Remaining']].sort_values('Remaining', ascending=False)
            st.dataframe(unmet.reset_index(drop=True), use_container_width=True, height=200)
        else:
            st.success(f"All projected patient demand ({final_output['Volume'].sum():,} patients) can be fully served within the {plan_weeks}-week deployment window.")

        # Download full plan
        st.markdown("---")
        sched_buffer = io.BytesIO()
        with pd.ExcelWriter(sched_buffer, engine='openpyxl') as writer:
            schedule_df.drop(columns=['Week_Start'], errors='ignore').to_excel(writer, index=False, sheet_name='Deployment_Schedule')
            final_output[display_cols].to_excel(writer, index=False, sheet_name='Site_Rankings')
        st.download_button("Download Full Deployment Plan (Excel)", data=sched_buffer.getvalue(),
                          file_name=f"UChicago_Dental_Deployment_Plan_{datetime.date.today()}.xlsx")
    else:
        st.warning("Please select at least one deployment day in the sidebar.")

    # --- Original rankings export ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        final_output[display_cols].to_excel(writer, index=False, sheet_name='Rankings')
    st.download_button("Generate Optimization Report Only (Excel)", data=buffer.getvalue(), file_name=f"UChicago_Dental_Optimization_{datetime.date.today()}.xlsx")

else:
    st.info("System Initialized. Please upload site location data to activate the optimization engine.")
