#include "../read_samples.h"
#include <iostream>
#include <iomanip>

void print_some(Waveforms<short>& w)
{
    std::cout << "channel #s: ";
    for(int i=0; i<10; ++i){
        std::cout << w.channels[i] << " ";
    }
    std::cout << std::endl;

    for(int i=0; i<10; ++i){
        for(int j=0; j<10; ++j){
            std::cout << std::setw(7) << w.samples[i][j] << " ";
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;
}

int main()
{
    Waveforms<short> samples_text=read_samples_text<short>("deleteme", 0);
    std::cout << "From text file: " << std::endl;
    print_some(samples_text);
    Waveforms<short> samples_npy=read_samples_npy<short>("deleteme.npy", 0);
    std::cout << "From numpy file: " << std::endl;
    print_some(samples_npy);
}
