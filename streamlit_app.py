
import streamlit as st
import requests
import time
import threading
from typing import List, Dict
import pandas as pd
from datetime import datetime
from config import REQUEST_TIMEOUT, USER_AGENT, DEFAULT_URLS, DEFAULT_INTERVAL
from utils import validate_urls, format_duration

# Page configuration
st.set_page_config(
    page_title="URL Pinger Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'ping_results' not in st.session_state:
    st.session_state.ping_results = []
if 'is_pinging' not in st.session_state:
    st.session_state.is_pinging = False
if 'ping_thread' not in st.session_state:
    st.session_state.ping_thread = None
if 'urls' not in st.session_state:
    st.session_state.urls = DEFAULT_URLS
if 'interval' not in st.session_state:
    st.session_state.interval = DEFAULT_INTERVAL

class StreamlitURLPinger:
    """URL Pinger class adapted for Streamlit."""
    
    def __init__(self):
        self.headers = {'User-Agent': USER_AGENT}
    
    def ping_url(self, url: str, retries: int = 2) -> Dict:
        """Ping a single URL and return result."""
        result = {
            'url': url,
            'timestamp': datetime.now(),
            'status': 'Failed',
            'response_time': None,
            'status_code': None,
            'error': None
        }
        
        for attempt in range(retries + 1):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=self.headers)
                response_time = time.time() - start_time
                
                result.update({
                    'status': 'Success' if response.status_code == 200 else 'Failed',
                    'response_time': response_time,
                    'status_code': response.status_code
                })
                
                if response.status_code == 200:
                    break
                    
            except requests.exceptions.Timeout:
                if attempt < retries:
                    time.sleep(2)
                else:
                    result['error'] = f"Timeout after {retries + 1} attempts"
            except requests.RequestException as e:
                if attempt < retries:
                    time.sleep(2)
                else:
                    result['error'] = str(e)
        
        return result
    
    def ping_urls_cycle(self, urls: List[str]):
        """Ping all URLs in one cycle."""
        results = []
        for url in urls:
            if not st.session_state.is_pinging:
                break
            result = self.ping_url(url)
            results.append(result)
            st.session_state.ping_results.append(result)
        
        # Keep only last 100 results to prevent memory issues
        if len(st.session_state.ping_results) > 100:
            st.session_state.ping_results = st.session_state.ping_results[-100:]
        
        return results

def ping_worker(urls: List[str], interval: int):
    """Background worker for continuous pinging."""
    pinger = StreamlitURLPinger()
    
    while st.session_state.is_pinging:
        pinger.ping_urls_cycle(urls)
        
        # Sleep in chunks to allow for responsive stopping
        for _ in range(interval):
            if not st.session_state.is_pinging:
                break
            time.sleep(1)

def start_pinging():
    """Start the pinging process."""
    if not st.session_state.is_pinging:
        st.session_state.is_pinging = True
        st.session_state.ping_thread = threading.Thread(
            target=ping_worker,
            args=(st.session_state.urls, st.session_state.interval),
            daemon=True
        )
        st.session_state.ping_thread.start()

def stop_pinging():
    """Stop the pinging process."""
    st.session_state.is_pinging = False

def main():
    """Main Streamlit app."""
    
    # Header
    st.title("🌐 URL Pinger Dashboard")
    st.markdown("Monitor your URLs with real-time pinging and status tracking")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # URL Management
        st.subheader("URLs to Monitor")
        
        # Add new URL
        new_url = st.text_input("Add new URL:", placeholder="https://example.com")
        if st.button("Add URL") and new_url:
            valid_urls = validate_urls([new_url])
            if valid_urls:
                if new_url not in st.session_state.urls:
                    st.session_state.urls.append(new_url)
                    st.success(f"Added: {new_url}")
                else:
                    st.warning("URL already exists")
            else:
                st.error("Invalid URL format")
        
        # Display current URLs
        if st.session_state.urls:
            st.write("Current URLs:")
            for i, url in enumerate(st.session_state.urls):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(url)
                with col2:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.urls.pop(i)
                        st.rerun()
        
        # Interval setting
        st.subheader("Ping Settings")
        st.session_state.interval = st.slider(
            "Ping Interval (seconds)",
            min_value=10,
            max_value=3600,
            value=st.session_state.interval,
            step=10
        )
        
        st.write(f"Interval: {format_duration(st.session_state.interval)}")
        st.write(f"Timeout: {REQUEST_TIMEOUT}s per request")
        
        # Control buttons
        st.subheader("Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start", disabled=st.session_state.is_pinging or not st.session_state.urls):
                start_pinging()
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop", disabled=not st.session_state.is_pinging):
                stop_pinging()
                st.rerun()
        
        # Status indicator
        if st.session_state.is_pinging:
            st.success("🟢 Pinging active")
        else:
            st.info("🔴 Pinging stopped")
        
        # Clear results
        if st.button("Clear Results"):
            st.session_state.ping_results = []
            st.rerun()
    
    # Main content area
    if not st.session_state.urls:
        st.warning("No URLs configured. Please add URLs in the sidebar to start monitoring.")
        return
    
    # Summary statistics
    if st.session_state.ping_results:
        col1, col2, col3, col4 = st.columns(4)
        
        recent_results = st.session_state.ping_results[-len(st.session_state.urls):]
        successful = len([r for r in recent_results if r['status'] == 'Success'])
        failed = len([r for r in recent_results if r['status'] == 'Failed'])
        avg_response_time = sum([r['response_time'] for r in recent_results if r['response_time']]) / len([r for r in recent_results if r['response_time']]) if recent_results else 0
        
        with col1:
            st.metric("Total URLs", len(st.session_state.urls))
        
        with col2:
            st.metric("Last Cycle - Success", successful, delta=None)
        
        with col3:
            st.metric("Last Cycle - Failed", failed, delta=None)
        
        with col4:
            st.metric("Avg Response Time", f"{avg_response_time:.2f}s" if avg_response_time else "N/A")
    
    # Current status table
    st.subheader("Current Status")
    
    if st.session_state.ping_results:
        # Get latest result for each URL
        latest_results = {}
        for result in reversed(st.session_state.ping_results):
            if result['url'] not in latest_results:
                latest_results[result['url']] = result
        
        # Create status dataframe
        status_data = []
        for url in st.session_state.urls:
            if url in latest_results:
                result = latest_results[url]
                status_data.append({
                    'URL': url,
                    'Status': result['status'],
                    'Response Time': f"{result['response_time']:.2f}s" if result['response_time'] else "N/A",
                    'Status Code': result['status_code'] or "N/A",
                    'Last Checked': result['timestamp'].strftime('%H:%M:%S'),
                    'Error': result['error'] or ""
                })
            else:
                status_data.append({
                    'URL': url,
                    'Status': 'Not checked',
                    'Response Time': "N/A",
                    'Status Code': "N/A",
                    'Last Checked': "N/A",
                    'Error': ""
                })
        
        df = pd.DataFrame(status_data)
        
        # Style the dataframe
        def color_status(val):
            if val == 'Success':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Failed':
                return 'background-color: #f8d7da; color: #721c24'
            else:
                return 'background-color: #fff3cd; color: #856404'
        
        styled_df = df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("No ping results yet. Start pinging to see status updates.")
    
    # Detailed results
    if st.session_state.ping_results:
        st.subheader("Recent Ping History")
        
        # Show last 20 results
        recent_results = st.session_state.ping_results[-20:]
        history_data = []
        
        for result in reversed(recent_results):
            history_data.append({
                'Timestamp': result['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'URL': result['url'],
                'Status': result['status'],
                'Response Time': f"{result['response_time']:.2f}s" if result['response_time'] else "N/A",
                'Status Code': result['status_code'] or "N/A",
                'Error': result['error'] or ""
            })
        
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    
    # Auto-refresh when pinging is active
    if st.session_state.is_pinging:
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    main()
