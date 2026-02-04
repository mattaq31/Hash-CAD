import streamlit as st
import threading
import queue

# Constants for default values
START_MIN_ON = -13.0
START_MAX_ON = -10.0
START_OFFTARGET = -7.5

def init_session_state():
    if "busy" not in st.session_state:
        st.session_state.busy = False
    if "stop_event" not in st.session_state:
        st.session_state.stop_event = threading.Event()
    
    # Computation flags
    if "run_compute_1" not in st.session_state:
        st.session_state.run_compute_1 = False
    if "run_compute_2" not in st.session_state:
        st.session_state.run_compute_2 = False
    if "run_compute_3" not in st.session_state:
        st.session_state.run_compute_3 = False

    if "registry" not in st.session_state:
        st.session_state.registry = None

    # Analysis Results
    if "on_e_pilot" not in st.session_state:
        st.session_state.on_e_pilot = None
    if "off_e_pilot" not in st.session_state:
        st.session_state.off_e_pilot = None
    
    if "on_e_range" not in st.session_state:
        st.session_state.on_e_range = None
    if "off_e_range" not in st.session_state:
        st.session_state.off_e_range = None

    if "orthogonal_seq_pairs" not in st.session_state:
        st.session_state.orthogonal_seq_pairs = None
    if "search_completed" not in st.session_state:
        st.session_state.search_completed = False
    if "search_duration" not in st.session_state:
        st.session_state.search_duration = 0.0
    
    # Committed parameters
    if "min_ontarget" not in st.session_state:
        st.session_state.min_ontarget = START_MIN_ON
    if "max_ontarget" not in st.session_state:
        st.session_state.max_ontarget = START_MAX_ON
    if "offtarget_limit" not in st.session_state:
        st.session_state.offtarget_limit = START_OFFTARGET

    # Drafts
    if "draft_min_ontarget" not in st.session_state:
        st.session_state.draft_min_ontarget = float(st.session_state.min_ontarget)
    if "draft_max_ontarget" not in st.session_state:
        st.session_state.draft_max_ontarget = float(st.session_state.max_ontarget)
    if "draft_offtarget_limit" not in st.session_state:
        st.session_state.draft_offtarget_limit = float(st.session_state.offtarget_limit)

    # Queues and buffers
    if "search_queue" not in st.session_state:
        st.session_state.search_queue = queue.Queue()
    if "search_running" not in st.session_state:
        st.session_state.search_running = False
    if "search_thread" not in st.session_state:
        st.session_state.search_thread = None
    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False
        
    if "log_queue" not in st.session_state:
        st.session_state.log_queue = queue.Queue()
    if "log_buffer" not in st.session_state:
        st.session_state.log_buffer = []

    if "pilot_queue" not in st.session_state:
        st.session_state.pilot_queue = queue.Queue()
    if "pilot_running" not in st.session_state:
        st.session_state.pilot_running = False
    if "pilot_thread" not in st.session_state:
        st.session_state.pilot_thread = None

    if "refine_queue" not in st.session_state:
        st.session_state.refine_queue = queue.Queue()
    if "refine_running" not in st.session_state:
        st.session_state.refine_running = False
    if "refine_thread" not in st.session_state:
        st.session_state.refine_thread = None
    
    if "final_cache_ready" not in st.session_state:
        st.session_state.final_cache_ready = False
    if "final_fig" not in st.session_state:
        st.session_state.final_fig = None
