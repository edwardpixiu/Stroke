from tools import read_data_bp, reshape_eegdata, get_timetree, Montage
from utils import write_eeg
from tools import Check_Raws, Auto_Detect_Bad_Segments

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


if __name__ == "__main__":
    
    eeg_hdr = r'rawdata/test03-20260617/huangweidong_3.vhdr' # BrainVision Format
    eeg_mrk = r'rawdata/test03-20260617/huangweidong_3.vmrk'
    
    events_eeg = Parser_Event_Related_EEG(
        eeg_hdr=eeg_hdr, eeg_mrk=eeg_mrk, 
        # savepath=r'/data/projects/EEG_analysis/eeg_npy/huangweidong_test03.npy',
        samplerate=5000, duration=20
    )

    # raw_eeg_data, raw = read_data_bp(eeg_hdr)
    
    # raw = Montage(raw, shows=False)
    
    # Check_Raws(raw, sfreq=5000)

    print(events_eeg.shape)
    
    _, _, _ = Auto_Detect_Bad_Segments(events_eeg, sfreq=5000, mode="V")