import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from organizer import organize_files 
from datetime import datetime
from pathlib import Path


# Import Tkinter for the native dialog
import tkinter as tk
from tkinter import filedialog
import platform

# --- Tkinter Folder Dialog Function ---
def ask_for_folder_path():
    """Opens the native OS folder dialog and returns the selected path."""
    root = tk.Tk()
    root.withdraw() 
    if platform.system() != 'Linux':
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass 

    folder_path = filedialog.askdirectory(title="Select Folder to Clean")

    root.destroy()
    return folder_path.replace('\\', '/') if folder_path else ""


# Streamlit page configuration
st.set_page_config(
    page_title="File Organization (Web)", 
    layout="wide",
    initial_sidebar_state="auto"
)

# --- UI Customization (CSS Injection) for Dark Mode ---
st.markdown("""
<style>
/* Dark Mode Background */
.stApp {
    background-color: #1e1e2d; /* Dark Blue/Gray */
    color: #f0f0f0; /* Light Text Color */
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
}

/* Center and style the main title */
.stApp > header {
    background-color: transparent;
}
.css-1ht1j4b { 
    text-align: center;
    text-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    color: #4ecdc4; /* Cyan/Teal Title color */
}

/* Style main content containers */
.css-1lcbmhc, .css-1d374r, .stProgress > div > div > div > div {
    background-color: #2a2a40; /* Slightly lighter dark background for elements */
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

/* Metric labels color adjustment */
[data-testid="stMetricLabel"] {
    color: #bdbdbd; 
}

/* Fix Selectbox, Checkbox labels and Help text color for dark mode */
.stSelectbox label, .stCheckbox label, .stCheckbox p, .stAlert p {
    color: #ffffff !important; 
    font-weight: bold;
}

/* Style the main action button (ORGANIZE FILES!) */
div.stButton > button:first-child {
    background-color: #ff6b6b; /* Reddish color for action button */
    color: #1e1e2d; /* Dark text on button */
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    transition: all 0.2s ease-in-out;
}
div.stButton > button:first-child:hover {
    background-color: #ee5253; /* Darker red on hover */
    transform: translateY(-2px);
}

/* *** નવો ફેરફાર: ડાઉનલોડ બટનનો કલર *** */
div[data-testid="stDownloadButton"] > button:first-child {
    background-color: #4ecdc4 !important; /* Cyan/Teal color */
    color: #1e1e2d !important; /* Dark text */
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


# --- UI Header ---
st.title("📁 File Organization (Web App)") 
st.markdown("---")


# --- Session State Initialization ---
if 'folder_path' not in st.session_state:
    st.session_state['folder_path'] = ""
if 'last_analytics' not in st.session_state:
    st.session_state['last_analytics'] = {}
if 'last_logs' not in st.session_state:
    st.session_state['last_logs'] = []


# --- Button Callback Function ---
def select_folder_callback():
    """Handles button click, calls dialog, and updates session state."""
    selected_path = ask_for_folder_path()
    if selected_path:
        st.session_state.folder_path = selected_path
        st.rerun() 


st.markdown("### 📂 Folder Selection and Options")

col1, col2 = st.columns([3, 1])

with col1:
    
    # Folder Select Button using the Tkinter dialog
    st.button(
        "📁 Browse Folder (Select Folder)",
        on_click=select_folder_callback,
        use_container_width=True
    )
    
    # Text Input to display and confirm path (Disabled)
    folder_path_display = st.text_input(
        "Selected Folder Path:",
        value=st.session_state.folder_path,
        disabled=True 
    )
    
    # Display current path
    if st.session_state.folder_path:
        st.success(f"**Selected Folder:** `{st.session_state.folder_path}`")
    else:
        st.warning("Please select a folder to proceed.")


# --- Organization Options (unchanged) ---

with col2:
    organize_mode = st.selectbox(
        "Organization Mode:",
        ['Category Only', 'Category / Year', 'Category / Year-Month'],
        index=0,
        help="How files should be organized inside category folders."
    )
    
    check_duplicates = st.checkbox(
        "Find and Remove Duplicates",
        value=True,
        help="Identifies and moves duplicate files to a 'Duplicates' folder."
    )

st.markdown("---")

# --- 3. Start Button and Process Logic (unchanged) ---

if st.session_state.folder_path and st.button("📁 ORGANIZE FILES!", use_container_width=True):
    
    cleaned_path = st.session_state.folder_path
    
    if not os.path.isdir(cleaned_path):
        st.error(f"Error: Folder path not found or is invalid: {cleaned_path}")
    else:
        st.info("Cleaning process started...")
        
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        def emit_progress(percent, text):
            progress_placeholder.progress(percent, text=text)
            status_placeholder.text(f"Status: {text}")

        with st.spinner('Running file organization logic...'):
            logs, analytics = organize_files(
                cleaned_path, 
                organize_mode,
                check_duplicates,
                emit_progress
            )
        
        st.session_state['last_analytics'] = analytics
        st.session_state['last_logs'] = logs
        st.session_state['cleaned_folder_path'] = cleaned_path 
        
        progress_placeholder.progress(100, text="Completed!")
        status_placeholder.text("Status: ✅ Cleaning Completed! Running analysis...")
        st.rerun() 

# --- 4. Results Display (Horizontal Bar Chart Added) ---

if st.session_state.last_analytics:
    analytics = st.session_state.last_analytics
    logs = st.session_state.last_logs
    
    st.markdown("### 📊 Cleaning Summary & Analytics")

    total_files = analytics.get("total_files", 0)
    time_taken = analytics.get("time_taken_sec", 0.0)
    categories = analytics.get("categories", {})
    duplicates_removed = analytics.get("duplicates_removed", 0)
    space_saved_mb = analytics.get("space_saved_bytes", 0) / (1024 * 1024)
    
    report_folder_path = st.session_state.get('cleaned_folder_path', 'N/A')

    # Display Summary using columns
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.metric(label="🎯 Total Files Processed", value=total_files)
        st.metric(label="⏱ Time Taken", value=f"{time_taken:.2f} sec")
    
    with summary_col2:
        st.metric(label="🧹 Duplicates Removed", value=duplicates_removed)
        st.metric(label="💾 Estimated Space Saved", value=f"{space_saved_mb:.2f} MB")
        
    st.markdown("---")

    # --- 5. Matplotlib Horizontal Bar Chart ---
    st.markdown("#### 📊 File Category Distribution")
    
    plt.style.use('dark_background') 

    if categories:
        # Create DataFrames for easy plotting
        df = pd.DataFrame(list(categories.items()), columns=['Category', 'Count'])
        df = df.sort_values('Count', ascending=False)
        
        # Determine chart dimensions
        num_categories = len(categories)
        fig_height = 2 
        
        # Set figure size (width=6, height=2)
        fig, ax = plt.subplots(figsize=(6, fig_height)) 
        
        # Horizontal Bar Plot
        ax.barh(df['Category'], df['Count'], color=plt.cm.get_cmap('viridis')(range(num_categories)), height=0.5) 
        
        # Add count labels next to the bars
        for index, value in enumerate(df['Count']):
            ax.text(value, index, f" {value}", va='center', color='white')

        ax.set_xlabel('Number of Files')
        ax.set_ylabel('File Category')
        ax.set_title('File Category Distribution by Count', fontsize=12) 
        
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No files were categorized or moved.")
    
    plt.style.use('default') 

    # --- 6. Full Log and Export ---
    st.markdown("### 📜 Recent Activity Log")
    
    with st.expander("Show Full Log"):
        st.code("\n".join(logs), language='text')

    # Report Content 
    cat_list = ", ".join(f'{k}: {v} files' for k, v in categories.items())
    
    report_content = (
        "===  File organazation - Cleaning Report ===\n"
        "Date: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
        "Folder Cleaned: " + report_folder_path + "\n"
        "----------------------------------------------------\n"
        "Total files processed: " + str(total_files) + "\n"
        "Time taken: " + f"{time_taken:.2f} seconds\n"
        "Duplicates Removed: " + str(duplicates_removed) + "\n"
        "Estimated Space Saved: " + f"{space_saved_mb:.2f} MB\n"
        "New/Updated Folders: " + cat_list + "\n"
        "================== FULL LOG ==================\n"
        + "\n".join(logs) + "\n"
        "==============================================\n"
    )

    st.download_button(
        label="\u2b07\ufe0f Download Full Report (.txt)", 
        data=report_content,
        file_name="cleaning_report.txt",
        mime="text/plain"
    )