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


#si aucune des variables en cle ne change, les actions sont inutiles
rend_indispensable={
    ("graine", "constellation", "duree", "pas", "isls", "deteriorISL", "sol", "nb-UEs-sol", "algo", "maxSatsGw"): ("analyse theorique", "casse liens sat")
}

def genere_cles(campagne):
    #ordonner les clefs dans l'ordre le plus efficace pour lancer le moins d'opérations possible
    liste=list(campagne.keys())
    note={cle:0 for cle in liste}
    for cle in campagne.keys():
        for genantes in rend_indispensable:
            if cle in genantes:
                note[cle]+=1
    liste.sort(key=lambda x: note[x])
    return liste
    
#base
class Experiences():
    def __init__(self, campagne, actions):
        self.courante={}
        self.campagne=campagne
        self.cles=genere_cles(campagne)
        self.indices_cles=[0]*len(self.cles)
        self.toutes_actions=set(actions)
        self.actions_non_indispensables=set()
        self.actions=set()
    
    def setCleSvgde(self, cle):
        # depreciee
        #set a key to be the last one to change
        self.cles.remove(cle)
        self.cles.append(cle)
        #assert "graine"==self.cles[-1]
        # it should be the seed
    
    def setStrDate(self, strdate):
        self.strdate=strdate

    def updateCstlInfo(self):
        cstl_config_fic = os.path.join('config', self.courante['constellation']+'.yaml')
        assert os.path.isfile(cstl_config_fic)
        with open(cstl_config_fic, 'r') as f:
            dico_cstl=yaml.load(f, Loader=yaml.Loader)
        remplace(dico_cstl, self.courante)
        tmp_cstl_config_fic = os.path.join('config', 'temp.'+self.courante['constellation']+'.yaml')
        with open(tmp_cstl_config_fic, 'w') as f:
            yaml.dump(dico_cstl, f)
            
    def paramExperience(self):
        for i,cle in enumerate(self.cles):
            self.courante[cle]=self.campagne[cle][self.indices_cles[i]]

    def experienceSuivante(self):
        #met à jour les paramètres pour l'expérience suivante
        # L'experience 0,0,0,0...0 est effectuée en dernière. C'est celle là qui indique la fin des expériences 
        self.actions_non_indispensables=set()
        for i, cle in enumerate(self.cles):
            self.indices_cles[i] = (self.indices_cles[i]+1)%len(self.campagne[cle])
            self.courante[cle] = self.campagne[cle][self.indices_cles[i]]
            if self.indices_cles[i] > 0:
                break
        #update missing information in constellation config file
        self.updateCstlInfo()
        # save current config
        with open(nomfic_courante, 'w') as f:
            yaml.dump(self.courante, f)
        if cle==self.cles[-1] and self.indices_cles[-1]==0:
            return True
        # si ce n'est pas le dernier cas, on sait quelle cle a été modifiée, donc optimisation
        for cle_activantes in rend_indispensable:
            if not cle in cle_activantes:
                self.actions_non_indispensables.update(rend_indispensable[cle_activantes])
        self.actions=self.toutes_actions-self.actions_non_indispensables
        return False

    def execution(self):
        
        #create ground nodes
        if 'noeuds' in self.actions:
            os.chdir("satellite_networks_state")
            mh=MainNetHelper(self.courante, os.path.join(configdir, 'temp.'+self.courante['constellation']+'.yaml'), "gen_data")
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

        if "casse liens sat" in self.actions:
            os.chdir("satellite_networks_state")
            mh.detraqueISL()
            os.chdir(basedir)
        
        ### SATGENPY ANALYSIS
        # analysis  of path and rtt based on networkx.
        # edit variables 'satgenpy_generated_constellation', 'duration_s' 
        # and 'list_update_interval_ms' in perform_full_analysis according to `liste_arguments`
        if "analyse theorique" in self.actions:
            os.chdir("satgenpy_analysis")
            subprocess.check_call(["python", "perform_full_analysis.py", nomfic_courante], stdout=sys.stdout, stderr=sys.stderr)
            os.chdir(basedir)
        
        # NS-3 EXPERIMENTS
        if "simulation" in self.actions:
            os.chdir("ns3_experiments")
            subprocess.check_call(["python", "step_2_run.py", "0", nomfic_courante], stdout=sys.stdout, stderr=sys.stderr)
            os.chdir(basedir)
        
    
    def operation_sauvegarde(self, destdir, sources):
        nomdestdir=destdir.format(strdate=time.strftime(self.strdate), **self.courante)
        sources_a_svgder=[]
        str_courante=str_recursif(self.courante)
        str_courante['protocolesNom'] = '_and_'.join(sorted({dic['nom'] for dic in self.courante['protocoles'].values()}))
        for dir, regexs in sources.items():
            dir_str=dir.format(**str_courante)
            if os.path.isdir(dir_str):
                if type(regexs)!=list:
                    regexs=[regexs]
                for regex in regexs:
                    regex_str=regex.format(**str_courante)
                    sources_a_svgder+=[os.path.join(dir_str,x) for x in os.listdir(dir_str) if re.match(regex_str, x) ]
            else:
                print(f"\n\n \t << {dir_str} >> is not a directory \n\n")
        subprocess.check_call(["mkdir", "-p", nomdestdir])
        for src in sources_a_svgder:
            if os.path.exists(src):
                subprocess.check_call(["cp", "-R", '-t', nomdestdir, src], stdout=sys.stdout, stderr=sys.stderr)
            else:
                print(f"\n\n \t << {src} >> does not exists. Could not be saved \n\n")


def str_recursif(dico, prefix=''):
    #tranform a dict of dict of dict.. in a 1-level dict
    dic={}
    for cle, val in dico.items():
        if type(val) is not dict:
            dic[prefix+cle]=val
        else:
            dic.update(str_recursif(val, prefix=prefix+cle+'_'))
    return dic

def remplace(dic_to, dic_from, prefix='$config/', sep='/'):
        """replace "prefix..." values of dic_to with related fields from dic_from"""
        if isinstance(dic_to, dict):
            #maj clefs
            for cle in list(dic_to.keys()):
                if isinstance(cle, str) and prefix in cle:
                    debut=cle.find(prefix)
                    liste=cle[debut:].split(sep)
                    maj_dic=dic_from
                    for i,u in enumerate(liste[1:]):
                        maj_dic=maj_dic[u]
                    else:
                        # loop ended correctly  
                        dic_to.update(maj_dic)
                        del dic_to[cle]
            enumerateur=dic_to.items()
        elif isinstance(dic_to, list):
            enumerateur=enumerate(dic_to)
        #maj valeurs
        for cle, val in enumerateur:
            if isinstance(val, str) and prefix in val:
                debut=val.find(prefix)
                liste=val[debut:].split(sep)
                rempl_val=dic_from
                for i,u in enumerate(liste[1:]):
                    try:
                        rempl_val=rempl_val[u]
                    except TypeError:
                        dic_to[cle]=val.replace(val[debut:], f"{rempl_val}"+sep.join(liste[i+1:]).strip('/'))
                        break
                else:
                    # loop ended correctly  
                    dic_to[cle]=rempl_val
            elif isinstance(val, dict) or isinstance(val, list):
                remplace(val, dic_from, prefix=prefix, sep=sep)

        
def main():
    with open(nomfic_campagne, 'r') as f:
        dico_campagne=yaml.load(f, Loader=yaml.Loader)

    dic=dico_campagne.pop('info-sauvegarde',{})  
    if 'currinfo' in dic:
        sys.stdout=open(dic['currinfo'], 'w')
        sys.stderr=open('err'+dic['currinfo'], 'w')
    strdate=dic.get('strdate', "%Y-%m-%d-%H%M")
    campagnedir=dic.get('campagnedir', '').rstrip('/') #"sauvegardes/{nom_campagne}"
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
        estPremiere=True
        while not fini:
            if estPremiere:
                exp.actions=set(liste_actions)
                #update missing information in constellation config file
                exp.updateCstlInfo()
                # save current config
                with open(nomfic_courante, 'w') as f:
                    yaml.dump(exp.courante, f)
                estPremiere=False
            exp.execution()
            if (destdir:=campagnedir+'/'+expedir) and sources:
                exp.operation_sauvegarde(destdir, sources)
            fini=exp.experienceSuivante()
        cd=campagnedir.format(nom_campagne=nom_campagne)
        with open(os.path.join(cd,'variations.txt'), "w") as f:
            f.write(str(cles_variantes))
        subprocess.check_call(["cp", '-t', cd, nomfic_campagne]) #finally save campagne config itself
    for glob in os.listdir(configdir):#clean temp files in config
        x=os.path.join(configdir, glob)
        if os.path.isfile(x) and glob.startswith('temp.'):
            subprocess.check_call(["rm",x])
            

if __name__ == '__main__':
    main()

