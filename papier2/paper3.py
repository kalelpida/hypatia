#!/usr/bin/python
# This script changes the current config to all other configs

import os, sys
import subprocess
import yaml
import re
import time # can be used in destdir
from satellite_networks_state.main_net_helper import MainNetHelper
from ns3_experiments.step_1_generate_runs2 import main_step1

#papier2 directory
basedir=os.getcwd()
assert re.match(basedir+'[^/]*', os.path.abspath(__file__))
configdir=os.path.join(basedir, "config")
#from where to set the config
nomfic_campagne=os.path.join(basedir, "config/campagne.yaml")
#where the script will read the config
nomfic_courante=os.path.join(basedir, "config/courante.yaml")


#base
class Experiences():
    def __init__(self, campagne, actions):
        self.courante={'graine': 2, 'constellation': 'tas_700', 'duree': 8, 'pas': 2000, 'isls': 'isls_plus_grid', 'sol': 'ground_stations_top_100', 'algo': 'algorithm_free_one_only_over_isls', 'threads': 4, 'debit_isl': 10}
        self.campagne=campagne
        self.cles=list(campagne.keys())
        self.indices_cles=[0]*len(self.cles)
        self.actions=actions
    
    def setCleSvgde(self, cle):
        # depreciee
        #set a key to be the last one to change
        self.cles.remove(cle)
        self.cles.append(cle)
        #assert "graine"==self.cles[-1]
        # it should be the seed
    
    def setStrDate(self, strdate):
        self.strdate=strdate

    def paramExperience(self):
        for i,cle in enumerate(self.cles):
            self.courante[cle]=self.campagne[cle][self.indices_cles[i]]

    def experienceSuivante(self):
        #met à jour les paramètres pour l'expérience suivante
        # L'experience 0,0,0,0...0 est effectuée en dernière. C'est celle là qui indique la fin des expériences 
        for i, cle in enumerate(self.cles):
            self.indices_cles[i] = (self.indices_cles[i]+1)%len(self.campagne[cle])
            self.courante[cle] = self.campagne[cle][self.indices_cles[i]]
            if self.indices_cles[i] > 0:
                break
        # save current config
        with open(nomfic_courante, 'w') as f:
            yaml.dump(self.courante, f)
        #save debitISL in a simple place for graph generation. Used by mcnf. #ToDo
        with open("satellite_networks_state/debitISL.temp", "w") as f:
            f.write(str(self.courante['debit_isl']))
        if cle==self.cles[-1] and self.indices_cles[-1]==0:
            return True
        return False

    def execution(self):
        
        #create ground nodes
        if 'noeuds' in self.actions:
            os.chdir("satellite_networks_state")
            mh=MainNetHelper(self.courante, os.path.join(configdir, self.courante['constellation']+'.yaml'), "gen_data")
            list_from_to=mh.init_ground_stations()
            os.chdir(basedir)

        ### Create commodities, prepare ns experiment
        if "commodites" in self.actions:
            os.chdir("ns3_experiments")
            main_step1(list_from_to)
            os.chdir(basedir)

        #create routing table
        if "routes" in self.actions:
            os.chdir("satellite_networks_state")
            mh.calculate()
            os.chdir(basedir)

        ### SATGENPY ANALYSIS
        # analysis  of path and rtt based on networkx.
        # edit variables 'satgenpy_generated_constellation', 'duration_s' 
        # and 'list_update_interval_ms' in perform_full_analysis according to `liste_arguments`
        if "analyse theorique" in self.actions:
            os.chdir("satgenpy_analysis")
            subprocess.check_call(["python", "perform_full_analysis.py", nomfic_courante])
            os.chdir(basedir)
        
        if "casse liens sat" in self.actions:
            os.chdir("satgenpy_analysis")
            from satgenpy_analysis.deteriorIsl import casseISLs
            casseISLs(self.courante)
            os.chdir(basedir)

        # NS-3 EXPERIMENTS
        if "simulation" in self.actions:
            os.chdir("ns3_experiments")
            subprocess.check_call(["python", "step_2_run.py", "0", nomfic_courante])
            os.chdir(basedir)

    
    def operation_sauvegarde(self, destdir, sources):
        nomdestdir=destdir.format(strdate=time.strftime(self.strdate), **self.courante)
        sources_a_svgder=[]
        for dir, regex in sources.items():
            dir_str=dir.format(**self.courante)
            regex_str=regex.format(**self.courante)
            sources_a_svgder+=[os.path.join(dir_str,x) for x in os.listdir(dir_str) if re.match(regex_str, x)]
        subprocess.check_call(["mkdir", "-p", nomdestdir])
        for src in sources_a_svgder:
            subprocess.check_call(["cp", "-R", '-t', nomdestdir, src])



def main():
    with open(nomfic_campagne, 'r') as f:
        dico_campagne=yaml.load(f, Loader=yaml.Loader)

    dic=dico_campagne.pop('info-sauvegarde',{})  
    if 'currinfo' in dic:
        sys.stdout=open(dic['currinfo'], 'w')
    strdate=dic.get('strdate', "%Y-%m-%d-%H%M")
    campagnedir=dic.get('campagnedir', '').rstrip('/') #"sauvegardes/svgde_{strdate}"
    expedir=dic.get('expedir', '').lstrip('/')
    sources=dic.get('sources', [])

    liste_actions=dico_campagne.pop('actions', [])

    for nom_campagne, campagne in dico_campagne.items():
        print("nom: ", nom_campagne)
        cles_variantes=[cle for cle, vals in campagne.items() if len(vals)>1]
        fini = False
        campagne['nom_campagne'] = [nom_campagne]
        exp=Experiences(campagne, liste_actions)
        exp.paramExperience()
        exp.setStrDate(strdate)

        while not fini:
            fini=exp.experienceSuivante()
            exp.execution()
            if (destdir:=campagnedir+'/'+expedir) and sources:
                exp.operation_sauvegarde(destdir, sources)
        if os.path.isdir(cd:=campagnedir.format(nom_campagne=nom_campagne)):
            with open(os.path.join(cd,'variations.txt'), "w") as f:
                f.write(str(cles_variantes))
            
            

if __name__ == '__main__':
    main()

