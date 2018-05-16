import argparse
simparser = argparse.ArgumentParser()

simparser.add_argument('--inName', type=str, help='Name of the input file', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('-N','--numEvents',  type=int, help='Number of simulation events to run', required=True)
simparser.add_argument("--physics", action='store_true', help="Physics events")

simparser.add_argument("--addElectronicsNoise", action='store_true', help="Add electronics noise (default: false)")
simparser.add_argument("--addPileupNoise", action='store_true', help="Add pileup noise")
simparser.add_argument("--mu", type=int, help="Number of pileup-events", default=0)
simparser.add_argument('--sigma1', type=int, default=4, help='Energy threshold [in number of sigmas] for seeding')
simparser.add_argument('--sigma2', type=int, default=2, help='Energy threshold [in number of sigmas] for neighbours')
simparser.add_argument('--sigma3', type=int, default=0, help='Energy threshold [in number of sigmas] for last neighbours')

simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
num_events = simargs.numEvents
input_name = simargs.inName
output_name = 'clusters.root'
elNoise = simargs.addElectronicsNoise
puNoise = simargs.addPileupNoise
puEvents = simargs.mu
sigma1 = simargs.sigma1
sigma2 = simargs.sigma2
sigma3 = simargs.sigma3

print "number of events = ", num_events
print "input name: ", input_name
print "output name: ", output_name
print "electronic noise in Barrel: ", elNoise
print "pileup noise in Barrel: ", puNoise
print 'assuming %i pileup events '%(puEvents)
print 'energy thresholds for reconstruction: ', sigma1, '-', sigma2, '-', sigma3

from Gaudi.Configuration import *
##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################

path_to_detector = '/afs/cern.ch/work/c/cneubuse/public/TopoClusters/FCCSW/'
detectors_to_use=[path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml']

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
# Readouts
ecalBarrelReadoutName = "ECalBarrelPhiEta"
ecalEndcapReadoutName = "EMECPhiEta"
ecalFwdReadoutName = "EMFwdPhiEta"
hcalBarrelReadoutName = "HCalBarrelReadout"
hcalExtBarrelReadoutName = "HCalExtBarrelReadout"
hcalEndcapReadoutName = "HECPhiEta"
hcalFwdReadoutName = "HFwdPhiEta"
tailCatcherReadoutName = "Muons_Readout"

# Geometry details to add noise to every Calo cell and paths to root files that have the noise const per cell
ecalBarrelNoisePath = "/afs/cern.ch/user/a/azaborow/public/FCCSW/elecNoise_ecalBarrel_50Ohm_traces2_2shieldWidth_noise.root"
ecalBarrelNoiseHistName = "h_elecNoise_fcc_"
# Geometry details to add noise to every Calo cell and paths to root files that have the noise const per cell
pileupNoisePath = "/afs/cern.ch/work/c/cneubuse/public/FCChh/inBfield/noiseBarrel_mu"+str(puEvents)+".root"
ecalBarrelPileupNoiseHistName = "h_pileup_ecal_layer"
hcalBarrelPileupNoiseHistName = "h_pileup_hcal_layer"
ecalBarrelPileupOffsetHistName = "h_mean_pileup_ecal_layer"
hcalBarrelPileupOffsetHistName = "h_mean_pileup_hcal_layer"
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

podioinput = PodioInput("PodioReader", collections = ["TrackerPositionedHits", "ECalBarrelCells", "HCalBarrelCells", "HCalExtBarrelCells", "ECalEndcapCells", "HCalEndcapCells", "ECalFwdCells", "HCalFwdCells", "TailCatcherCells","GenParticles","GenVertices"], OutputLevel = DEBUG)

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

##############################################################################################################
#######                                       CELL POSITIONS  TOOLS                              #############
##############################################################################################################

#Configure tools for calo cell positions
from Configurables import CellPositionsECalBarrelTool, CellPositionsHCalBarrelTool, CellPositionsHCalBarrelNoSegTool, CellPositionsCaloDiscsTool, CellPositionsTailCatcherTool
ECalBcells = CellPositionsECalBarrelTool("CellPositionsECalBarrel",
                                         readoutName = ecalBarrelReadoutName,
                                         OutputLevel = INFO)
EMECcells = CellPositionsCaloDiscsTool("CellPositionsEMEC",
                                       readoutName = ecalEndcapReadoutName,
                                       OutputLevel = INFO)
ECalFwdcells = CellPositionsCaloDiscsTool("CellPositionsECalFwd",
                                          readoutName = ecalFwdReadoutName,
                                          OutputLevel = INFO)
HCalBcellVols = CellPositionsHCalBarrelNoSegTool("CellPositionsHCalBarrelVols",
                                                 readoutName = hcalBarrelReadoutName,
                                                 OutputLevel = INFO)
HECcells = CellPositionsCaloDiscsTool("CellPositionsHEC",
                                      readoutName = hcalEndcapReadoutName,
                                      OutputLevel = INFO)
HCalFwdcells = CellPositionsCaloDiscsTool("CellPositionsHCalFwd",
                                          readoutName = hcalFwdReadoutName,
                                          OutputLevel = INFO)

##############################################################################################################
#######                          PREPARE TOPO CLUSTERING :                                       #############
#######                          PREPARE EMPTY CELL COLLECTIONS                                  #############
#######                          READ NEIGHBOURS MAP                                             #############
##############################################################################################################

# Fill empty collections for un-used Calo systems
from Configurables import CreateEmptyCaloCellsCollection
createemptycells = CreateEmptyCaloCellsCollection("CreateEmptyCaloCells")
createemptycells.cells.Path = "emptyCaloCells"

from Configurables import TopoCaloNeighbours, TopoCaloNoisyCells
# read the neighbours map
readNeighboursMap = TopoCaloNeighbours("ReadNeighboursMap",
                                       fileName = "/afs/cern.ch/work/c/cneubuse/public/FCChh/neighbours_map_segHcal.root",
                                       OutputLevel = DEBUG)

##############################################################################################################
#######                          NOISE/NO NOISE TOOL FOR CLUSTER THRESHOLDS                      #############
##############################################################################################################

if elNoise:

    from Configurables import CreateCaloCells, NoiseCaloCellsFromFileTool, TubeLayerPhiEtaCaloTool, CalibrateCaloHitsTool, NoiseCaloCellsFlatTool, NestedVolumesCaloTool
    # ECal Barrel noise
    noiseBarrel = NoiseCaloCellsFromFileTool("NoiseBarrel",
                                             readoutName = ecalBarrelReadoutName,
                                             noiseFileName = ecalBarrelNoisePath,
                                             elecNoiseHistoName = ecalBarrelNoiseHistName,
                                             activeFieldName = "layer",
                                             addPileup = False,
                                             numRadialLayers = 8)

    # add noise, create all existing cells in detector
    barrelGeometry = TubeLayerPhiEtaCaloTool("EcalBarrelGeo",
                                             readoutName = ecalBarrelReadoutName,
                                             activeVolumeName = "LAr_sensitive",
                                             activeFieldName = "layer",
                                             fieldNames = ["system"],
                                             fieldValues = [5],
                                             activeVolumesNumber = 8)

    createEcalBarrelCells = CreateCaloCells("CreateECalBarrelCells",
                                            geometryTool = barrelGeometry,
                                            doCellCalibration=False, # already calibrated
                                            addCellNoise=True, filterCellNoise=False,
                                            noiseTool = noiseBarrel,
                                            hits="ECalBarrelCellsRedo",
                                            cells="ECalBarrelCellsNoise")

    # HCal Barrel noise
    noiseHcal = NoiseCaloCellsFlatTool("HCalNoise", cellNoise = 0.009)

    hcalgeo = NestedVolumesCaloTool("HcalGeo",
                                    activeVolumeName = hcalVolumeName,
                                    activeFieldName = hcalIdentifierName,
                                    readoutName = hcalBarrelReadoutName,
                                    fieldNames = hcalFieldNames,
                                    fieldValues = hcalFieldValues,
                                    OutputLevel = INFO)

    createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                            geometryTool = hcalgeo,
                                            doCellCalibration = False,
                                            addCellNoise = True, filterCellNoise = False,
                                            noiseTool = noiseHcal,
                                            OutputLevel = INFO)
    createHcalBarrelCells.hits.Path="HCalBarrelCells"
    createHcalBarrelCells.cells.Path="HCalBarrelCellsNoise"

    # Create topo clusters
    from Configurables import CaloTopoClusterInputTool, CaloTopoCluster
    createTopoInputNoise = CaloTopoClusterInputTool("CreateTopoInputNoise",
                                                    ecalBarrelReadoutName = ecalBarrelReadoutName,
                                                    ecalEndcapReadoutName = "",
                                                    ecalFwdReadoutName = "",
                                                    hcalBarrelReadoutName = hcalBarrelReadoutName,
                                                    hcalExtBarrelReadoutName = "",
                                                    hcalEndcapReadoutName = "",
                                                    hcalFwdReadoutName = "",
                                                    OutputLevel = INFO)
    createTopoInputNoise.ecalBarrelCells.Path = "ECalBarrelCellsNoise"
    createTopoInputNoise.ecalEndcapCells.Path = "emptyCaloCells"
    createTopoInputNoise.ecalFwdCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalBarrelCells.Path = "HCalBarrelCellsNoise"
    createTopoInputNoise.hcalExtBarrelCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalEndcapCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalFwdCells.Path = "emptyCaloCells"

    readNoisyCellsMap = TopoCaloNoisyCells("ReadNoisyCellsMap",
                                           fileName = "/afs/cern.ch/work/c/cneubuse/public/FCChh/cellNoise_map_segHcal_electronicsNoiseLevel.root",
                                           OutputLevel = DEBUG)

    # Topo-Cluster Algorithm
    # Seed and neighbour thresholds 4 - 2 - 0 w/noise
    createTopoClustersNoise = CaloTopoCluster("CreateTopoClustersNoise",
                                              TopoClusterInput = createTopoInputNoise,
                                              # expects neighbours map from cellid->vec<neighbourIds>
                                              neigboursTool = readNeighboursMap,
                                              # tool to get noise level per cellid
                                              noiseTool = readNoisyCellsMap,
                                              # cell positions tools for all sub-systems
                                              positionsECalBarrelTool = ECalBcells,
                                              positionsHCalBarrelTool = HCalBcellVols,
                                              seedSigma = sigma1,
                                              neighbourSigma = sigma2,
                                              lastNeighbourSigma = sigma3,
                                              OutputLevel = INFO)
    createTopoClustersNoise.clusters.Path = "caloClustersBarrelNoise"
    createTopoClustersNoise.clusterCells.Path = "caloClusterBarrelNoiseCells"

    from Configurables import CreateCaloCellPositions
    positionsClusterBarrelNoise = CreateCaloCellPositions("positionsClusterBarrelNoise",
                                                          positionsECalBarrelTool = ECalBcells,
                                                          positionsHCalBarrelTool = HCalBcellVols,
                                                          positionsHCalExtBarrelTool = HCalBcellVols,
                                                          positionsEMECTool = EMECcells,
                                                          positionsHECTool = HECcells,
                                                          positionsEMFwdTool = ECalFwdcells,
                                                          positionsHFwdTool = HCalFwdcells,
                                                          hits = "caloClusterBarrelNoiseCells",
                                                          positionedHits = "caloClusterBarrelNoiseCellPositions",
                                                          OutputLevel = INFO)
##############################################################################################################
#######                          NOISE/NO NOISE TOOL FOR CLUSTER THRESHOLDS                      #############
##############################################################################################################

if puNoise:

    from Configurables import CreateCaloCells, NoiseCaloCellsFromFileTool, TubeLayerPhiEtaCaloTool, CalibrateCaloHitsTool, NoiseCaloCellsFlatTool, NestedVolumesCaloTool
    # ECal Barrel noise
    noiseBarrel = NoiseCaloCellsFromFileTool("NoiseECalBarrel",
                                             readoutName = ecalBarrelReadoutName,
                                             cellPositionsTool = ECalBcells,
                                             noiseFileName = pileupNoisePath,
                                             elecNoiseHistoName = ecalBarrelNoiseHistName,
                                             pileupHistoName = ecalBarrelPileupNoiseHistName,
                                             activeFieldName = "layer",
                                             addPileup = True,
                                             numRadialLayers = 8)
    
    # add noise, create all existing cells in detector
    barrelGeometry = TubeLayerPhiEtaCaloTool("EcalBarrelGeo",
                                             readoutName = ecalBarrelReadoutName,
                                             activeVolumeName = "LAr_sensitive",
                                             activeFieldName = "layer",
                                             fieldNames = ["system"],
                                             fieldValues = [5],
                                             activeVolumesNumber = 8)
    
    createEcalBarrelCells = CreateCaloCells("CreateECalBarrelCells",
                                            geometryTool = barrelGeometry,
                                            doCellCalibration=False, # already calibrated
                                            addCellNoise=True, filterCellNoise=False,
                                            noiseTool = noiseBarrel,
                                            hits="ECalBarrelCellsRedo",
                                            cells="ECalBarrelCellsNoise")
    
    # HCal Barrel noise
    noiseHcal = NoiseCaloCellsFromFileTool("NoiseHCalBarrel",
                                           readoutName = hcalBarrelReadoutName,
                                           cellPositionsTool = HCalBcellVols,
                                           noiseFileName = pileupNoisePath,
                                           elecNoiseHistoName = hcalBarrelPileupNoiseHistName,
                                           activeFieldName = "layer",
                                           addPileup = False,
                                           numRadialLayers = 10)
    
    hcalgeo = NestedVolumesCaloTool("HcalGeo",
                                    activeVolumeName = hcalVolumeName,
                                    activeFieldName = hcalIdentifierName,
                                    readoutName = hcalBarrelReadoutName,
                                    fieldNames = hcalFieldNames,
                                    fieldValues = hcalFieldValues,
                                    OutputLevel = INFO)
    
    createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                            geometryTool = hcalgeo,
                                            doCellCalibration = False,
                                            addCellNoise = True, filterCellNoise = False,
                                            noiseTool = noiseHcal,
                                            OutputLevel = INFO)
    createHcalBarrelCells.hits.Path="HCalBarrelCells"
    createHcalBarrelCells.cells.Path="HCalBarrelCellsNoise"
    
    # Create topo clusters
    from Configurables import CaloTopoClusterInputTool, CaloTopoCluster
    createTopoInputNoise = CaloTopoClusterInputTool("CreateTopoInputNoise",
                                                    ecalBarrelReadoutName = ecalBarrelReadoutName,
                                                    ecalEndcapReadoutName = "",
                                                    ecalFwdReadoutName = "",
                                                    hcalBarrelReadoutName = hcalBarrelReadoutName,
                                                    hcalExtBarrelReadoutName = "",
                                                    hcalEndcapReadoutName = "",
                                                    hcalFwdReadoutName = "",
                                                    OutputLevel = DEBUG)
    createTopoInputNoise.ecalBarrelCells.Path = "ECalBarrelCellsNoise"
    createTopoInputNoise.ecalEndcapCells.Path = "emptyCaloCells"
    createTopoInputNoise.ecalFwdCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalBarrelCells.Path = "HCalBarrelCellsNoise"
    createTopoInputNoise.hcalExtBarrelCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalEndcapCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalFwdCells.Path = "emptyCaloCells"
    
    readNoisyCellsMap = TopoCaloNoisyCells("ReadNoisyCellsMap",
                                           fileName = "/afs/cern.ch/work/c/cneubuse/public/FCChh/inBfield/cellNoise_map_segHcal_noiseLevelElectronicsPileup_mu"+str(puEvents)+".root",
                                           OutputLevel = INFO)
    
    # Topo-Cluster Algorithm
    # Seed and neighbour thresholds 4 - 2 - 0 w/noise
    createTopoClustersNoise = CaloTopoCluster("CreateTopoClustersNoise",
                                              TopoClusterInput = createTopoInputNoise,
                                              # expects neighbours map from cellid->vec<neighbourIds>
                                              neigboursTool = readNeighboursMap,
                                              # tool to get noise level per cellid
                                              noiseTool = readNoisyCellsMap,
                                              # cell positions tools for all sub-systems
                                              positionsECalBarrelTool = ECalBcells,
                                              positionsHCalBarrelTool = HCalBcellVols,
                                              seedSigma = sigma1,
                                              neighbourSigma = sigma2,
                                              lastNeighbourSigma = sigma3,
                                              OutputLevel = DEBUG)
    createTopoClustersNoise.clusters.Path = "caloClustersBarrelNoise"
    createTopoClustersNoise.clusterCells.Path = "caloClusterBarrelNoiseCells"
    
    from Configurables import CreateCaloCellPositions
    positionsClusterBarrelNoise = CreateCaloCellPositions("positionsClusterBarrelNoise",
                                                          positionsECalBarrelTool = ECalBcells,
                                                          positionsHCalBarrelTool = HCalBcellVols,
                                                          positionsHCalExtBarrelTool = HCalBcellVols,
                                                          positionsEMECTool = EMECcells,
                                                          positionsHECTool = HECcells,
                                                          positionsEMFwdTool = ECalFwdcells,
                                                          positionsHFwdTool = HCalFwdcells,
                                                          hits = "caloClusterBarrelNoiseCells",
                                                          positionedHits = "caloClusterBarrelNoiseCellPositions",
                                                          OutputLevel = INFO)
    
##############################################################################################################
#######                                 TOPO-CLUSTERING                                          #############
##############################################################################################################
    
# "Noise" level without added noise for topo thresholds set to 1.875MeV and 2.875MeV in E and HCal
readNoNoisyCellsMap = TopoCaloNoisyCells("ReadNoNoisyCellsMap",
                                         fileName = "/afs/cern.ch/work/c/cneubuse/public/FCChh/cellNoise_map_segHcal_constNoiseLevel.root",
                                         OutputLevel = DEBUG)
# Create topo clusters
from Configurables import CaloTopoClusterInputTool, CaloTopoCluster, TopoCaloNeighbours
createTopoInput = CaloTopoClusterInputTool("CreateTopoInput",
                                           ecalBarrelReadoutName = ecalBarrelReadoutName,
                                           ecalEndcapReadoutName = "",
                                           ecalFwdReadoutName = "",
                                           hcalBarrelReadoutName = hcalBarrelReadoutName,
                                           hcalExtBarrelReadoutName = "",
                                           hcalEndcapReadoutName = "",
                                           hcalFwdReadoutName = "",
                                           OutputLevel = INFO)
createTopoInput.ecalBarrelCells.Path = "ECalBarrelCellsRedo"
createTopoInput.ecalEndcapCells.Path = "emptyCaloCells"
createTopoInput.ecalFwdCells.Path = "emptyCaloCells"
createTopoInput.hcalBarrelCells.Path = "HCalBarrelCells"
createTopoInput.hcalExtBarrelCells.Path = "emptyCaloCells"
createTopoInput.hcalEndcapCells.Path = "emptyCaloCells"
createTopoInput.hcalFwdCells.Path = "emptyCaloCells"

# Topo-Cluster Algorithm
# Seed and neighbour thresholds 4 - 0 - 0 if no noise added
createTopoClusters = CaloTopoCluster("CreateTopoClusters",
                                     TopoClusterInput = createTopoInput,
                                     # expects neighbours map from cellid->vec<neighbourIds>
                                     neigboursTool = readNeighboursMap,
                                     # tool to get noise level per cellid
                                     noiseTool = readNoNoisyCellsMap,
                                     # cell positions tools for all sub-systems
                                     positionsECalBarrelTool = ECalBcells,
                                     positionsHCalBarrelTool = HCalBcellVols,
                                     seedSigma = sigma1,
                                     neighbourSigma = sigma2,
                                     lastNeighbourSigma = sigma3,
                                     OutputLevel = INFO)
createTopoClusters.clusters.Path = "caloClustersBarrel"
createTopoClusters.clusterCells.Path = "caloClusterBarrelCells"


##############################################################################################################
#######                                       TOPO-CLUSTER CELL POSITIONS                        #############
##############################################################################################################
from Configurables import CreateCaloCellPositions
positionsClusterBarrel = CreateCaloCellPositions("positionsClusterBarrel",
                                                 positionsECalBarrelTool = ECalBcells,
                                                 positionsHCalBarrelTool = HCalBcellVols,
                                                 positionsHCalExtBarrelTool = HCalBcellVols,
                                                 positionsEMECTool = EMECcells,
                                                 positionsHECTool = HECcells,
                                                 positionsEMFwdTool = ECalFwdcells,
                                                 positionsHFwdTool = HCalFwdcells,
                                                 hits = "caloClusterBarrelCells",
                                                 positionedHits = "caloClusterBarrelCellPositions",
                                                 OutputLevel = INFO)

# PODIO algorithm
out = PodioOutput("out", OutputLevel=DEBUG)
out.outputCommands = ["drop *", "keep GenParticles", "keep GenVertices", "keep TrackerPositionedHits", "keep caloClustersBarrel", "keep caloClusterBarrelCells", "keep caloClusterBarrelCellPositions",]
out.filename = output_name

if elNoise or puNoise:
    out.outputCommands += ["keep ECalBarrelCellsNoise", "keep HCalBarrelCellsNoise", "keep caloClustersBarrelNoise","keep caloClusterBarrelNoiseCells",  "keep caloClusterBarrelCellPositions"]
out.filename = output_name

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
podioinput.AuditExecute = True
createemptycells.AuditExecute = True
out.AuditExecute = True

list_of_algorithms = [podioinput,
                      recreateEcalBarrelCells,
                      createemptycells]

if elNoise or puNoise:
    list_of_algorithms += [createEcalBarrelCells, createHcalBarrelCells, createTopoClustersNoise, positionsClusterBarrelNoise]

else:
    list_of_algorithms += [createTopoClusters, positionsClusterBarrel]

list_of_algorithms += [out]

ApplicationMgr(
    TopAlg = list_of_algorithms,
    EvtSel = 'NONE',
    EvtMax   = num_events,
    ExtSvc = [geoservice, podioevent, audsvc],
    )
