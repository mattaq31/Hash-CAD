import logging
import streamlit as st

class QueueLogHandler(logging.Handler):
    def __init__(self, q):
        super().__init__()
        self.q = q

    def emit(self, record):
        try:
            self.q.put(self.format(record))
        except Exception:
            pass

def setup_logger(log_queue):
    logger = logging.getLogger("orthoseq")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    UI_HANDLER_NAME = "orthoseq_ui_queue"
    existing = None
    for h in logger.handlers:
        if getattr(h, "name", None) == UI_HANDLER_NAME:
            existing = h
            break

    if existing is None:
        ui_handler = QueueLogHandler(log_queue)
        ui_handler.name = UI_HANDLER_NAME
        ui_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
        logger.addHandler(ui_handler)
    else:
        if getattr(existing, "q", None) is not log_queue:
            existing.q = log_queue
    return logger

def drain_log_queue():
    while not st.session_state.log_queue.empty():
        st.session_state.log_buffer.append(st.session_state.log_queue.get())
