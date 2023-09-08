#!/usr/bin/python
# This script changes the current config to all other configs

import os, sys
import subprocess
import yaml
import re, copy
import time # can be used in destdir
from satellite_networks_state.main_net_helper import MainNetHelper
from satellite_networks_state.positionneur import Positionneur
from ns3_experiments.step_1_generate_runs2 import main_step1
from ns3_experiments.step_2_run import main_step2
from multiprocessing import Pool

#papier2 directory
basedir=os.getcwd()
assert re.match(basedir+'[^/]*', os.path.abspath(__file__))
configdir=os.path.join(basedir, "config")
#from where to set the config
nomfic_campagne=os.path.join(basedir, "config/campagne.yaml")

def genere_cles(campagne, rend_inutile):
    #ordonner les clefs dans l'ordre le plus efficace pour lancer le moins d'opérations possible
    liste=list(campagne.keys())
    note={cle:0 for cle in liste}
    for cle in campagne.keys():
        for cles_simples in rend_inutile.values():
            if cle in cles_simples:
                note[cle]+=1
    liste.sort(key=lambda x: note[x])
    return liste
    
#base
class Experiences():
    def __init__(self, campagne, actions, rend_inutile, evals):
        self.courante={}
        self.campagne=campagne
        self.rend_inutile=rend_inutile
        self.cles=genere_cles(campagne, rend_inutile)
        self.indices_cles=[0]*len(self.cles)
        self.toutes_actions=set(actions)
        self.actions_non_indispensables=set()
        self.actions=set()
        self.evals=evals
        self.nomfic_courante=os.path.join(basedir, f"config/temp{os.getpid()}.campagne.yaml")#where the script will read the config
        self.dico_cstl={}
    
    def setCleSvgde(self, cle):
        # depreciee
        #set a key to be the last one to change
        self.cles.remove(cle)
        self.cles.append(cle)
        #assert "graine"==self.cles[-1]
        # it should be the seed

    def updateCstlInfo(self):
        cstl_config_fic = os.path.join('config', self.courante['constellation']+'.yaml')
        assert os.path.isfile(cstl_config_fic)
        with open(cstl_config_fic, 'r') as f:
            self.dico_cstl=yaml.load(f, Loader=yaml.Loader)
        remplace(self.dico_cstl, self.courante|var_evals(self.evals))
        tmp_cstl_config_fic = os.path.join('config', f'temp{os.getpid()}.'+self.courante['constellation']+'.yaml')
        with open(tmp_cstl_config_fic, 'w') as f:
            yaml.dump(self.dico_cstl, f)
            
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
        with open(self.nomfic_courante, 'w') as f:
            yaml.dump(self.courante, f)
        if cle==self.cles[-1] and self.indices_cles[-1]==0:
            return True
        # si ce n'est pas le dernier cas, on sait quelle cle a été modifiée, donc optimisation
        for action in self.rend_inutile:
            if cle in self.rend_inutile.get(action, []):
                self.actions_non_indispensables.add(action)
        self.actions=self.toutes_actions-self.actions_non_indispensables
        return False

    def execution(self):
        #generate positions
        if 'positionne' in self.actions:
            os.chdir("satellite_networks_state")
            Positionneur(self.courante['constellation'], self.dico_cstl)
            os.chdir(basedir)

        #create ground nodes
        if 'noeuds' in self.actions:
            os.chdir("satellite_networks_state")
            mh=MainNetHelper(self.courante, os.path.join(configdir, f'temp{os.getpid()}.'+self.courante['constellation']+'.yaml'), "gen_data")
            list_from_to=mh.init_ground_stations()
            os.chdir(basedir)

        ### Create commodities, prepare ns experiment
        if "commodites" in self.actions:
            os.chdir("ns3_experiments")
            main_step1(list_from_to, self.courante, self.dico_cstl)
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
            subprocess.check_call(["python", "perform_full_analysis.py", self.nomfic_courante], stdout=sys.stdout, stderr=sys.stderr)
            os.chdir(basedir)
        
        # NS-3 EXPERIMENTS
        if "simulation" in self.actions:
            os.chdir("ns3_experiments")
            main_step2(self.nomfic_courante)
            os.chdir(basedir)
        
    
    def operation_sauvegarde(self, destdir, sources):
        str_courante=str_recursif(self.courante|var_evals(self.evals))
        str_courante['protocolesNom'] = '_and_'.join(sorted({dic['nom'] for dic in self.courante['protocoles'].values()}))
        nomdestdir=destdir.format(**str_courante)
        sources_a_svgder=[]
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
    
    def operation_mrpropre(self, a_supprimer):
        str_courante=str_recursif(self.courante|var_evals(self.evals))
        str_courante['protocolesNom'] = '_and_'.join(sorted({dic['nom'] for dic in self.courante['protocoles'].values()}))
        globs_a_supprimer=[]
        for dir, regexs in a_supprimer.items():
            dir_str=dir.format(**str_courante)
            if os.path.isdir(dir_str):
                if type(regexs)!=list:
                    regexs=[regexs]
                for regex in regexs:
                    regex_str=regex.format(**str_courante)
                    globs_a_supprimer+=[x.path for x in os.scandir(dir_str) if re.match(regex_str, x.name)]
            else:
                print(f"\n\n \t << {dir_str} >> is not a directory \n\n")
        for glob in globs_a_supprimer:
            if basedir!=os.path.commonpath([basedir, os.path.abspath(glob)]):
                print(f"\n\n \t << {glob} >> should not be accessed. Skip delete \n\n")
            elif os.path.exists(glob):
                subprocess.check_call(["rm", "-r", glob], stdout=sys.stdout, stderr=sys.stderr)
            else:
                print(f"\n\n \t << {glob} >> does not exists. Could not be deleted \n\n")

    

def str_recursif(dico, prefix=''):
    #tranform a dict of dict of dict.. in a 1-level dict
    dic={}
    for cle, val in dico.items():
        if type(val) is not dict:
            dic[prefix+cle]=val
        else:
            dic.update(str_recursif(val, prefix=prefix+cle+'_'))
    return dic

def var_evals(dic_evals):
    return {c: eval(v) for c, v in dic_evals.items()}

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
            while isinstance(val, str) and prefix in val:
                debut=val.find(prefix)
                liste=val[debut:].split(sep)
                rempl_val=dic_from
                for i,u in enumerate(liste[1:]):
                    try:
                        rempl_val=rempl_val[u]
                    except TypeError:
                        val=val.replace(val[debut:], f"{rempl_val}"+sep.join(liste[i+1:]).strip('/'))
                        break
                else:
                    # loop ended correctly  
                    if debut:
                        val=f"{val[:debut]}{rempl_val}"
                    else:
                        val=rempl_val
                dic_to[cle]=val
            if (isinstance(val, dict) or isinstance(val, list)):
                remplace(val, dic_from, prefix=prefix, sep=sep)

def exec_campagne(campagne, nom_campagne, info_experience, info_campagne):
    liste_actions=info_campagne.get('actions', [])
    rend_inutile=info_campagne.get('actions-inutiles-si',{})
    evals=info_campagne.get('evals', {})

    if 'currinfo' in info_experience:
        sys.stdout=open(info_experience['currinfo'], 'w')
        sys.stderr=open('err'+info_experience['currinfo'], 'w')
    campagnedir=info_experience.get('campagnedir', '').rstrip('/') #"sauvegardes/{nom_campagne}"
    expedir=info_experience.get('expedir', '').lstrip('/')
    sources=info_experience.get('sources', {})

    fini = False
    campagne['nom_campagne'] = [nom_campagne]
    campagne['coms-log-actifs']= [info_campagne.get('coms-logs',{})]
    campagne['props-ns3']=[info_campagne.get('props-ns3',{})]

    exp=Experiences(campagne, liste_actions, rend_inutile, evals)
    exp.paramExperience()
    exp.actions=set(liste_actions)
    #update missing information in constellation config file
    exp.updateCstlInfo()
    # save current config
    with open(exp.nomfic_courante, 'w') as f:
        yaml.dump(exp.courante, f)
    destdir=campagnedir+'/'+expedir
    while not fini:
        exp.execution()
        if destdir and sources:
            exp.operation_sauvegarde(destdir, sources)
        fini=exp.experienceSuivante()

    exp.operation_mrpropre(info_campagne.get('mrpropre', {}))
    return os.getpid()

def divise_campagnes(campagne, cles, nbprocs):
    # diviser la campagne en sous-campagnes, en fonction du nombre de processus max.
    # les clés triées permettent de minimiser le nombre d'actions avant la simulation elle-même. 
    # Dans le cas d'expériences courtes et beaucoup de processeurs, pour aller plus vite il vaudrait mieux diviser jusqu'à avoir des campagnes à expérience unique 
    sous_campagnes=[campagne]
    while len(cles) and nbprocs>len(sous_campagnes):
        cle=cles.pop(0)
        n_ss_cpgns=len(sous_campagnes)
        for _ in range(n_ss_cpgns):
            ss_cpgn=sous_campagnes.pop(0)
            val_possibles=ss_cpgn[cle]
            for val in val_possibles:
                nvl_ss_cpgn=copy.deepcopy(ss_cpgn)
                nvl_ss_cpgn[cle]=[val]
                sous_campagnes.append(nvl_ss_cpgn)
    return sous_campagnes

def options_campagne(nom_campagne, info_exp):
    cd=info_exp.get('campagnedir').format(nom_campagne=nom_campagne)
    if not os.path.exists(cd):
        return nom_campagne, cd
    print(nom_campagne , "existe déjà. Continuer (o/N)?")
    z=input()
    if z.lower().startswith('n') or not len(z):
    	exit(0) 
    return nom_campagne, cd
        
def main():
    with open(nomfic_campagne, 'r') as f:
        dico_campagne=yaml.load(f, Loader=yaml.Loader)

    info_exp=dico_campagne.pop('info-experience',{}) 

    info_campagne=dico_campagne.pop('info-campagne',{})
    rend_inutile=info_campagne.get('actions-inutiles-si',{})
    nb_processus=info_campagne.get('processus', 1)

    for nom_campagne, campagne in dico_campagne.items():
        nom_campagne, cd = options_campagne(nom_campagne, info_exp)
        os.makedirs(cd, exist_ok=True)
        cles_variantes=[cle for cle, vals in campagne.items() if len(vals)>1]
        cles_variantes.sort(key= lambda x : sum(x in vals for vals in rend_inutile.values()))#les cles les moins contraignantes en bout de liste

        with open(os.path.join(cd,'variations.txt'), "w") as f:
                f.write(str(cles_variantes))
        subprocess.check_call(["cp", '-t', cd, nomfic_campagne]) #finally save campagne config itself
        

        if info_campagne.get('parallelise', True):
            sous_campagnes=divise_campagnes(campagne, cles_variantes, nb_processus)
            sous_campagnes_infos=[(x, nom_campagne, info_exp, info_campagne) for x in sous_campagnes]
            with Pool(nb_processus) as p:
                print(p.starmap(exec_campagne, sous_campagnes_infos))
        else:
            exec_campagne(campagne, nom_campagne, info_exp, info_campagne)
            

if __name__ == '__main__':
    main()

