import yaml
import subprocess
import numpy as np
import sys, os


CONF_DIR = '../papier2/config/campagne.yaml'
EXPE_LOG_UTIL_DIR = ""

SAVE_FILE=""

#PARAMS=["debit-if-gsl&ue", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-isl", "nb-UEs-sol"]

def remplace_un_param(dic, nom_param, nvelle_valeur):
    decoupe=nom_param.split('&')
    ledic=dic
    prems=decoupe.pop(0)
    if not len(decoupe):
        ledic[prems] = [nvelle_valeur]
        return
    for subdic in ledic[prems]:
        for elt in decoupe[:-1]:
            subdic=subdic[elt]
        subdic[decoupe[-1]]=nvelle_valeur

def change_params(dico_nvx_params, confdir=CONF_DIR):
    with open("campagne_template.yaml", 'r')as f:
        dico_template=yaml.load(f, Loader=yaml.Loader)
    a_conserver=dico_template.pop("a-conserver-dans-campagne")
    for nomparam, nvelleval in dico_nvx_params.items():
        remplace_un_param(dico_template["paramTester"], nomparam, nvelleval)
    
    if not os.path.isfile(confdir+".svgde"):
        subprocess.check_call(["cp", confdir, confdir+'.svgde'])
    with open(confdir, 'r') as f:
        dico_config=yaml.load(f, Loader=yaml.Loader)
    for elt in list(dico_config.keys()):
        if elt not in a_conserver:
            del dico_config[elt]
    dico_config.update(dico_template)
    with open(confdir, 'w') as f:
        yaml.dump(dico_config, f)
    
def remise_ancien_fic(confdir=CONF_DIR):
    if os.path.isfile(confdir+".svgde"):
        subprocess.check_call(["mv", confdir+'.svgde', confdir])



def execution(dico_nvx_params):
    
    change_params(dico_nvx_params)
    #exécuter simu
    cwd = os.getcwd()
    os.chdir("../papier2")
    subprocess.check_call(["python", "paper3.py"])
    os.chdir(cwd)
    remise_ancien_fic()

    

if __name__ == '__main__':
    PARAMS=["debit-if-gsl&ue", "debit-if-gsl&gateway", "debit-if-gsl&satellite", "debit-if-isl", "nb-UEs-sol"]
    import random
    execution({x: random.randint(2, 10) for x in PARAMS})