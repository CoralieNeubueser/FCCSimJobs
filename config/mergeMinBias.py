import argparse, os, math
simparser = argparse.ArgumentParser()

simparser.add_argument('--inNames', nargs='+', help='Names of the input files', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('-N','--numEvents',  type=int, help='Number of simulation events to run', required=True)

simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
num_events = simargs.numEvents
All_pileupfilenames = simargs.inNames
output_name = simargs.outName

newList = []
for ifile in All_pileupfilenames:
    infile1 = ifile.replace(',', ' ')
    infile2 = infile1.replace('[', ' ')
    infile3 = infile2.replace(']', ' ')
    newList.append(infile3)
    
print "number of events = ", num_events
print "input file names: ", newList
print "output name: ", output_name

from Gaudi.Configuration import *
##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################

path_to_detector = '/afs/cern.ch/work/h/helsens/public/FCCsoft/FCCSW-0.8.3/'
detectors_to_use=[path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhTrackerTkLayout/compact/Tracker.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalExtendedBarrel_TileCal.xml',
                  path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Endcaps_coneCryo.xml',
                  path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Forward_coneCryo.xml',
                  path_to_detector+'/Detector/DetFCChhTailCatcher/compact/FCChh_TailCatcher.xml',
                  path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_Solenoids.xml',
                  path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_Shielding.xml']

from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc", detectors = detectors_to_use, OutputLevel = WARNING)

# Names of cells collections
ecalBarrelCellsName = "ECalBarrelCells"
ecalEndcapCellsName = "ECalEndcapCells"
ecalFwdCellsName = "ECalFwdCells"
hcalBarrelCellsName = "HCalBarrelCells"
hcalExtBarrelCellsName = "HCalExtBarrelCells"
hcalEndcapCellsName = "HCalEndcapCells"
hcalFwdCellsName = "HCalFwdCells"

##############################################################################################################
#######                                        INPUT                                             #############
##############################################################################################################

# reads HepMC text file and write the HepMC::GenEvent to the data service
from Configurables import ApplicationMgr, FCCDataSvc, PodioInput, PodioOutput
podioevent = FCCDataSvc("EventDataSvc")

podioinput = PodioInput("PodioReader", collections = ["ECalBarrelCells", "HCalBarrelCells", "HCalExtBarrelCells", "ECalEndcapCells", "HCalEndcapCells", "ECalFwdCells", "HCalFwdCells", "TailCatcherCells"], OutputLevel = DEBUG)

pileupFilenames = [f for f in newList if 'converted' not in f]
import random
random.shuffle(pileupFilenames)

from Configurables import PileupParticlesMergeTool
particlemergetool = PileupParticlesMergeTool("MyPileupParticlesMergeTool")
# branchnames for the pileup
particlemergetool.genParticlesBranch = "GenParticles"
particlemergetool.genVerticesBranch = "GenVertices"
# branchnames for the signal
particlemergetool.signalGenVertices.Path = "GenVertices"
particlemergetool.signalGenParticles.Path = "GenParticles"
# branchnames for the output
particlemergetool.mergedGenParticles.Path = "overlaidGenParticles"
particlemergetool.mergedGenVertices.Path = "overlaidGenVertices"

# edm data from simulation: hits and positioned hits for the EM Calo
from Configurables import PileupCaloCellMergeTool
ECalhitsmergetool = PileupCaloCellMergeTool("MyECalHitMergeTool")
# branchnames for the pileup
ECalhitsmergetool.pileupHitsBranch = ecalBarrelCellsName
# branchnames for the signal
ECalhitsmergetool.signalHits = ecalBarrelCellsName
# branchnames for the output
ECalhitsmergetool.mergedHits = "overlaidECalBarrelCells"
ECalEChitsmergetool = PileupCaloCellMergeTool("MyECalECHitMergeTool")
# branchnames for the pileup
ECalEChitsmergetool.pileupHitsBranch = ecalEndcapCellsName
# branchnames for the signal
ECalEChitsmergetool.signalHits = ecalEndcapCellsName
# branchnames for the output
ECalEChitsmergetool.mergedHits = "overlaidECalEndcapsCells"
ECalFwdhitsmergetool = PileupCaloCellMergeTool("MyECalFwdHitMergeTool")
# branchnames for the pileup
ECalFwdhitsmergetool.pileupHitsBranch = ecalFwdCellsName
# branchnames for the signal
ECalFwdhitsmergetool.signalHits = ecalFwdCellsName
# branchnames for the output
ECalFwdhitsmergetool.mergedHits = "overlaidECalFwdCells"

HCalhitsmergetool = PileupCaloCellMergeTool("MyHCalHitMergeTool")
# branchnames for the pileup
HCalhitsmergetool.pileupHitsBranch = hcalBarrelCellsName
# branchnames for the signal
HCalhitsmergetool.signalHits = hcalBarrelCellsName
# branchnames for the output
HCalhitsmergetool.mergedHits = "overlaidHCalBarrelCells"
HCalExthitsmergetool = PileupCaloCellMergeTool("MyHCalExtHitMergeTool")
# branchnames for the pileup
HCalExthitsmergetool.pileupHitsBranch = hcalExtBarrelCellsName
# branchnames for the signal
HCalExthitsmergetool.signalHits = hcalExtBarrelCellsName
# branchnames for the output
HCalExthitsmergetool.mergedHits = "overlaidHCalExtBarrelCells"
HCalEChitsmergetool = PileupCaloCellMergeTool("MyHCalECHitMergeTool")
# branchnames for the pileup
HCalEChitsmergetool.pileupHitsBranch = hcalEndcapCellsName
# branchnames for the signal
HCalEChitsmergetool.signalHits = hcalEndcapCellsName
# branchnames for the output
HCalEChitsmergetool.mergedHits = "overlaidHCalEndcapCells"
HCalFwdhitsmergetool = PileupCaloCellMergeTool("MyHCalFwdHitMergeTool")
# branchnames for the pileup
HCalFwdhitsmergetool.pileupHitsBranch = hcalFwdCellsName
# branchnames for the signal
HCalFwdhitsmergetool.signalHits = hcalFwdCellsName
# branchnames for the output
HCalFwdhitsmergetool.mergedHits = "overlaidHCalFwdCells"


# use the pileuptool to specify the number of pileup
from Configurables import ConstPileUp
pileuptool = ConstPileUp("MyPileupTool", numPileUpEvents=num_events)

# algorithm for the overlay
from Configurables import PileupOverlayAlg
overlay = PileupOverlayAlg()
overlay.pileupFilenames = pileupFilenames
overlay.randomizePileup = False
overlay.noSignal = True
overlay.mergeTools = [
                      "PileupCaloCellMergeTool/MyECalHitMergeTool",
#                      "PileupCaloCellMergeTool/MyECalECHitMergeTool",
#                      "PileupCaloCellMergeTool/MyECalFwdHitMergeTool",
                      "PileupCaloCellMergeTool/MyHCalHitMergeTool"
#                      "PileupCaloCellMergeTool/MyHCalExtHitMergeTool",
#                      "PileupCaloCellMergeTool/MyHCalECHitMergeTool",
#                      "PileupCaloCellMergeTool/MyHCalFwdHitMergeTool",
                      ]
overlay.PileUpTool = pileuptool

################################################################
################################################################


out = PodioOutput("out", 
                  OutputLevel=INFO)
out.outputCommands = ["keep *", "drop ECalBarrelCells", "drop HCalBarrelCells", "drop HCalExtBarrelCells", "drop ECalEndcapCells", "drop HCalEndcapCells", "drop ECalFwdCells", "drop HCalFwdCells", "drop TailCatcherCells" ]
out.filename = "output_pileupOverlay.root"

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
out.AuditExecute = True

ApplicationMgr(
    TopAlg = [
        overlay,
        out
        ],
    EvtSel = 'NONE',
    # input are 10 files, assuming every file has 100events 
    EvtMax   = math.floor(10*100/float(num_events)),
    ExtSvc = [podioevent, geoservice, audsvc],
    OutputLevel = VERBOSE
 )

