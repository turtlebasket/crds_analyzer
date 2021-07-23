import numpy as np
from scipy.signal import find_peaks, correlate
from memdb import mem

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

    Returns 2D array of raw data; every other group
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


def correlate_groups(groups_raw):
    """
    Overlay groups using `scipy.correlate`.

    Returns 2D array of overlayed groups
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

def isolate_peaks(
    peak_width: int, 
    groups_adjusted: list, 
    peak_minheight: int,
    peak_prominence: int,
    sma_denom: int
):

    def moving_average(x, w):
        return np.convolve(x, np.ones(w), 'valid') / w

    group_peaks = []
    for g in groups_adjusted:
        y_data_av = moving_average(g, sma_denom)
        peak_indices = find_peaks(y_data_av, height=peak_minheight, prominence=peak_prominence) # Get indices of all peaks
        group_peaks.append(peak_indices)
