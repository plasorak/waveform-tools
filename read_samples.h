#ifndef READ_SAMPLES_H
#define READ_SAMPLES_H

#include <fstream>
#include <sstream>
#include <vector>
#include <iostream>
#include <utility> // for std::pair

#include "cnpy.h"

// A struct to hold waveforms with sample type `T`
template<class T>
struct Waveforms
{
    // List of channel numbers
    std::vector<int> channels;
    // Waveforms in each channel. First index is channel, second index
    // is sample
    std::vector<std::vector<T> > samples;
};

// Read up to `max_channels` channels from `inputfile` produced by `extract_larsoft_waveforms`
template<class T>
Waveforms<T> read_samples_text(const char* inputfile, unsigned int max_channels)
{
    Waveforms<T> ret;

    // We do all this rigmarole because we want to get the number of
    // samples from the input file instead of hardcoding it

    std::ifstream ifstr(inputfile);
    T sample;
    unsigned int ichan=0; // channel counter
    unsigned int nsamples=0;
    // Each line in the input file is the set of samples for a given channel
    std::string input_line;
    while(std::getline(ifstr, input_line)){
        std::istringstream istr(input_line);

        std::vector<T> chan_samples;
        // The first two entries in each line are the event number and
        // channel number. We're going to hack things and pretend that
        // everything comes from one events with way more channels than
        // there actually are, so I don't have to separate out events
        // later. The simulated geometry is 1x2x6, ie 12 APAs, so just
        // offset the channel number by (evt no)*(channels per
        // APA)*(1*2*6)
        int evtno;
        istr >> evtno;
        int chno;
        istr >> chno;
        const int channels_per_apa=2560;
        int modified_chno=evtno*channels_per_apa*12+chno;
        ret.channels.push_back(modified_chno);
        // Now read the actual samples
        while(istr >> sample){
            chan_samples.push_back(sample);
        }
        // Make sure we get the same number of samples on each line (ie, for each channel)
        if(ichan==0){
            nsamples=chan_samples.size();
        }
        else{
            if(chan_samples.size() != nsamples){
                std::cerr << "Got " << ret.samples[ichan].size() << " samples on channel " << ichan << ": expected " << nsamples << std::endl;
                exit(1);
            }
        }
        ret.samples.push_back(chan_samples);
        ++ichan;

        if(max_channels>0 && ichan>=max_channels) break;
    }
    // Check we filled all the channels
    if(ret.samples.back().size()!=nsamples){
        std::cerr << "Didn't read all the channels" << std::endl;
        exit(1);
    }

    return ret;
}

template<class T>
Waveforms<T> read_samples_npy(const char* inputfile, unsigned int max_channels)
{
    Waveforms<T> ret;

    cnpy::NpyArray arr = cnpy::npy_load(inputfile);
    int nchannels=max_channels>0 ? max_channels : arr.shape[0];
    int nsamples=arr.shape[1];
    int nadcsamples=nsamples-2;
    ret.samples.resize(nchannels);
    for(int ichan=0; ichan<nchannels; ++ichan){
        // The first two entries in each line are the event number and
        // channel number. We're going to hack things and pretend that
        // everything comes from one events with way more channels than
        // there actually are, so I don't have to separate out events
        // later. The simulated geometry is 1x2x6, ie 12 APAs, so just
        // offset the channel number by (evt no)*(channels per
        // APA)*(1*2*6)
        int evtno=arr.data<int>()[ichan*nsamples+0];
        int chno=arr.data<int>()[ichan*nsamples+1];
        const int channels_per_apa=2560;
        int modified_chno=evtno*channels_per_apa*12+chno;
        ret.channels.push_back(modified_chno);
        
        for(int isample=2; isample<nsamples; ++isample){
            int sample=arr.data<int>()[ichan*nsamples+isample];
            ret.samples[ichan].push_back((T)sample);
        }
    }

    // Check we filled all the channels
    if(ret.samples.back().size()!=nadcsamples){
        std::cerr << "Didn't read all the channels" << std::endl;
        exit(1);
    }

    return ret;
}

#endif // include guard
