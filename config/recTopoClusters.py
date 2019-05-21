import argparse
simparser = argparse.ArgumentParser()

simparser.add_argument('--inName', type=str, help='Name of the input file', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)
simparser.add_argument('-N','--numEvents',  type=int, help='Number of simulation events to run', required=True)
simparser.add_argument("--addElectronicsNoise", action='store_true', help="Add electronics noise (default: false)")
simparser.add_argument("--addPileupNoise", action='store_true', help="Add pileup noise")
simparser.add_argument('--sigma1', type=int, default=4, help='Energy threshold [in number of sigmas] for seeding')
simparser.add_argument('--sigma2', type=float, default=2., help='Energy threshold [in number of sigmas] for neighbours')
simparser.add_argument('--sigma3', type=int, default=0, help='Energy threshold [in number of sigmas] for last neighbours')
simparser.add_argument('--detectorPath', type=str, help='Path to detectors', default = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj")
simparser.add_argument("--calibrate", action='store_true', help="Calibrate clusters (default: false)")
simparser.add_argument("--benchmark", action='store_true', help="Calibrate clusters, using cell-level benchmark parameters (default: false)")
simparser.add_argument("--pileup", type=int, help="Added pileup events to signal", default=0)
simparser.add_argument('--prefixCollections', type=str, help='Prefix added to the collection names', default="")
simparser.add_argument("--resegmentHCal", action='store_true', help="Merge HCal cells in DeltaEta=0.025 bins", default = False)
simparser.add_argument("--bFieldOff", action='store_true', help="Switch OFF magnetic field (default: B field ON)")
simparser.add_argument('--cone', type=float, help='Pre-selection of to be clustered cells.')
simparser.add_argument("--split", action='store_true', help="Use split cluster algorithm.")

simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
num_events = simargs.numEvents
input_name = simargs.inName
output_name = simargs.outName
elNoise = simargs.addElectronicsNoise
puNoise = simargs.addPileupNoise
puEvents = simargs.pileup
sigma1 = simargs.sigma1
sigma2 = simargs.sigma2
sigma3 = simargs.sigma3
path_to_detector = simargs.detectorPath
calib = simargs.calibrate
addedPU = 0
prefix = simargs.prefixCollections
resegmentHCal = simargs.resegmentHCal
bFieldOff = simargs.bFieldOff
split = simargs.split

print "number of events = ", num_events
print "input name: ", input_name
print "output name: ", output_name
print "prefix : ", prefix
print 'energy thresholds for reconstruction: ', sigma1, '-', sigma2, '-', sigma3
print "detectors are taken from: ", path_to_detector
if split:
    print 'topo-clusters are splitted. '
print "calibrate clusters: ", calib
print "resegment HCal: ", resegmentHCal
print "no B field: ", bFieldOff

cone = -1.
if simargs.cone:
    cone = simargs.cone
    print "Cells pre selected within cone of R < ", cone

# correct EM calibration of hcal cells                                                                                                                                                    
hadronSampl_hcal = 0.024
emSampl_hcal = 0.0255
# Paramerters for cluster calibration                                                                                                                                         
# Bfield on:
benchmark_a = 0.996
benchmark_b = 0.565
benchmark_c = -7.4E-6
benchmark_d = 0. #-.92
benchmark_e = 1. #0.9697
benchmark_f = 1. #1./0.9956

if bFieldOff:
    emSampl_hcal = 0.0249
    benchmark_a = 1.062
    benchmark_b = 0.659
    benchmark_c = -6.3E-6
    benchmark_d = 0. #-.83
    benchmark_e = 1. #0.9834
    benchmark_f = 1. #1./0.9973

# from minimisation (bFieldOn, C=0): 0.975799,-2.54738e-06,0.822663,-0.140975,-2.18657e-05,-0.0193682
edepCalib = True
benchCalib = False

a1 = 0.975799
a2 = -2.54738e-06
a3 = 0.822663
b1 = -0.140975
b2 = -2.18657e-05
b3 = -0.0193682
c1 = 0
c2 = 0
c3 = 1
if simargs.benchmark:
    calib = True
    edepCalib = False
    benchCalib = True
    a1 = benchmark_a
    a2 = 0.
    a3 = 0.
    b1 = benchmark_b
    b2 = 0.
    b3 = 0.
    c1 = benchmark_c
    c2 = 0.
    c3 = 0.
    

# no distrinction of shared clusters needed
fractionECal = 1

print "added pileup events : ", addedPU
print "add electronic noise in Barrel: ", elNoise
print "add pileup noise in Barrel: ", puNoise

if puNoise:
    print 'adding noise corresponding to %i pileup events '%(puEvents)

if not puNoise:
    addedPU = simargs.pileup
    print "added pileup: ",addedPU
if addedPU!=0:
    elNoise = True

from Gaudi.Configuration import *

##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################

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
hcalBarrelReadoutNamePhiEta = "BarHCal_Readout_phieta"
hcalExtBarrelReadoutName = "HCalExtBarrelReadout"
hcalEndcapReadoutName = "HECPhiEta"
hcalFwdReadoutName = "HFwdPhiEta"
tailCatcherReadoutName = "Muons_Readout"

# Geometry details to add noise to every Calo cell and paths to root files that have the noise const per cell
ecalBarrelNoisePath = "/afs/cern.ch/user/a/azaborow/public/FCCSW/elecNoise_ecalBarrel_50Ohm_traces2_2shieldWidth_noise.root"
ecalBarrelNoiseHistName = "h_elecNoise_fcc_"
hcalBarrelNoiseHistName = "h_elec_hcal_layer"
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

# inputs for topo-clustering
inputCellCollectionECalBarrel = prefix+"ECalBarrelCells"
inputCellCollectionHCalBarrel = prefix+"HCalBarrelCells"
inputCollections = [prefix+"ECalBarrelCells", prefix+"HCalBarrelCells", ]
inputCollections += ["GenParticles", "GenVertices"] 
inputNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/cellNoise_map_segHcal_constNoiseLevel.root"
inputPileupNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/inBfield/cellNoise_map_segHcal_noiseLevelElectronicsPileup_mu"+str(puEvents)+".root"
inputNeighboursMap = "/afs/cern.ch/work/c/cneubuse/public/FCChh/neighbours_map_segHcal.root"
noSegmentationHCal = True

if bFieldOff:
    pileupNoisePath = "/afs/cern.ch/work/c/cneubuse/public/FCChh/noBfield/noiseBarrel_mu"+str(puEvents)+".root"
    inputPileupNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/cellNoise_map_segHcal_noiseLevelElectronicsPileup_mu"+str(puEvents)+".root"

##############################################################################################################
#######                                        INPUT                                             #############
##############################################################################################################

# reads HepMC text file and write the HepMC::GenEvent to the data service
from Configurables import ApplicationMgr, FCCDataSvc, PodioInput, PodioOutput
podioevent = FCCDataSvc("EventDataSvc", input=input_name)

podioinput = PodioInput("PodioReader", collections=inputCollections, OutputLevel=DEBUG)

print "Reading collections: ", inputCollections

from Configurables import SimG4ParticleSmearFormula, SimG4SmearGenParticles
from FCChhTkLayoutResolutionFormula import momentumResolutionFormula 

# create particle smearing tool, used for smearing in the tracker
smeartool = SimG4ParticleSmearFormula()
smeartool.resolutionMomentum = momentumResolutionFormula
#smeartool = SimG4ParticleSmearRootFile("SmearTool", filename="/eos/project/f/fccsw-web/testsamples/tkLayout_example_resolutions.root")

smear = SimG4SmearGenParticles("smear",
                               inParticles = "GenParticles",
                               smearedParticles = "SmearedParticles",
                               smearTool = smeartool,
                               OutputLevel=INFO)

##############################################################################################################
#######                                       CELL POSITIONS  TOOLS                              #############
##############################################################################################################

#Configure tools for calo cell positions
from Configurables import CellPositionsECalBarrelTool, CellPositionsHCalBarrelNoSegTool, CellPositionsHCalBarrelTool, CellPositionsCaloDiscsTool, CellPositionsTailCatcherTool
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
                                                 readoutName = "HCalBarrelReadout",
                                                 OutputLevel = INFO)
HCalBsegcells = CellPositionsHCalBarrelTool("CellPositionsHCalBarrel",
                                            readoutName = "BarHCal_Readout_phieta",
                                            radii = [291.05, 301.05, 313.55, 328.55, 343.55, 358.55, 378.55, 413.55, 428.55, 453.55],
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
##############################################################################################################

# Fill empty collections for un-used Calo systems
from Configurables import CreateEmptyCaloCellsCollection
createemptycells = CreateEmptyCaloCellsCollection("CreateEmptyCaloCells")
createemptycells.cells.Path = "emptyCaloCells"

############################################################################################################
#######                                       RESEGMENT HCAL                                   #############
############################################################################################################                                                                                       
from Configurables import CreateVolumeCaloPositions,RedoSegmentation,CreateCaloCells
# Create cells in HCal                                           
# 2. step - rewrite the cellId using the Phi-Eta segmentation    
# 3. step - merge new cells corresponding to eta-phi segmentation  
# Hcal barrel cell positions                                     
posHcalBarrel = CreateVolumeCaloPositions("posBarrelHcal", OutputLevel = INFO)
posHcalBarrel.hits.Path = inputCellCollectionHCalBarrel
posHcalBarrel.positionedHits.Path = "HCalBarrelPositions"

# Use Phi-Eta segmentation in Hcal barrel                                                                
resegmentHcalBarrel = RedoSegmentation("ReSegmentationHcal",
                                       # old bitfield (readout)
                                       oldReadoutName = "HCalBarrelReadout",
                                       # specify which fields are going to be altered (deleted/rewritten)
                                       oldSegmentationIds = ["module","row"],
                                       # new bitfield (readout), with new segmentation
                                       newReadoutName = "BarHCal_Readout_phieta",
                                       inhits = "HCalBarrelPositions",
                                       outhits = "HCalBarrelCellsStep2")

createHcalBarrelCells = CreateCaloCells("CreateHCalBarrelCells",
                                        doCellCalibration=False, recalibrateBaseline =False,
                                        addCellNoise=False, filterCellNoise=False,
                                        hits="HCalBarrelCellsStep2",
                                        cells="newHCalBarrelCells")

##############################################################################################################
#######                                      GEOMETRY DISCRIPTIONS                               #############
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


############## DEFINE OPTIONS FOR RESEGMENTED HCAL 
inputTopoCellCollectionHCalBarrel = inputCellCollectionHCalBarrel
cellPosToolHCal = HCalBcellVols
if resegmentHCal:
    cellPosToolHCal = HCalBsegcells
    inputNeighboursMap = "/afs/cern.ch/work/c/cneubuse/public/FCChh/neighbours_map_barrel.root"
    inputNoisePerCell = "/eos/project/f/fccsw-web/testsamples/calo/cellNoise_map_electronicsNoiseLevel.root"
    inputPileupNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/inBfield/resegmentedHCal/cellNoise_map_electronicsNoiseLevel_forPU"+str(puEvents)+"_recTopo.root"
    if bFieldOff:
        inputPileupNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/noBfield/resegmentedHCal/cellNoise_map_electronicsNoiseLevel_forPU"+str(puEvents)+"_recTopo.root"
        pileupNoisePath = "/afs/cern.ch/work/c/cneubuse/public/FCChh/noBfield/resegmentedHCal/noiseBarrel_mu"+str(puEvents)+".root"
    if not addedPU > 0:
        inputTopoCellCollectionHCalBarrel = "newHCalBarrelCells"
    hcalBarrelReadoutName = hcalBarrelReadoutNamePhiEta
    noSegmentationHCal = False
    inputPileupNoisePerCell.replace('mu', 'PU')
    print 'HCal is resegmented in DeltaEta=0.025. '
    print 'Use postion tool w/o segmentation : ', noSegmentationHCal
    print 'input topo cells : ', inputTopoCellCollectionHCalBarrel
    print 'readout name: ', hcalBarrelReadoutName
    if puNoise:
        print 'pileup noise file name: ', inputPileupNoisePerCell

print 'Full HCal granularity used: ', noSegmentationHCal

##############################################################################################################                              
#######                                       READ NEIGHBOURS MAP                                   #############                           
##############################################################################################################                              

from Configurables import TopoCaloNeighbours, TopoCaloNoisyCells
# read the neighbours map
readNeighboursMap = TopoCaloNeighbours("ReadNeighboursMap",
                                       fileName = inputNeighboursMap,
                                       OutputLevel = INFO)

##############################################################################################################
#######                          NOISE/NO NOISE TOOL FOR CLUSTER THRESHOLDS                      #############
##############################################################################################################

if elNoise and not puNoise:
    # Apply cell thresholds for electronics noise only if no pileup events have been merged
    if not resegmentHCal:
        inputNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/cellNoise_map_segHcal_electronicsNoiseLevel.root"
        if addedPU > 0:
            # no offset, but rms from  MinBias/simuPU200/ 
            # input cells already resegmented HCal segmentation
            inputNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/inBfield/cellNoise_map_electronicsNoiseLevel_forPU"+str(addedPU)+"_recTopo.root"
    else:
        if addedPU > 0:
            # no offset, but rms from  MinBias/simuPU200/                                                                                                                   
            # input cells already resegmented HCal segmentation                                                                                                             
            inputNoisePerCell = "/afs/cern.ch/work/c/cneubuse/public/FCChh/inBfield/resegmentedHCal/cellNoise_map_electronicsNoiseLevel_forPU"+str(addedPU)+"_recTopo.root"
            
            
    print 'Using electronics noise per cell map: ', inputNoisePerCell
        
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
                                                 hits = inputCellCollectionECalBarrel,
                                                 cells = "ECalBarrelCellsNoise")
    
    # re-calibrate HCal Barrel cells to correct EM scale 
    calibHcells = CalibrateCaloHitsTool("CalibrateHCal", invSamplingFraction= str(hadronSampl_hcal/emSampl_hcal))
    if not calib:
        EMscale = True
    else:
        EMscale = False
    # HCal Barrel noise
    noiseHcal = NoiseCaloCellsFlatTool("HCalNoise", cellNoise = 0.01)
    
    if resegmentHCal:
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = barrelHcalGeometry,
                                                     doCellCalibration = EMscale, recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     calibTool = calibHcells,
                                                     noiseTool = noiseHcal)
        createHcalBarrelCellsNoise.hits.Path = inputTopoCellCollectionHCalBarrel
        createHcalBarrelCellsNoise.cells.Path = "HCalBarrelCellsNoise"
    else:
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = hcalgeo,
                                                     doCellCalibration = EMscale, recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     calibTool = calibHcells,
                                                     noiseTool = noiseHcal)
        createHcalBarrelCellsNoise.hits.Path = inputTopoCellCollectionHCalBarrel
        createHcalBarrelCellsNoise.cells.Path = "HCalBarrelCellsNoise"

    # Select cells before running clustering
    from Configurables import ConeSelection
    selectionECal = ConeSelection("selectionECal",
                                  cells = "ECalBarrelCellsNoise",
                                  particles = "GenParticles",
                                  selCells = "selectedECalBarrelCellsNoise",
                                  positionsTool = ECalBcells,
                                  radius = cone,
                                  OutputLevel = INFO)
    selectionHCal = ConeSelection("selectionHCal",
                                  cells = "HCalBarrelCellsNoise",
                                  particles = "GenParticles",
                                  selCells = "selectedHCalBarrelCellsNoise",
                                  positionsTool = cellPosToolHCal,
                                  radius = cone,
                                  OutputLevel = INFO)

    cellInputECal = "ECalBarrelCellsNoise"
    cellInputHCal = "HCalBarrelCellsNoise"
    
    if simargs.cone:
            cellInputECal = "selectedECalBarrelCellsNoise"
            cellInputHCal = "selectedHCalBarrelCellsNoise"

    print "ECal cell collection used: ", cellInputECal
    print "HCal cell collection used: ", cellInputHCal
   
    # Create topo clusters
    from Configurables import CaloTopoClusterInputTool, CaloTopoCluster
    createTopoInputNoise = CaloTopoClusterInputTool("CreateTopoInputNoise",
                                                    ecalBarrelReadoutName = ecalBarrelReadoutName,
                                                    ecalEndcapReadoutName = "",
                                                    ecalFwdReadoutName = "",
                                                    hcalBarrelReadoutName = hcalBarrelReadoutName,
                                                    hcalExtBarrelReadoutName = "",
                                                    hcalEndcapReadoutName = "",
                                                    hcalFwdReadoutName = "")
    createTopoInputNoise.ecalBarrelCells.Path = cellInputECal
    createTopoInputNoise.ecalEndcapCells.Path = "emptyCaloCells"
    createTopoInputNoise.ecalFwdCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalBarrelCells.Path = cellInputHCal
    createTopoInputNoise.hcalExtBarrelCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalEndcapCells.Path = "emptyCaloCells"
    createTopoInputNoise.hcalFwdCells.Path = "emptyCaloCells"

    readNoisyCellsMap = TopoCaloNoisyCells("ReadNoisyCellsMap",
                                           fileName = inputNoisePerCell)
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
                                              positionsHCalBarrelTool = HCalBsegcells,
                                              positionsHCalBarrelNoSegTool = HCalBcellVols,
                                              noSegmentationHCal = noSegmentationHCal,
                                              seedSigma = sigma1,
                                              neighbourSigma = sigma2,
                                              lastNeighbourSigma = sigma3)
    createTopoClustersNoise.clusters.Path = "caloClustersBarrelNoiseStep1"
    createTopoClustersNoise.clusterCells.Path = "caloClusterBarrelNoiseCellsStep1"

    outputCluster = "caloClustersBarrelNoiseStep1"

    from Configurables import SplitClusters
    splitClusters = SplitClusters("splitClusters",
                                  clusters = "caloClustersBarrelNoiseStep1",
                                  outClusters = "caloClustersBarrelNoise",
                                  outCells = "caloClusterBarrelNoiseCells",
                                  readoutECal = ecalBarrelReadoutName,
                                  readoutHCal = hcalBarrelReadoutName,
                                  #expects neighbours map from cellid->vec < neighbourIds >                                                                                        
                                  neigboursTool = readNeighboursMap,
                                  threshold = 0.01,
                                  OutputLevel=INFO)
    if split:
        outputCluster = "caloClustersBarrelNoise"
    
    from Configurables import CreateCaloCellPositions
    if resegmentHCal:
        positionsClusterBarrelNoise = CreateCaloCellPositions("positionsClusterBarrelNoise",
                                                              positionsECalBarrelTool = ECalBcells,
                                                              positionsHCalBarrelTool = HCalBsegcells,
                                                              positionsHCalExtBarrelTool = HCalBsegcells,
                                                              positionsEMECTool = EMECcells,
                                                              positionsHECTool = HECcells,
                                                              positionsEMFwdTool = ECalFwdcells,
                                                              positionsHFwdTool = HCalFwdcells,
                                                              hits = "caloClusterBarrelNoiseCellsStep1",
                                                              positionedHits = "caloClusterBarrelNoiseCellPositions",
                                                              OutputLevel = INFO)
        
    else:
        positionsClusterBarrelNoise = CreateCaloCellPositions("positionsClusterBarrelNoise",
                                                              positionsECalBarrelTool = ECalBcells,
                                                              positionsHCalBarrelTool = HCalBsegcells,
                                                              positionsHCalExtBarrelTool = HCalBcellVols,
                                                              positionsEMECTool = EMECcells,
                                                              positionsHECTool = HECcells,
                                                              positionsEMFwdTool = ECalFwdcells,
                                                              positionsHFwdTool = HCalFwdcells,
                                                              hits = "caloClusterBarrelNoiseCellsStep1",
                                                              positionedHits = "caloClusterBarrelNoiseCellPositions")
    if (calib) :
        from Configurables import CreateCaloClusters
        calibrateClustersNoise = CreateCaloClusters("CalibrateClustersNoise",
                                                    clusters = outputCluster,
                                                    outClusters = "calibCaloClustersBarrelNoise",
                                                    outCells = "calibCaloClusterBarrelCellsNoise",
                                                    genParticles = "GenParticles",
                                                    readoutECal = ecalBarrelReadoutName,
                                                    readoutHCal = hcalBarrelReadoutName,
                                                    positionsECalTool = ECalBcells,
                                                    positionsHCalTool = HCalBsegcells,
                                                    positionsHCalNoSegTool = HCalBcellVols,
                                                    noSegmentationHCal = noSegmentationHCal,
                                                    calibrate = True,
                                                    cryoCorrection = benchCalib,
                                                    eDepCryoCorrection = edepCalib,
                                                    ehECal = 1.,
                                                    ehHCal = 1.,
                                                    a1 = a1,
                                                    a2 = a2,
                                                    a3 = a3,
                                                    b1 = b1,
                                                    b2 = b2,
                                                    b3 = b3,
                                                    c1 = c1,
                                                    c2 = c2,
                                                    c3 = c3,
                                                    fractionECal = fractionECal)

        THistSvc().Output = ["rec DATAFILE='calibrateCluster_histograms.root' TYP='ROOT' OPT='RECREATE'"]
        THistSvc().PrintAll=True
        THistSvc().AutoSave=True
        THistSvc().AutoFlush=True
        THistSvc().OutputLevel=INFO

##############################################################################################################
#######                          NOISE/NO NOISE TOOL FOR CLUSTER THRESHOLDS                      #############
##############################################################################################################
if puNoise:
    from Configurables import CreateCaloCells, NoiseCaloCellsFromFileTool, CalibrateCaloHitsTool
    # ECal Barrel noise
    noiseEcalBarrel = NoiseCaloCellsFromFileTool("NoiseECalBarrel",
                                             readoutName = ecalBarrelReadoutName,
                                             cellPositionsTool = ECalBcells,
                                             noiseFileName = pileupNoisePath,
                                             elecNoiseHistoName = ecalBarrelNoiseHistName,
                                             pileupHistoName = ecalBarrelPileupNoiseHistName,
                                             activeFieldName = "layer",
                                             addPileup = True,
                                             numRadialLayers = 8)
    
    createEcalBarrelCellsNoise = CreateCaloCells("CreateECalBarrelCellsNoise",
                                            geometryTool = barrelEcalGeometry,
                                            doCellCalibration=False, recalibrateBaseline =False, # already calibrated
                                            addCellNoise=True, filterCellNoise=False,
                                            noiseTool = noiseEcalBarrel,
                                            hits=inputCellCollectionECalBarrel,
                                            cells="ECalBarrelCellsNoise")
    
    if resegmentHCal:
        # HCal Barrel noise
        noiseHcal = NoiseCaloCellsFromFileTool("NoiseHCalBarrel",
                                               readoutName = hcalBarrelReadoutNamePhiEta,
                                               cellPositionsTool = HCalBsegcells,
                                               noiseFileName = pileupNoisePath,
                                               elecNoiseHistoName = hcalBarrelNoiseHistName, 
                                               pileupHistoName = hcalBarrelPileupNoiseHistName,
                                               activeFieldName = "layer",
                                               addPileup = True,
                                               numRadialLayers = 10)
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = barrelHcalGeometry,
                                                     doCellCalibration = False, recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     noiseTool = noiseHcal,
                                                     OutputLevel = INFO)
        createHcalBarrelCellsNoise.hits.Path = inputTopoCellCollectionHCalBarrel
        createHcalBarrelCellsNoise.cells.Path="HCalBarrelCellsNoise"
    else:
        # HCal Barrel noise
        noiseHcal = NoiseCaloCellsFromFileTool("NoiseHCalBarrel",
                                               readoutName = hcalBarrelReadoutName,
                                               cellPositionsTool = HCalBcellVols,
                                               noiseFileName = pileupNoisePath,
                                               elecNoiseHistoName = hcalBarrelNoiseHistName,
                                               pileupHistoName = hcalBarrelPileupNoiseHistName,
                                               activeFieldName = "layer",
                                               addPileup = True,
                                               numRadialLayers = 10)
    
        createHcalBarrelCellsNoise = CreateCaloCells("CreateHCalBarrelCellsNoise",
                                                     geometryTool = hcalgeo,
                                                     doCellCalibration = False, recalibrateBaseline =False,
                                                     addCellNoise = True, filterCellNoise = False,
                                                     noiseTool = noiseHcal,
                                                     OutputLevel = INFO)
        createHcalBarrelCellsNoise.hits.Path = inputTopoCellCollectionHCalBarrel
        createHcalBarrelCellsNoise.cells.Path="HCalBarrelCellsNoise"

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
                                           fileName = inputPileupNoisePerCell)
    
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
                                              positionsHCalBarrelTool = HCalBsegcells,
                                              positionsHCalBarrelNoSegTool = HCalBcellVols,
                                              noSegmentationHCal = noSegmentationHCal,
                                              seedSigma = sigma1,
                                              neighbourSigma = sigma2,
                                              lastNeighbourSigma = sigma3)
    createTopoClustersNoise.clusters.Path = "caloClustersBarrelNoise"
    createTopoClustersNoise.clusterCells.Path = "caloClusterBarrelNoiseCells"

    if (calib) :
        from Configurables import CreateCaloClusters
        calibrateClustersNoise = CreateCaloClusters("CalibrateClustersNoise",
                                                    clusters = "caloClustersBarrelNoise",
                                                    genParticles = "GenParticles",
                                                    outClusters = "calibCaloClustersBarrelNoise",
                                                    outCells = "calibCaloClusterBarrelCellsNoise",
                                                    readoutECal = ecalBarrelReadoutName,
                                                    readoutHCal = hcalBarrelReadoutName,
                                                    positionsECalTool = ECalBcells,
                                                    positionsHCalTool = HCalBsegcells,
                                                    positionsHCalNoSegTool = HCalBcellVols,
                                                    noSegmentationHCal = noSegmentationHCal,
                                                    calibrate = True,
                                                    eDepCryoCorrection = True,
                                                    ehECal = 1.,
                                                    ehHCal = 1.1,
                                                    a1 = a1,
                                                    a2 = a2,
                                                    a3 = a3,
                                                    b1 = b1,
                                                    b2 = b2,
                                                    b3 = b3,
                                                    c1 = c1,
                                                    c2 = c2,
                                                    c3 = c3,
                                                    fractionECal = fractionECal)

        THistSvc().Output = ["rec DATAFILE='calibrateCluster_histograms.root' TYP='ROOT' OPT='RECREATE'"]
        THistSvc().PrintAll=True
        THistSvc().AutoSave=True
        THistSvc().AutoFlush=True
        THistSvc().OutputLevel=INFO

##############################################################################################################
#######                                 TOPO-CLUSTERING                                          #############
##############################################################################################################
    
# "Noise" level without added noise for topo thresholds set to 1.875MeV and 2.875MeV in E and HCal
# in case of added PU events, the thresholds are set to the PU/cell estimates
readNoNoisyCellsMap = TopoCaloNoisyCells("ReadNoNoisyCellsMap",
                                         fileName = inputNoisePerCell,
                                         OutputLevel = INFO)
if not elNoise and not puNoise:
    print "ECal cell collection used: ", inputCellCollectionECalBarrel
    print "HCal cell collection used: ", inputCellCollectionHCalBarrel
    print "HCal cell collection used in topo: ", inputTopoCellCollectionHCalBarrel

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
createTopoInput.ecalBarrelCells.Path = inputCellCollectionECalBarrel
createTopoInput.ecalEndcapCells.Path = "emptyCaloCells"
createTopoInput.ecalFwdCells.Path = "emptyCaloCells"
createTopoInput.hcalBarrelCells.Path = inputCellCollectionHCalBarrel
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
                                     positionsHCalBarrelTool = HCalBsegcells,
                                     positionsHCalBarrelNoSegTool = HCalBcellVols,
                                     noSegmentationHCal = noSegmentationHCal,
                                     seedSigma = sigma1,
                                     neighbourSigma = sigma2,
                                     lastNeighbourSigma = sigma3)
createTopoClusters.clusters.Path = "caloClustersBarrel"
createTopoClusters.clusterCells.Path = "caloClusterBarrelCells"

##############################################################################################################                                                                                                     
#######                                       CALIBRATE TOPO-CLUSTERS                            #############
##############################################################################################################                                                                                                                               
if (calib) :
    from Configurables import CreateCaloClusters
    calibrateClusters = CreateCaloClusters("CalibrateClusters",
                                           genParticles = "GenParticles",
                                           clusters = "caloClustersBarrel",
                                           outClusters = "calibCaloClustersBarrel",
                                           outCells = "calibCaloClusterBarrelCells",
                                           readoutECal = ecalBarrelReadoutName,
                                           readoutHCal = hcalBarrelReadoutName,
                                           positionsECalTool = ECalBcells,
                                           positionsHCalTool = HCalBcellVols,
                                           calibrate = True,
                                           eDepCryoCorrection = True,
                                           ehECal = 1.,
                                           ehHCal = 1.1,
                                           a1 = a1,
                                           a2 = a2,
                                           a3 = a3,
                                           b1 = b1,
                                           b2 = b2,
                                           b3 = b3,
                                           c1 = c1,
                                           c2 = c2,
                                           c3 = c3,
                                           fractionECal = fractionECal)

    THistSvc().Output = ["rec DATAFILE='calibrateCluster_histograms.root' TYP='ROOT' OPT='RECREATE'"]
    THistSvc().PrintAll=True
    THistSvc().AutoSave=True
    THistSvc().AutoFlush=True
    THistSvc().OutputLevel=INFO


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
out = PodioOutput("out", OutputLevel=INFO)
out.outputCommands = ["drop *", "keep GenParticles", "keep GenVertices", "keep SmearedParticles", "keep caloClustersBarrel", "keep caloClusterBarrelCells", "keep caloClusterBarrelCellPositions", "keep calibCaloClusterBarrelCells", "keep caloClustersBarrelNoiseStep1", "keep caloClusterBarrelNoiseCellsStep1"]
out.filename = output_name

if elNoise or puNoise:
    if simargs.cone:
        out.outputCommands += ["keep selectedECalBarrelCellsNoise", "keep selectedHCalBarrelCellsNoise"]
    if calib:
        out.outputCommands += ["keep calibCaloClustersBarrelNoise", "keep caloClusterBarrelNoiseCells", "keep calibCaloClusterBarrelCellsNoise", "keep caloClusterBarrelNoiseCellPositions"]
    else:
        out.outputCommands += ["keep caloClustersBarrelNoise", "keep caloClusterBarrelNoiseCells", "keep caloClusterBarrelNoiseCellPositions"]

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
podioinput.AuditExecute = True
createemptycells.AuditExecute = True
out.AuditExecute = True

list_of_algorithms = [podioinput,
                      smear,
                      createemptycells]

if resegmentHCal and addedPU==0:
    list_of_algorithms += [posHcalBarrel, resegmentHcalBarrel, createHcalBarrelCells]

if elNoise or puNoise:
    list_of_algorithms += [createEcalBarrelCellsNoise, createHcalBarrelCellsNoise]
    if simargs.cone:
        list_of_algorithms += [selectionECal, selectionHCal]
    # add cluster splitting
    list_of_algorithms += [createTopoClustersNoise]
    if split:
        list_of_algorithms += [splitClusters]
    if not puNoise:
        list_of_algorithms += [positionsClusterBarrelNoise]
    if calib:
        list_of_algorithms += [calibrateClustersNoise]

else:
    list_of_algorithms += [createTopoClusters, positionsClusterBarrel]
    if calib:
        list_of_algorithms += [calibrateClusters]

list_of_algorithms += [out]

ApplicationMgr(
    TopAlg = list_of_algorithms,
    EvtSel = 'NONE',
    EvtMax = num_events,
    ExtSvc = [geoservice, podioevent],
#    OutputLevel = DEBUG
)
