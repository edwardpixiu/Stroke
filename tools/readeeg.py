
import mne
import numpy as np

def read_data_bp(eeg_hdr:str):

    # eeg_hdr = r'rawdata/test03-20260617/huangweidong_3.vhdr'
    
    raw = mne.io.read_raw_brainvision(eeg_hdr, preload=True)
    
    print(f"[DEBUG]:raw ====> \n{raw}")
    print(f"[DEBUG]:info ====> \n{raw.info}")
    print(f"[DEBUG]:channels ====> \n{raw.ch_names}")
    
    # read data
    data = raw.get_data()
    print(f"[DEBUG]:data shape:{data.shape}")
    
    # read marker
    events, events_id = mne.events_from_annotations(raw)
    
    print(f"[DEBUG]:Events: ====> \n{events} - {events.shape}")
    print(f"[DEBUG]:Events_id: ====> \n{events_id}")
    
    return data, raw

def reshape_eegdata(eeg_data:np.ndarray, sfreq:float, duration:float, timetree:dict, mode:str="tail"):
    
    target_points = sfreq * duration
    
    parser_eeg = []
    
    for i in range(1, len(timetree.keys())):
        
        if i + 1 < len(timetree.keys()):
            
            start_idx = timetree["marker_"+str(i)]["index"]
            end_idx = timetree["marker_"+str(i+1)]["index"]
        
        else:
            start_idx = timetree["marker_"+str(i-1)]["index"]
            end_idx = eeg_data.shape[-1]
        
        print(f"[Info]: No.{i} start at {start_idx} | end at {end_idx} | data points:{end_idx-start_idx}")
        
        if end_idx-start_idx > target_points:
            print(f"[Info]: Current work on part:{i}: particular data points {end_idx-start_idx} > target {target_points}")
            diff = end_idx-start_idx - target_points
            if mode == "pre":
                part_eeg = eeg_data[:, start_idx+diff:end_idx]
            elif mode == "tail":
                part_eeg = eeg_data[:, start_idx:end_idx-diff]
                
            print(f"[Info]: Part {i} eeg data reshaped:{part_eeg.shape}")
            parser_eeg.append(part_eeg[..., np.newaxis])
    
    reshape_eeg = np.concatenate(parser_eeg, axis=-1)
    
    print(f"[Info]: EEG data after parser: {reshape_eeg.shape}")
    
    return reshape_eeg