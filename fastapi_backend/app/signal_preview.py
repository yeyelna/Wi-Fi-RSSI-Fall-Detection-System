from __future__ import annotations

from io import BytesIO
from typing import Dict, Tuple

import numpy as np
from scipy.io import loadmat
from scipy.signal import savgol_filter, find_peaks, detrend
from scipy.interpolate import interp1d

try:
    import h5py
except Exception:  # pragma: no cover
    h5py = None


FS0 = 5000.0
DOWNSAMPLE_FACTOR = 5
FS = FS0 / DOWNSAMPLE_FACTOR
RECORDING_DURATION_SEC = 20.0


def _safe_1d_array(value) -> np.ndarray:
    arr = np.asarray(value).squeeze()
    if arr.ndim > 1:
        arr = arr.reshape(-1)
    arr = arr.astype(float)
    arr = arr[np.isfinite(arr)]
    return arr


def _find_first_numeric_array(obj) -> np.ndarray | None:
    if isinstance(obj, dict):
        for key in ['A', 'a', 'RSSI', 'rssi', 'signal', 'data']:
            if key in obj:
                try:
                    arr = _safe_1d_array(obj[key])
                    if arr.size >= 10:
                        return arr
                except Exception:
                    pass
        for key, value in obj.items():
            if str(key).startswith('__'):
                continue
            try:
                arr = _safe_1d_array(value)
                if arr.size >= 10:
                    return arr
            except Exception:
                continue
    return None


def _load_with_scipy(file_bytes: bytes) -> Tuple[np.ndarray, str]:
    mat = loadmat(BytesIO(file_bytes), squeeze_me=True)
    if 'A' in mat:
        arr = _safe_1d_array(mat['A'])
        if arr.size >= 10:
            return arr, 'A'
    arr = _find_first_numeric_array(mat)
    if arr is None:
        raise ValueError('No usable numeric signal array found in .mat file.')
    return arr, 'auto_numeric_array'


def _load_with_h5py(file_bytes: bytes) -> Tuple[np.ndarray, str]:
    if h5py is None:
        raise ValueError('This .mat file appears to be v7.3/HDF5, but h5py is not available.')

    best = {'name': None, 'array': None}

    def visit(name, obj):
        if not hasattr(obj, 'shape') or not hasattr(obj, 'dtype'):
            return
        try:
            if not np.issubdtype(obj.dtype, np.number):
                return
            arr = _safe_1d_array(obj[()])
            if arr.size < 10:
                return
            if name.split('/')[-1] == 'A':
                best['name'] = name
                best['array'] = arr
            elif best['array'] is None:
                best['name'] = name
                best['array'] = arr
        except Exception:
            return

    with h5py.File(BytesIO(file_bytes), 'r') as f:
        f.visititems(visit)

    if best['array'] is None:
        raise ValueError('No usable numeric signal array found in HDF5 .mat file.')
    return best['array'], str(best['name'])


def load_mat_signal(file_bytes: bytes) -> Tuple[np.ndarray, str]:
    try:
        return _load_with_scipy(file_bytes)
    except NotImplementedError:
        return _load_with_h5py(file_bytes)
    except ValueError:
        raise
    except Exception:
        return _load_with_h5py(file_bytes)


def _normalize_range(x: np.ndarray, low: float = 0.0, high: float = 3.0) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    xmin = np.nanmin(x)
    xmax = np.nanmax(x)
    if not np.isfinite(xmin) or not np.isfinite(xmax) or abs(xmax - xmin) < 1e-12:
        return np.zeros_like(x) + low
    return low + (x - xmin) * (high - low) / (xmax - xmin)


def _safe_savgol(x: np.ndarray, preferred_window: int, polyorder: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    n = x.size
    if n < 5:
        return x
    win = min(int(preferred_window), n)
    if win % 2 == 0:
        win -= 1
    win = max(win, 5)
    if win > n:
        win = n if n % 2 == 1 else n - 1
    if win < 5:
        return x
    order = min(int(polyorder), win - 1)
    return savgol_filter(x, window_length=win, polyorder=order, mode='interp')


def _moving_mean(x: np.ndarray, window: int) -> np.ndarray:
    window = max(1, min(int(window), x.size))
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(x, kernel, mode='same')


def _fallback_preview(signal: np.ndarray, note: str, variable_name: str) -> Dict:
    n = min(300, max(50, signal.size))
    src_x = np.linspace(0.0, 1.0, signal.size)
    dst_x = np.linspace(0.0, 1.0, n)
    y = np.interp(dst_x, src_x, signal)
    y = _normalize_range(y, 0.0, 1.0)
    x = np.linspace(0.0, RECORDING_DURATION_SEC, n)
    return {
        'x': [float(round(v, 4)) for v in x],
        'y': [float(round(v, 6)) for v in y],
        'x_axis': 'Time (s)',
        'y_axis': 'Amplitude',
        'tooltip_label': 'Amplitude',
        'title': 'Envelope Signal Preview',
        'signal_source': 'uploaded_raw_mat_fallback',
        'signal_variable': variable_name,
        'preview_note': note,
    }


def extract_envelope_preview(signal: np.ndarray, variable_name: str) -> Dict:
    A = _safe_1d_array(signal)
    if A.size < 10:
        raise ValueError('Signal is too short to display envelope preview.')

    A0 = _normalize_range(A, 0.0, 3.0)
    if A0.size >= 51:
        sg_win0, sg_ord0 = 51, 10
    else:
        sg_win0 = A0.size if A0.size % 2 == 1 else A0.size - 1
        sg_win0 = max(sg_win0, 5)
        sg_ord0 = min(3, sg_win0 - 1)
    A0 = _safe_savgol(A0, sg_win0, sg_ord0)

    M0 = _moving_mean(A0, min(2000, A0.size))
    nb = float(np.nanmean(M0))
    A_gate = A0.copy()
    A_gate[A_gate <= nb] = 0.0
    A_gate[~np.isfinite(A_gate)] = 0.0

    A_ds = A_gate[::DOWNSAMPLE_FACTOR]
    if A_ds.size < 10:
        return _fallback_preview(A_gate, 'Downsampled signal was too short; showing processed signal preview.', variable_name)

    duration_ds = A_ds.size / FS
    numbpeaks = max(1, int(round(10 * duration_ds)))
    ipk, _ = find_peaks(A_ds, distance=89, width=2)
    pks = A_ds[ipk]
    if ipk.size > numbpeaks:
        ipk = ipk[:numbpeaks]
        pks = pks[:numbpeaks]

    if ipk.size < 2:
        return _fallback_preview(A_ds, 'Not enough peaks found; showing processed downsampled signal preview.', variable_name)

    xq = np.arange(int(ipk[0]), int(ipk[-1]) + 1)
    kind = 'cubic' if ipk.size >= 4 else 'linear'
    try:
        f = interp1d(ipk.astype(float), pks.astype(float), kind=kind, fill_value='extrapolate')
        ylow = f(xq.astype(float))
    except Exception:
        f = interp1d(ipk.astype(float), pks.astype(float), kind='linear', fill_value='extrapolate')
        ylow = f(xq.astype(float))

    dtr_env = detrend(np.asarray(ylow, dtype=float))
    sg_win_env = 501 if dtr_env.size >= 501 else dtr_env.size
    if sg_win_env % 2 == 0:
        sg_win_env -= 1
    sg_win_env = max(sg_win_env, 5)
    dtr_env = _safe_savgol(dtr_env, sg_win_env, 1)

    if dtr_env.size < 8:
        return _fallback_preview(A_ds, 'Envelope was too short; showing processed downsampled signal preview.', variable_name)

    n_out = 300
    t_native = xq / FS
    t_native = t_native - float(t_native[0])
    if float(t_native[-1]) > 0:
        t_display_native = (t_native / float(t_native[-1])) * RECORDING_DURATION_SEC
    else:
        t_display_native = np.linspace(0.0, RECORDING_DURATION_SEC, dtr_env.size)
    t_display = np.linspace(0.0, RECORDING_DURATION_SEC, n_out)
    y_display = np.interp(t_display, t_display_native, dtr_env)

    return {
        'x': [float(round(v, 4)) for v in t_display.tolist()],
        'y': [float(round(v, 6)) for v in y_display.tolist()],
        'x_axis': 'Time (s)',
        'y_axis': 'Amplitude',
        'tooltip_label': 'Amplitude',
        'title': 'Envelope Signal Preview',
        'signal_source': 'uploaded_raw_mat_envelope',
        'signal_variable': variable_name,
        'preview_note': 'Envelope extracted from uploaded .mat file using the Feature_Extractions.m preprocessing logic.',
    }


def envelope_preview_from_mat_bytes(file_bytes: bytes, filename: str = '') -> Dict:
    signal, variable_name = load_mat_signal(file_bytes)
    preview = extract_envelope_preview(signal, variable_name)
    preview['file_name'] = filename
    return preview
