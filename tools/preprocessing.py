# Preprocessing follow the MNE-python Pipeline

import os
from copy import deepcopy
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import mne

# Set montage 10-20
def Montage(raw:mne.Info, shows:bool=False):
    """
    make standard montage system 10-20 for mne.raw
    
    Args:
        raw (mne.raw): load from .fif or .vhdr
        shows (boolean): plot sensors if turn on
    Returns:
        raw (mne.raw): raw after set montage system 10-20
    """
    
    montage = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage=montage, on_missing="ignore")
    
    print(f"[Info]: Setting the standard 1020 montage...")
    
    if shows:
        print(f"[Info]: Manually check the sensors...")
        
        fig = raw.plot_sensors(show_names=True, show=False)
        fig.savefig("sensors.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
                
    return raw

# Check the raw data
def Check_Raws(raw:mne.Info, sfreq:int, duration:int=10,simple:bool=True):
    # Due to Linux remote is not supported Interactive GUI
    # Thus we save the segment directly
    # Please check the raw segmented signal or psd follow the path: .\eeg_check\signal .\eeg_check\psd
    
    """
    Check the dipole quality with serveral major time part\n
    Default is 0-10s, 150-160s, 300-310s, and PSD related
    
    Args:
        raw (mne.Info): raw eeg data from .vhdr or .fif
        sfreq (int): sampling rate
        duration (int): check time period
        simple (boolean): if True will output serveral time part or will output all segemented
    Returns:
        None
    """
    
    raw_data = raw.get_data() * 1e6  # V -> µV
    channels = raw.ch_names

    n_parts = raw_data.shape[-1] // (sfreq * duration)
    offset = np.nanpercentile(np.abs(raw_data), 95) * 3

    def plot_save(raw_data: np.ndarray, start_sample: int, end_sample: int, out_png: str):
        out_dir = os.path.dirname(out_png)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        segment = raw_data[:, start_sample:end_sample]
        n_channels = segment.shape[0]

        times = np.arange(start_sample, end_sample) / sfreq

        plt.figure(figsize=(16, max(8, n_channels * 0.25)))

        for ch_idx in range(n_channels):
            plt.plot(
                times,
                segment[ch_idx] + ch_idx * offset,
                linewidth=0.8
            )

        plt.yticks(
            np.arange(n_channels) * offset,
            channels
        )

        plt.xlabel("Time (s)")
        plt.ylabel("Channels")
        plt.title(f"Raw EEG segment: {start_sample / sfreq:.1f}-{end_sample / sfreq:.1f}s")
        plt.tight_layout()
        plt.savefig(out_png, dpi=200)
        plt.close()
        
    if simple:
        part_0_start = 0
        part_0_end = sfreq * duration

        mid_part = n_parts // 2
        part_1_start = mid_part * sfreq * duration
        part_1_end = (mid_part + 1) * sfreq * duration

        last_part = n_parts - 1
        part_2_start = last_part * sfreq * duration
        part_2_end = n_parts * sfreq * duration

        plot_save(
            raw_data,
            part_0_start,
            part_0_end,
            os.path.join("eeg_check", "signal", "raw_0_10.png")
        )

        plot_save(
            raw_data,
            part_1_start,
            part_1_end,
            os.path.join("eeg_check", "signal", f"raw_{mid_part}_{mid_part + 1}.png")
        )

        plot_save(
            raw_data,
            part_2_start,
            part_2_end,
            os.path.join("eeg_check", "signal", f"raw_{last_part}_{last_part + 1}.png")
        )
        
# Handling bad channels
# def Set_Bad_Channels(raw:mne.Info, bad_channel_list:list):
    
    """
    Setting the bad channels manually after view the raw segmented signal check
    
    Args:
        raw (mne.Info): raw data read from .fif / .vhdr
        
    """

def robust_z(x:np.ndarray, axis=None, eps=1e-12):
    med = np.nanmedian(x, axis=axis, keepdims=True)
    mad = np.nanmedian(np.abs(x-med), axis=axis, keepdims=True)

    return 0.6475 * (x -med) / (mad + eps)
    
def Auto_Detect_Bad_Segments(
    data:np.ndarray, 
    sfreq:int,
    win_sec:float = 1.0,
    step_sec:float = 1.0,
    ptp_uv_thresh:float = 300.0,
    flat_uv_thresh:float = 1.0,
    robust_z_thresh:float = 6.0,
    bad_channel_ratio:float = 0.2,
    mode:str="uv"
):
    """
    Auto-detect bad eeg segments based on three major metrics: ptp, flat, robust\n
    ptp: Peak-to-Peak threshold, ptp = max(windowed-signal) - min(windowed-signal)\n
    flat: If the windowed-signal seems over-smoothed or flat, it may be a bad\n
    robust: Finding the outliers respect to other windows
    
    Args:
        data (np.ndarray): segmented eeg data for each epoch
        sfreq (int): sampling rate each second
        win_sec (float): the window-width to observe
        step_sec (float): the step
        ptp_uv_thresh (float): ptp
        flat_uv_thresh (float): flat
        robust_z_thresh (float): robust
        bad_channel_ratio (float): the upper limitation of bad channel overall
        mode (str): data mode, default is "uV"
        
    Returns:
        bad_events
    """
    
    if mode == "V":
        data = data * 1e6
    
    n_channels, n_samples, n_tasks = data.shape
    
    wind = int(sfreq * win_sec)
    step = int(sfreq * step_sec)
    
    starts = np.arange(0, n_samples - wind +1, step)
    n_windows = len(starts)
    
    ptp = np.zeros((n_tasks, n_windows, n_channels))
    rms = np.zeros((n_tasks, n_windows, n_channels))
    flat = np.zeros((n_tasks, n_windows, n_channels), dtype=bool)
    
    for task in range(n_tasks):
        for wi, start in enumerate(starts):
            seg = data[:, start:start+wind, task]
            
            ptp[task, wi] = np.ptp(seg, axis=1)
            rms[task, wi] = np.sqrt(np.mean(seg**2, axis=1))

            flat[task, wi] = np.ptp(seg, axis=1) < flat_uv_thresh
            
    bad_by_ptp_abs = ptp > ptp_uv_thresh    
    
    ptp_z = robust_z(ptp, axis=(0,1))
    rms_z = robust_z(rms, axis=(0,1))
    
    bad_by_ptp_z = np.abs(ptp_z) > robust_z_thresh
    bad_by_rms_z = np.abs(rms_z) > robust_z_thresh
    
    bad_channel_mask = (
        bad_by_ptp_abs | bad_by_ptp_z | bad_by_rms_z | flat
    )

    bad_ratio = bad_channel_mask.mean(axis=2)
    bad_mask = bad_ratio > bad_channel_ratio
    
    bad_segment = []
    
    for task in range(n_tasks):
        segments =[]
        
        in_bad = False
        start_bad = None
        
        for wi, is_bad in enumerate(bad_mask[task]):
            if is_bad and not in_bad:
                in_bad = True
                start_bad = starts[wi] / sfreq
                
            if not is_bad and in_bad:
                in_bad = False
                end_bad = starts[wi] / sfreq
                segments.append((start_bad, end_bad))
        
        if in_bad:
            end_bad = (starts[-1] + wind) / sfreq
            segments.append((start_bad, end_bad))
    
        bad_segment.append(segments)
        
    metrics = {
        "starts_samples": starts,
        "ptp": ptp,
        "rms": rms,
        "flat": flat,
        "bad_channel_mask": bad_channel_mask,
        "bad_ratio": bad_ratio
    }
    
    for task_idx, segs in enumerate(bad_segment):
        print(f"Task {task_idx}:")
        for start, end in segs:
            print(f"   BAD {start:.2f}s - {end:.2f}s")
    
    return bad_mask, bad_segment, metrics