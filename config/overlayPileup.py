import argparse
simparser = argparse.ArgumentParser()
simparser.add_argument('--inName', type=str, nargs = "+", help='Name of the input file', required=True)
simparser.add_argument('--inSignalName', type=str, help='Name of the input file with signal')
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('-N','--numEvents', type=int, help='Number of simulation events to run', required=True)
simparser.add_argument('--pileup', type=int, help='Pileup', default = 1000)
simparser.add_argument('--detectorPath', type=str, help='Path to detectors', default = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj")
simparser.add_argument('--rebase', action='store_true', help='Rebase the merged PU to baseline 0, with averaged mean values.', default=False)
simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
num_events = simargs.numEvents
path_to_detector = simargs.detectorPath
rebase = simargs.rebase
print "detectors are taken from: ", path_to_detector
input_name = simargs.inName
if simargs.inSignalName:
    input_signal_name = simargs.inSignalName
    print "input signal name: ", input_name
output_name = simargs.outName
print "input pileup name: ", input_name
print "output name: ", output_name
print "rebase mean energy/cell to 0: ", rebase
print "=================================="

from Gaudi.Configuration import *

# list of names of files with pileup event data -- to be overlaid
pileupFilenames = input_name
# the file containing the signal events
if simargs.inSignalName:
    signalFilename = input_signal_name
    noSignal = False
    # the collections to be read from the signal event
    signalCollections = ["GenParticles", "GenVertices",
                         "ECalBarrelCells", "ECalEndcapCells", "ECalFwdCells",
                         "HCalBarrelCells", "HCalExtBarrelCells", "HCalEndcapCells", "HCalFwdCells"]
    # Data service
    from Configurables import FCCDataSvc
    podioevent = FCCDataSvc("EventDataSvc", input=signalFilename)
    # use PodioInput for Signal
    from Configurables import PodioInput
    podioinput = PodioInput("PodioReader", collections=signalCollections, OutputLevel=DEBUG)
    list_of_algorithms = [podioevent]
else:
    signalFilename = ""
    noSignal = True
    list_of_algorithms = []
    from Configurables import FCCDataSvc
    podioevent = FCCDataSvc("EventDataSvc")
print signalFilename, noSignal

import random
seed=int(filter(str.isdigit, output_name))
print 'seed : ', seed
random.seed(seed)
random.shuffle(pileupFilenames)

##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################
path_to_detector = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj"
detectors_to_use=[path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalExtendedBarrel_TileCal.xml',
                  path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Endcaps_coneCryo.xml',
                  path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Forward_coneCryo.xml',
#                  path_to_detector+'/Detector/DetFCChhTailCatcher/compact/FCChh_TailCatcher.xml',
                  ]

from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc", detectors = detectors_to_use, OutputLevel = WARNING)

# edm data from generation: particles and vertices
from Configurables import PileupParticlesMergeTool
particlemergetool = PileupParticlesMergeTool("ParticlesMerge")
# branchnames for the pileup
particlemergetool.genParticlesBranch = "GenParticles"
particlemergetool.genVerticesBranch = "GenVertices"
# branchnames for the signal
particlemergetool.signalGenParticles.Path = "GenParticles"
particlemergetool.signalGenVertices.Path = "GenVertices"
# branchnames for the output
particlemergetool.mergedGenParticles.Path = "pileupGenParticles"
particlemergetool.mergedGenVertices.Path = "pileupGenVertices"

# edm data from simulation: hits and positioned hits
from Configurables import PileupCaloHitMergeTool
ecalbarrelmergetool = PileupCaloHitMergeTool("ECalBarrelHitMerge")
ecalbarrelmergetool.pileupHitsBranch = "ECalBarrelCells"
ecalbarrelmergetool.signalHits = "ECalBarrelCells"
ecalbarrelmergetool.mergedHits = "pileupECalBarrelCells"

# edm data from simulation: hits and positioned hits
ecalendcapmergetool = PileupCaloHitMergeTool("ECalEndcapHitMerge")
ecalendcapmergetool.pileupHitsBranch = "ECalEndcapCells"
ecalendcapmergetool.signalHits = "ECalEndcapCells"
ecalendcapmergetool.mergedHits = "pileupECalEndcapCells"

# edm data from simulation: hits and positioned hits
ecalfwdmergetool = PileupCaloHitMergeTool("ECalFwdHitMerge")
# branchnames for the pileup
ecalfwdmergetool.pileupHitsBranch = "ECalFwdCells"
ecalfwdmergetool.signalHits = "ECalFwdCells"
ecalfwdmergetool.mergedHits = "pileupECalFwdCells"

# edm data from simulation: hits and positioned hits
hcalbarrelmergetool = PileupCaloHitMergeTool("HCalBarrelHitMerge")
hcalbarrelmergetool.pileupHitsBranch = "HCalBarrelCells"
hcalbarrelmergetool.signalHits = "HCalBarrelCells"
hcalbarrelmergetool.mergedHits = "pileupHCalBarrelCells"

# edm data from simulation: hits and positioned hits
hcalextbarrelmergetool = PileupCaloHitMergeTool("HCalExtBarrelHitMerge")
hcalextbarrelmergetool.pileupHitsBranch = "HCalExtBarrelCells"
hcalextbarrelmergetool.signalHits = "HCalExtBarrelCells"
hcalextbarrelmergetool.mergedHits = "pileupHCalExtBarrelCells"

# edm data from simulation: hits and positioned hits
hcalfwdmergetool = PileupCaloHitMergeTool("HCalFwdHitMerge")
hcalfwdmergetool.pileupHitsBranch = "HCalFwdCells"
hcalfwdmergetool.signalHits = "HCalFwdCells"
hcalfwdmergetool.mergedHits = "pileupHCalFwdCells"

# edm data from simulation: hits and positioned hits
hcalfwdmergetool = PileupCaloHitMergeTool("HCalEndcapHitMerge")
hcalfwdmergetool.pileupHitsBranch = "HCalEndcapCells"
hcalfwdmergetool.signalHits = "HCalEndcapCells"
hcalfwdmergetool.mergedHits = "pileupHCalEndcapCells"

# use the pileuptool to specify the number of pileup
from Configurables import ConstPileUp
pileuptool = ConstPileUp("MyPileupTool", numPileUpEvents=simargs.pileup)

# algorithm for the overlay
from Configurables import PileupOverlayAlg
overlay = PileupOverlayAlg()
overlay.pileupFilenames = pileupFilenames
overlay.doShuffleInputFiles = True
overlay.randomizePileup = True
overlay.mergeTools = [
 "PileupParticlesMergeTool/ParticlesMerge",
  "PileupCaloHitMergeTool/ECalBarrelHitMerge",
  "PileupCaloHitMergeTool/ECalEndcapHitMerge",
  "PileupCaloHitMergeTool/ECalFwdHitMerge",
  "PileupCaloHitMergeTool/HCalBarrelHitMerge",
  "PileupCaloHitMergeTool/HCalExtBarrelHitMerge",
  "PileupCaloHitMergeTool/HCalEndcapHitMerge",
  "PileupCaloHitMergeTool/HCalFwdHitMerge"]
overlay.PileUpTool = pileuptool
overlay.noSignal = noSignal


ecalBarrelOutput1 = "mergedECalBarrelCells"
hcalBarrelOutput1 = "mergedHCalBarrelCells"

if rebase:
    ecalBarrelOutput1 = "mergedECalBarrelCellsStep1"
    hcalBarrelOutput1 = "mergedHCalBarrelCellsStep1"


##############################################################################################################
#######                                       DIGITISATION                                       #############
##############################################################################################################

from Configurables import CreateCaloCells
createEcalBarrelCells = CreateCaloCells("CreateEcalBarrelCells",
                                        doCellCalibration=False, recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False)
createEcalBarrelCells.hits.Path="pileupECalBarrelCells"
createEcalBarrelCells.cells.Path=ecalBarrelOutput1
createEcalEndcapCells = CreateCaloCells("CreateEcalEndcapCells",
                                        doCellCalibration=False, recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False)
createEcalEndcapCells.hits.Path="pileupECalEndcapCells"
createEcalEndcapCells.cells.Path="mergedECalEndcapCells"
createEcalFwdCells = CreateCaloCells("CreateEcalFwdCells",
                                     doCellCalibration=False, recalibrateBaseline =False,
                                     addCellNoise=False, filterCellNoise=False)
createEcalFwdCells.hits.Path="pileupECalFwdCells"
createEcalFwdCells.cells.Path="mergedECalFwdCells"
createHcalBarrelCells = CreateCaloCells("CreateHcalBarrelCells",
                                        doCellCalibration=False, recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False)
createHcalBarrelCells.hits.Path="pileupHCalBarrelCells"
createHcalBarrelCells.cells.Path=hcalBarrelOutput1
createHcalExtBarrelCells = CreateCaloCells("CreateHcalExtBarrelCells",
                                           doCellCalibration=False, recalibrateBaseline =False,
                                           addCellNoise=False, filterCellNoise=False)
createHcalExtBarrelCells.hits.Path="pileupHCalExtBarrelCells"
createHcalExtBarrelCells.cells.Path="mergedHCalExtBarrelCells"
createHcalEndcapCells = CreateCaloCells("CreateHcalEndcapCells",
                                        doCellCalibration=False, recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False)
createHcalEndcapCells.hits.Path="pileupHCalEndcapCells"
createHcalEndcapCells.cells.Path="mergedHCalEndcapCells"
createHcalFwdCells = CreateCaloCells("CreateHcalFwdCells",
                                     doCellCalibration=False, recalibrateBaseline =False,
                                     addCellNoise=False, filterCellNoise=False)
createHcalFwdCells.hits.Path="pileupHCalFwdCells"
createHcalFwdCells.cells.Path="mergedHCalFwdCells"

##############################################################################################################
#######                                       REBASE PU TO 0                              #############
##############################################################################################################
#Configure tools for calo cell positions
inputPileupNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/inBfield/cellNoise_map_fullGranularity_electronicsNoiseLevel_forPU"+str(simargs.pileup)+".root"

from Configurables import TopoCaloNoisyCells
readNoisyCellsMap = TopoCaloNoisyCells("ReadNoisyCellsMap",
                                       fileName = inputPileupNoisePerCell)

rebaseEcalBarrelCells = CreateCaloCells("RebaseECalBarrelCells",
                                        doCellCalibration=False,
                                        addCellNoise=False, filterCellNoise=False,
                                        recalibrateBaseline =True,
                                        readCellNoiseTool = readNoisyCellsMap,
                                        hits=ecalBarrelOutput1,
                                        cells="mergedECalBarrelCells")

rebaseHcalBarrelCells = CreateCaloCells("RebaseHCalBarrelCells",
                                        doCellCalibration=False,
                                        addCellNoise=False, filterCellNoise=False,
                                        recalibrateBaseline =True,
                                        readCellNoiseTool = readNoisyCellsMap,
                                        hits=hcalBarrelOutput1,
                                        cells="mergedHCalBarrelCells")
# PODIO algorithm
from Configurables import PodioOutput
out = PodioOutput("out", OutputLevel=DEBUG)
out.outputCommands = ["drop *", "keep pileupGenVertices", "keep pileupGenParticles", "keep mergedECalBarrelCells", "keep mergedECalEndcapCells", "keep mergedECalFwdCells", "keep mergedHCalBarrelCells", "keep mergedHCalExtBarrelCells", "keep mergedHCalEndcapCells", "keep mergedHCalFwdCells"]
out.filename = output_name

list_of_algorithms += [overlay,
                       createEcalBarrelCells,
                       createEcalEndcapCells,
                       createEcalFwdCells,
                       createHcalBarrelCells,
                       createHcalExtBarrelCells,
                       createHcalEndcapCells,
                       createHcalFwdCells,
                       ]

if rebase: 
    list_of_algorithms += [
        rebaseEcalBarrelCells,
        rebaseHcalBarrelCells,
        ]
    
list_of_algorithms += [out]

# ApplicationMgr
from Configurables import ApplicationMgr
ApplicationMgr( TopAlg=list_of_algorithms,
                EvtSel='NONE',
                EvtMax=num_events,
                ExtSvc=[geoservice, podioevent],
 #               OutputLevel = VERBOSE
 )
