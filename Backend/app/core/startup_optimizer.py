"""
Startup Optimizer
Suppresses unnecessary warnings and optimizes backend startup time
"""

import os
import warnings
import logging

def optimize_startup():
    """
    Optimize backend startup by:
    1. Suppressing unnecessary warnings
    2. Setting environment variables for faster loading
    3. Configuring logging levels
    """
    
    # Suppress TensorFlow warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logging
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN messages
    
    # Suppress other warnings
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # Configure logging to be less verbose
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('faiss').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Optimize torch for CPU
    try:
        import torch
        torch.set_num_threads(4)  # Limit threads for faster startup
    except ImportError:
        pass

# Call on module import
optimize_startup()
