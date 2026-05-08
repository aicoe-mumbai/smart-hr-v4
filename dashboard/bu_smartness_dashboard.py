"""
BU SMARTNESS & Alignment Dashboard
An aesthetic Streamlit dashboard to visualize BU SMARTNESS scores and cross-BU alignment
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page configuration
st.set_page_config(
    page_title="BU SMARTNESS & Alignment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for aesthetic design
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6c757d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        margin: 2rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 2rem;
        background-color: #f8f9fa;
        border-radius: 10px 10px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_excel_data(file_path):
    """Load data from Excel file"""
    try:
        # Check if file exists
        import os
        if not os.path.exists(file_path):
            st.error(f"File not found: {file_path}")
            return None, None
        
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        
        # Load summary
        summary_df = pd.read_excel(file_path, sheet_name='Summary')
        
        # Load individual BU sheets
        bu_data = {}
        for sheet_name in excel_file.sheet_names:
            if sheet_name != 'Summary':
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                bu_data[sheet_name] = df
        
        return summary_df, bu_data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

def create_smartness_gauge(value, title):
    """Create a gauge chart for SMARTNESS score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        delta={'reference': 75, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ffebee'},
                {'range': [40, 60], 'color': '#fff3e0'},
                {'range': [60, 75], 'color': '#e8f5e9'},
                {'range': [75, 100], 'color': '#c8e6c9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig

def create_symmetric_alignment_matrix(bu_data):
    """Create symmetric alignment matrix by averaging both directions"""
    bu_names = list(bu_data.keys())
    alignment_matrix = pd.DataFrame(index=bu_names, columns=bu_names, dtype=float)
    
    # Fill the matrix
    for bu1 in bu_names:
        for bu2 in bu_names:
            if bu1 == bu2:
                alignment_matrix.loc[bu1, bu2] = 100.0  # Self-alignment is 100%
            else:
                # Get alignment from bu1 to bu2
                df1 = bu_data[bu1]
                alignment_section1 = df1[
                    df1.iloc[:, 0].notna() & 
                    (df1.iloc[:, 0] != 'Goal ID') &
                    ~df1.iloc[:, 0].astype(str).str.contains('ALIGNMENT', case=False, na=False)
                ]
                align_1_to_2 = None
                for _, row in alignment_section1.iterrows():
                    if row.iloc[0] == bu2:
                        align_1_to_2 = pd.to_numeric(row.iloc[1], errors='coerce')
                        break
                
                # Get alignment from bu2 to bu1
                df2 = bu_data[bu2]
                alignment_section2 = df2[
                    df2.iloc[:, 0].notna() & 
                    (df2.iloc[:, 0] != 'Goal ID') &
                    ~df2.iloc[:, 0].astype(str).str.contains('ALIGNMENT', case=False, na=False)
                ]
                align_2_to_1 = None
                for _, row in alignment_section2.iterrows():
                    if row.iloc[0] == bu1:
                        align_2_to_1 = pd.to_numeric(row.iloc[1], errors='coerce')
                        break
                
                # Average both directions for symmetric alignment
                if align_1_to_2 is not None and align_2_to_1 is not None:
                    alignment_matrix.loc[bu1, bu2] = (align_1_to_2 + align_2_to_1) / 2
                elif align_1_to_2 is not None:
                    alignment_matrix.loc[bu1, bu2] = align_1_to_2
                elif align_2_to_1 is not None:
                    alignment_matrix.loc[bu1, bu2] = align_2_to_1
                else:
                    alignment_matrix.loc[bu1, bu2] = 0.0
    
    return alignment_matrix

def create_directional_alignment_matrix(bu_data):
    """Create directional alignment matrix (Source BU → Target BU)"""
    bu_names = list(bu_data.keys())
    alignment_matrix = pd.DataFrame(index=bu_names, columns=bu_names, dtype=float)
    
    for bu1 in bu_names:
        for bu2 in bu_names:
            if bu1 == bu2:
                alignment_matrix.loc[bu1, bu2] = 100.0
            else:
                df = bu_data[bu1]
                alignment_section = df[
                    df.iloc[:, 0].notna() & 
                    (df.iloc[:, 0] != 'Goal ID') &
                    ~df.iloc[:, 0].astype(str).str.contains('ALIGNMENT', case=False, na=False)
                ]
                alignment_val = 0.0
                for _, row in alignment_section.iterrows():
                    if row.iloc[0] == bu2:
                        alignment_val = pd.to_numeric(row.iloc[1], errors='coerce')
                        if pd.isna(alignment_val):
                            alignment_val = 0.0
                        break
                alignment_matrix.loc[bu1, bu2] = alignment_val
    
    return alignment_matrix

def create_smartness_comparison(summary_df):
    """Create bar chart comparing SMARTNESS across BUs"""
    summary_df = summary_df.sort_values('Average SMARTNESS %', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=summary_df['Average SMARTNESS %'],
        y=summary_df['Business Unit'],
        orientation='h',
        marker=dict(
            color='#667eea',
            line=dict(color='rgba(0,0,0,0.3)', width=1)
        ),
        text=summary_df['Average SMARTNESS %'].apply(lambda x: f'{x:.1f}%'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title="SMARTNESS Scores by Business Unit",
        xaxis_title="SMARTNESS %",
        yaxis_title="",
        height=500,
        showlegend=False,
        xaxis=dict(range=[0, 100]),
        font=dict(size=12)
    )
    
    return fig

def create_radar_chart(bu_name, bu_data):
    """Create radar chart for BU alignment with others"""
    df = bu_data[bu_name]
    
    # Extract alignment data (skip SMARTNESS section)
    alignment_data = df[df.iloc[:, 0].notna() & (df.iloc[:, 0] != 'Goal ID')]
    
    if len(alignment_data) > 0:
        categories = alignment_data.iloc[:, 0].tolist()
        values = alignment_data.iloc[:, 1].tolist()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=bu_name,
            line=dict(color='#667eea', width=2),
            fillcolor='rgba(102, 126, 234, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title=f"{bu_name} Alignment with Other BUs",
            height=500
        )
        
        return fig
    return None

def main():
    # Header
    st.markdown('<div class="main-header">BU SMARTNESS & Alignment Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive Analysis of Business Unit Goals</div>', unsafe_allow_html=True)
    
    # Load data from default file
    default_file = "/home/aicoe/Desktop/smart-hr-v4/xlsx_data/BU_SMARTNESS_ALIGNMENT_REPORT_20260507_171137.xlsx"
    summary_df, bu_data = load_excel_data(default_file)
    
    if summary_df is None or bu_data is None:
        st.error("Failed to load data. Please check the file format.")
        return
    
    # Key Metrics
    st.markdown("---")
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total BUs</div>
            <div class="metric-value">{len(summary_df)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_goals = summary_df['Total Goals'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Goals</div>
            <div class="metric-value">{total_goals}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_smartness = summary_df['Average SMARTNESS %'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg SMARTNESS</div>
            <div class="metric-value">{avg_smartness:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📊 Overview", "🔗 Alignment Matrix"])
    
    with tab1:
        st.subheader("Business Unit Overview")
        
        # BU SMARTNESS table
        st.markdown("#### SMARTNESS Scores by Business Unit")
        display_summary = summary_df[['Business Unit', 'Average SMARTNESS %']].copy()
        display_summary = display_summary.sort_values('Average SMARTNESS %', ascending=False)
        display_summary['Average SMARTNESS %'] = display_summary['Average SMARTNESS %'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_summary, use_container_width=True, height=400)
        
        st.markdown("---")
        
        # SMARTNESS comparison chart
        fig = create_smartness_comparison(summary_df)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Summary statistics
        st.subheader("📊 Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Highest SMARTNESS", f"{summary_df['Average SMARTNESS %'].max():.1f}%")
        with col2:
            st.metric("Lowest SMARTNESS", f"{summary_df['Average SMARTNESS %'].min():.1f}%")
        with col3:
            st.metric("Standard Deviation", f"{summary_df['Average SMARTNESS %'].std():.1f}%")
    
    with tab2:
        st.subheader("Cross-BU Alignment Analysis")
        
        alignment_matrix = create_symmetric_alignment_matrix(bu_data)
        
        # BU selector for focused view
        st.markdown("### Select Business Unit")
        selected_bu_align = st.selectbox(
            "Choose a BU to view its alignment with others",
            list(alignment_matrix.index),
            key='alignment_bu_selector'
        )
        
        if selected_bu_align:
            st.markdown(f"### {selected_bu_align} - Alignment with Other BUs")
            
            # Get alignment data for selected BU
            bu_alignments = []
            for other_bu in alignment_matrix.columns:
                if other_bu != selected_bu_align:
                    align_val = alignment_matrix.loc[selected_bu_align, other_bu]
                    if pd.notna(align_val):
                        bu_alignments.append({
                            'Business Unit': other_bu,
                            'Alignment %': align_val
                        })
            
            if bu_alignments:
                bu_align_df = pd.DataFrame(bu_alignments).sort_values('Alignment %', ascending=False)
                
                # Display as table first
                st.markdown("#### Detailed Alignment Data")
                display_df = bu_align_df[['Business Unit', 'Alignment %']].copy()
                display_df['Alignment %'] = display_df['Alignment %'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(display_df, use_container_width=True, height=400)
                
                st.markdown("---")
                
                # Create bar chart
                fig = px.bar(
                    bu_align_df,
                    x='Alignment %',
                    y='Business Unit',
                    orientation='h',
                    title=f"{selected_bu_align} Alignment Overview",
                    text='Alignment %'
                )
                fig.update_traces(
                    marker_color='#667eea',
                    texttemplate='%{text:.1f}%',
                    textposition='outside'
                )
                fig.update_layout(height=500, yaxis_title="", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #6c757d; padding: 1rem;">
        <p>🔒 <strong>Privacy Protected:</strong> No goal content is displayed in this dashboard</p>
        <p>📊 Data Source: BU SMARTNESS & Alignment Report | Generated with Azure OpenAI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
