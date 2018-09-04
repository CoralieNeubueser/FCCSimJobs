#python jobchecker.py LHE or FCC
import utils as ut
import os, sys

class remove():

#__________________________________________________________
    def __init__(self, process, eosdir, yamldir, version):
        self.process = process
        self.eosdir = eosdir
        self.yamldir = yamldir

        if process.split('/')[0]!=version:
            print 'version mismatch process/version in agrs %s/%s exit' %(process.split('/')[0],version)
            sys.exit(3)

        if not ut.dir_exist(eosdir+'/'+process):
            print 'process eos does not exist, exit ',eosdir+'/'+process
            sys.exit(3)

        if not ut.dir_exist(yamldir+'/'+process):
            print 'process yaml does not exist, exit ',yamldir+'/'+process
            sys.exit(3)


#__________________________________________________________
    def remove(self):
        
        
        print 'remove process in eos'
        cmd="rm %s/%s/output*"%(self.eosdir, self.process)
        print cmd
        #os.system(cmd)
        print 'remove process in yaml'
        cmd="rm %s/%s/output*"%(self.yamldir, self.process)
        print cmd
        #os.system(cmd)
        print 'remove merged yaml'
        cmd="rm %s/%s/merge.yaml"%(self.yamldir, self.process)
        print cmd
        #os.system(cmd)
