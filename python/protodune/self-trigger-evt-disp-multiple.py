import waveform_utils as wutil
import numpy as np
import matplotlib.pyplot as plt
import argparse
import re
import arrow
import os.path

def plot_with_hits(ax, s, hits=None, minmax=100, use_channel_number=True):
    wutil.plot_on_axes(ax, s, minmax=minmax, use_channel_number=use_channel_number)
    if hits is not None:
        hit_ch=hits[:,0]
        hit_t=hits[:,1]
        ax.autoscale(False)
        ax.plot(hit_t, hit_ch+0.5, "gx")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filenames", required=True, help="Input file name list, comma separated")
    parser.add_argument("--apas", default=None,
                        help="Comma-separated list of APAs to show")
    parser.add_argument("--cmax", default=20, type=float,
                        help="Maximum value for the colour scale")
    parser.add_argument("--tmin", default=None, type=float,
                        help="Minimum value of time to show, in ticks since first time in file")
    parser.add_argument("--tmax", default=None, type=float,
                        help="Maximum value of time to show, in ticks since first time in file")
    parser.add_argument("--show-hits", action="store_true",
                        help='Show hits from a file with the same name as --filenames, but with "waveform" replaced by "hits"' )
    parser.add_argument("--batch", action="store_true",
                        help="Don't display anything on screen (useful if saving many event displays to file")
    parser.add_argument("--save-name", default=None,
                        help="Name of image file to save event display to")
    parser.add_argument("--format", default="offline", choices=["online", "offline"])
    
    parser.add_argument("--collection-only", action="store_true",
                        help="Only show collection view")
    parser.add_argument("--figsize", nargs=2, default=[6.4, 4.8], metavar=("width", "height"),
                        help="Set width and height of figure, if saved")

    
    args=parser.parse_args()

    files=[]
    
    if args.format=="online":
        time_start=[]
        time_end=[]
        lines_start=[]
        skiprows=[]
    
        for f in args.filenames.split(","):
            with open(f) as this_file:
                count=0
                time={}
                for x in this_file:
                    if count>0:
                        num_st = x.split(None, 1)[0]
                        num_64 = int(num_st, 0)
                        time[num_64] = count
                    count+=1
                    # if count>100:
                    #     break
                    
                time_start.append(min(time.keys()))
                time_end  .append(max(time.keys()))
                lines_start.append(time)
                
        time_start = max(time_start)
        time_end = min(time_end)
        print("Time start is for all the files is:", hex(time_start))
        print("Time end is for all the files is:", hex(time_end))
        
        for i,f in enumerate(args.filenames.split(",")):
            array = np.loadtxt(f).astype(np.int32)
            
            start_at = lines_start[i][time_start]
            end_at = lines_start[i][time_end]
            
            if (end_at+1<array.shape[0]):
                print("ignoring lines", end_at,"to", array.shape[0],"for file",f,"for time sync")
                array = np.delete(array, range(end_at+1,array.shape[0]), 0)
                                  
            if (start_at>1):
                print("ignoring lines 1 to", start_at,"for file",f,"for time sync")
                array = np.delete(array, range(1,start_at),0)

            files.append(array)
            
    else:
        for f in args.filenames.split(","):
            if f.endswith("npy"):
                files.append(np.load(f))
            else:
                files.append(np.loadtxt(f).astype(np.int32))
    
    # "Offline" format has a channel per row, with the first column
    # being the event number, and the second column being the channel
    # number. "Online" format has a channel per column. The first row
    # contains the channel numbers. The rest of the code assumes
    # "offline" format, so we just munge online arrays to look like
    # offline arrays right at the start: transpose, remove the
    # timestamp column, and add a fake "event number" column
    chans = np.array([])
    
    if args.format=="online":
        for i,f in enumerate(files):
            tmp=f.T[1:]
            z=np.zeros((tmp.shape[0],1), dtype=np.int32)
            a1=np.hstack((z,tmp))

            chans=np.append(chans,a1[:,1])
            
            if i==0:
                a = a1
            else:
                a=np.concatenate((a,a1))
            
    
    if args.apas:
        apas=[int(x) for x in args.apas.split(",")]
    else:
        apas=[3,1]

    views={}
    for apa in apas:
        for view in ("u", "v", "z"):
            views.setdefault(apa, {})[view]=wutil.pedsub(wutil.get_apa(a,
                                                                       apa,
                                                                       view,
                                                                       wallorcryo="both" if view=="z" else "both"))
                    

    # Parse the filenames for run, evt, timestamp
    fname_re=re.compile(r"np04_raw_run([0-9]+)_...._dl.*_waveform_evt([0-9]+)_t(0x[0-9a-f]+)")
    m=fname_re.search(args.filenames)
    if m:
        # Apparently python ignores leading zeros,
        # so don't have to worry about
        # accidentally interpreting the value as
        # octal here
        run=int(m.group(1))
        evt=int(m.group(2))
        timestamp=int(m.group(3), base=16)
        timestr=arrow.get(timestamp/50e6).format("YYYY-MM-DD HH:mm:ss UTC")
        title="Run %d, event %d (timestamp 0x%x, %s)" % (run, evt, timestamp, timestr)
    else:
        title=""

    if args.show_hits:
        hits_fname=args.filenames.replace("waveform", "hits").replace(".npy", ".txt")
        hits=np.loadtxt(hits_fname)
    else:
        hits=None

    nview=1 if args.collection_only else 3
    fig,ax=plt.subplots(len(apas), nview, sharex=True, gridspec_kw=dict(top=0.85, left=0.1, right=0.95, hspace=0.02), figsize=list(map(float, args.figsize)), squeeze=False)
    
    for i,apa in enumerate(apas):
        plot_with_hits(ax[i,0], views[apa]["z"], hits)
        if not args.collection_only:
            plot_with_hits(ax[i,1], views[apa]["u"], hits)
            plot_with_hits(ax[i,2], views[apa]["v"], hits)

    if args.tmin is not None: ax[0,0].set_xlim(left=args.tmin)
    if args.tmax is not None: ax[0,0].set_xlim(right=args.tmax)

    ax[0,0].set_title("Z view")
    if not args.collection_only:
        ax[0,1].set_title("U view")
        ax[0,2].set_title("V view")

    fig.suptitle(title, fontsize="small")

    for a in ax.flat: a.label_outer()

    if args.save_name:
        plt.savefig(args.save_name, bbox_inches="tight", dpi=200)

    if not args.batch: plt.show()
