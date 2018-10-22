import argparse
simparser = argparse.ArgumentParser()

simparser.add_argument('--inName', type=str, help='Name of the input file', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('-N','--numEvents',  type=int, help='Number of simulation events to run', required=True)
simparser.add_argument('--prefixCollections', type=str, help='Prefix added to the collection names', default="")
simparser.add_argument("--addMuons", action='store_true', help="Add tail catcher cells", default = False)
simparser.add_argument("--resegmentHCal", action='store_true', help="Merge HCal cells in DeltaEta=0.025 bins", default = False)
simparser.add_argument('--detectorPath', type=str, help='Path to detectors', default = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj")
simparser.add_argument("--addElectronicsNoise", action='store_true', help="Add electronics noise (default: false)")
simparser.add_argument('--flat', action='store_true', help='flat energy distribution for single particle generation')

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
noise = simargs.addElectronicsNoise
print "number of events = ", num_events
print "input name: ", input_name
print "output name: ", output_name
print "prefix added to the collections' name: ", prefix
print "Muons: ", addMuons
print "resegment HCal: ", resegmentHCal

from Gaudi.Configuration import *
##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################
detectors_to_use=[path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml']
if not noise and not simargs.flat:
    detectors_to_use+=[path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalExtendedBarrel_TileCal.xml',
                       path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Endcaps_coneCryo.xml',
                       path_to_detector+'/Detector/DetFCChhCalDiscs/compact/Forward_coneCryo.xml',
                       path_to_detector+'/Detector/DetFCChhTailCatcher/compact/FCChh_TailCatcher.xml']
    
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

# cell collections used for positions reco
ecalBarrelCellsForPositions = prefix+"ECalBarrelCells"
hcalBarrelCellsForPositions = prefix+"HCalBarrelCells"

# Geometry details to add noise to every Calo cell and paths to root files that have the noise const per cell
ecalBarrelNoisePath = "/afs/cern.ch/user/a/azaborow/public/FCCSW/elecNoise_ecalBarrel_50Ohm_traces2_2shieldWidth_noise.root"
ecalBarrelNoiseHistName = "h_elecNoise_fcc_"
hcalBarrelNoiseHistName = "h_elec_hcal_layer"
# active material identifier name
hcalIdentifierName = ["module", "row", "layer"]
# active material volume name
hcalVolumeName = ["moduleVolume", "wedgeVolume", "layerVolume"]
# ECAL bitfield names & values
hcalFieldNames=["system"]
hcalFieldValues=[8]

##############################################################################################################
#######                                        INPUT                                             #############
##############################################################################################################
# reads HepMC text file and write the HepMC::GenEvent to the data service
from Configurables import ApplicationMgr, FCCDataSvc, PodioInput, PodioOutput
podioevent = FCCDataSvc("EventDataSvc", input=input_name)

coll_names_read = [prefix+"ECalBarrelCells", prefix+"HCalBarrelCells"]
if not noise:
    coll_names_read += [prefix+"HCalExtBarrelCells", prefix+"ECalEndcapCells", prefix+"HCalEndcapCells", prefix+"ECalFwdCells", prefix+"HCalFwdCells"]
if not prefix:
    coll_names_read += ["GenParticles", "GenVertices"]
if addMuons:
    coll_names_read += ["TailCatcherCells"]

podioinput = PodioInput("PodioReader", collections = coll_names_read, OutputLevel = DEBUG)

ecalCells = prefix+"ECalBarrelCells"
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
                                debugPrint = 10,
                                OutputLevel= INFO)
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
                                debugPrint = 10,
                                OutputLevel = INFO)
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
                                       inhits = "HCalBarrelPositions",
                                       outhits = "HCalBarrelCellsStep2")
createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                        doCellCalibration=False, recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False,
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
if resegmentHCal:
    hcalBarrelCellsForPositions = "newHCalExtBarrelCells"

##############################################################################################################                                                                            
#######                                       GEOMETRIES                                     #############                                                                             
##############################################################################################################                                                                            
from Configurables import NestedVolumesCaloTool, TubeLayerPhiEtaCaloTool, LayerPhiEtaCaloTool
# add noise, create all existing cells in detector
barrelEcalGeometry = TubeLayerPhiEtaCaloTool("BarrelEcalGeo",
                                             readoutName = "ECalBarrelPhiEta",
                                             activeVolumeName = "LAr_sensitive",
                                             activeFieldName = "layer",
                                             fieldNames = ["system"],
                                             fieldValues = [5],
                                             activeVolumesNumber = 8)

# No segmentation, geometry with nested volumes
hcalgeo = NestedVolumesCaloTool("HcalGeo",
                                activeVolumeName = hcalVolumeName,
                                activeFieldName = hcalIdentifierName,
                                readoutName = "HCalBarrelReadout",
                                fieldNames = hcalFieldNames,
                                fieldValues = hcalFieldValues)

# Geometry for layer-eta-phi segmentation
barrelHcalGeometry = LayerPhiEtaCaloTool("BarrelHcalGeo",
                                         readoutName = "BarHCal_Readout_phieta",
                                         activeVolumeName = "layerVolume",
                                         activeFieldName = "layer",
                                         fieldNames = ["system"],
                                         fieldValues = [8],
                                         activeVolumesNumber = 10,
                                         activeVolumesEta = [1.2524, 1.2234, 1.1956, 1.15609, 1.1189, 1.08397, 1.0509, 0.9999, 0.9534, 0.91072]
                                         )

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
                                            radii = [2910.5, 3010.5, 3135.5, 3285.5, 3435.5, 3585.5, 3785.5, 4035.5, 4285.5, 4535.5],
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

##############################################################################################################
#######                                       NOISE                                     #############
##############################################################################################################

if noise:
    ecalBarrelCellsForPositions = "ECalBarrelCellsNoise"
    hcalBarrelCellsForPositions = "HCalBarrelCellsNoise"

    from Configurables import CreateCaloCells, NoiseCaloCellsFromFileTool, CalibrateCaloHitsTool, NoiseCaloCellsFlatTool
    # ECal Barrel noise
    noiseEcalBarrel = NoiseCaloCellsFromFileTool("NoiseECalBarrel",
                                                 readoutName = ecalBarrelReadoutName,
                                                 noiseFileName = ecalBarrelNoisePath,
                                                 elecNoiseHistoName = ecalBarrelNoiseHistName,
                                                 cellPositionsTool = ECalBcells,
                                                 activeFieldName = "layer",
                                                 addPileup = False,
                                                 numRadialLayers = 8)
    
    createEcalBarrelCellsNoise = CreateCaloCells("CreateECalBarrelCellsNoise",
                                                 geometryTool = barrelEcalGeometry,
                                                 doCellCalibration=False, recalibrateBaseline =False, # already calibrated                                                                  
                                                 addCellNoise=True, filterCellNoise=False,
                                                 noiseTool = noiseEcalBarrel,
                                                 hits = ecalCells,
                                                 cells = "ECalBarrelCellsNoise")
    
    # HCal Barrel noise                                                                                                                                                              
    noiseHcal = NoiseCaloCellsFlatTool("HCalNoise", cellNoise = 0.01)
    
    if resegmentHCal:
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = barrelHcalGeometry,
                                                     doCellCalibration = False, recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     noiseTool = noiseHcal)
        createHcalBarrelCellsNoise.hits.Path = "newHCalBarrelCells"
        createHcalBarrelCellsNoise.cells.Path = "HCalBarrelCellsNoise"
    else:
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = hcalgeo,
                                                     doCellCalibration = False, recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     noiseTool = noiseHcal)
        createHcalBarrelCellsNoise.hits.Path = hcalCells
        createHcalBarrelCellsNoise.cells.Path = "HCalBarrelCellsNoise"


# cell positions
from Configurables import CreateCellPositions
positionsEcalBarrel = CreateCellPositions("positionsEcalBarrel",
                                          positionsTool=ECalBcells,
                                          hits = ecalBarrelCellsForPositions,
                                          positionedHits = "ECalBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalBarrel = CreateCellPositions("positionsHcalBarrel",
                                          positionsTool=HCalBcells,
                                          hits = hcalBarrelCellsForPositions,
                                          positionedHits = "HCalBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalExtBarrel = CreateCellPositions("positionsHcalExtBarrel",
                                          positionsTool=HCalExtBcells,
                                          hits = prefix+"HCalExtBarrelCells",
                                          positionedHits = "HCalExtBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalSegBarrel = CreateCellPositions("positionsSegHcalBarrel",
                                          positionsTool=HCalBsegcells,
                                          hits = hcalBarrelCellsForPositions,
                                          positionedHits = "HCalBarrelCellPositions",
                                          OutputLevel = INFO)
positionsHcalSegExtBarrel = CreateCellPositions("positionsSegHcalExtBarrel",
                                          positionsTool=HCalExtBsegcells,
                                          hits = hcalBarrelCellsForPositions,
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
positionsEcalEndcap.AuditExecute = True
positionsEcalFwd.AuditExecute = True
positionsHcalBarrel.AuditExecute = True
positionsHcalExtBarrel.AuditExecute = True
positionsHcalEndcap.AuditExecute = True
positionsHcalFwd.AuditExecute = True
if addMuons:
    positionsTailCatcher.AuditExecute = True
out.AuditExecute = True

list_of_algorithms = [podioinput]

if resegmentHCal and not noise:
    list_of_algorithms += [
        posHcalBarrel,
        posHcalExtBarrel,
        resegmentHcalBarrel,
        resegmentHcalExtBarrel,
        createHcalBarrelCells,
        createHcalExtBarrelCells,
        ]
elif resegmentHCal and noise:
    list_of_algorithms += [
        posHcalBarrel,
        resegmentHcalBarrel,
        createHcalBarrelCells,
        createEcalBarrelCellsNoise,
        createHcalBarrelCellsNoise,
        positionsEcalBarrel,
        positionsHcalSegBarrel,
        ]
elif noise and not resegmentHCal:
    list_of_algorithms += [ 
        createEcalBarrelCellsNoise,
        createHcalBarrelCellsNoise,
        positionsEcalBarrel,
        positionsHcalBarrel,
        ]

elif not noise and not simargs.flat:
    list_of_algorithms += [rewriteECalEC,
                           rewriteHCalEC,
                           positionsEcalEndcap,
                           positionsEcalFwd,
                           positionsHcalEndcap,
                           positionsHcalFwd,
                           ]
if addMuons:
    list_of_algorithms += [positionsTailCatcher]

list_of_algorithms += [out]

ApplicationMgr(
    TopAlg = list_of_algorithms,
    EvtSel = 'NONE',
    EvtMax   = num_events,
    ExtSvc = [geoservice, podioevent, audsvc],
)
