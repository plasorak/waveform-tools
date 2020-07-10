# Python tools for raw data

The only tool so far is `self-trigger-evt-disp.py` which will draw an event display from a text or numpy file. You'll need the python packages `numpy`, `matplotlib` and `arrow` installed. Both python 2 and python 3 should work, although most testing has been in python 2.

Two input formats are supported: "offline", which is the format produced by `extract_larsoft_waveforms` in this repository; and "online", which is the format produced by `dumpfile_to_text` in [philiprodrigues/felix-long-readout-tools](https://github.com/philiprodrigues/felix-long-readout-tools). Specify the format of the input file with the `--format` flag.

Typical usage:

```bash
python self-trigger-evt-disp.py --filename felix-2020-06-02-093338.0.1.0-10k-ticks.txt --format=online --apas 5
```
