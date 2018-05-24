#include <chrono>
#include <functional>
#include <iostream>
#include <string>
#include <vector>
#include <fstream>

#include "boost/program_options.hpp"

#include "canvas/Utilities/InputTag.h"
#include "gallery/Event.h"

#include "lardataobj/Simulation/SimChannel.h"
#include "lardataobj/RawData/RawDigit.h"

using namespace art;
using namespace std;
using namespace std::chrono;

namespace po = boost::program_options;

void
extract_larsoft_waveforms(std::string const& filename,
                          std::string const& outfile,
                          std::string const& truth_outfile,
                          int nevents, bool onlySignal)
{
  InputTag daq_tag{ "daq" };
  // Create a vector of length 1, containing the given filename.
  vector<string> filenames(1, filename);

  std::ofstream fout(outfile);
  std::ofstream* fout_truth(truth_outfile!="" ? new std::ofstream(truth_outfile) : nullptr);

  int iev=0;
  for (gallery::Event ev(filenames); !ev.atEnd(); ev.next()) {
    std::set<int> channelsWithSignal;
    if(iev>=nevents) break;
    std::cout << "Event " << iev << std::endl;
    //------------------------------------------------------------------
    // Get the SimChannels so we can see where the actual energy depositions were
    auto& simchs=*ev.getValidHandle<std::vector<sim::SimChannel>>(InputTag{"largeant"});

    for(auto&& simch: simchs){
      channelsWithSignal.insert(simch.Channel());
      if(fout_truth){
          double charge=0;
          (*fout_truth) << iev << " " << simch.Channel() << " ";
          for (const auto& TDCinfo: simch.TDCIDEMap()) {
              for (const sim::IDE& ide: TDCinfo.second) {
                  charge += ide.numElectrons;
              } // for IDEs
              auto const tdc = TDCinfo.first;
              (*fout_truth) << tdc << " " << charge << " ";
          } // for TDCs
          (*fout_truth) << std::endl;
      }
    } // loop over SimChannels

    //------------------------------------------------------------------
    // Look at the digits
    auto& digits =
      *ev.getValidHandle<vector<raw::RawDigit>>(daq_tag);
    for(auto&& digit: digits){
      if(digit.Compression()!=0){
        std::cout << "Compression type " << digit.Compression() << std::endl;
      }
      if(onlySignal && channelsWithSignal.find(digit.Channel())==channelsWithSignal.end()){
        continue;
      }
      fout << iev << " " << digit.Channel() <<  " ";
      for(auto&& sample: digit.ADCs()){
        fout << sample << " ";
      }
      fout << std::endl;
    } // end loop over digits (=?channels)
    ++iev;
  } // end loop over events
}

int main(int argc, char** argv)
{
    po::options_description desc("Allowed options");
    desc.add_options()
        ("help,h", "produce help message")
        ("input,i", po::value<string>(), "input file name")
        ("output,o", po::value<string>(), "output file name")
        ("truth,t", po::value<string>()->default_value(""), "truth output file name")
        ("nevent,n", po::value<int>()->default_value(1), "number of events")
        ("onlysignal", "only output channels with true signal")
        ;

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);    

    if(vm.count("help") || vm.empty()) {
        cout << desc << "\n";
        return 1;
    }

    if(!vm.count("input")){
        cout << "No input file specified" << endl;
        cout << desc << endl;
        return 1;
    }

    if(!vm.count("output")){
        cout << "No output file specified" << endl;
        cout << desc << endl;
        return 1;
    }

    extract_larsoft_waveforms(vm["input"].as<string>(),
                              vm["output"].as<string>(),
                              vm["truth"].as<string>(),
                              vm["nevent"].as<int>(),
                              vm.count("onlysignal"));
    return 0;
}
