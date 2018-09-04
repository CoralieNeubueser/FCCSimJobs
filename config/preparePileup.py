import argparse
simparser = argparse.ArgumentParser()
simparser.add_argument('--inName', type=str, help='Name of the input file', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('--detectorPath', type=str, help='Path to detectors', default = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj")
simparser.add_argument('--prefixCollections', type=str, help='Prefix added to the collection names', default="")
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
prefix = simargs.prefixCollections
print "prefix : ", prefix
print "=================================="

from Gaudi.Configuration import *

from Configurables import ApplicationMgr, FCCDataSvc, PodioOutput

# v01 production - min. bias events
podioevent = FCCDataSvc("EventDataSvc", input=input_name)

from Configurables import PodioInput

podioinput = PodioInput("in", collections = [prefix+"ECalBarrelCells", prefix+"HCalBarrelCells"])

from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc", detectors = [ path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                                            path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                                            path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml',
                                            ],
                    OutputLevel = WARNING)

# Pileup in ECal Barrel
# readout name
ecalBarrelReadoutNamePhiEta = "ECalBarrelPhiEta"
hcalBarrelReadoutName = "HCalBarrelReadout"
hcalBarrelReadoutNamePhiEta = "BarHCal_Readout_phieta"

##############################################################################################################                                                                                                 
#######                                       CELL POSITIONS  TOOLS                              #############                                                                                                 
##############################################################################################################                                                                                                                              
# Configure tools for calo cell positions                                                                            
from Configurables import CellPositionsECalBarrelTool, CellPositionsHCalBarrelNoSegTool, CellPositionsHCalBarrelTool
ECalBcells = CellPositionsECalBarrelTool("CellPositionsECalBarrel",
                                         readoutName = ecalBarrelReadoutNamePhiEta,
                                         OutputLevel = INFO)
HCalBcellVols = CellPositionsHCalBarrelNoSegTool("CellPositionsHCalBarrelVols",
                                                 readoutName = hcalBarrelReadoutName,
                                                 OutputLevel = INFO)
HCalBsegcells = CellPositionsHCalBarrelTool("CellPositionsHCalSegBarrel",
                                            readoutName = hcalBarrelReadoutNamePhiEta,
                                            radii = [291.05, 301.05, 313.55, 328.55, 343.55, 358.55, 378.55, 413.55, 428.55, 453.55],
                                            OutputLevel = INFO)

##############################################################################################################                                                                                                          
#######                                       RESEGMENT HCAL                                   #############                                                                                                                                
##############################################################################################################                                                                                                                              
from Configurables import CreateVolumeCaloPositions,RedoSegmentation,CreateCaloCells,CreateCellPositions
# Create cells in HCal                                           
# 2. step - rewrite the cellId using the Phi-Eta segmentation    
# 3. step - merge new cells corresponding to eta-phi segmentation
# Hcal barrel cell positions                                                                                                                                                                                                                 
posHcalBarrel = CreateCellPositions("posHcalBarrel",
                                    positionsTool=HCalBcellVols,
                                    hits = prefix+"HCalBarrelCells",
                                    positionedHits = "HCalBarrelPositions")

# Use Phi-Eta segmentation in Hcal barrel                       
resegmentHcalBarrel = RedoSegmentation("ReSegmentationHcal",
                                       # old bitfield (readout) 
                                       oldReadoutName = hcalBarrelReadoutName,
                                       # specify which fields are going to be altered (deleted/rewritten)                                                                                                                              
                                       oldSegmentationIds = ["module","row"],
                                       # new bitfield (readout), with new segmentation                                                                                                                                                 
                                       newReadoutName = hcalBarrelReadoutNamePhiEta,
                                       inhits = "HCalBarrelPositions",
                                       outhits = "HCalBarrelCellsStep2")

createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                        doCellCalibration=False,recalibrateBaseline =False, 
                                        addCellNoise=False, filterCellNoise=False,
                                        hits="HCalBarrelCellsStep2",
                                        cells="newHCalBarrelCells")

# geometry tool
from Configurables import TubeLayerPhiEtaCaloTool, LayerPhiEtaCaloTool
ecalBarrelGeometry = TubeLayerPhiEtaCaloTool("EcalBarrelGeo",
                                             readoutName = ecalBarrelReadoutNamePhiEta,
                                             activeVolumeName = "LAr_sensitive",
                                             activeFieldName = "layer",
                                             fieldNames = ["system"],
                                             fieldValues = [5],
                                             activeVolumesNumber = 8)
# Geometry for layer-eta-phi segmentation                                                                                                                                                                                                  
hcalBarrelGeometry = LayerPhiEtaCaloTool("HcalBarrelGeo",
                                         readoutName = "BarHCal_Readout_phieta",
                                         activeVolumeName = "layerVolume",
                                         activeFieldName = "layer",
                                         fieldNames = ["system"],
                                         fieldValues = [8],
                                         activeVolumesNumber = 10,
                                         activeVolumesEta = [1.2524, 1.2234, 1.1956, 1.15609, 1.1189, 1.08397, 1.0509, 0.9999, 0.9534, 0.91072]
                                         )

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
                               hcalBarrelReadoutName = hcalBarrelReadoutNamePhiEta,
                               hcalExtBarrelReadoutName = "",
                               hcalEndcapReadoutName = "",
                               hcalFwdReadoutName = "")
towers.ecalBarrelCells.Path = prefix+"ECalBarrelCells"
towers.ecalEndcapCells.Path = "emptyCaloCells"
towers.ecalFwdCells.Path = "emptyCaloCells"
towers.hcalBarrelCells.Path = "newHCalBarrelCells"
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
                                 etaSize = [7,  5,  7,   9,   3,   3,  99],
                                 phiSize = [19, 15, 21, 21,  15,  11, 101])
pileupEcalBarrel.hits.Path=prefix+"ECalBarrelCells"

pileupHcalBarrel = PreparePileup("PreparePileupHcalBarrel",
                                 geometryTool = hcalBarrelGeometry,
                                 readoutName = hcalBarrelReadoutNamePhiEta,
                                 layerFieldName = "layer",
                                 towerTool = towers,
                                 histogramName = "hcalBarrelEnergyVsAbsEta",
                                 numLayers = 10,
                                 etaSize = [7,  5,  7,   9,   3,   3,  99],
                                 phiSize = [19, 15, 21, 21,  15,  11, 101])
pileupHcalBarrel.hits.Path="newHCalBarrelCells"

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
              posHcalBarrel,
              resegmentHcalBarrel,
              createHcalBarrelCells,
              createemptycells,
              pileupEcalBarrel,
              pileupHcalBarrel,
              ],
    EvtSel = 'NONE',
    EvtMax = -1,
    ExtSvc = [podioevent, geoservice],
 )
