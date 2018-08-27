import argparse
simparser = argparse.ArgumentParser()

simparser.add_argument('--inName', type=str, help='Name of the input file', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('-N','--numEvents',  type=int, help='Number of simulation events to run', required=True)
simparser.add_argument('--flat', action='store_true', help='flat energy distribution for single particle generation')

simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
num_events = simargs.numEvents
input_name = simargs.inName
output_name = simargs.outName
print "number of events = ", num_events
print "input name: ", input_name
print "output name: ", output_name
print "reco Barrel only:  ", simargs.flat

from Gaudi.Configuration import *
##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################
path_to_detector = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj"
detectors_to_use=[path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhTrackerTkLayout/compact/Tracker.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml']
if not simargs.flat:
    detectors_to_use += [path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalExtendedBarrel_TileCal.xml',
                         path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Endcaps_coneCryo.xml',
                         path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Forward_coneCryo.xml',
                         path_to_detector+'/Detector/DetFCChhTailCatcher/compact/FCChh_TailCatcher.xml',
                         path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_Solenoids.xml',
                         path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_Shielding.xml']

from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc", detectors = detectors_to_use, OutputLevel = WARNING)

# ECAL readouts
ecalBarrelReadoutName = "ECalBarrelPhiEta"
ecalEndcapReadoutName = "EMECPhiEtaReco"
ecalFwdReadoutName = "EMFwdPhiEta"
# HCAL readouts
hcalBarrelReadoutName = "HCalBarrelReadout"
hcalBarrelReadoutNamePhiEta = "BarHCal_Readout_phieta"
hcalExtBarrelReadoutName = "HCalExtBarrelReadout"
hcalExtBarrelReadoutNamePhiEta = "ExtBarHCal_Readout_phieta"
hcalEndcapReadoutName = "HECPhiEtaReco"
hcalFwdReadoutName = "HFwdPhiEta"
# Tail Catcher readout
tailCatcherReadoutName = "Muons_Readout"

hcalCellCollection = "HCalBarrelCells"

##############################################################################################################
#######                                        INPUT                                             #############
##############################################################################################################
# reads HepMC text file and write the HepMC::GenEvent to the data service
from Configurables import ApplicationMgr, FCCDataSvc, PodioInput, PodioOutput
podioevent = FCCDataSvc("EventDataSvc", input=input_name)

inputCollections = ["ECalBarrelCells", "HCalBarrelCells", "HCalExtBarrelCells", "ECalEndcapCells", "HCalEndcapCells", "ECalFwdCells", "HCalFwdCells", "TailCatcherCells","GenParticles","GenVertices"]

if simargs.flat:
    inputCollections = ["ECalBarrelCells", "HCalBarrelCells"]

podioinput = PodioInput("PodioReader", collections = inputCollections, OutputLevel = DEBUG)

##############################################################################################################                                                                                                                                
#######                                       RECALIBRATE ECAL                                   #############                                                                                                                                
##############################################################################################################                                                                                                                                

from Configurables import CalibrateInLayersTool, CreateCaloCells
recalibEcalBarrel = CalibrateInLayersTool("RecalibrateEcalBarrel",
                                          samplingFraction = [0.299654475899/0.12125] + [0.148166996525/0.14283] + [0.163005489744/0.16354] + [0.176907220821/0.17662] + [0.189980731321/0.18867] + [0.202201963561/0.19890] + [0.214090761907/0.20637] + [0.224706564289/0.20802],
                                          readoutName = ecalBarrelReadoutName,
                                          layerFieldName = "layer")
recreateEcalBarrelCells = CreateCaloCells("redoEcalBarrelCells",
                                          doCellCalibration=True,
                                          calibTool=recalibEcalBarrel, recalibrateBaseline =False,
                                          addCellNoise=False, filterCellNoise=False)
recreateEcalBarrelCells.hits.Path="ECalBarrelCells"
recreateEcalBarrelCells.cells.Path="ECalBarrelCellsRedo"

from Configurables import RewriteBitfield
rewriteECalEC = RewriteBitfield("RewriteECalEC",
                                # old bitfield (readout)
                                oldReadoutName = "EMECPhiEta",
                                # specify which fields are going to be deleted
                                removeIds = ["sublayer"],
                                # new bitfield (readout), with new segmentation
                                newReadoutName = ecalEndcapReadoutName,
                                debugPrint = 10)
# clusters are needed, with deposit position and cellID in bits
rewriteECalEC.inhits.Path = "ECalEndcapCells"
rewriteECalEC.outhits.Path = "newECalEndcapCells"

rewriteHCalEC = RewriteBitfield("RewriteHCalEC",
                                # old bitfield (readout)
                                oldReadoutName = "HECPhiEta",
                                # specify which fields are going to be deleted
                                removeIds = ["sublayer"],
                                # new bitfield (readout), with new segmentation
                                newReadoutName = hcalEndcapReadoutName,
                                debugPrint = 10)
# clusters are needed, with deposit position and cellID in bits
rewriteHCalEC.inhits.Path = "HCalEndcapCells"
rewriteHCalEC.outhits.Path = "newHCalEndcapCells"

##############################################################################################################                                                                                                                                
#######                                       RECALIBRATE ECAL                                   #############                                                                                                                                
##############################################################################################################                                                                                                                                

from Configurables import CalibrateInLayersTool, CreateCaloCells
recalibEcalBarrel = CalibrateInLayersTool("RecalibrateEcalBarrel",
                                          samplingFraction = [0.299654475899/0.12125] + [0.148166996525/0.14283] + [0.163005489744/0.16354] + [0.176907220821/0.17662] + [0.189980731321/0.18867] + [0.202201963561/0.19890] + [0.214090761907/0.20637] + [0.224706564289/0.20802],
                                          readoutName = ecalBarrelReadoutName,
                                          layerFieldName = "layer")
recreateEcalBarrelCells = CreateCaloCells("redoEcalBarrelCells",
                                          doCellCalibration=True,
                                          calibTool=recalibEcalBarrel,
                                          addCellNoise=False, filterCellNoise=False)
recreateEcalBarrelCells.hits.Path="ECalBarrelCells"
recreateEcalBarrelCells.cells.Path="ECalBarrelCellsRedo"

from Configurables import RewriteBitfield
rewriteECalEC = RewriteBitfield("RewriteECalEC",
                                # old bitfield (readout)
                                oldReadoutName = "EMECPhiEta",
                                # specify which fields are going to be deleted
                                removeIds = ["sublayer"],
                                # new bitfield (readout), with new segmentation
                                newReadoutName = ecalEndcapReadoutName,
                                debugPrint = 10)
# clusters are needed, with deposit position and cellID in bits
rewriteECalEC.inhits.Path = "ECalEndcapCells"
rewriteECalEC.outhits.Path = "newECalEndcapCells"

rewriteHCalEC = RewriteBitfield("RewriteHCalEC",
                                # old bitfield (readout)
                                oldReadoutName = "HECPhiEta",
                                # specify which fields are going to be deleted
                                removeIds = ["sublayer"],
                                # new bitfield (readout), with new segmentation
                                newReadoutName = hcalEndcapReadoutName,
                                debugPrint = 10)
# clusters are needed, with deposit position and cellID in bits
rewriteHCalEC.inhits.Path = "HCalEndcapCells"
rewriteHCalEC.outhits.Path = "newHCalEndcapCells"

##############################################################################################################
#######                                       CELL POSITIONS                                     #############
##############################################################################################################

#Configure tools for calo cell positions
from Configurables import CellPositionsECalBarrelTool, CellPositionsHCalBarrelNoSegTool, CellPositionsCaloDiscsTool, CellPositionsCaloDiscsTool, CellPositionsTailCatcherTool 
ECalBcells = CellPositionsECalBarrelTool("CellPositionsECalBarrel", 
                                    readoutName = ecalBarrelReadoutName)
HCalBcells = CellPositionsHCalBarrelNoSegTool("CellPositionsHCalBarrel", 
                                              readoutName = hcalBarrelReadoutName)
if not simargs.flat:
    EMECcells = CellPositionsCaloDiscsTool("CellPositionsEMEC", 
                                           readoutName = ecalEndcapReadoutName)
    ECalFwdcells = CellPositionsCaloDiscsTool("CellPositionsECalFwd", 
                                              readoutName = ecalFwdReadoutName)
    HCalExtBcells = CellPositionsHCalBarrelNoSegTool("CellPositionsHCalExtBarrel", 
                                                     readoutName = hcalExtBarrelReadoutName)
    HECcells = CellPositionsCaloDiscsTool("CellPositionsHEC", 
                                          readoutName = hcalEndcapReadoutName)
    HCalFwdcells = CellPositionsCaloDiscsTool("CellPositionsHCalFwd", 
                                              readoutName = hcalFwdReadoutName)
    TailCatchercells = CellPositionsTailCatcherTool("CellPositionsTailCatcher", 
                                                    readoutName = tailCatcherReadoutName, 
                                                    centralRadius = 901.5)

# cell positions
from Configurables import CreateCellPositions
positionsEcalBarrel = CreateCellPositions("positionsEcalBarrel", 
                                          positionsTool=ECalBcells, 
                                          hits = "ECalBarrelCellsRedo", 
                                          positionedHits = "ECalBarrelCellPositions")
positionsHcalBarrel = CreateCellPositions("positionsHcalBarrel", 
                                          positionsTool=HCalBcells, 
                                          hits = "HCalBarrelCells", 
                                          positionedHits = "HCalBarrelCellPositions")

if not simargs.flat:
    positionsHcalExtBarrel = CreateCellPositions("positionsHcalExtBarrel", 
                                                 positionsTool=HCalExtBcells, 
                                                 hits = "HCalExtBarrelCells", 
                                                 positionedHits = "HCalExtBarrelCellPositions")
    positionsEcalEndcap = CreateCellPositions("positionsEcalEndcap", 
                                              positionsTool=EMECcells, 
                                              hits = "newECalEndcapCells", 
                                              positionedHits = "ECalEndcapCellPositions")
    positionsHcalEndcap = CreateCellPositions("positionsHcalEndcap", 
                                              positionsTool=HECcells, 
                                              hits = "newHCalEndcapCells", 
                                              positionedHits = "HCalEndcapCellPositions")
    positionsEcalFwd = CreateCellPositions("positionsEcalFwd", 
                                           positionsTool=ECalFwdcells, 
                                           hits = "ECalFwdCells", 
                                           positionedHits = "ECalFwdCellPositions")
    positionsHcalFwd = CreateCellPositions("positionsHcalFwd", 
                                           positionsTool=HCalFwdcells, 
                                           hits = "HCalFwdCells", 
                                           positionedHits = "HCalFwdCellPositions")
    positionsTailCatcher = CreateCellPositions("positionsTailCatcher", 
                                               positionsTool=TailCatchercells, 
                                               hits = "TailCatcherCells", 
                                               positionedHits = "TailCatcherCellPositions")

# PODIO algorithm
out = PodioOutput("out", OutputLevel=DEBUG)
out.outputCommands = ["keep *","drop ECalBarrelCells","drop ECalEndcapCells","drop ECalFwdCells","drop HCalBarrelCells", "drop HCalExtBarrelCells", "drop HCalEndcapCells", "drop HCalFwdCells", "drop TailCatcherCells"]
out.filename = "edm.root"

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
podioinput.AuditExecute = True
recreateEcalBarrelCells.AuditExecute = True
positionsEcalBarrel.AuditExecute = True
positionsHcalBarrel.AuditExecute = True
out.AuditExecute = True

list_of_algorithms = [podioinput,
                      recreateEcalBarrelCells,
                      positionsEcalBarrel,
                      positionsHcalBarrel]
 
if not simargs.flat:
    list_of_algorithms += [ rewriteECalEC,
                            rewriteHCalEC,
                            positionsEcalEndcap,
                            positionsEcalFwd, 
                            positionsHcalExtBarrel, 
                            positionsHcalEndcap, 
                            positionsHcalFwd,
                            positionsTailCatcher,
                            out]
else:
    list_of_algorithms += [out]

ApplicationMgr(
    TopAlg = list_of_algorithms,
    EvtSel = 'NONE',
    EvtMax   = num_events,
    ExtSvc = [geoservice, podioevent, audsvc],
    #OutputLevel = DEBUG
)
