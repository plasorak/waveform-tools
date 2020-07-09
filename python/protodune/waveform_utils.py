import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin
from mpl_toolkits.axes_grid1 import make_axes_locatable

def get_channel(all_chans, chan):
    index=np.argwhere(all_chans[:,1]==chan)
    assert(index.shape==(1,1))
    return all_chans[index[0,0],2:]

def get_collection_channel(all_chans, apa, collindex):
    chan=2560*apa+1600+collindex
    return get_channel(all_chans, chan)
    
def get_apa(all_chans, apanum, planetype="z", wallorcryo="both"):
    assert(planetype in ("u", "v", "z"))
    assert(wallorcryo in ("wall", "cryo", "both"))
    assert(wallorcryo=="both" or planetype=="z")
    starts = {"u": 0,   "v": 800,  "z": 1600}
    ends   = {"u": 800, "v": 1600, "z": 2560}
    # For even-numbered APAs, the wall-facing collection wires are
    # 0-480; for odd-numbered APAs, 480-960
    wall_start =   0 if apanum%2==0 else 480
    wall_end   = 480 if apanum%2==0 else 960
    cryo_start = 480 if apanum%2==0 else   0
    cryo_end   = 960 if apanum%2==0 else 480
    chans=all_chans[:,1]
    
    first_chan=2560*apanum+starts[planetype]
    last_chan=2560*apanum+ends[planetype]
    if wallorcryo=="wall":
        first_chan=2560*apanum+starts[planetype]+wall_start
        last_chan=2560*apanum+starts[planetype]+wall_end
    elif wallorcryo=="cryo":
        first_chan=2560*apanum+starts[planetype]+cryo_start
        last_chan=2560*apanum+starts[planetype]+cryo_end
    print "Looking for %d,%d" % (first_chan, last_chan)
    apachanbool=np.logical_and((chans>=first_chan),
                               (chans<last_chan))
    apaindices=np.argwhere(apachanbool)
    if apaindices.size==0:
        raise Exception("No channels in input for apa %d view %s wall/cryo %s" % (apanum, planetype, wallorcryo))
    apavals=np.vstack(all_chans[apaindices])
    # The channels in the npy aren't ordered by channel number, but
    # however they came out of the electronics, so fix that. (Order by
    # offline channel number is effectively order-in-space for
    # collection channels)
    thechans=apavals[:,1]
    i=np.argsort(thechans)
    apasort=apavals[i]
    return apasort

def pedsub(vals):
    """
    Subtract the pedestal, estimated as median ADC value, from `vals`,
    which is assumed to contain event number and channel number in the
    first two columns
    """
    # Calculate the median of each channel; just the actual ADCs (not the first two columns)
    peds=np.median(vals[:,2:], axis=1)
    nchans=vals.shape[0]
    nticks=vals.shape[1]-2
    # To leave the first two columns unmolested, we expand the
    # pedestal values into a 2D array with np.tile, and add two
    # columns of zeros at the start with hstack. Then the subtraction
    # is elementwise without any broadcasting
    tmp=np.hstack([np.zeros((nchans,2)), np.tile(peds, [nticks,1]).T])
    return vals-tmp

def get_pedsub_apa_from_file(filename, apanum, planetype="z", wallorcryo="both"):
    all_chans=np.load(filename)
    this_apa=get_apa(all_chans, apanum, planetype, wallorcryo)
    return pedsub(this_apa)

def split_contig(raw):
    """
    Split the input 2D array into multiple arrays with contiguous channel numbers
    """
    chs=raw[:,1]
    breaks=np.argwhere((chs[1:]-chs[:-1])!=1)
    ret=[]
    prev=0
    for i in np.hstack([breaks.ravel(), chs.shape[0]]):
        ret.append(raw[prev:i+1])
        prev=i+1
    return ret

def plot_on_axes(ax, s, minmax=100, rasterized=False, use_channel_number=False):
    if use_channel_number:
        chmin=np.min(s[:,1])
        chmax=np.max(s[:,1])
        contigs=split_contig(s)
        for contig in contigs:
            chans=contig[:,1]
            adcs=contig[:,2:]
            extent=[0, adcs.shape[1], np.min(chans), np.max(chans)]
            im=ax.imshow(adcs,
                       interpolation="none",
                       aspect="auto", 
                       cmap="coolwarm",
                       vmin=-1*minmax, vmax=minmax,
                       origin="lower",
                       rasterized=rasterized,
                       extent=extent)
        ax.set_ylim(chmin, chmax)
    else:
        adcs=s[:,2:]
        im=ax.imshow(adcs,
                   interpolation="none",
                   aspect="auto", 
                   cmap="coolwarm",
                   vmin=-1*minmax, vmax=minmax,
                   origin="lower",
                   rasterized=rasterized)
                   
    ax.set_xlabel("Time (tick)")
    ax.set_ylabel("Offline channel number" if use_channel_number else "Channel within view")
    return im

def plot_samples(s, minmax=100, figname=None, title=None, colorbarlabel="ADC", rasterized=False, use_channel_number=False):
    fig,ax=plt.subplots(nrows=1, ncols=1, squeeze=True, num=figname)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    im=plot_on_axes(ax, s, minmax, rasterized, use_channel_number)
    if title is not None: plt.title(title)
    fig.colorbar(im, cax=cax, orientation='vertical', label=colorbarlabel)
    return fig,ax

def make_filter(ntaps, multiplier, do_rounding):
    unrounded=firwin(ntaps, 0.1)*multiplier
    if do_rounding:
        return np.round(unrounded)
    else:
        return unrounded

def apply_filter(coeffs, waveform, multiplier):
    return np.array(np.convolve(waveform, coeffs, mode="valid"))/multiplier

def frugal_pedestal(raw_in):
    median=raw_in[0]
    ped=np.zeros_like(raw_in)
    for i,s in enumerate(raw_in):
        if s>median: median+=1
        if s<median: median-=1
        ped[i]=median
    return ped

def frugal_pedestal_sigkill(raw_in, lookahead, threshold, ncontig):
    median=raw_in[0]
    ped=np.zeros_like(raw_in)
    accum=0
    # Are we updating the median (because we're not within a hit)?
    updating=True
    for i in range(len(raw_in)-lookahead):
        s=raw_in[i] # The current sample
        sig_cand=raw_in[i+lookahead] # The sample a little way ahead
        # Do we later go over the threshold?
        cand_above=(sig_cand>median+threshold)
        # Are we currently below the threshold?
        current_below=(s<median)
        # Is there an upcoming transition over threshold? If so, freeze the pedestal...
        if updating and cand_above:
            updating=False
        # ...until we fall below the pedestal again
        if (not updating) and (current_below):
            updating=True
        # Do the frugal streaming if we're not in a hit
        if updating:
            if s>median: accum+=1
            if s<median: accum-=1

            if accum > ncontig:
                median+=1
                accum=0
            if accum < -1*ncontig:
                median-=1
                accum=0

        ped[i]=median
    # Get the last few samples, which we couldn't do in the main loop
    # because we'd go out-of-bounds
    for i in range(len(raw_in)-lookahead, len(raw_in)):
        ped[i]=median
    return ped

def stringToIntList(s):
    '''Convert a string of comma-separated natural numbers into a list, where the
       string may also contain ranges like "N-M". So some valid strings are
       "1,2", "1,3,10-20,21" etc'''
    ret=[]
    try:
        for i in s.split(","):
            if "-" in i:
                tmp=i.split("-")
                ret+=range(int(tmp[0]), int(tmp[1])+1)
            else:
                ret.append(int(i))
    except ValueError:
        raise Exception("stringToIntList: invalid subrun range string \"%s\"" % s)
    return ret

def plot_step(s, **kwargs):
    return plt.step(range(len(s)), s, **kwargs)
