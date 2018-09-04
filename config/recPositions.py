import argparse
simparser = argparse.ArgumentParser()

simparser.add_argument('--inName', type=str, help='Name of the input file', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('-N','--numEvents',  type=int, help='Number of simulation events to run', required=True)
simparser.add_argument('--flat', action='store_true', help='flat energy distribution for single particle generation')
simparser.add_argument('--prefixCollections', type=str, help='Prefix added to the collection names', default="")
simparser.add_argument("--addMuons", action='store_true', help="Add tail catcher cells", default = False)
simparser.add_argument("--resegmentHCal", action='store_true', help="Merge HCal cells in DeltaEta=0.025 bins", default = False)
simparser.add_argument('--detectorPath', type=str, help='Path to detectors', default = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj")

simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
num_events = simargs.numEvents
input_name = simargs.inName
output_name = simargs.outName
prefix = simargs.prefixCollections
addMuons = simargs.addMuons
resegmentHCal = simargs.resegmentHCal
path_to_detector = simargs.detectorPath
print "number of events = ", num_events
print "input name: ", input_name
print "output name: ", output_name
print "reco Barrel only:  ", simargs.flat
print "prefix added to the collections' name: ", prefix
print "Muons: ", addMuons
print "resegment HCal: ", resegmentHCal

from Gaudi.Configuration import *
##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################
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

coll_names_read = [prefix+"ECalBarrelCells", prefix+"HCalBarrelCells", prefix+"HCalExtBarrelCells", prefix+"ECalEndcapCells", prefix+"HCalEndcapCells", prefix+"ECalFwdCells", prefix+"HCalFwdCells"]

if addMuons:
    coll_names_read += ["TailCatcherCells"]

elif simargs.flat:
    coll_names_read= ["ECalBarrelCells", "HCalBarrelCells"]

if not prefix:
    coll_names_read += ["GenParticles", "GenVertices"]

podioinput = PodioInput("PodioReader", collections = coll_names_read, OutputLevel = DEBUG)

hcalCells = prefix+"HCalBarrelCells"
hcalExtCells = prefix+"HCalExtBarrelCells"

##############################################################################################################
#######                                       RECALIBRATE ECAL                                   #############
##############################################################################################################

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
rewriteECalEC.inhits.Path = prefix+"ECalEndcapCells"
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
rewriteHCalEC.inhits.Path = prefix+"HCalEndcapCells"
rewriteHCalEC.outhits.Path = "newHCalEndcapCells"

##############################################################################################################
#######                                       RESEGMENT HCAL                                   #############
##############################################################################################################

from Configurables import CreateVolumeCaloPositions,RedoSegmentation,CreateCaloCells
# Create cells in HCal
# 2. step - rewrite the cellId using the Phi-Eta segmentation
# 3. step - merge new cells corresponding to eta-phi segmentation

# Hcal barrel cell positions                                                                                                                                                                                                              
posHcalBarrel = CreateVolumeCaloPositions("posBarrelHcal", OutputLevel = INFO)
posHcalBarrel.hits.Path = hcalCells
posHcalBarrel.positionedHits.Path = "HCalBarrelPositions"
# Use Phi-Eta segmentation in Hcal barrel                                                                                                                                                                                                  
resegmentHcalBarrel = RedoSegmentation("ReSegmentationHcal",
                                       # old bitfield (readout)                         
                                       oldReadoutName = hcalBarrelReadoutName,
                                       # specify which fields are going to be altered (deleted/rewritten)
                                       oldSegmentationIds = ["module","row"],
                                       # new bitfield (readout), with new segmentation                   
                                       newReadoutName = hcalBarrelReadoutNamePhiEta,
                                       OutputLevel = INFO,
                                       inhits = "HCalBarrelPositions",
                                       outhits = "HCalBarrelCellsStep2")
createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                        doCellCalibration=False, recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False,
                                        OutputLevel=DEBUG,
                                        hits="HCalBarrelCellsStep2",
                                        cells="newHCalBarrelCells")

# Ext Hcal barrel cell positions                                                                                                                                                                                    
posHcalExtBarrel = CreateVolumeCaloPositions("posExtBarrelHcal", OutputLevel = INFO)
posHcalExtBarrel.hits.Path = hcalExtCells
posHcalExtBarrel.positionedHits.Path = "HCalExtBarrelPositions"
# Use Phi-Eta segmentation in Hcal barrel                                                                                                                                                                                                  
resegmentHcalExtBarrel = RedoSegmentation("ReSegmentationHcalExt",
                                          # old bitfield (readout)   
                                          oldReadoutName = hcalExtBarrelReadoutName,
                                          # specify which fields are going to be altered (deleted/rewritten)
                                          oldSegmentationIds = ["module","row"],
                                          # new bitfield (readout), with new segmentation                   
                                          newReadoutName = hcalExtBarrelReadoutNamePhiEta,
                                          OutputLevel = INFO,
                                          inhits = "HCalExtBarrelPositions",
                                          outhits = "HCalExtBarrelCellsStep2")
createHcalExtBarrelCells = CreateCaloCells("CreateHCalExtBarrelCells",
                                           doCellCalibration=False, recalibrateBaseline =False,
                                           addCellNoise=False, filterCellNoise=False,
                                           OutputLevel=INFO,
                                           hits="HCalExtBarrelCellsStep2",
                                           cells="newHCalExtBarrelCells")

##############################################################################################################
#######                                       CELL POSITIONS                                     #############
##############################################################################################################

#Configure tools for calo cell positions
from Configurables import CellPositionsECalBarrelTool, CellPositionsHCalBarrelNoSegTool, CellPositionsHCalBarrelTool, CellPositionsCaloDiscsTool, CellPositionsCaloDiscsTool
ECalBcells = CellPositionsECalBarrelTool("CellPositionsECalBarrel",
                                    readoutName = ecalBarrelReadoutName,
                                    OutputLevel = INFO)
EMECcells = CellPositionsCaloDiscsTool("CellPositionsEMEC",
                                    readoutName = ecalEndcapReadoutName,
                                    OutputLevel = INFO)
ECalFwdcells = CellPositionsCaloDiscsTool("CellPositionsECalFwd",
                                        readoutName = ecalFwdReadoutName,
                                        OutputLevel = INFO)
HCalBcells = CellPositionsHCalBarrelNoSegTool("CellPositionsHCalBarrel",
                                              readoutName = hcalBarrelReadoutName,
                                              OutputLevel = INFO)
HCalExtBcells = CellPositionsHCalBarrelNoSegTool("CellPositionsHCalExtBarrel",
                                                 readoutName = hcalExtBarrelReadoutName,
                                                 OutputLevel = INFO)
HCalBsegcells = CellPositionsHCalBarrelTool("CellPositionsHCalSegBarrel",
                                            readoutName = hcalBarrelReadoutNamePhiEta,
                                            radii = [291.05, 301.05, 313.55, 328.55, 343.55, 358.55, 378.55, 403.55, 428.55, 453.55],
                                            OutputLevel = INFO)
HCalExtBsegcells = CellPositionsHCalBarrelTool("CellPositionsHCalExtSegBarrel",
                                               readoutName = hcalExtBarrelReadoutNamePhiEta,
                                               radii = [ 356.05
                                                         , 373.55
                                                         , 398.55
                                                         , 423.55
                                                         , 291.05
                                                         , 301.05
                                                         , 313.55
                                                         , 328.55
                                                         , 348.55
                                                         , 373.55
                                                         , 398.55
                                                         , 423.55
                                                         ],
                                               OutputLevel = INFO)
HECcells = CellPositionsCaloDiscsTool("CellPositionsHEC",
                                   readoutName = hcalEndcapReadoutName,
                                   OutputLevel = INFO)
HCalFwdcells = CellPositionsCaloDiscsTool("CellPositionsHCalFwd",
                                        readoutName = hcalFwdReadoutName,
                                        OutputLevel = INFO)
if addMuons:
    from Configurables import CellPositionsTailCatcherTool
    TailCatchercells = CellPositionsTailCatcherTool("CellPositionsTailCatcher",
                                                    readoutName = tailCatcherReadoutName,
                                                    centralRadius = 901.5,
                                                    OutputLevel = INFO)

# cell positions
from Configurables import CreateCellPositions
positionsEcalBarrel = CreateCellPositions("positionsEcalBarrel",
                                          positionsTool=ECalBcells,
                                          hits = prefix+"ECalBarrelCells",
                                          positionedHits = "ECalBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalBarrel = CreateCellPositions("positionsHcalBarrel",
                                          positionsTool=HCalBcells,
                                          hits = prefix+"HCalBarrelCells",
                                          positionedHits = "HCalBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalExtBarrel = CreateCellPositions("positionsHcalExtBarrel",
                                          positionsTool=HCalExtBcells,
                                          hits = prefix+"HCalExtBarrelCells",
                                          positionedHits = "HCalExtBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalSegBarrel = CreateCellPositions("positionsSegHcalBarrel",
                                          positionsTool=HCalBsegcells,
                                          hits = "newHCalBarrelCells",
                                          positionedHits = "HCalBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalSegExtBarrel = CreateCellPositions("positionsSegHcalExtBarrel",
                                          positionsTool=HCalExtBsegcells,
                                          hits = "newHCalExtBarrelCells",
                                          positionedHits = "HCalExtBarrelCellPositions",
                                          OutputLevel = INFO)
positionsEcalEndcap = CreateCellPositions("positionsEcalEndcap",
                                          positionsTool=EMECcells,
                                          hits = "newECalEndcapCells",
                                          positionedHits = "ECalEndcapCellPositions",
                                          OutputLevel = INFO)
positionsHcalEndcap = CreateCellPositions("positionsHcalEndcap",
                                          positionsTool=HECcells,
                                          hits = "newHCalEndcapCells",
                                          positionedHits = "HCalEndcapCellPositions",
                                          OutputLevel = INFO)
positionsEcalFwd = CreateCellPositions("positionsEcalFwd",
                                          positionsTool=ECalFwdcells,
                                          hits = prefix+"ECalFwdCells",
                                          positionedHits = "ECalFwdCellPositions",
                                          OutputLevel = INFO)
positionsHcalFwd = CreateCellPositions("positionsHcalFwd",
                                          positionsTool=HCalFwdcells,
                                          hits = prefix+"HCalFwdCells",
                                          positionedHits = "HCalFwdCellPositions",
                                          OutputLevel = INFO)
if addMuons:
    positionsTailCatcher = CreateCellPositions("positionsTailCatcher",
                                               positionsTool=TailCatchercells,
                                               hits = "TailCatcherCells",
                                               positionedHits = "TailCatcherCellPositions",
                                               OutputLevel = INFO)

# PODIO algorithm
out = PodioOutput("out", OutputLevel=DEBUG)
out.outputCommands = ["keep *","drop "+prefix+"ECalBarrelCells","drop "+prefix+"ECalEndcapCells","drop "+prefix+"ECalFwdCells","drop "+prefix+"HCalBarrelCells", "drop "+prefix+"HCalExtBarrelCells", "drop "+prefix+"HCalEndcapCells", "drop "+prefix+"HCalFwdCells"]
if addMuons:
    out.outputCommands += ["drop TailCatcherCells"]
out.filename = "edm.root"

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
podioinput.AuditExecute = True
positionsEcalBarrel.AuditExecute = True
positionsHcalBarrel.AuditExecute = True
positionsHcalExtBarrel.AuditExecute = True
positionsHcalEndcap.AuditExecute = True
positionsHcalFwd.AuditExecute = True
if addMuons:
    positionsTailCatcher.AuditExecute = True
out.AuditExecute = True

if not simargs.flat:
    list_of_algorithms += [ 
        rewriteECalEC,
        rewriteHCalEC,
        positionsEcalEndcap,
        positionsEcalFwd,
        positionsHcalExtBarrel,
        positionsHcalEndcap,
        positionsHcalFwd
        ]
    
list_of_algorithms = [podioinput]

if not simargs.flat:
    list_of_algorithms += [rewriteECalEC,
                           rewriteHCalEC,
                           positionsEcalBarrel,
                           positionsEcalEndcap,
                           positionsEcalFwd,
                           positionsHcalEndcap,
                           positionsHcalFwd,
                           ]
    if resegmentHCal:
        list_of_algorithms += [
            posHcalBarrel,
            posHcalExtBarrel,
            resegmentHcalBarrel,
            resegmentHcalExtBarrel,
            createHcalBarrelCells,
            createHcalExtBarrelCells,
            positionsHcalSegBarrel,
            positionsHcalSegExtBarrel
            ]
    else:
        list_of_algorithms += [ positionsHcalBarrel,
                                positionsHcalExtBarrel,
                                ]
    if addMuons:
        list_of_algorithms += [positionsTailCatcher]

else:
    list_of_algorithms += [ 
        positionsEcalBarrel,
        positionsHcalBarrel,
        ]
    
list_of_algorithms += [out]

ApplicationMgr(
    TopAlg = list_of_algorithms,
    EvtSel = 'NONE',
    EvtMax   = num_events,
    ExtSvc = [geoservice, podioevent, audsvc],
    #OutputLevel = DEBUG
)
