# Stroke
Stroke MI Model Program, include EEG part and MRI part

# 当前这个文件是EEG预处理的部分
### 主要实现了MNE-Python原始数据读取和坏导快速检查、坏段快速报告
### 以及去噪Pipeline函数

### 文件结构
 - main.py
 - tools
   - parser.py
   - preprocessing.py
   - readeeg.py
     
### 关键函数调用
  1. 读取BrainVision原始数据信息 \n
      from tools import read_data_bp \n
      raw_eeg_data(np.ndarray), raw(mne.Info) = read_data_bp(x.vhdr) \n
        \n
  2. 检查电极->10-20标准蒙太奇映射 \n
     from tools import Montage \n
     Montage(raw, show=True) \n
      \n
  3. 将多导联数据分为Events-related数据结构 \n
     events_eeg = Parser_Event_Related_EEG( \n
        x.vhdr, x.vmrk, sample_rate, duration \n
     ) \n
      \n
  4. 坏导检查 \n
     from tools import Check_Raws \n
     Check_Raws(raw:mne.Info, sfreq:int) \n
      \n
  5. 坏段检查 \n
     from tools import Auto_Detect_Bad_Segments \n
     Auto_Detect_Bad_Segments(events_eeg:np.ndarray, sfreq:int, mode="uV"/"V") \n
      \n
  6. 局部窗口内AAS \n
     Same_Slice_Local_AAS( \n
        events_eeg:np.ndarray, # shape like [n_events, n_channels, n_samples] \n
        labels:np.ndarray, # shape like [n_events, 2], each column = [start_index_time, sample_times] \n
     ) # 这个函数开发时是按照同步eeg-fmri设计的，所以需要改造 \n
     \n
  7. OBS-PCA \n
      Obs_Pca_Epochs(eeg_data:np.ndarray, mode:str, components:int) \n
      mode = A时，输出artifacts-epochs \n
      otherwise, 输出cleaned-epochs \n
      components, 定义使用的伪影特征数量，default is 1-3 \n
       \n
  8. ANC自适应噪声抑制 \n
      ANC_Regression(eeg_data:np.ndarray, reference_eeg_data:np.ndarray) \n
      reference_eeg_data：选定参考电极或ECG\EMG电极 \n
       \n
  9. Bandpass滤波 \n
      BandPass_Filter(eeg_data:np.ndarray, sfreq, low_pass, high_pass, order=1) \n
      使用巴甫洛夫滤波器进行带宽滤波，low_pass经验为0.5-0.8，high_pass经验为50-100 \n
      order越大，滤波结果越平滑
