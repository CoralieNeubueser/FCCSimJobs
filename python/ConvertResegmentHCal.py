import os
import sys
import math
import numpy as n
import ROOT as r

from ROOT import gSystem
result=gSystem.Load("libDDCorePlugins")
from ROOT import dd4hep
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

def benchmarkCorr(ecal, ecal_last, ehad, ehad_first):
    a=0.978
    b=0.479
    c=-0.0000054
    ebench = ecal*a + ehad + b * math.sqrt(math.fabs(a*ecal_last*ehad_first)) + c*(ecal*a)**2
    return ebench

def signy(y):
    if y>0: return 1
    elif y<0: return -1
    return 0

if len(sys.argv)!=3:
    print 'usage python Convert.py infile outfile'
infile_name = sys.argv[1]
outfile_name = sys.argv[2]

infile=r.TFile.Open(infile_name)
intree=infile.Get('events')

gen_eta = r.std.vector(float)()
gen_phi = r.std.vector(float)()
gen_pt  = r.std.vector(float)()
gen_energy = r.std.vector(float)()
gen_pdgid = r.std.vector(float)()
gen_status = r.std.vector(float)()
gen_bits = r.std.vector(float)()

cluster_eta = r.std.vector(float)()
cluster_phi = r.std.vector(float)()
cluster_pt  = r.std.vector(float)()
cluster_ene = r.std.vector(float)()
cluster_x = r.std.vector(float)()
cluster_y = r.std.vector(float)()
cluster_z = r.std.vector(float)()

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

maxEvent = intree.GetEntries()
print 'Number of events : ',maxEvent

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
outtree.Branch("gen_eta", gen_eta)
outtree.Branch("gen_phi", gen_phi)
outtree.Branch("gen_energy", gen_energy)
outtree.Branch("gen_status", gen_status)
outtree.Branch("gen_pdgid", gen_pdgid)
outtree.Branch("gen_bits", gen_bits)

# storage for new HCal cells:
newRechit_eta = {}
newRechit_phi = {}
newRechit_pt = {}
newRechit_energy ={}
newRechit_x = {}
newRechit_y = {}
newRechit_z = {}
newRechit_layer = {}
newRechit_detid = {}
newRechit_bits = {}

#n.array([(e,p,l),(0.)]) newRechit_eta;
#n.array([(e,p,l),(0.)]) newRechit_phi;
#n.array([(e,p,l),(0.)]) newRechit_pt;
#n.array([(e,p,l),(0.)]) newRechit_energy;
#n.array([(e,p,l),(0.)]) newRechit_x;
#n.array([(e,p,l),(0.)]) newRechit_y;
#n.array([(e,p,l),(0.)]) newRechit_z;
#n.array([(e,p,l),(0.)]) newRechit_layer;

etaOffset = 1.256

numEvent = 0
for event in intree:
    ev_num[0] = numEvent
    numHits = 0
    E = .0
    Ebench = .0
    Eem = 0
    Ehad = 0
    EemLast = 0
    EhadFirst = 0
    if event.GetBranchStatus("GenParticles"):
        for g in event.GenParticles:
            position = r.TVector3(g.core.p4.px,g.core.p4.py,g.core.p4.pz)
            
            pt=math.sqrt(g.core.p4.px**2+g.core.p4.py**2)
            eta=position.Eta()
            phi=position.Phi()
            
            tlv=r.TLorentzVector()
            tlv.SetPtEtaPhiM(pt,eta,phi,g.core.p4.mass)
            gen_pt.push_back(pt)
            gen_eta.push_back(eta)
            gen_phi.push_back(phi)
            gen_energy.push_back(math.sqrt(g.core.p4.mass**2+g.core.p4.px**2+g.core.p4.py**2+g.core.p4.pz**2))
            gen_bits.push_back(g.core.bits)

            if math.fabs(tlv.E()-math.sqrt(g.core.p4.mass**2+g.core.p4.px**2+g.core.p4.py**2+g.core.p4.pz**2))>0.01 and g.core.status==1:
                print '=======================etlv  ',tlv.E(),'    ',math.sqrt(g.core.p4.mass**2+g.core.p4.px**2+g.core.p4.py**2+g.core.p4.pz**2),'  eta  ',eta,'   phi   ',phi,'  x  ',g.core.p4.px,'  y  ',g.core.p4.py,'  z  ',g.core.p4.pz
            gen_pdgid.push_back(g.core.pdgId)
            gen_status.push_back(g.core.status)

    if event.GetBranchStatus("caloClustersBarrel"):
        for c in event.caloClustersBarrel:
            position = r.TVector3(c.core.position.x,c.core.position.y,c.core.position.z)
            cluster_ene.push_back(c.core.energy)
            cluster_eta.push_back(position.Eta())
            cluster_phi.push_back(position.Phi())
            cluster_pt.push_back(c.core.energy*position.Unit().Perp())
            cluster_x.push_back(c.core.position.x/10.)
            cluster_y.push_back(c.core.position.y/10.)
            cluster_z.push_back(c.core.position.z/10.)

    elif event.GetBranchStatus("calibCaloClustersBarrelNoise"):
        for c in event.calibCaloClustersBarrelNoise:
            position = r.TVector3(c.core.position.x,c.core.position.y,c.core.position.z)
            cluster_ene.push_back(c.core.energy)
            cluster_eta.push_back(position.Eta())
            cluster_phi.push_back(position.Phi())
            cluster_pt.push_back(c.core.energy*position.Unit().Perp())
            cluster_x.push_back(c.core.position.x/10.)
            cluster_y.push_back(c.core.position.y/10.)
            cluster_z.push_back(c.core.position.z/10.)

    elif event.GetBranchStatus("caloClustersBarrelNoise"):
        for c in event.caloClustersBarrelNoise:
            position = r.TVector3(c.core.position.x,c.core.position.y,c.core.position.z)
            cluster_ene.push_back(c.core.energy)
            cluster_eta.push_back(position.Eta())
            cluster_phi.push_back(position.Phi())
            cluster_pt.push_back(c.core.energy*position.Unit().Perp())
            cluster_x.push_back(c.core.position.x/10.)
            cluster_y.push_back(c.core.position.y/10.)
            cluster_z.push_back(c.core.position.z/10.)

    elif event.GetBranchStatus("caloClusters"):
        for c in event.caloClusters:
            position = r.TVector3(c.core.position.x,c.core.position.y,c.core.position.z)
            cluster_ene.push_back(c.core.energy)
            cluster_eta.push_back(position.Eta())
            cluster_phi.push_back(position.Phi())
            cluster_pt.push_back(c.core.energy*position.Unit().Perp())
            cluster_x.push_back(c.core.position.x/10.)
            cluster_y.push_back(c.core.position.y/10.)
            cluster_z.push_back(c.core.position.z/10.)

    elif event.GetBranchStatus("caloClustersNoise"):
        for c in event.caloClustersNoise:
            position = r.TVector3(c.core.position.x,c.core.position.y,c.core.position.z)
            cluster_ene.push_back(c.core.energy)
            cluster_eta.push_back(position.Eta())
            cluster_phi.push_back(position.Phi())
            cluster_pt.push_back(c.core.energy*position.Unit().Perp())
            cluster_x.push_back(c.core.position.x/10.)
            cluster_y.push_back(c.core.position.y/10.)
            cluster_z.push_back(c.core.position.z/10.)

    else:
        if event.GetBranchStatus("HCalBarrelCellPositions"):
            for c in event.HCalBarrelCellPositions:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                if hcalBarrel_decoder["layer"] == 0:
                    EhadFirst += c.core.energy
 
                E += c.core.energy
                Ehad += c.core.energy
                numHits += 1

                # resegment cells into deltaEta=0.025
                eta = position.Eta()
                phi = position.Phi()
                layer = hcalBarrel_decoder.get(c.core.cellId, "layer")
                
                etaBin = math.floor(eta/0.025 - etaOffset)
                phiBin = math.floor(phi/(256./2*math.pi) - math.pi);
                
                key = (int(etaBin), int(phiBin), int(layer))
                if key not in newRechit_energy:
                    newRechit_energy[key] = 0.
                    newRechit_eta[key] = 0.
                    newRechit_phi[key] = 0.
                    newRechit_pt[key] = 0.
                    newRechit_x[key] = 0.
                    newRechit_y[key] = 0.
                    newRechit_z[key] = 0.
                    newRechit_detid[key] = 0.
                    newRechit_bits[key] = 0.
                
                newRechit_energy[key] += c.core.energy
                newRechit_eta[key] += eta * c.core.energy
                newRechit_phi[key] += phi * c.core.energy
                newRechit_layer[key] = layer
                newRechit_pt[key] += position.Unit().Perp() * c.core.energy
                newRechit_x[key] += c.position.x/10. * c.core.energy
                newRechit_y[key] += c.position.y/10. * c.core.energy
                newRechit_z[key] += c.position.z/10. * c.core.energy
                newRechit_detid[key] = systemID(c.core.cellId)
                newRechit_bits[key] = c.core.bits

            # fill new cells
            for key, value in newRechit_eta.iteritems():
                rec_ene.push_back(newRechit_energy[key])
                rec_eta.push_back(value/newRechit_energy[key])
                rec_phi.push_back(newRechit_phi[key]/newRechit_energy[key])
                rec_pt.push_back(newRechit_pt[key])
                rec_layer.push_back(newRechit_layer[key] + lastECalBarrelLayer + 1)
                rec_x.push_back(newRechit_x[key]/newRechit_energy[key])
                rec_y.push_back(newRechit_y[key]/newRechit_energy[key])
                rec_z.push_back(newRechit_z[key]/newRechit_energy[key])
                rec_detid.push_back(newRechit_detid[key])
                rec_bits.push_back(newRechit_bits[key])
    
        if event.GetBranchStatus("ECalBarrelCellPositions"):
            for c in event.ECalBarrelCellPositions:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                rec_ene.push_back(c.core.energy)
                rec_eta.push_back(position.Eta())
                rec_phi.push_back(position.Phi())
                rec_pt.push_back(c.core.energy*position.Unit().Perp())
                rec_layer.push_back(ecalBarrel_decoder.get(c.core.cellId, "layer"))
                rec_x.push_back(c.position.x/10.)
                rec_y.push_back(c.position.y/10.)
                rec_z.push_back(c.position.z/10.)
                rec_detid.push_back(systemID(c.core.cellId))
                rec_bits.push_back(c.core.bits)
                if ecalBarrel_decoder["layer"] == lastECalBarrelLayer:
                    EemLast += c.core.energy
                E += c.core.energy
                Eem += c.core.energy
                numHits += 1
                    
        if event.GetBranchStatus("HCalExtBarrelCellPositions"):
            for c in event.HCalExtBarrelCellPositions:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                rec_ene.push_back(c.core.energy)
                rec_eta.push_back(position.Eta())
                rec_phi.push_back(position.Phi())
                rec_pt.push_back(c.core.energy*position.Unit().Perp())
                rec_layer.push_back(hcalExtBarrel_decoder.get(c.core.cellId, "layer") + lastECalBarrelLayer + 1)
                rec_x.push_back(c.position.x/10.)
                rec_y.push_back(c.position.y/10.)
                rec_z.push_back(c.position.z/10.)
                rec_detid.push_back(systemID(c.core.cellId))
                rec_bits.push_back(c.core.bits)
                E += c.core.energy
                numHits += 1
            
        if event.GetBranchStatus("ECalEndcapCellPositions"):
            for c in event.ECalEndcapCellPositions:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                rec_ene.push_back(c.core.energy)
                rec_eta.push_back(position.Eta())
                rec_phi.push_back(position.Phi())
                rec_pt.push_back(c.core.energy*position.Unit().Perp())
                rec_layer.push_back(ecalEndcap_decoder.get(c.core.cellId, "layer"))
                rec_x.push_back(c.position.x/10.)
                rec_y.push_back(c.position.y/10.)
                rec_z.push_back(c.position.z/10.)
                rec_detid.push_back(systemID(c.core.cellId))
                rec_bits.push_back(c.core.bits)
                E += c.core.energy
                numHits += 1

        if event.GetBranchStatus("HCalEndcapCellPositions"):
            for c in event.HCalEndcapCellPositions:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                rec_ene.push_back(c.core.energy)
                rec_eta.push_back(position.Eta())
                rec_phi.push_back(position.Phi())
                rec_pt.push_back(c.core.energy*position.Unit().Perp())
                rec_layer.push_back(hcalEndcap_decoder.get(c.core.cellId, "layer") + lastECalEndcapLayer + 1)
                rec_x.push_back(c.position.x/10.)
                rec_y.push_back(c.position.y/10.)
                rec_z.push_back(c.position.z/10.)
                rec_detid.push_back(systemID(c.core.cellId))
                rec_bits.push_back(c.core.bits)
                E += c.core.energy
                numHits += 1
                
        if event.GetBranchStatus("ECalFwdCellPositions"):
            for c in event.ECalFwdCellPositions:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                rec_ene.push_back(c.core.energy)
                rec_eta.push_back(position.Eta())
                rec_phi.push_back(position.Phi())
                rec_pt.push_back(c.core.energy*position.Unit().Perp())
                rec_layer.push_back(ecalFwd_decoder.get(c.core.cellId, "layer"))
                rec_x.push_back(c.position.x/10.)
                rec_y.push_back(c.position.y/10.)
                rec_z.push_back(c.position.z/10.)
                rec_detid.push_back(systemID(c.core.cellId))
                rec_bits.push_back(c.core.bits)
                E += c.core.energy
                numHits += 1

        if event.GetBranchStatus("HCalFwdCellPositions"):
            for c in event.HCalFwdCellPositions:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                rec_ene.push_back(c.core.energy)
                rec_eta.push_back(position.Eta())
                rec_phi.push_back(position.Phi())
                rec_pt.push_back(c.core.energy*position.Unit().Perp())
                rec_layer.push_back(hcalFwd_decoder.get(c.core.cellId, "layer") + lastECalFwdLayer + 1)
                rec_x.push_back(c.position.x/10.)
                rec_y.push_back(c.position.y/10.)
                rec_z.push_back(c.position.z/10.)
                rec_detid.push_back(systemID(c.core.cellId))
                rec_bits.push_back(c.core.bits)
                E += c.core.energy
                numHits += 1

        if event.GetBranchStatus("TrackerPositionedHits"):
            for c in event.TrackerPositionedHits:
                position = r.TVector3(c.position.x,c.position.y,c.position.z)
                rec_ene.push_back(c.core.energy)
                rec_eta.push_back(position.Eta())
                rec_phi.push_back(position.Phi())
                rec_pt.push_back(c.core.energy*position.Unit().Perp())
                sysID = systemID(c.core.cellId)
                if  sysID == 0 :
                    rec_layer.push_back(trackerBarrel_decoder.get(c.core.cellId, "layer"))
                elif sysID == 1 :
                    rec_layer.push_back(trackerBarrel_decoder.get(c.core.cellId, "layer") + lastInnerTrackerBarrelLayer + 1)
                elif sysID == 2 :
                    posneg = trackerEndcap_decoder.get(c.core.cellId, "posneg")
                    if posneg == 0 :
                        rec_layer.push_back(trackerEndcap_decoder.get(c.core.cellId, "disc") + lastOuterTrackerBarrelLayer + 1)
                    else :
                        rec_layer.push_back(trackerEndcap_decoder.get(c.core.cellId, "disc") + lastInnerTrackerPosECapLayer + 1)
                elif sysID == 3:
                    posneg = trackerEndcap_decoder.get(c.core.cellId, "posneg")
                    if posneg == 0 :
                        rec_layer.push_back(trackerEndcap_decoder.get(c.core.cellId, "disc") + lastInnerTrackerNegECapLayer + 1)
                    else :
                        rec_layer.push_back(trackerEndcap_decoder.get(c.core.cellId, "disc") + lastOuterTrackerPosECapLayer + 1)
                else :
                    posneg = trackerEndcap_decoder.get(c.core.cellId, "posneg")
                    if posneg == 0 :
                        rec_layer.push_back(trackerEndcap_decoder.get(c.core.cellId, "disc") + lastOuterTrackerNegECapLayer + 1)
                    else :
                        rec_layer.push_back(trackerEndcap_decoder.get(c.core.cellId, "disc") + lastFwdTrackerPosECapLayer + 1)
                rec_x.push_back(c.position.x/10.)
                rec_y.push_back(c.position.y/10.)
                rec_z.push_back(c.position.z/10.)
                rec_detid.push_back(systemID(c.core.cellId))
                rec_bits.push_back(c.core.bits)
                E += c.core.energy
                numHits += 1

    ev_ebench[0] = benchmarkCorr(Eem,EemLast,Ehad,EhadFirst)
    ev_e[0] = E
    ev_nRechits[0] = numHits
    
    outtree.Fill()

    gen_eta.clear()
    gen_phi.clear()
    gen_pt.clear()
    gen_energy.clear()
    gen_pdgid.clear()
    gen_status.clear()

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


