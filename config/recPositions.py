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
simparser.add_argument('--cone', type=float, help='Pre-selection of to be clustered cells.')

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
cone = -1.
if simargs.cone:
    cone = simargs.cone
    print "Cells selected within cone of R < ", cone

from Gaudi.Configuration import *
##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################
detectors_to_use=[path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml']
if not noise:
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
hcalExtBarrelCellsForPositions = prefix+"HCalExtBarrelCells"
# cell collections used to add noise
ecalBarrelCellsForNoise = ecalBarrelCellsForPositions
hcalBarrelCellsForNoise = hcalBarrelCellsForPositions
# cell collections used to add noise
ecalBarrelCellsForSelection = ecalBarrelCellsForPositions
hcalBarrelCellsForSelection = hcalBarrelCellsForPositions

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

from Configurables import CreateVolumeCaloPositions,RewriteBitfield,CreateCaloCells
                   
rewriteHCal = RewriteBitfield("RewriteHCal",
                                # old bitfield (readout)
                                oldReadoutName = "HCalBarrelReadout",
                                # specify which fields are going to be deleted
                                removeIds = ["row"],
                                # new bitfield (readout), with new segmentation
                                newReadoutName = "BarHCal_Readout_phieta",
                                debugPrint = 10,
                                OutputLevel= INFO)
# clusters are needed, with deposit position and cellID in bits
rewriteHCal.inhits.Path = "HCalBarrelCells"
rewriteHCal.outhits.Path = "HCalBarrelCellsStep1"

createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                        doCellCalibration=False, #recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False,
                                        hits="HCalBarrelCellsStep1",
                                        cells="newHCalBarrelCells")

rewriteExtHCal = RewriteBitfield("RewriteExtHCal",
                                # old bitfield (readout)
                                oldReadoutName = "HCalExtBarrelReadout",
                                # specify which fields are going to be deleted
                                removeIds = ["row"],
                                # new bitfield (readout), with new segmentation
                                newReadoutName = "ExtBarHCal_Readout_phieta",
                                debugPrint = 10,
                                OutputLevel= INFO)
# clusters are needed, with deposit position and cellID in bits
rewriteExtHCal.inhits.Path = "HCalExtBarrelCells"
rewriteExtHCal.outhits.Path = "HCalExtBarrelCellsStep1"

createHcalExtBarrelCells = CreateCaloCells("CreateHCalExtBarrelCells",
                                           doCellCalibration=False, #recalibrateBaseline =False,
                                           addCellNoise=False, filterCellNoise=False,
                                           hits="HCalExtBarrelCellsStep1",
                                           cells="newHCalExtBarrelCells")
if resegmentHCal:
    hcalBarrelCellsForNoise = "newHCalBarrelCells"
    hcalBarrelCellsForPositions = "newHCalBarrelCells"
    hcalExtBarrelCellsForPositions = "newHCalExtBarrelCells"

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
#######                                       CELL POSITION TOOLS                                #############
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
# hcal cell positions tool
hcalCellPositionsTool = HCalBcells
if resegmentHCal:
    hcalCellPositionsTool = HCalBsegcells

##############################################################################################################
#######                                       NOISE                                     #############
##############################################################################################################
print 'Cell collections for adding noise: ', ecalBarrelCellsForNoise, hcalBarrelCellsForNoise

if noise:
    ecalBarrelCellsForPositions = "ECalBarrelCellsNoise"
    hcalBarrelCellsForPositions = "HCalBarrelCellsNoise"
    ecalBarrelCellsForSelection = "ECalBarrelCellsNoise"
    hcalBarrelCellsForSelection = "HCalBarrelCellsNoise"

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
                                                 doCellCalibration=False, #recalibrateBaseline =False, # already calibrated                                                                  
                                                 addCellNoise=True, filterCellNoise=False,
                                                 noiseTool = noiseEcalBarrel,
                                                 hits = ecalBarrelCellsForNoise,
                                                 cells = "ECalBarrelCellsNoise")
    
    # HCal Barrel noise                                                                                                                                                              
    noiseHcal = NoiseCaloCellsFlatTool("HCalNoise", cellNoise = 0.01)
    
    if resegmentHCal:
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = barrelHcalGeometry,
                                                     doCellCalibration = False, #recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     noiseTool = noiseHcal)
        createHcalBarrelCellsNoise.hits.Path = hcalBarrelCellsForNoise
        createHcalBarrelCellsNoise.cells.Path = "HCalBarrelCellsNoise"
    else:
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = hcalgeo,
                                                     doCellCalibration = False, #recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     noiseTool = noiseHcal)
        createHcalBarrelCellsNoise.hits.Path = hcalBarrelCellsForNoise
        createHcalBarrelCellsNoise.cells.Path = "HCalBarrelCellsNoise"

##############################################################################################################
#######                                       CELL SELECTION                                     #############
##############################################################################################################
if simargs.cone:
    print 'Cell collections for cone selection: ', ecalBarrelCellsForSelection, hcalBarrelCellsForSelection
    # Select cells before running clustering
    from Configurables import ConeSelection
    selectionECalBarrel = ConeSelection("selectionECalBarrel",
                                        cells = ecalBarrelCellsForSelection,
                                        particles = "GenParticles",
                                        selCells = "selectedECalBarrelCells",
                                        positionsTool = ECalBcells,
                                        radius = cone,
                                        OutputLevel = INFO)
    selectionHCalBarrel = ConeSelection("selectionHCalBarrel",
                                        cells = hcalBarrelCellsForSelection,
                                        particles = "GenParticles",
                                        selCells = "selectedHCalBarrelCells",
                                        positionsTool = hcalCellPositionsTool,
                                        radius = cone,
                                        OutputLevel = INFO)

    ecalBarrelCellsForPositions = "selectedECalBarrelCells"
    hcalBarrelCellsForPositions = "selectedHCalBarrelCells"

print 'Cell collections for cell positions: ', ecalBarrelCellsForPositions, hcalBarrelCellsForPositions

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
                                          hits = hcalExtBarrelCellsForPositions,
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
out.outputCommands = ["drop *", "keep GenParticles", "keep GenVertices", "keep ECalBarrelCellPositions","keep ECalEndcapCellPositions","keep ECalFwdCellPositions","keep HCalBarrelCellPositions", "keep HCalExtBarrelCellPositions", "keep HCalEndcapCellPositions", "keep HCalFwdCellPositions"]
if addMuons:
    out.outputCommands += ["drop TailCatcherCells"]
out.filename = output_name

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
        rewriteHCal,
        rewriteExtHCal,
        createHcalBarrelCells,
        createHcalExtBarrelCells,
        ]
    if simargs.cone:
        list_of_algorithms += [selectionECalBarrel,
                               selectionHCalBarrel,]
    list_of_algorithms += [
        positionsEcalBarrel,
        positionsHcalSegBarrel,
        positionsHcalSegExtBarrel,
        ]
elif resegmentHCal and noise:
    list_of_algorithms += [
        rewriteHCal,
        createHcalBarrelCells,
        createEcalBarrelCellsNoise,
        createHcalBarrelCellsNoise,
        ]
    if simargs.cone:
        list_of_algorithms += [selectionECalBarrel,
                               selectionHCalBarrel,]
    list_of_algorithms += [
        positionsEcalBarrel,
        positionsHcalSegBarrel,
        ]

elif not resegmentHCal and noise:
    list_of_algorithms += [
        createEcalBarrelCellsNoise,
        createHcalBarrelCellsNoise,
        ]
    if simargs.cone:
        list_of_algorithms += [selectionECalBarrel,
                               selectionHCalBarrel,
                               ]
    list_of_algorithms += [
        positionsEcalBarrel,
        positionsHcalBarrel,
        ]
else:
    list_of_algorithms += [rewriteECalEC,
                           rewriteHCalEC,
                           ]
    if simargs.cone:
        list_of_algorithms += [selectionECalBarrel,
                               selectionHCalBarrel,
                               ]
    list_of_algorithms += [
        positionsEcalBarrel,
        positionsHcalBarrel,
        positionsEcalEndcap,
        positionsEcalFwd,
        positionsHcalEndcap,
        positionsHcalFwd,
        ]

if addMuons:
    list_of_algorithms += [positionsTailCatcher]

list_of_algorithms += [out]

print list_of_algorithms

ApplicationMgr(
    TopAlg = list_of_algorithms,
    EvtSel = 'NONE',
    EvtMax   = num_events,
    ExtSvc = [geoservice, podioevent, audsvc],
)
