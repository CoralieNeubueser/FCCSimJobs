import argparse
simparser = argparse.ArgumentParser()
simparser.add_argument('--inName', type=str, help='Name of the input file', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('--detectorPath', type=str, help='Path to detectors', default = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj")
simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
input_name = simargs.inName
output_name = simargs.outName
path_to_detector = simargs.detectorPath
print "detectors are taken from: ", path_to_detector
print "input name: ", input_name
print "output name: ", output_name
print "=================================="

from Gaudi.Configuration import *

from Configurables import ApplicationMgr, FCCDataSvc, PodioOutput

# v01 production - min. bias events
podioevent = FCCDataSvc("EventDataSvc", input=input_name)

from Configurables import PodioInput

podioinput = PodioInput("in", collections = ["ECalBarrelCells"])

from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc", detectors = [ path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
],
                    OutputLevel = WARNING)

# Pileup in ECal Barrel
# readout name
ecalBarrelReadoutNamePhiEta = "ECalBarrelPhiEta"
# hcalBarrelReadoutNamePhiEta = "BarHCal_Readout_phieta"

# geometry tool
from Configurables import TubeLayerPhiEtaCaloTool
ecalBarrelGeometry = TubeLayerPhiEtaCaloTool("EcalBarrelGeo",
                                             readoutName = ecalBarrelReadoutNamePhiEta,
                                             activeVolumeName = "LAr_sensitive",
                                             activeFieldName = "layer",
                                             fieldNames = ["system"],
                                             fieldValues = [5],
                                             activeVolumesNumber = 8)

from Configurables import CreateEmptyCaloCellsCollection
createemptycells = CreateEmptyCaloCellsCollection("CreateEmptyCaloCells")
createemptycells.cells.Path = "emptyCaloCells"
#Create calo clusters
from Configurables import CreateCaloClustersSlidingWindow, CaloTowerTool
from GaudiKernel.PhysicalConstants import pi

towers = CaloTowerTool("towers",
                               deltaEtaTower = 0.01, deltaPhiTower = 2*pi/704.,
                               ecalBarrelReadoutName = ecalBarrelReadoutNamePhiEta,
                               ecalEndcapReadoutName = "",
                               ecalFwdReadoutName = "",
                               hcalBarrelReadoutName = "",
                               hcalExtBarrelReadoutName = "",
                               hcalEndcapReadoutName = "",
                               hcalFwdReadoutName = "")
towers.ecalBarrelCells.Path = "ECalBarrelCells"
towers.ecalEndcapCells.Path = "emptyCaloCells"
towers.ecalFwdCells.Path = "emptyCaloCells"
towers.hcalBarrelCells.Path = "emptyCaloCells"
towers.hcalExtBarrelCells.Path = "emptyCaloCells"
towers.hcalEndcapCells.Path = "emptyCaloCells"
towers.hcalFwdCells.Path = "emptyCaloCells"

# call pileup tool
# prepare TH2 histogram with pileup per abs(eta)
from Configurables import PreparePileup
pileupEcalBarrel = PreparePileup("PreparePileupEcalBarrel",
                                 geometryTool = ecalBarrelGeometry,
                                 readoutName = ecalBarrelReadoutNamePhiEta,
                                 layerFieldName = "layer",
                                 towerTool = towers,
                                 histogramName = "ecalBarrelEnergyVsAbsEta",
                                 numLayers = 8,
                                 etaSize = [7,  5,  7,   9,    3,      3],
                                 phiSize = [19,15, 21, 21,  15,  11])
pileupEcalBarrel.hits.Path="ECalBarrelCells"

THistSvc().Output = ["rec DATAFILE='" + output_name + "' TYP='ROOT' OPT='RECREATE'"]
THistSvc().PrintAll=True
THistSvc().AutoSave=True
THistSvc().AutoFlush=True
THistSvc().OutputLevel=INFO

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
podioinput.AuditExecute = True

ApplicationMgr(
    TopAlg = [podioinput,
              createemptycells,
              pileupEcalBarrel,
              ],
    EvtSel = 'NONE',
    EvtMax = -1,
    ExtSvc = [podioevent, geoservice],
 )
