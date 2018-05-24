# Tools for extracting waveforms from DUNE MC

## Contents

### `extract_larsoft_waveforms.cxx`

Extracts waveforms from a non-zero-suppressed DUNE MC file using
[http://art.fnal.gov/gallery](gallery). If you're on a Fermilab
machine, `source setup.sh` should set up everything you'll need.

The software is built using `cmake`, so eg:

```shell
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
make
```

Output is to text file or numpy format (using
[https://github.com/rogersce/cnpy](cnpy)). See
`extract_larsoft_waveforms --help` for options, and see the source for
a description of the output format.

### `read_samples.h`

Contains functions to read the output from `extract_larsoft_waveforms.cxx` (in text or numpy format) back into C++
