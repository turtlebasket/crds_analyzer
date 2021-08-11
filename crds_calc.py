import numpy as np
from scipy.signal import find_peaks, correlate
from scipy.optimize import curve_fit
from db import mem

def minmax(data):
    return np.min(data), np.max(data)

def exp_func(x, x0, a, y0, tau): # NOTE: X is not something we pass in 🤦‍♂️
    return y0 + a*np.exp(-(x-x0)/tau)

def spaced_groups(
    x_data: np.array,
    y_data: np.array,
    group_len: float,
    peak_minheight: float,
    peak_prominence: float,
    sma_denom: int,
    mirrored: bool=True,
    start=None,
    end=None
):
    """
    Use SpacedGroups algo to separate groups

    Returns
    -------
    2D array of raw data; every other group
    """

    # Helpers
    def t2i(t): # STATIC time to index
        delta_t = abs(x_data[0] - t)
        timestep = abs(x_data[1] - x_data[0])
        return int(delta_t / timestep)

    def t2i_range(t): # time to index RANGE (just get the delta)
        timestep = abs(x_data[1] - x_data[0])
        return int(t / timestep)

    def moving_average(x, w):
        return np.convolve(x, np.ones(w), 'valid') / w

    def isolate_group(i):
        i_min = i - t2i_range(group_len)
        i_max = i + t2i_range(group_len)
        # NOTE: Groups that are too short just get left out. Too bad!
        group = y_data.tolist()[i_min:i_max]
        return group

    # Check if custom start & end values are set

    if not end == None:
        stop_ind = t2i(end)
        x_data = x_data[:stop_ind]
        y_data = y_data[:stop_ind]

    if not start == None:
        start_ind = t2i(start)
        x_data = x_data[start_ind:]
        y_data = y_data[start_ind:]

    # Detect peaks w/ averaged data
    x_data_av = np.delete(x_data, [range(int(sma_denom / 2))])
    x_data_av = np.delete(x_data_av, [range(len(x_data)-int((sma_denom / 2) - 1), len(x_data_av))])
    y_data_av = moving_average(y_data, sma_denom)
    peak_indices = find_peaks(y_data_av, height=peak_minheight, prominence=peak_prominence) # Get indices of all peaks

    peaks = []
    for p in peak_indices[0]: # Get x-values of all peaks
        peaks.append(x_data[p])


    # Group peaks together
    peak_groups = [[]]
    group_index = 0
    for i in range(len(peaks)):
        item = peaks[i]
        next_item = 0
        try:
            next_item = peaks[i+1]
        except:
            pass

        peak_groups[group_index].append(item)

        # Removed overlapping peak checks; don't really need that anymore
        if abs(next_item - item) >= group_len: # Check if far enough away for new group
            peak_groups.append([])
            group_index += 1

    for g in peak_groups: # empty group check
        if len(g) == 0:
            peak_groups.remove(g)

    peaks_init = [] # Get peaks[0] for every group
    for g in peak_groups:
        peaks_init.append(g[0])

    # Isolate group data

    groups_raw = [] 
    for p in peaks_init:
        if mirrored:
            if peaks_init.index(p) % 2 == 0:
                groups_raw.append(isolate_group(t2i(p)))
            else:
                pass
        else:
            groups_raw.append(isolate_group(t2i(p)))

    for i in groups_raw:
        if len(i) == 0:
            groups_raw.remove(i)

    return groups_raw


def vthreshold(
    x_data: np.array,
    y_data: np.array,
    v_data: np.array,
    vmin: float,
    vmax: float,
    mirrored: bool=True,
    start=None,
    end=None
):
    """
    Voltage-threshold grouping algorithm

    Returns
    -------
    A `list` of all peak groups
    """

    # Helpers
    def t2i(t):
        delta_t = abs(x_data[0] - t)
        timestep = abs(x_data[1] - x_data[0])
        return int(delta_t / timestep)

    def t2i_range(t):
        timestep = abs(x_data[1] - x_data[0])
        return int(t / timestep)

    groups_raw = []
    return groups_raw

def correlate_groups(groups_raw):
    """
    Overlay groups using `scipy.correlate`.

    Returns
    -------
    2D array of overlayed groups
    """

    # Compare groups (scipy correlate)

    group_base = np.array(groups_raw[0])
    groups_adjusted = [group_base]
    for x in groups_raw[1:]:
        # calculate how much to shift
        corr = correlate(group_base, np.array(x))
        shift = corr.tolist().index(max(corr))

        # adjust alignment to fit on top of base group
        diff = shift - len(x)
        if diff < 0:
            for i in range(abs(diff)):
                x.pop(0)
        elif diff > 0:
            x = [0 for i in range(abs(diff))] + x

        groups_adjusted.append(x)

    return groups_adjusted

def add_peaks_only(groups_adjusted: list):

    def unequal_add_truncation(a,b): # Instead of padding with 0, truncate
        if len(a) < len(b):
            c = b.copy()
            c = c[:len(a)]
            c += a
        else:
            c = a.copy()
            c = c[:len(b)]
            c += b
        return(c)

    added_peaks = np.array(groups_adjusted[0])

    for g in groups_adjusted[1:]:
        g1 = np.array(g)
        g0 = added_peaks
        added_peaks = unequal_add_truncation(g0, g1)

    return added_peaks

def isolate_peaks(
    groups_adjusted: list,
    peak_width: int, 
    sma_denom: int,
    peak_minheight: int = None,
    peak_prominence: int = None,
    shift_over: int = 0
):

    def unequal_add(a,b): # NOTE: See https://www.delftstack.com/howto/numpy/vector-addition-in-numpy/
        if len(a) < len(b):
            c = b.copy()
            c[:len(a)] += a
        else:
            c = a.copy()
            c[:len(b)] += b
        return(c)

    def unequal_add_truncation(a,b): # Instead of padding with 0, truncate
        if len(a) < len(b):
            c = b.copy()
            c = c[:len(a)]
            c += a
        else:
            c = a.copy()
            c = c[:len(b)]
            c += b
        return(c)

    def moving_average(x, w):
        return np.convolve(x, np.ones(w), 'valid') / w

    added_peaks = np.array(groups_adjusted[0])

    for g in groups_adjusted[1:]:
        g1 = np.array(g)
        g0 = added_peaks
        added_peaks = unequal_add_truncation(g0, g1)

    added_peaks_av = moving_average(added_peaks, sma_denom)
    peak_indices = find_peaks(added_peaks_av, height=peak_minheight, prominence=peak_prominence, distance=peak_width/2)[0] # Get indices of all peaks

    isolated_peaks = []
    delta = peak_width/2

    for g in groups_adjusted:
        peaks_cut = []
        for i in peak_indices:
            peak = g[int(i-delta+shift_over):int(i+delta+shift_over)]
            peaks_cut.append(peak)
        isolated_peaks.append(peaks_cut)

    return added_peaks, peak_indices, isolated_peaks


def fit_peaks(
    isolated_peaks: list,
    peak_indices: list,
    min_peak_height: float,
    min_peak_prominence: float,
    moving_avg_size: int,
    a: float,
    tau: float,
    y0: float,
    shift_over: int,
    use_advanced: bool
):
    
    """
    Returns
    -------
    Peak fit equations. Linked to `mem['isolated_peaks']`.
    """

    params_guess = (0.0000, a, y0, tau)
    equations = []
    overlayed_peak_indices = []
    for peaks_cut in isolated_peaks:
        equation_row = []
        overlayed_peak_row = []
        for peak_data in peaks_cut:
            x_data = np.arange(len(peak_data)) # just placeholder indices
            # x_data = np.arange(0, len(peak_data)*mem['timestep'], mem['timestep'])
            print(x_data)
            if not use_advanced:
                peak_index = np.argmax(peak_data, axis=0)
            else:
                peak_index = find_peaks(peak_data, height=min_peak_height, prominence=min_peak_prominence)[0][0]
            # print(peak_index)
            params_guess = (peak_index+shift_over, a, y0, tau)
            x_data_target = x_data[peak_index+shift_over:]
            peak_data_target = peak_data[peak_index+shift_over:]
            popt, pcov = curve_fit(exp_func, x_data_target, peak_data_target, bounds=([-np.inf, 0.0, -np.inf, 0.0], np.inf), p0=params_guess, maxfev=10000000)
            equation_row.append({'popt': popt, 'pcov': pcov})
            overlayed_peak_row.append(peak_index)
        equations.append(equation_row)
        overlayed_peak_indices.append(overlayed_peak_row)
        mem['overlayed_peak_indices'] = overlayed_peak_indices

    return equations # list linked with isolated_peaks


def get_time_constants(equation_data):
    """
    Extracts time constant from all fit-output equations (2d array)
    
    Returns
    -------

    Tau data in same dimensions as `equation_data`
    """
    
    tau_data = []
    for r in equation_data:
        row = []
        for e in r:
            tau = e['popt'][3]*mem['timestep']
            row.append(tau)
        tau_data.append(row)

    print(tau_data)

    return tau_data
