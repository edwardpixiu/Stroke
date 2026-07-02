from tools import read_data_bp, reshape_eegdata, get_timetree, Montage
from utils import write_eeg
from tools import Check_Raws, Auto_Detect_Bad_Segments, Auto_Detect_Bad_Channels
import numpy as np
import mne
import matplotlib.pyplot as plt

def Parser_Event_Related_EEG(eeg_hdr:str, eeg_mrk:str, samplerate:int, duration:int, savepath:str=None, write:bool=False):
    """
    Parser and save the event-related eeg data into savepath
    
    Args:
        eeg_hdr (str): BrainVision Format EEG header file
        eeg_mrk (str): BrainVision Format EEG marker file
        savepath (str): eeg data savepath
        samplerate (int): integer sampling rate
        duration (int): integer sampling duration
        write (bool): False
    Returns:
        parser_eeg (np.ndarray)
    """
    
    raw_eeg_data, _ = read_data_bp(eeg_hdr)
    
    timetree = get_timetree(eeg_mrk)
    
    parser_eeg = reshape_eegdata(raw_eeg_data, samplerate, duration, timetree)    

    if write:
        write_eeg(parser_eeg, savepath)
    
    return parser_eeg

def compute_welch_psd(raw, fmin=1, fmax=160, n_fft=4096, n_overlap=2048):
    psd = raw.compute_psd(
        method="welch",
        fmin=fmin,
        fmax=fmax,
        picks="eeg",
        n_fft=n_fft,
        n_overlap=n_overlap,
        window="hamming",   # MNE 支持 hamming/hann 
        reject_by_annotation=True
    )
    freqs = psd.freqs
    data = psd.get_data()  # [channels, freqs]
    return freqs, data

if __name__ == "__main__":
    
    eeg_hdr = r'rawdata/test03-20260617/huangweidong_3.vhdr' # BrainVision Format
    eeg_mrk = r'rawdata/test03-20260617/huangweidong_3.vmrk'
    
    events_eeg = Parser_Event_Related_EEG(
        eeg_hdr=eeg_hdr, eeg_mrk=eeg_mrk, 
        # savepath=r'/data/projects/EEG_analysis/eeg_npy/huangweidong_test03.npy',
        samplerate=5000, duration=20
    )

    raw_eeg_data, raw = read_data_bp(eeg_hdr)
    
    # raw = Montage(raw, shows=False)
    
    # Check_Raws(raw, sfreq=5000)
    ch_names = raw.ch_names
    
    print(events_eeg.shape)
    
    # Concatenate the eeg data [channels, n_samples, blocks] -> [channels, n_samples*blocks]
    ch_types = raw.get_channel_types()
    
    eeg_cont = np.concatenate(
        [events_eeg[..., b] for b in range(events_eeg.shape[-1])], axis=1
    )
    
    info = mne.create_info(ch_names=ch_names, sfreq=5000, ch_types=ch_types)
    nraw = mne.io.RawArray(eeg_cont, info)
    nraw.set_montage("standard_1020", on_missing="ignore")
    
    # Set Bad Channels
    nraw = Auto_Detect_Bad_Channels(nraw)
    
    _, bad_segments, _ = Auto_Detect_Bad_Segments(events_eeg, sfreq=5000, mode="V")
    
    # Set Bad Segments
    onsets = []
    duration = []
    for task_idx, segs in enumerate(bad_segments):
        for start, end in segs:
            onsets.append(start)
            duration.append(end-start)
            
    descriptions = ["BAD_artifacts"] * len(onsets)
    
    annot = mne.Annotations(onsets, duration, descriptions)
    nraw.set_annotations(nraw.annotations + annot)
    ndata_1 = nraw.copy()
    
    # filter 50, 100, 150
    nraw.notch_filter(freqs=[50, 100, 150], picks="eeg")
    ndata_2 = nraw.copy()
    
    # Bandpass 0.8-50
    nraw.filter(l_freq=0.8, h_freq=50, picks="eeg")
    ndata_3 = nraw.copy()
    
    # Observe Difference
    freqs, psd_before = compute_welch_psd(ndata_1)
    _, psd_notch = compute_welch_psd(ndata_2)
    _, psd_band = compute_welch_psd(ndata_3)
    
    psd_before_db = 10 * np.log10(psd_before)
    psd_notch_db = 10 * np.log10(psd_notch)
    psd_band_db = 10 * np.log10(psd_band)
    
    plt.figure(figsize=(10, 5))

    plt.plot(freqs, psd_before_db.mean(axis=0), label="Before filter", alpha=0.8)
    plt.plot(freqs, psd_notch_db.mean(axis=0), label="After notch", alpha=0.8)
    plt.plot(freqs, psd_band_db.mean(axis=0), label="After notch + bandpass", alpha=0.8)

    plt.axvline(50, color="r", linestyle="--", alpha=0.4)
    plt.axvline(100, color="r", linestyle="--", alpha=0.4)
    plt.axvline(150, color="r", linestyle="--", alpha=0.4)

    plt.xlabel("Frequency (Hz)")
    plt.ylabel("PSD (dB)")
    plt.title("Welch PSD before/after filtering")
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    # downsample
    # nraw.resample(sfreq=500)
    
    # set reference
    nraw.set_eeg_reference("average")
    
    # ICA
    ica = mne.preprocessing.ICA(
        n_components=0.95,
        method="fastica",
        random_state=42,
        max_iter="auto"
    )
    
    ica.fit(nraw, reject_by_annotation=True)
    
    ica.plot_components()
    
    nraw_clean = ica.apply(nraw.copy())
    
    # Second-times bad segments
    bad_segments2 = Auto_Detect_Bad_Segments(
        nraw_clean,
        sfreq=500,
        win_sec=1.0,
        step_sec=0.5,        
        ptp_uv_thresh=200
    )
    
    annot2 = mne.Annotations(
        [s for s, e in bad_segments2],
        [e - s for s, e in bad_segments2],
        ["BAD_residual"] * len(bad_segments2)
    )
    nraw_clean.set_annotations(nraw_clean.annotations + annot2)    
    # nraw_clean.set_montage("standard_1020", on_missing="ignore")
    # # Bad Segments Interpolate
    # nraw_clean.interpolate_bads(reset_bads=False)
    # nraw_clean.info["bads"] = []
    
    # reshape into events_related
    sfreq_new = nraw_clean.info["sfreq"]
    samples_per_block = int(20 * sfreq_new)

    clean_data = nraw_clean.get_data()

    blocks = []
    for b in range(16):
        start = b * samples_per_block
        stop = start + samples_per_block
        blocks.append(clean_data[:, start:stop])

    eeg_clean = np.stack(blocks, axis=2)
    
    print(f"[Info-python]: eeg_clean:{eeg_clean.shape}")
    
    # Show difference
    fig, axs = plt.subplots(2, 1, figsize=(14,6))
    
    axs[0].plot(events_eeg[5, 50000:52500, 1]*1e6, color='blue')
    axs[0].set_title("Origin")
    axs[1].plot(eeg_clean[5, 50000:52500, 1]*1e6, color='red')
    axs[1].set_title("Clean")    
    plt.tight_layout()
    plt.show()