from scipy.io import loadmat
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import detrend
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from scipy.signal import welch

def has_decimal_value(arr):
    # 首先转为浮点型避免整型取模报错，然后对1取模，若余数不为0则存在小数
    # 使用 np.any 只要有任意一个元素满足条件即返回 True
    return np.any(arr.astype(float) % 1 != 0)

def EEG_Activate_Sampling_Points(
    TR:float, fs:float, slice_perTR:int, n_TR:int
):
    """
    获取读出梯度启动时的EEG采样点
    
    Args:
        TR (float): TR value
        fs (float): 采样频率
        slice_perTR (int): 每个TR周期内扫描得到的slice数量
        n_TR (int): 总TR
        
    Returns:
        slice_onset (np.ndarray): EEG采样时序列表
    """
    
    samples_perTR = int(TR * fs)
    slice_interval = samples_perTR / slice_perTR
    
    slice_onsets = []
    labels = []
    
    for r in range(n_TR):
        tr0 = r * samples_perTR
        for s in range(slice_perTR):
            onset = tr0 + s * slice_interval
            slice_onsets.append(onset)
            labels.append((r, s))
            
    slice_onsets = np.array(slice_onsets)
    
    return slice_onsets, np.array(labels)

def Extract_Epochs_fractional(
    x:np.ndarray, onsets:np.ndarray, pre=5, post=57
):
    """
    带插值的伪迹片段提取
    
    Args:
        x (np.ndarray): 重塑形状后的原始数据
        onsets (np.ndarray): 读出梯度启动时序表
        pre (int): 从梯度开始前第pre个采样点开始截取
        post (int): 一直截到梯度开始后第post个采样点
        
    Returns:
        epochs (np.ndarray): 截取片段\n
        rel (np.ndarray): 截取时间范围
    """

    t = np.arange(x.shape[-1])
    f = interp1d(
        t, x, axis=-1 ,kind='linear', bounds_error=False, fill_value='extrapolate'
    )
    
    rel = np.arange(-pre, post+1)

    epochs = np.stack([
        f(onset + rel) for onset in onsets if onset - pre >= 0 and onset + post < x.shape[-1]
    ])
    
    return epochs, rel

def Moving_Windows_AAS_Rough(
    epochs:np.ndarray,
    half_window:int=10
):
    """
    参考原始Allen论文方法对扫描信号进行滑动窗口AAS
    
    Args:
        epochs (np.ndarray): 重塑形状后的原始数据
        half_window (int): 半窗宽
        
    Returns:
        out (np.ndarray): 
    """

def Same_Slice_Local_AAS(
    epochs:np.ndarray, labels:np.ndarray, half_window:int=15
):
    """
    对同一层slice不同采样点进行局部窗口内AAS
    
    Args:
        epochs (np.ndarray): shape like [n_events x n_channels x n_samples]
        labels (np.ndarray): shape like [n_events x 2], column = [TR_index, Slice_index]
        
    Returns:
        cleaned (np.ndarray): 清洁EEG信号\n
        template (np.ndarray): 伪迹模板

    """
    
    tr_idx = labels[:, 0]
    slice_idx = labels[:, 1]
    
    cleaned = np.zeros_like(epochs)
    template = np.zeros_like(epochs)
    
    for i in range(epochs.shape[0]):
        r = tr_idx[i]
        s = slice_idx[i]
        
        use = (
            (slice_idx == s) &
            (tr_idx >= r - half_window) &
            (tr_idx <= r + half_window) &
            (np.arange(epochs.shape[0]) != i)
        )   
        
        temp = epochs[use].mean(axis=0)
        
        template[i] = temp
        cleaned[i] = epochs[i] - temp
        
    return cleaned, template

def add_fractional(accum, weight, times, values):
    """
    将一个 epoch 的模板 values 按浮点时间 times 回投到原始采样网格。

    Parameters
    ----------
    accum : array, shape (n_channels, n_samples)
        伪迹模板累加器。
    weight : array, shape (n_channels, n_samples)
        权重累加器。
    times : array, shape (epoch_len,)
        当前 epoch 每个点对应的原始浮点采样时间。
    values : array, shape (n_channels, epoch_len)
        当前 epoch 的伪迹模板。
    """
    n_channels, n_samples = accum.shape

    left = np.floor(times).astype(int)
    frac = times - left
    right = left + 1

    # 分配到左侧整数采样点
    valid_left = (left >= 0) & (left < n_samples)
    idx_left = left[valid_left]
    w_left = (1.0 - frac[valid_left])

    accum[:, idx_left] += values[:, valid_left] * w_left[None, :]
    weight[:, idx_left] += w_left[None, :]

    # 分配到右侧整数采样点
    valid_right = (right >= 0) & (right < n_samples)
    idx_right = right[valid_right]
    w_right = frac[valid_right]

    accum[:, idx_right] += values[:, valid_right] * w_right[None, :]
    weight[:, idx_right] += w_right[None, :]


def subtract_templates_fractional(
    raw_data:np.ndarray, onsets:np.ndarray, templates:np.ndarray, pre:int, post:int  
):
    
    C, N = raw_data.shape
    rel = np.arange(-pre, post+1)
    
    artifacts_sum = np.zeros_like(raw_data)
    weight = np.zeros_like(raw_data)
    
    for i, onset in enumerate(onsets):
        times = onset + rel
        add_fractional(
            artifacts_sum,
            weight,
            times,
            templates[i, ...]            
        )

    artifact = np.zeros_like(raw_data)
    mask = weight > 0
    artifact[mask] = artifacts_sum[mask] / weight[mask]

    cleaned = raw_data - artifact
    
    return cleaned, artifact

def Obs_Pca_Epochs(AAS_Epochs:np.ndarray, mode:str, n_component:int=3):
    n_events, n_channels, epoch_len = AAS_Epochs.shape
    
    artifact_epochs = np.zeros_like(AAS_Epochs)
    cleaned_epochs = np.zeros_like(AAS_Epochs)
    
    for ch in range(n_channels):
        R = AAS_Epochs[:, ch, :]
        R_centered = R - R.mean(axis=0, keepdims=True)
        
        U, S, Vt = np.linalg.svd(R_centered, full_matrices=False)
        P = Vt[:n_component].T
        
        for i in range(n_events):
            r = R[i]
            artifact_epochs[i, ch, :] = P @ (P.T @ r)
            cleaned_epochs[i, ch, :] = r -  P @ (P.T @ r)
            
    if mode == "A": # artifacts
        return artifact_epochs
    else:
        return cleaned_epochs

def ANC_Regression(X_eeg, refs, block=20000, ridge=1e-3):
    """
    将EOG作为参考信号进行自适应噪声抑制
    """
    Y = X_eeg.copy()
    n_samples = X_eeg.shape[-1]
    
    for lo in range(0, n_samples, block):
        
        hi = min(n_samples, lo+block)
        
        R = refs[:, lo:hi].T
        R = np.column_stack([R, np.ones(hi - lo)])
        
        Xb = X_eeg[:, lo:hi].T
        
        beta = np.linalg.solve(
            R.T @ R + ridge * np.eye(R.shape[1]),
            R.T @ Xb            
        )
        
        noise = R @ beta
        Y[:, lo:hi] = (Xb - noise).T

    return Y

def BandPass_Filter(Signal:np.ndarray, fs:float, lowpass=0.3, highpass=48, order=4):
    
    sos = butter(
        N=order, Wn=[lowpass, highpass], btype="bandpass", fs=fs, output="sos"
    )
    
    x_filt = sosfiltfilt(sos, Signal, axis=-1)
    
    return x_filt

if __name__ == "__main__":
    
    # 设置基础信息
    fs = 1000
    TR = 2.0
    n_TR = 170
    L_TR = int(TR * fs) # 2000
    slice_perTR = 32
    
    Channel_NeedNoGA = np.arange(0, 47) # 指定需要移除GA的通道范围
    
    # 读取原始EEG数据
    eeg_mat = r'datasets\EEG\EEG_raw.mat'
    mat = loadmat(eeg_mat)
    
    # 读取RawData
    raw_data = mat["data"] # channels x samples
    
    print(
        f"[Info]: 检查原始数据: {raw_data.shape}"
    )
    
    assert raw_data.shape[1] == n_TR * L_TR, \
        f"[Error]: 数据维度与设置的基础参数不一致！请手动检查..."
        
    X = raw_data[Channel_NeedNoGA, ...] * 100 # 转微伏
    
    # 对每个通道进行线性去趋势
    X = detrend(X, axis=-1, type='linear')
    
    epochs = X.reshape(len(Channel_NeedNoGA), n_TR, L_TR)
    
    print(f"[Info]: 检查重塑数据: {epochs.shape}")
    
    slice_onset, labels = EEG_Activate_Sampling_Points(TR=TR, fs=fs, slice_perTR=slice_perTR, n_TR=n_TR)
    
    print(
        f"[Info]: 获取到读出梯度onset时间表:{slice_onset} | {slice_onset.shape}" + "\n",
        f"[Info]: 获取到的TR labels:{labels} | {len(labels)}"
    )
    
    Epochs, rel = Extract_Epochs_fractional(X, slice_onset)
    
    print(f"[Info]: 插值截取后的epoch片段:{Epochs.shape}")
    
    # 丢弃边界epoch并保留labels
    valid_epochs = []
    valid_labels = []
    
    for onset, label in zip(slice_onset, labels):
        print(f"{onset} - {label}")
        if (onset - 5 >= 0) and (onset + 57 < L_TR*n_TR):
            valid_epochs.append(onset)
            valid_labels.append(label)
    
    valid_epochs = np.array(valid_epochs)
    valid_labels = np.array(valid_labels)
    
    print(f"[DEBUG]: 检查更新后的TR-Slice对应关系:\nValid Epochs:{len(valid_epochs)} | Valid labels:{len(valid_labels)}")
    
    cleaned_eeg, template_arti = Same_Slice_Local_AAS(Epochs, valid_labels)
    cleaned_eegs = cleaned_eeg.reshape(len(Channel_NeedNoGA), -1)
    
    print(f"[DEBUG]: 检查清洁EEG输出:{cleaned_eegs.shape} | template_artifacts:{template_arti.shape}")
    
    obs_epochs = Obs_Pca_Epochs(cleaned_eeg, mode='A', n_component=1)
    print(f"[DEBUG]: 检查OBS输出:{obs_epochs.shape}")
    
    cleaned, _ = subtract_templates_fractional(X, valid_epochs, template_arti, 5, 57)
 
    _, obs_continuous = subtract_templates_fractional(
        np.zeros_like(cleaned), valid_epochs, obs_epochs, 5, 57
    )
    
    cleaned_obs = cleaned - obs_continuous
    
    cleaned_final = ANC_Regression(cleaned_obs[:43], cleaned_obs[43:47])
    
    cleaned_bandpass_100 = BandPass_Filter(cleaned_final, fs, lowpass=0.8, highpass=100, order=1)
    cleaned_bandpass_50 = BandPass_Filter(cleaned_final, fs, lowpass=0.8, highpass=50, order=1) 
    
    
    print(f"[DEBUG]: 检查重映射后的清洁EEG输出:{cleaned.shape}")
    print(f"[DEBUG]: 检查重映射后的OBS-PCA清洁EEG输出:{cleaned_obs.shape}")
    print(f"[DEBUG]: 检查ANC抑制肌电、眼电后的信号:{cleaned_final.shape}")
    print(f"[DEBUG]: 检查bandpass滤波后的信号:{cleaned_bandpass_50.shape}")
    
    # 恢复通道形状
    ch = 0 
    t0 = 100000
    t1 = 102000
    
    fig, axs = plt.subplots(6,1,figsize=(12, 8), constrained_layout=True)
    
    axs[0].plot(raw_data[ch, t0:t1]*100, label="RAW", color='blue')
    axs[0].set_title("Raw Data")
    axs[1].plot(cleaned[ch, t0:t1], label="Sliding-windows AAS", color='orange')
    axs[1].set_title("Windowed-AAS")
    axs[2].plot(cleaned_obs[ch, t0:t1], color='red')
    axs[2].set_title("OBS/PCA")
    axs[3].plot(cleaned_final[ch, t0:t1], color='purple')
    axs[3].set_title(f"ANC")
    axs[4].plot(cleaned_bandpass_50[ch, t0:t1], color='green')
    axs[4].set_title(f"Bandpass 0.3-50")    
    axs[5].plot(cleaned_bandpass_100[ch, t0:t1], color='orange')
    axs[5].set_title(f"Bandpass 0.3-100")    

    plt.show()
    
    
    f50, p50 = welch(cleaned_bandpass_50[ch], fs=fs, nperseg=4096)
    f100, p100 = welch(cleaned_bandpass_100[ch], fs=fs, nperseg=4096)

    plt.semilogy(f50, p50, label="0.8-50")
    plt.semilogy(f100, p100, label="0.8-100")
    plt.xlim(0, 150)
    plt.legend()
    plt.show()