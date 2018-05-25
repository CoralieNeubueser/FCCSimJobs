import argparse
simparser = argparse.ArgumentParser()
simparser.add_argument("--bFieldOff", action='store_true', help="Switch OFF magnetic field (default: B field ON)")

simparser.add_argument('-s','--seed', type=int, help='Seed for the random number generator', required=True)
simparser.add_argument('-N','--numEvents', type=int, help='Number of simulation events to run', required=True)
simparser.add_argument('--outName', type=str, help='Name of the output file', required=True)


genTypeGroup = simparser.add_mutually_exclusive_group(required = True) # Type of events to generate
genTypeGroup.add_argument("--singlePart", action='store_true', help="Single particle events")
genTypeGroup.add_argument("--pythia", action='store_true', help="Events generated with Pythia")
genTypeGroup.add_argument("--useVertexSmearTool", action='store_true', help="Use the Gaudi Vertex Smearing Tool")

from math import pi
singlePartGroup = simparser.add_argument_group('Single particles')
import sys
singlePartGroup.add_argument('-e','--energy', type=int, required='--singlePart' in sys.argv, help='Energy of particle in GeV')
singlePartGroup.add_argument('--etaMin', type=float, default=0., help='Minimal pseudorapidity')
singlePartGroup.add_argument('--etaMax', type=float, default=0., help='Maximal pseudorapidity')
singlePartGroup.add_argument('--phiMin', type=float, default=0, help='Minimal azimuthal angle')
singlePartGroup.add_argument('--phiMax', type=float, default=2*pi, help='Maximal azimuthal angle')
singlePartGroup.add_argument('--particle', type=int, required='--singlePart' in sys.argv, help='Particle type (PDG)')
singlePartGroup.add_argument('--flat', action='store_true', help='flat energy distribution for single particle generation')

pythiaGroup = simparser.add_argument_group('Pythia','Common for min bias and LHE')
pythiaGroup.add_argument('-c', '--card', type=str, default='Generation/data/Pythia_minbias_pp_100TeV.cmd', help='Path to Pythia card (default: PythiaCards/default.cmd)')

simargs, _ = simparser.parse_known_args()

print "=================================="
print "==      GENERAL SETTINGS       ==="
print "=================================="
magnetic_field = not simargs.bFieldOff
num_events = simargs.numEvents
seed = simargs.seed
output_name = simargs.outName
flat = simargs.flat
print "B field: ", magnetic_field
print "number of events = ", num_events
print "seed: ", seed
print "output name: ", output_name
if simargs.singlePart:
    energy = simargs.energy
    if simargs.flat:
        energy = 'flat'
    etaMin = simargs.etaMin
    etaMax = simargs.etaMax
    phiMin = simargs.phiMin
    phiMax = simargs.phiMax
    pdg = simargs.particle
    particle_geant_names = {11: 'e-', -11: 'e+', -13: 'mu+', 13: 'mu-', 22: 'gamma', 111: 'pi0', 211: 'pi+', -211: 'pi-', 130: 'kaon0L', 0:'geantino'}
    print "=================================="
    print "==       SINGLE PARTICLES      ==="
    print "=================================="
    print "particle PDG, name: ", pdg, " ", particle_geant_names[pdg]
    print "energy: ", energy, "GeV"
    if etaMin == etaMax:
        print "eta: ", etaMin
    else:
        print "eta: from ", etaMin, " to ", etaMax
    if phiMin == phiMax:
        print "phi: ", phiMin
    else:
        print "phi: from ", phiMin, " to ", phiMax
elif simargs.pythia:
    card = simargs.card
    print "=================================="
    print "==            PYTHIA           ==="
    print "=================================="
    print "card = ", card
print "=================================="


from Gaudi.Configuration import *
from GaudiKernel import SystemOfUnits as units
##############################################################################################################
#######                                         GEOMETRY                                         #############
##############################################################################################################
path_to_detector = "/cvmfs/fcc.cern.ch/sw/releases/0.9.1/x86_64-slc6-gcc62-opt/linux-scientificcernslc6-x86_64/gcc-6.2.0/fccsw-0.9.1-c5dqdyv4gt5smfxxwoluqj2pjrdqvjuj"
detectors_to_use=[path_to_detector+'/Detector/DetFCChhBaseline1/compact/FCChh_DectEmptyMaster.xml',
                  path_to_detector+'/Detector/DetFCChhTrackerTkLayout/compact/Tracker.xml',
                  path_to_detector+'/Detector/DetFCChhECalInclined/compact/FCChh_ECalBarrel_withCryostat.xml',
                  path_to_detector+'/Detector/DetFCChhHCalTile/compact/FCChh_HCalBarrel_TileCal.xml',
                  ]

from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc", detectors = detectors_to_use, OutputLevel = WARNING)

# ECAL readouts
ecalBarrelReadoutName = "ECalBarrelEta"
ecalBarrelReadoutNamePhiEta = "ECalBarrelPhiEta"
ecalEndcapReadoutName = "EMECPhiEta"
ecalFwdReadoutName = "EMFwdPhiEta"
# HCAL readouts
hcalBarrelReadoutName = "HCalBarrelReadout"
hcalBarrelReadoutNamePhiEta = hcalBarrelReadoutName + "_phieta"
hcalExtBarrelReadoutName = "HCalExtBarrelReadout"
hcalExtBarrelReadoutNamePhiEta = hcalExtBarrelReadoutName + "_phieta"
hcalEndcapReadoutName = "HECPhiEta"
hcalFwdReadoutName = "HFwdPhiEta"
# Tail Catcher readout
tailCatcherReadoutName = "Muons_Readout"
# layers to be merged in endcaps, field name of the readout
ecalEndcapNumberOfLayersToMerge = [2] + [2] + [4]*37 + [5]
hcalEndcapNumberOfLayersToMerge = [2] + [4]*19 + [5]
identifierName = "layer"
volumeName = "layer"
##############################################################################################################
#######                                        SIMULATION                                        #############
##############################################################################################################
# Setting random seed, will be propagated to Geant
from Configurables import  RndmGenSvc
from GaudiSvc.GaudiSvcConf import HepRndm__Engine_CLHEP__RanluxEngine_
randomEngine = eval('HepRndm__Engine_CLHEP__RanluxEngine_')
randomEngine = randomEngine('RndmGenSvc.Engine')
randomEngine.Seeds = [seed]

# Magnetic field
from Configurables import SimG4ConstantMagneticFieldTool
if magnetic_field:
    field = SimG4ConstantMagneticFieldTool("bField", FieldOn=True, FieldZMax=20*units.m, IntegratorStepper="ClassicalRK4")
else:
    field = SimG4ConstantMagneticFieldTool("bField", FieldOn=False)

from Configurables import SimG4Svc
geantservice = SimG4Svc("SimG4Svc", detector='SimG4DD4hepDetector', physicslist="SimG4FtfpBert", actions="SimG4FullSimActions", magneticField=field)
# range cut
geantservice.g4PostInitCommands += ["/run/setCut 0.1 mm"]

from Configurables import SimG4Alg, SimG4SaveCalHits, SimG4SingleParticleGeneratorTool, SimG4SaveTrackerHits

savetrackertool = SimG4SaveTrackerHits("saveTrackerHits", readoutNames = ["TrackerBarrelReadout", "TrackerEndcapReadout"]) 
savetrackertool.positionedTrackHits.Path = "TrackerPositionedHits"
savetrackertool.trackHits.Path = "TrackerHits"
savetrackertool.digiTrackHits.Path = "TrackerDigiPostPoint"
saveecaltool = SimG4SaveCalHits("saveECalBarrelHits",readoutNames = [ecalBarrelReadoutName])
saveecaltool.positionedCaloHits.Path = "ECalBarrelPositionedHits"
saveecaltool.caloHits.Path = "ECalBarrelHits"
savehcaltool = SimG4SaveCalHits("saveHCalBarrelHits",readoutNames = [hcalBarrelReadoutName])
savehcaltool.positionedCaloHits.Path = "HCalBarrelPositionedHits"
savehcaltool.caloHits.Path = "HCalBarrelHits"
outputHitsTools = ["SimG4SaveCalHits/saveECalBarrelHits", "SimG4SaveCalHits/saveHCalBarrelHits"]

geantsim = SimG4Alg("SimG4Alg", outputs = outputHitsTools)

if simargs.singlePart:
    from Configurables import SimG4SingleParticleGeneratorTool
    if simargs.flat:
        pgun=SimG4SingleParticleGeneratorTool("SimG4SingleParticleGeneratorTool", saveEdm=True,
                                              particleName=particle_geant_names[pdg],
                                              energyMin=10 * 1000, energyMax=1000 * 1000, # flat energy from 10GeV to 1TeV
                                              etaMin=etaMin, etaMax=etaMax, phiMin = phiMin, phiMax = phiMax)
        geantsim.eventProvider = pgun
    else:
        pgun=SimG4SingleParticleGeneratorTool("SimG4SingleParticleGeneratorTool", saveEdm=True,
                                              particleName=particle_geant_names[pdg], 
                                              energyMin=energy * 1000, energyMax=energy * 1000,
                                              etaMin=etaMin, etaMax=etaMax, phiMin = phiMin, phiMax = phiMax)
        geantsim.eventProvider = pgun
else:
    from Configurables import PythiaInterface, GenAlg, GaussSmearVertex
    smeartool = GaussSmearVertex("GaussSmearVertex")
    if simargs.useVertexSmearTool:
      smeartool.xVertexSigma = 0.5*units.mm
      smeartool.yVertexSigma = 0.5*units.mm
      smeartool.zVertexSigma = 40*units.mm
      smeartool.tVertexSigma = 180*units.picosecond

    pythia8gentool = PythiaInterface("Pythia8",Filename=card)
    pythia8gen = GenAlg("Pythia8", SignalProvider=pythia8gentool, VertexSmearingTool=smeartool)
    pythia8gen.hepmc.Path = "hepmc"
    from Configurables import HepMCToEDMConverter
    hepmc_converter = HepMCToEDMConverter("Converter")
    hepmc_converter.hepmc.Path="hepmc"
    hepmc_converter.genparticles.Path="allGenParticles"
    hepmc_converter.genvertices.Path="GenVertices"
    from Configurables import GenParticleFilter
### Filters generated particles
# accept is a list of particle statuses that should be accepted
    genfilter = GenParticleFilter("StableParticles", accept=[1], OutputLevel=DEBUG)
    genfilter.allGenParticles.Path = "allGenParticles"
    genfilter.filteredGenParticles.Path = "GenParticles"
    from Configurables import SimG4PrimariesFromEdmTool
    particle_converter = SimG4PrimariesFromEdmTool("EdmConverter")
    particle_converter.genParticles.Path = "GenParticles"
    geantsim.eventProvider = particle_converter


##############################################################################################################
#######                                       DIGITISATION                                       #############
##############################################################################################################

# Calibration constants
from Configurables import CalibrateInLayersTool, CalibrateCaloHitsTool
calibEcalBarrel = CalibrateInLayersTool("CalibrateEcalBarrel",
                                        # sampling fraction obtained using SamplingFractionInLayers from DetStudies package
                                        samplingFraction = [0.12125] + [0.14283] + [0.16354] + [0.17662] + [0.18867] + [0.19890] + [0.20637] + [0.20802],
                                        readoutName = ecalBarrelReadoutName,
                                        layerFieldName = "layer")
calibHcells = CalibrateCaloHitsTool("CalibrateHCal", invSamplingFraction="41.66")
calibEcalEndcap = CalibrateCaloHitsTool("CalibrateECalEndcap", invSamplingFraction="13.89")
calibEcalFwd = CalibrateCaloHitsTool("CalibrateECalFwd", invSamplingFraction="303.03")
calibHcalEndcap = CalibrateCaloHitsTool("CalibrateHCalEndcap", invSamplingFraction="33.62")
calibHcalFwd = CalibrateCaloHitsTool("CalibrateHCalFwd", invSamplingFraction="1207.7")

# Create cells
from Configurables import CreateCaloCells
# -> ECal barrel
# 1. step - merge hits into cells with default Eta segmentation
createEcalBarrelCellsStep1 = CreateCaloCells("EcalBarrelCellsStep1",
                                             doCellCalibration=True,
                                             calibTool=calibEcalBarrel,
                                             addCellNoise=False, filterCellNoise=False)
createEcalBarrelCellsStep1.hits.Path="ECalBarrelHits"
createEcalBarrelCellsStep1.cells.Path="ECalBarrelCellsStep1"
# 2. step - rewrite the cellId using the Phi-Eta segmentation (remove 'module')
# 2.1. retrieve phi positions from centres of cells
from Configurables import CreateVolumeCaloPositions
positionsEcalBarrel = CreateVolumeCaloPositions("positionsEcalBarrel")
positionsEcalBarrel.hits.Path = "ECalBarrelCellsStep1"
positionsEcalBarrel.positionedHits.Path = "ECalBarrelPositions"
# 2.2. assign cells into phi bins
from Configurables import RedoSegmentation
resegmentEcalBarrel = RedoSegmentation("ReSegmentationEcalBarrel",
                                       oldReadoutName = 'ECalBarrelEta',
                                       oldSegmentationIds = ['module'],
                                       newReadoutName = 'ECalBarrelPhiEta',
                                       inhits = "ECalBarrelPositions",
                                       outhits = "ECalBarrelCellsStep2")
# 3. step - merge cells in the same phi bin
createEcalBarrelCells = CreateCaloCells("CreateECalBarrelCells",
                                        doCellCalibration=False, # already calibrated in step 1
                                        addCellNoise=False, filterCellNoise=False,
                                        hits="ECalBarrelCellsStep2",
                                        cells="ECalBarrelCells")

# -> Hcal barrel
createHcalCells = CreateCaloCells("CreateHCalBarrelCells",
                                  doCellCalibration=True,
                                  calibTool=calibHcells,
                                  addCellNoise = False, filterCellNoise = False,
                                  hits="HCalBarrelHits",
                                  cells="HCalBarrelCells")

# PODIO algorithm
from Configurables import ApplicationMgr, FCCDataSvc, PodioOutput
podioevent = FCCDataSvc("EventDataSvc")
out = PodioOutput("out")
out.outputCommands = ["drop *",
                      "keep GenParticles",
                      "keep GenVertices",
                      "keep ECalBarrelCells",
                      "keep HCalBarrelCells"]
out.filename = output_name

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
geantsim.AuditExecute = True
createEcalBarrelCellsStep1.AuditExecute = True
positionsEcalBarrel.AuditExecute = True
resegmentEcalBarrel.AuditExecute = True
createEcalBarrelCells.AuditExecute = True
createHcalCells.AuditExecute = True
out.AuditExecute = True

list_of_algorithms = [geantsim,
                      createEcalBarrelCellsStep1,
                      positionsEcalBarrel,
                      resegmentEcalBarrel,
                      createEcalBarrelCells,
                      createHcalCells,
                      out]

if simargs.pythia:
    list_of_algorithms = [pythia8gen, hepmc_converter, genfilter] + list_of_algorithms

ApplicationMgr(
    TopAlg = list_of_algorithms,
    EvtSel = 'NONE',
    EvtMax   = num_events,
    ExtSvc = [podioevent, geoservice, geantservice],
#    OutputLevel = VERBOSE
)