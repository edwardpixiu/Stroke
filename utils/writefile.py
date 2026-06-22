import numpy as np
import os

def write_eeg(eeg:np.ndarray, save_filepath:str):
    """
    Write the event-related part eeg data in to .npy
    
    Args:
        eeg (np.ndarray): Event-related part eeg data
    Returns:
        eeg save path
    """
    
    try:
        if not os.path.exists(os.path.dirname(save_filepath)):
            os.makedirs(os.path.dirname(save_filepath), exist_ok=True)
    except PermissionError as P:
        raise PermissionError(f"[Error]: Fail to find or create the directory:{os.path.dirname(save_filepath)}")
    np.save(save_filepath, eeg)
    print(f"[Info]: The Event-related eeg data had been save into:{save_filepath}")