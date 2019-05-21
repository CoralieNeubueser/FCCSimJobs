import os
import sys
import math
import numpy as n
import ROOT as r
import argparse

from ROOT import gSystem
result=gSystem.Load("libDDCorePlugins")
from ROOT import dd4hep
from EventStore import EventStore
if result < 0:
    print "No lib loadable!"

system_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4")
ecalBarrel_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,cryo:1,type:3,subtype:3,layer:8,eta:9,phi:10")
hcalBarrel_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,module:8,row:9,layer:5")
hcalExtBarrel_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,module:8,row:9,layer:5")
ecalEndcap_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,subsystem:1,type:3,subtype:3,layer:8,eta:10,phi:10")
hcalEndcap_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,subsystem:1,type:3,subtype:3,layer:8,eta:10,phi:10")
ecalFwd_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,subsystem:1,type:3,subtype:3,layer:8,eta:11,phi:10")
hcalFwd_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,subsystem:1,type:3,subtype:3,layer:8,eta:11,phi:10")
trackerBarrel_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,layer:5,module:18,x:-15,z:-15")
trackerEndcap_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,posneg:1,disc:5,component:17,x:-15,z:-15")

lastECalBarrelLayer = int(7)
lastECalEndcapLayer = int(39)
lastECalFwdLayer = int(41)
lastInnerTrackerBarrelLayer = int(5)
lastOuterTrackerBarrelLayer = int(11)
lastInnerTrackerPosECapLayer = int(16)
lastInnerTrackerNegECapLayer = int(21)
lastOuterTrackerPosECapLayer = int(27)
lastOuterTrackerNegECapLayer = int(33)
lastFwdTrackerPosECapLayer = int(42)

def systemID(cellid):
    return system_decoder.get(cellid, "system")

def benchmarkCorr(ecal, ecal_last, ehad, ehad_first, aA, aB, aC):
    ebench = ecal*aA + ehad + aB * math.sqrt(math.fabs(aA*ecal_last*ehad_first)) + aC*(ecal*aA)**2
    return ebench

def signy(y):
    if y>0: return 1
    elif y<0: return -1
    return 0

if len(sys.argv)!=3:
    print 'usage python Convert.py infile outfile'
infile_name = sys.argv[1]
outfile_name = sys.argv[2]

a=1.062
b=0.659
c1=-0.0000063
if outfile_name.find("bFieldOn"):
    a=0.996
    b=0.565
    c1=-0.00000074

rminECal = 175
bField = 4

parser = argparse.ArgumentParser()
parser.add_argument('--resegmentedHCal', action='store_true', help="HCal cells are resegmented to deltaEta = 0.025, use different decoder")
parser.add_argument('--noSignal', action='store_true', help='cone around opposite gen particle eta positions, to extract noise/cell')
args, _ = parser.parse_known_args()

if args.resegmentedHCal:
    hcalBarrel_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,layer:5,eta:9,phi:10")
    hcalExtBarrel_decoder = dd4hep.DDSegmentation.BitFieldCoder("system:4,type:2:,layer:4,eta:10,phi:10")

gen_eta = r.std.vector(float)()
gen_phi = r.std.vector(float)()
gen_pt  = r.std.vector(float)()
gen_x  = r.std.vector(float)()
gen_y  = r.std.vector(float)()
gen_z  = r.std.vector(float)()
gen_energy = r.std.vector(float)()
gen_pdgid = r.std.vector(float)()
gen_status = r.std.vector(float)()
gen_bits = r.std.vector(float)()

track_eta = r.std.vector(float)()
track_phi = r.std.vector(float)()
track_pt  = r.std.vector(float)()
track_x  = r.std.vector(float)()
track_y  = r.std.vector(float)()
track_z  = r.std.vector(float)()
track_energy = r.std.vector(float)()
track_pdgid = r.std.vector(float)()
track_status = r.std.vector(float)()
track_bits = r.std.vector(float)()

cluster_eta = r.std.vector(float)()
cluster_phi = r.std.vector(float)()
cluster_pt  = r.std.vector(float)()
cluster_ene = r.std.vector(float)()
cluster_x = r.std.vector(float)()
cluster_y = r.std.vector(float)()
cluster_z = r.std.vector(float)()
cluster_cells = r.std.vector(int)()
cluster_seedCells = r.std.vector(int)()
cluster_neighbourCells = r.std.vector(int)()
cluster_arbitraryCells = r.std.vector(int)()
cluster_deltaR = r.std.vector(float)()

rec_eta = r.std.vector(float)()
rec_phi = r.std.vector(float)()
rec_pt  = r.std.vector(float)()
rec_ene = r.std.vector(float)()
rec_x = r.std.vector(float)()
rec_y = r.std.vector(float)()
rec_z = r.std.vector(float)()
rec_layer = r.std.vector(int)()
rec_detid = r.std.vector(int)()
rec_bits = r.std.vector(float)()

outfile=r.TFile(outfile_name,"recreate")
outtree=r.TTree('events','Events')

ev_num = n.zeros(1, dtype=int) 
ev_e =  n.zeros(1, dtype=float)
ev_ebench =  n.zeros(1, dtype=float)
ev_nRechits = n.zeros(1, dtype=int) 

outtree.Branch("ev_num", ev_num, "ev_num/I")
outtree.Branch("ev_e", ev_e, "ev_e/D")
outtree.Branch("ev_ebench", ev_ebench, "ev_ebench/D")
outtree.Branch("ev_nRechits", ev_nRechits, "ev_nRechits/I")

outtree.Branch("cluster_pt", cluster_pt)
outtree.Branch("cluster_eta", cluster_eta)
outtree.Branch("cluster_phi", cluster_phi)
outtree.Branch("cluster_energy", cluster_ene)
outtree.Branch("cluster_x", cluster_x)
outtree.Branch("cluster_y", cluster_y)
outtree.Branch("cluster_z", cluster_z)

outtree.Branch("cluster_cells", cluster_cells)
outtree.Branch("cluster_seedCells", cluster_seedCells)
outtree.Branch("cluster_neighbourCells", cluster_neighbourCells)
outtree.Branch("cluster_arbitraryCells", cluster_arbitraryCells)
outtree.Branch("cluster_deltaR", cluster_deltaR)

outtree.Branch("rechit_pt", rec_pt)
outtree.Branch("rechit_eta", rec_eta)
outtree.Branch("rechit_phi", rec_phi)
outtree.Branch("rechit_energy", rec_ene)
outtree.Branch("rechit_layer", rec_layer)
outtree.Branch("rechit_x", rec_x)
outtree.Branch("rechit_y", rec_y)
outtree.Branch("rechit_z", rec_z)
outtree.Branch("rechit_detid", rec_detid)
outtree.Branch("rechit_bits", rec_bits)

outtree.Branch("gen_pt", gen_pt)
outtree.Branch("gen_x", gen_x)
outtree.Branch("gen_y", gen_y)
outtree.Branch("gen_z", gen_z)
outtree.Branch("gen_eta", gen_eta)
outtree.Branch("gen_phi", gen_phi)
outtree.Branch("gen_energy", gen_energy)
outtree.Branch("gen_status", gen_status)
outtree.Branch("gen_pdgid", gen_pdgid)
outtree.Branch("gen_bits", gen_bits)

outtree.Branch("track_pt", track_pt)
outtree.Branch("track_x", track_x)
outtree.Branch("track_y", track_y)
outtree.Branch("track_z", track_z)
outtree.Branch("track_eta", track_eta)
outtree.Branch("track_phi", track_phi)
outtree.Branch("track_energy", track_energy)
outtree.Branch("track_status", track_status)
outtree.Branch("track_pdgid", track_pdgid)
outtree.Branch("track_bits", track_bits)


numEvent = 0
with EventStore([infile_name]) as evs: # p.ex output of Examples/options/simple_pythia.py
    for ev in evs:
        
        ev_num[0] = numEvent
        numHits = 0
        E = .0
        Ebench = .0
        Eem = .0
        Ehad = .0
        EemLast = .0
        EhadFirst = .0
        etaGen = .0
        phiGen = .0
        energyGen = .0 
        
        if ev.get("GenParticles"):
            for g in ev.get("GenParticles"):
                if g.status() == 1:
                    position = r.TVector3(g.p4().px,g.p4().py,g.p4().pz)
                    
                    gen_x.push_back(g.startVertex().x()/10.)
                    gen_y.push_back(g.startVertex().y()/10.)
                    gen_z.push_back(g.startVertex().z()/10.)
                    
                    pt=math.sqrt(g.p4().px**2+g.p4().py**2)
                    
                    eta=position.Eta()
                    phi=position.Phi()
                    
                    tlv=r.TLorentzVector()
                    tlv.SetPtEtaPhiM(pt,eta,phi,g.p4().mass)
                    gen_pt.push_back(pt)
                    gen_eta.push_back(eta)
                    gen_phi.push_back(phi)
                    gen_energy.push_back(math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2))
                    gen_bits.push_back(g.bits())
                    
                    etaGen += eta*math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2)
                    phiGen += phi*math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2)
                    energyGen += math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2)
                    
                    if math.fabs(tlv.E()-math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2))>0.01 and g.status==1:
                        print '=======================etlv  ',tlv.E(),'    ',math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2),'  eta  ',eta,'   phi   ',phi,'  x  ',g.p4().px,'  y  ',g.p4().py,'  z  ',g.p4().pz
                    gen_pdgid.push_back(g.pdgId())
                    gen_status.push_back(g.status())
                        
                    if energyGen != 0.:
                        etaGen = float(etaGen)/float(energyGen)
                        phiGen = float(phiGen)/float(energyGen)
                        
                    # used to collect cells without signal -> noise/cone estimations
                    if args.noSignal:
                        etaGen = -etaGen
                        phiGen = -phiGen

            print 'gen particle:  ', etaGen,phiGen,energyGen

        if ev.get("SmearedParticles"):
            for g in ev.get("SmearedParticles"):
                if g.status() == 1:
                    position = r.TVector3(g.p4().px,g.p4().py,g.p4().pz)

                    track_x.push_back(g.startVertex().x()/10.)
                    track_y.push_back(g.startVertex().y()/10.)
                    track_z.push_back(g.startVertex().z()/10.)

                    pt=math.sqrt(g.p4().px**2+g.p4().py**2)

                    eta=position.Eta()
                    phi=position.Phi()

                    tlv=r.TLorentzVector()
                    tlv.SetPtEtaPhiM(pt,eta,phi,g.p4().mass)
                    track_pt.push_back(pt)
                    track_eta.push_back(eta)
                    track_phi.push_back(phi)
                    track_energy.push_back(math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2))
                    track_bits.push_back(g.bits())

                    if math.fabs(tlv.E()-math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2))>0.01 and g.status==1:
                        print '=======================etlv  ',tlv.E(),'    ',math.sqrt(g.p4().mass**2+g.p4().px**2+g.p4().py**2+g.p4().pz**2),'  eta  ',eta,'   phi   ',phi,'  x  ',g.p4().px,'  y  ',g.p4().py,'  z  ',g.p4().pz
                    track_pdgid.push_back(g.pdgId())
                    track_status.push_back(g.status())
    
                        
        if ev.get("caloClustersBarrel"):
            print 'Using cluster collection "caloClustersBarrel" '
            for c in ev.get("caloClustersBarrel"):
                position = r.TVector3(c.position().x,c.position().y,c.position().z)
                cluster_ene.push_back(c.energy())
                cluster_eta.push_back(position.Eta())
                cluster_phi.push_back(position.Phi())
                cluster_pt.push_back(c.energy()*position.Unit().Perp())
                cluster_x.push_back(c.position().x/10.)
                cluster_y.push_back(c.position().y/10.)
                cluster_z.push_back(c.position().z/10.)
                cluster_cells.push_back(c.hits_size())
    
        elif ev.get("calibCaloClustersBarrelNoise"):
            print 'Using cluster collection "calibCaloClustersBarrelNoise" '
            for c in ev.get("calibCaloClustersBarrelNoise"):
                position = r.TVector3(c.position().x,c.position().y,c.position().z)
                cluster_ene.push_back(c.energy())
                cluster_eta.push_back(position.Eta())
                cluster_phi.push_back(position.Phi())
                cluster_pt.push_back(c.energy()*position.Unit().Perp())
                cluster_x.push_back(c.position().x/10.)
                cluster_y.push_back(c.position().y/10.)
                cluster_z.push_back(c.position().z/10.)
                cluster_deltaR.push_back(c.time())

                cluster_cells.push_back(c.hits_size())
                # calculate rmsEta, rmsPhi
                # get cell types
                energySum=float(0)
                rmsEta=float(0)
                rmsPhi=float(0)
                rmsR=float(0)
                cellTypes = [int(0)] * 3
                
                for cell in range(0, c.hits_size()):
                    cellTypes[int(c.hits(cell).core().bits-1)] += 1
                    
                cluster_seedCells.push_back(cellTypes[0])
                cluster_neighbourCells.push_back(cellTypes[1])
                cluster_arbitraryCells.push_back(cellTypes[2])

        elif ev.get("caloClustersBarrelNoise"):
            print 'Using cluster collection "caloClustersBarrelNoise" '
            for c in ev.get("caloClustersBarrelNoise"):
                position = r.TVector3(c.position().x,c.position().y,c.position().z)
                cluster_ene.push_back(c.energy())
                cluster_eta.push_back(position.Eta())
                cluster_phi.push_back(position.Phi())
                cluster_pt.push_back(c.energy()*position.Unit().Perp())
                cluster_x.push_back(c.position().x/10.)
                cluster_y.push_back(c.position().y/10.)
                cluster_z.push_back(c.position().z/10.)
                cluster_deltaR.push_back(c.time())
                cluster_cells.push_back(c.hits_size())
                # calculate rmsEta, rmsPhi                                                                                                                                                               
                # get cell types                                                                                                                                                                        
                energySum=float(0)
                rmsEta=float(0)
                rmsPhi=float(0)
                rmsR=float(0)
                cellTypes = [int(0)] * 3
                
                for cell in range(0, c.hits_size()):
                    cellTypes[int(c.hits(cell).core().bits-1)] += 1

                cluster_seedCells.push_back(cellTypes[0])
                cluster_neighbourCells.push_back(cellTypes[1])
                cluster_arbitraryCells.push_back(cellTypes[2])

        elif ev.get("caloClusters"):
            print 'Using cluster collection "caloClusters" '
            for c in ev.get("caloClusters"):
                position = r.TVector3(c.position().x,c.position().y,c.position().z)
                cluster_ene.push_back(c.energy())
                cluster_eta.push_back(position.Eta())
                cluster_phi.push_back(position.Phi())
                cluster_pt.push_back(c.energy()*position.Unit().Perp())
                cluster_x.push_back(c.position().x/10.)
                cluster_y.push_back(c.position().y/10.)
                cluster_z.push_back(c.position().z/10.)
                cluster_cells.push_back(c.hits_size())

        elif ev.get("caloClustersNoise"):
            print 'Using cluster collection "caloClustersNoise" '
            for c in ev.get("caloClustersNoise"):
                position = r.TVector3(c.position().x,c.position().y,c.position().z)
                cluster_ene.push_back(c.energy())
                cluster_eta.push_back(position.Eta())
                cluster_phi.push_back(position.Phi())
                cluster_pt.push_back(c.energy()*position.Unit().Perp())
                cluster_x.push_back(c.position().x/10.)
                cluster_y.push_back(c.position().y/10.)
                cluster_z.push_back(c.position().z/10.)
                cluster_cells.push_back(c.hits_size())
                    
        else:
            if ev.get("HCalBarrelCellPositions"):
                print 'Using cell collection "HCalBarrelCellPositions" '
                for c in ev.get("HCalBarrelCellPositions"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    recPhi = float(position.Phi())
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(hcalBarrel_decoder.get(c.cellId(), "layer") + lastECalBarrelLayer + 1)
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    if hcalBarrel_decoder["layer"] == 0:
                        EhadFirst += c.energy()
                    E += c.energy()
                    Ehad += c.energy()
                    numHits += 1
                        
            if ev.get("ECalBarrelCellPositions"):
                print 'Using cell collection "ECalBarrelCellPositions" '
                for c in ev.get("ECalBarrelCellPositions"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(ecalBarrel_decoder.get(c.cellId(), "layer"))
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    if ecalBarrel_decoder["layer"] == lastECalBarrelLayer:
                        EemLast += c.energy()
                    E += c.energy()
                    Eem += c.energy()
                    numHits += 1
                    
            if ev.get("HCalExtBarrelCellPositions"):
                for c in ev.get("HCalExtBarrelCellPositions"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(hcalExtBarrel_decoder.get(c.cellId(), "layer") + lastECalBarrelLayer + 1)
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    E += c.energy()
                    numHits += 1
            
            if ev.get("ECalEndcapCellPositions"):
                for c in ev.get("ECalEndcapCellPositions"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(ecalEndcap_decoder.get(c.cellId(), "layer"))
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    E += c.energy()
                    numHits += 1
                        
            if ev.get("HCalEndcapCellPositions"):
                for c in ev.get("HCalEndcapCellPositions"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(hcalEndcap_decoder.get(c.cellId(), "layer") + lastECalEndcapLayer + 1)
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    E += c.energy()
                    numHits += 1
                        
            if ev.get("ECalFwdCellPositions"):
                for c in ev.get("ECalFwdCellPositions"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(ecalFwd_decoder.get(c.cellId(), "layer"))
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    E += c.energy()
                    numHits += 1
                    
            if ev.get("HCalFwdCellPositions"):
                for c in ev.get("HCalFwdCellPositions"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(hcalFwd_decoder.get(c.cellId(), "layer") + lastECalFwdLayer + 1)
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    E += c.energy()
                    numHits += 1


            if ev.get("HCalPositionedHits"):
                for c in ev.get("HCalPositionedHits"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    rec_layer.push_back(ecalFwd_decoder.get(c.cellId(), "layer"))
                    rec_x.push_back(c.position().x/10.)
                    rec_y.push_back(c.position().y/10.)
                    rec_z.push_back(c.position().z/10.)
                    rec_detid.push_back(systemID(c.cellId()))
                    rec_bits.push_back(c.bits())
                    E += c.energy()
                    numHits += 1

            if ev.get("TrackerPositionedHits"):
                for c in ev.get("TrackerPositionedHits"):
                    position = r.TVector3(c.position().x,c.position().y,c.position().z)
                    rec_ene.push_back(c.energy())
                    rec_eta.push_back(position.Eta())
                    rec_phi.push_back(position.Phi())
                    rec_pt.push_back(c.energy()*position.Unit().Perp())
                    sysID = systemID(c.cellId())
                    if  sysID == 0 :
                        rec_layer.push_back(trackerBarrel_decoder["layer"])
                    elif sysID == 1 :
                        rec_layer.push_back(trackerBarrel_decoder["layer"] + lastInnerTrackerBarrelLayer + 1)
                    elif sysID == 2 :
                        posneg = trackerEndcap_decoder["posneg"]
                        if posneg == 0 :
                            rec_layer.push_back(trackerEndcap_decoder["disc"] + lastOuterTrackerBarrelLayer + 1)
                        else :
                            rec_layer.push_back(trackerEndcap_decoder["disc"] + lastInnerTrackerPosECapLayer + 1)
                    elif sysID == 3:
                        posneg = trackerEndcap_decoder["posneg"]
                        if posneg == 0 :
                            rec_layer.push_back(trackerEndcap_decoder["disc"] + lastInnerTrackerNegECapLayer + 1)
                        else :
                            rec_layer.push_back(trackerEndcap_decoder["disc"] + lastOuterTrackerPosECapLayer + 1)
                    else :
                        posneg = trackerEndcap_decoder["posneg"]
                        if posneg == 0 :
                            rec_layer.push_back(trackerEndcap_decoder["disc"] + lastOuterTrackerNegECapLayer + 1)
                        else :
                            rec_layer.push_back(trackerEndcap_decoder["disc"] + lastFwdTrackerPosECapLayer + 1)
                            rec_x.push_back(c.position().x/10.)
                            rec_y.push_back(c.position().y/10.)
                            rec_z.push_back(c.position().z/10.)
                            rec_detid.push_back(systemID(c.cellId()))
                            rec_bits.push_back(c.bits())
                            E += c.energy()
                            numHits += 1
                            
        ev_ebench[0] = benchmarkCorr(Eem,EemLast,Ehad,EhadFirst,a,b,c1)
        ev_e[0] = E
        ev_nRechits[0] = numHits
        
        outtree.Fill()
        
        gen_eta.clear()
        gen_phi.clear()
        gen_pt.clear()
        gen_energy.clear()
        gen_pdgid.clear()
        gen_status.clear()

        track_eta.clear()
        track_phi.clear()
        track_pt.clear()
        track_energy.clear()
        track_pdgid.clear()
        track_status.clear()
        
        cluster_cells.clear()
        cluster_seedCells.clear()
        cluster_neighbourCells.clear()
        cluster_arbitraryCells.clear()
        cluster_deltaR.clear()
        cluster_eta.clear()
        cluster_phi.clear()
        cluster_pt.clear()
        cluster_ene.clear()
        cluster_x.clear()
        cluster_y.clear()
        cluster_z.clear()
        
        rec_eta.clear()
        rec_phi.clear()
        rec_pt.clear()
        rec_ene.clear()
        rec_layer.clear()
        rec_x.clear()
        rec_y.clear()
        rec_z.clear()
        rec_detid.clear()
        rec_bits.clear()
        
        numEvent += 1

outtree.Write()
outfile.Write()
outfile.Close()


