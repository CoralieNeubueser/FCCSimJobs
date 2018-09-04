import glob, os, sys
import yaml
import utils as ut
eostest='/eos/experiment/fcc/hh/tests/testfile.lhe.gz'
eostest_size=1312594

class checker_eos():

#__________________________________________________________
    def __init__(self, indirafs, indireos, process):
        self.process = process
        self.indirafs  = indirafs
        self.indireos  = indireos


#__________________________________________________________
    def touch(self, path):
        with open(path, 'a'):
            os.utime(path, None)

#__________________________________________________________
    def check(self):

        ldir=[x[0] for x in os.walk(self.indireos)]
        
        if not ut.testeos(eostest,eostest_size):
            print 'eos seems to have problems, should check, will exit'
            sys.exit(3)
        dic={}
        for l in ldir:
            proc=l.replace(self.indireos,'')
            #print proc,'    ',self.process
            if self.process!='' and self.process!=proc: 
                continue

            psplit=l.split('/')
            isana=False
            for a in psplit:
                if a=="ana":isana=True
            if isana:
                print 'is anana'
                print l
                continue

            #continue if process has been checked
            if l=='BADPYTHIA' or l=='lhe' or l=="__restored_files__" or l=="backup": continue
            print '--------------------- eos process ',l
            nfileseos=0
            if os.path.isdir('%s/%s'%(self.indireos,proc)):
                listeos = [x for x in os.listdir('%s/%s'%(self.indireos,proc)) if 'output' in x]
                nfileseos=len(listeos)
                
            if nfileseos==0: continue
            nfilesmerged=0
            mergefile=self.indirafs+'/'+proc+'/merge.yaml'
            print 'mergefile  ',mergefile
            if not ut.file_exist(mergefile): 
                if not ut.dir_exist('%s/%s'%(self.indirafs,proc)):
                    os.system('mkdir -p %s/%s'%(self.indirafs,proc))
                self.touch('%s/%s/check'%(self.indirafs,proc))
                continue

            if not os.path.isdir(self.indirafs):
                os.system('mkdir %s'%self.indirafs)

            tmpf=None
            with open(mergefile, 'r') as stream:
                try:
                    tmpf = yaml.load(stream)
                except yaml.YAMLError as exc:
                    print(exc)

            bad_tot=tmpf['merge']['nbad']
            files_tot=tmpf['merge']['ndone']

            ntot_files=bad_tot+files_tot
            print "tot files  ",ntot_files,"  files eos  ",nfileseos
            dic[proc]={'neos':nfileseos,'nmerged':ntot_files}
            print '%s/%s/check'%(self.indirafs,proc)
            if ntot_files<nfileseos:
                self.touch('%s/%s/check'%(self.indirafs,proc))
            elif  ntot_files>nfileseos:
                print ' ntot_files>nfileseos ', ntot_files,nfileseos,proc
                os.system('rm %s/%s/output*.yaml'%(self.indirafs,proc))
                os.system('rm %s/%s/merge.yaml'%(self.indirafs,proc))
            else:
                if ut.file_exist('%s/%s/check'%(self.indirafs,proc)):
                    os.system('rm %s/%s/check'%(self.indirafs,proc))
   
        outfile=self.indirafs+'/files.yaml'
        with open(outfile, 'w') as outyaml:
            yaml.dump(dic, outyaml, default_flow_style=False) 
            
        
