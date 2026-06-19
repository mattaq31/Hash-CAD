import streamlit as st
import threading
import queue

# Constants for default values
START_MIN_ON = -13.0
START_MAX_ON = -10.0
START_OFFTARGET = -7.5
START_SELF_ENERGY = -2.0

def init_session_state():
    if "_defaults_seeded" not in st.session_state:
        st.session_state.min_ontarget = START_MIN_ON
        st.session_state.max_ontarget = START_MAX_ON
        st.session_state.offtarget_limit = START_OFFTARGET
        st.session_state.self_energy_limit = START_SELF_ENERGY
        st.session_state._defaults_seeded = True

    if "busy" not in st.session_state:
        st.session_state.busy = False
    if "stop_event" not in st.session_state:
        st.session_state.stop_event = threading.Event()
    if "checkpoint_event" not in st.session_state:
        st.session_state.checkpoint_event = threading.Event()
    if "input_invalid" not in st.session_state:
        st.session_state.input_invalid = False
    
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
    if "self_e_pilot" not in st.session_state:
        st.session_state.self_e_pilot = None
    
    if "on_e_range" not in st.session_state:
        st.session_state.on_e_range = None
    if "off_e_range" not in st.session_state:
        st.session_state.off_e_range = None
    if "self_e_range" not in st.session_state:
        st.session_state.self_e_range = None

    if "orthogonal_seq_pairs" not in st.session_state:
        st.session_state.orthogonal_seq_pairs = None
    if "search_run_data" not in st.session_state:
        st.session_state.search_run_data = None
    if "search_completed" not in st.session_state:
        st.session_state.search_completed = False
    if "search_duration" not in st.session_state:
        st.session_state.search_duration = 0.0
    if "search_report_path" not in st.session_state:
        st.session_state.search_report_path = None
    
    # Committed parameters
    if "min_ontarget" not in st.session_state:
        st.session_state.min_ontarget = START_MIN_ON
    if "max_ontarget" not in st.session_state:
        st.session_state.max_ontarget = START_MAX_ON
    if "offtarget_limit" not in st.session_state:
        st.session_state.offtarget_limit = START_OFFTARGET
    if "self_energy_limit" not in st.session_state:
        st.session_state.self_energy_limit = START_SELF_ENERGY

    # Inputs / drafts used by tabs

    # Queues and buffers
    if "search_queue" not in st.session_state:
        st.session_state.search_queue = queue.Queue()
    if "search_running" not in st.session_state:
        st.session_state.search_running = False
    if "search_thread" not in st.session_state:
        st.session_state.search_thread = None
    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False
    if "checkpoint_requested" not in st.session_state:
        st.session_state.checkpoint_requested = False
    if "latest_checkpoint_initial_orthogonal" not in st.session_state:
        st.session_state.latest_checkpoint_initial_orthogonal = None
    if "latest_checkpoint_candidate_count" not in st.session_state:
        st.session_state.latest_checkpoint_candidate_count = None
    if "latest_checkpoint_candidate_orthogonal" not in st.session_state:
        st.session_state.latest_checkpoint_candidate_orthogonal = None
    if "latest_checkpoint_estimate" not in st.session_state:
        st.session_state.latest_checkpoint_estimate = None
        
    if "log_queue" not in st.session_state:
        st.session_state.log_queue = queue.Queue()
    if "log_buffer" not in st.session_state:
        st.session_state.log_buffer = []
    if "log_console_height_px" not in st.session_state:
        st.session_state.log_console_height_px = 180
    if "log_visible_line_count" not in st.session_state:
        st.session_state.log_visible_line_count = 3000
    if "log_buffer_max_lines" not in st.session_state:
        st.session_state.log_buffer_max_lines = 50000

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
    if "refine_error" not in st.session_state:
        st.session_state.refine_error = None
    
    if "final_cache_ready" not in st.session_state:
        st.session_state.final_cache_ready = False
    if "final_fig" not in st.session_state:
        st.session_state.final_fig = None
    if "final_self_fig" not in st.session_state:
        st.session_state.final_self_fig = None
    if "search_error" not in st.session_state:
        st.session_state.search_error = None
    if "subset_size_search" not in st.session_state:
        st.session_state.subset_size_search = 450
    if "search_vc_max_iterations" not in st.session_state:
        st.session_state.search_vc_max_iterations = 5000
    if "search_prune_fraction" not in st.session_state:
        st.session_state.search_prune_fraction = 0.2
    if "pilot_size" not in st.session_state:
        st.session_state.pilot_size = 50
    if "refine_size" not in st.session_state:
        st.session_state.refine_size = 50
    if "selection_helper_conc_nm" not in st.session_state:
        st.session_state.selection_helper_conc_nm = 1000.0
    if "selection_helper_assoc_fig" not in st.session_state:
        st.session_state.selection_helper_assoc_fig = None
    if "selection_helper_secondary_fig" not in st.session_state:
        st.session_state.selection_helper_secondary_fig = None
    if "loaded_report_metadata" not in st.session_state:
        st.session_state.loaded_report_metadata = None
    if "loaded_report_name" not in st.session_state:
        st.session_state.loaded_report_name = None
    if "loaded_report_pair_count" not in st.session_state:
        st.session_state.loaded_report_pair_count = None
    if "loaded_report_fig" not in st.session_state:
        st.session_state.loaded_report_fig = None
    if "loaded_report_self_fig" not in st.session_state:
        st.session_state.loaded_report_self_fig = None
    if "loaded_report_on_off_pdf_path" not in st.session_state:
        st.session_state.loaded_report_on_off_pdf_path = None
    if "loaded_report_self_pdf_path" not in st.session_state:
        st.session_state.loaded_report_self_pdf_path = None
    if "loaded_report_error" not in st.session_state:
        st.session_state.loaded_report_error = None
    if "use_seqwalk" not in st.session_state:
        st.session_state.use_seqwalk = False
    if "seqwalk_k" not in st.session_state:
        st.session_state.seqwalk_k = 6
    if "seqwalk_rcfree" not in st.session_state:
        st.session_state.seqwalk_rcfree = True
