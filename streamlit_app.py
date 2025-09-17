"""
Streamlit Frontend for Email Automation Pipeline
"""

import streamlit as st
import pandas as pd
import requests
import io
import os
from datetime import datetime
import time
import zipfile

# Set page config
st.set_page_config(
    page_title="TrueFoundry Sales Email Automation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Backend API configuration
BACKEND_URL = "http://127.0.0.1:8080/api"  # FastAPI backend URL for unified app

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 TrueFoundry Sales Email Automation</h1>', unsafe_allow_html=True)
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("### 📋 About This Tool")
        st.markdown("""
        This tool generates comprehensive sales research and personalized emails for prospects using AI.
        
        **Features:**
        - 🔍 Deep research analysis (27+ categories)
        - 📧 Personalized email generation  
        - 📊 Multiple output formats
        - ⚡ Unlimited batch processing (perfect for overnight runs)
        - 🌙 No timeouts - process large files overnight
        """)
        
        st.markdown("### 📝 CSV Format Required")
        st.markdown("""
        Your CSV must contain these columns:
        - `person_name`
        - `company_name`
        - `linkedin_url`
        """)
        
        # Sample CSV download
        if st.button("📥 Download Sample CSV"):
            sample_data = pd.DataFrame({
                'person_name': ['Karl Martin', 'John Smith'],
                'company_name': ['integrate.ai', 'TechCorp AI'],
                'linkedin_url': ['https://www.linkedin.com/in/karlmartin0', 'https://linkedin.com/in/johnsmith']
            })
            csv = sample_data.to_csv(index=False)
            st.download_button(
                label="📄 sample_prospects.csv",
                data=csv,
                file_name="sample_prospects.csv",
                mime="text/csv"
            )

    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h2 class="section-header">📤 Upload Prospect Data</h2>', unsafe_allow_html=True)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a CSV file with prospect information",
            type=['csv'],
            help="Upload a CSV file with columns: person_name, company_name, linkedin_url"
        )
        
        # Clear cache button for troubleshooting
        col_clear1, col_clear2 = st.columns(2)
        with col_clear1:
            if st.button("🧹 Clear Cache & Reset", help="Clear any cached errors or data"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col_clear2:
            if st.button("🗑️ Clear Downloads", help="Clear download results to start fresh"):
                if 'processing_result' in st.session_state:
                    del st.session_state.processing_result
                if 'processing_stats' in st.session_state:
                    del st.session_state.processing_stats
                st.rerun()
        
        if uploaded_file is not None:
            # Clear any previous error states
            if 'upload_error' in st.session_state:
                del st.session_state.upload_error
                
            # Validate CSV format
            try:
                df = pd.read_csv(uploaded_file)
                required_columns = ['person_name', 'company_name', 'linkedin_url']
                
                if all(col in df.columns for col in required_columns):
                    st.markdown('<div class="success-box">✅ CSV file validated successfully!</div>', unsafe_allow_html=True)
                    
                    # Show preview
                    st.markdown("### 👀 Data Preview")
                    st.dataframe(df.head(), use_container_width=True)
                    st.info(f"📊 **Total prospects to process:** {len(df)}")
                    
                    # Processing section
                    st.markdown('<h2 class="section-header">⚡ Process Data</h2>', unsafe_allow_html=True)
                    
                    # Process button
                    if st.button("🚀 Generate Research & Emails", type="primary", use_container_width=True):
                        process_prospects(uploaded_file, df)
                        
                else:
                    missing_cols = [col for col in required_columns if col not in df.columns]
                    st.markdown(f'<div class="error-box">❌ Missing required columns: {", ".join(missing_cols)}</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f'<div class="error-box">❌ Error reading CSV file: {str(e)}</div>', unsafe_allow_html=True)
    
    # Display download results if available (persists across page refreshes)
    if 'processing_result' in st.session_state:
        display_results()
    
    with col2:
        st.markdown('<h2 class="section-header">📊 Processing Stats</h2>', unsafe_allow_html=True)
        
        # Display processing statistics if available
        if 'processing_stats' in st.session_state:
            stats = st.session_state.processing_stats
            
            st.metric("Prospects Processed", stats.get('total_prospects', 0))
            st.metric("Processing Time", f"{stats.get('processing_time', 0):.1f}s")
            st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
        else:
            st.markdown('<div class="info-box">📈 Processing statistics will appear here after running the pipeline.</div>', unsafe_allow_html=True)


def process_prospects(uploaded_file, df):
    """Process prospects through the email automation pipeline"""
    
    # Reset file pointer
    uploaded_file.seek(0)
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        start_time = time.time()
        
        # Step 1: Upload file to backend
        status_text.text("📤 Uploading file to backend...")
        progress_bar.progress(10)
        
        files = {"file": ("prospects.csv", uploaded_file.getvalue(), "text/csv")}
        
        # Step 2: Process file
        status_text.text("🔍 Processing prospects (perfect for overnight runs with large files)...")
        progress_bar.progress(30)
        
        # Call backend API - no timeout for overnight processing
        response = requests.post(f"{BACKEND_URL}/process", files=files)
        
        if response.status_code == 200:
            progress_bar.progress(90)
            status_text.text("✅ Processing completed successfully!")
            
            # Get result data
            result = response.json()
            
            # Step 3: Display results and download options
            progress_bar.progress(100)
            processing_time = time.time() - start_time
            
            # Store stats in session state
            st.session_state.processing_stats = {
                'total_prospects': len(df),
                'processing_time': processing_time,
                'success_rate': 100.0  # Assuming success if we get here
            }
            
            # Success message
            st.markdown('<div class="success-box">🎉 Email automation pipeline completed successfully!</div>', unsafe_allow_html=True)
            
            # Store results in session state for persistent downloads
            st.session_state.processing_result = result
            
            # Display results
            display_results(result)
            
        elif response.status_code == 400:
            # Bad request - usually validation error
            try:
                error_detail = response.json().get('detail', 'Invalid request')
            except:
                error_detail = response.text
            st.markdown(f'<div class="error-box">❌ Request Error: {error_detail}</div>', unsafe_allow_html=True)
            st.markdown('<div class="info-box">💡 Please check that your CSV has the correct format with columns: person_name, company_name, linkedin_url</div>', unsafe_allow_html=True)
            
        elif response.status_code == 500:
            # Server error
            try:
                error_detail = response.json().get('detail', 'Server error')
            except:
                error_detail = response.text
            st.markdown(f'<div class="error-box">❌ Server Error: {error_detail}</div>', unsafe_allow_html=True)
            if "API" in error_detail:
                st.markdown('<div class="info-box">💡 This might be an issue with the LLM API. Check API key configuration.</div>', unsafe_allow_html=True)
        else:
            # Other errors
            try:
                error_detail = response.json().get('detail', response.text)
            except:
                error_detail = response.text
            st.markdown(f'<div class="error-box">❌ Processing failed (Status {response.status_code}): {error_detail}</div>', unsafe_allow_html=True)
            
    except requests.exceptions.Timeout:
        st.markdown('<div class="error-box">⏰ Processing timed out. Please try with fewer prospects or try again later.</div>', unsafe_allow_html=True)
    except requests.exceptions.ConnectionError:
        st.markdown('<div class="error-box">🔌 Could not connect to backend server. Make sure the API server is running.</div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<div class="error-box">❌ An error occurred: {str(e)}</div>', unsafe_allow_html=True)
    finally:
        progress_bar.empty()
        status_text.empty()


def display_results(result=None):
    """Display processing results and download options"""
    
    # Use session state result if available and no result passed
    if result is None and 'processing_result' in st.session_state:
        result = st.session_state.processing_result
    
    if result is None:
        return
    
    st.markdown('<h2 class="section-header">📥 Download Results</h2>', unsafe_allow_html=True)
    
    # Create download columns
    col1, col2, col3 = st.columns(3)
    
    # Generate timestamp once for consistent file naming and unique keys
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create unique key suffix to prevent duplicate keys across multiple display_results calls
    key_suffix = f"_{timestamp}_{id(result)}"
    
    with col1:
        if 'research_csv' in result:
            st.download_button(
                label="📊 Download Research CSV",
                data=result['research_csv'],
                file_name=f"research_output_{timestamp}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
                key=f"download_research_csv{key_suffix}"
            )
    
    with col2:
        if 'email_txt' in result:
            st.download_button(
                label="📧 Download Email TXT",
                data=result['email_txt'],
                file_name=f"email_output_{timestamp}.txt",
                mime="text/plain",
                type="primary",
                use_container_width=True,
                key=f"download_email_txt{key_suffix}"
            )
    
    with col3:
        if 'research_md' in result:
            st.download_button(
                label="📝 Download Research Markdown",
                data=result['research_md'],
                file_name=f"research_output_{timestamp}.md",
                mime="text/markdown",
                type="secondary",
                use_container_width=True,
                key=f"download_research_md{key_suffix}"
            )
    
    # Display summary
    if 'summary' in result:
        st.markdown('<h3 class="section-header">📋 Processing Summary</h3>', unsafe_allow_html=True)
        summary = result['summary']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Prospects Processed", summary.get('total_prospects', 0))
        with col2:
            st.metric("Research Categories", summary.get('research_categories', 27))
        with col3:
            st.metric("Emails Generated", summary.get('emails_generated', 0))
    
    # Show preview of research data
    if 'research_preview' in result:
        st.markdown('<h3 class="section-header">🔍 Research Preview</h3>', unsafe_allow_html=True)
        preview_df = pd.read_csv(io.StringIO(result['research_preview']))
        st.dataframe(preview_df.head(3), use_container_width=True)
        
        with st.expander("View All Research Categories"):
            st.write("Research includes these categories:")
            categories = [
                "General Report", "AI/ML Initiatives", "Key Challenges", "TrueFoundry Fit", "Personal Details",
                "Executive Urgency", "Regulatory Compliance", "Technical Deployment", "Competitive Stack",
                "Recent AI Posts", "Conference Activity", "Org Map", "Event Activity", "And more..."
            ]
            st.write("• " + "\n• ".join(categories))


def show_backend_status():
    """Check and display backend server status"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("🟢 Backend Server: Online")
        else:
            st.sidebar.error("🔴 Backend Server: Error")
    except:
        st.sidebar.error("🔴 Backend Server: Offline")
        st.sidebar.info("💡 Make sure to run: `uvicorn backend:app --reload`")


if __name__ == "__main__":
    # Check backend status
    show_backend_status()
    
    # Run main app
    main()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "Built with ❤️ using Streamlit | Powered by TrueFoundry LLM Gateway"
        "</div>",
        unsafe_allow_html=True
    )
