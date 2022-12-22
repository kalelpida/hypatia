#generate X users spread uniformly on Earth
import numpy as np
import os
import yaml
from constants import *

TYPE_OBJET='ue'

this_file_path=os.path.dirname(os.path.abspath(__file__))

def create_users_randomGlobe(Nb):
    np.random.seed(32)

    fic_prenoms=os.path.join(this_file_path,"prenoms.txt")
    with open(fic_prenoms, 'r') as f:
        prenoms=f.readlines()[1:]
    if Nb>len(prenoms):
        raise Exception("Pas assez de prenoms, compléter le fichier")
    prenoms_sel=np.random.choice(prenoms, Nb, replace=False)

    #get the parameters of the constellation, forbid out of range 
    """
    with open("../../config/courante.yaml", "r") as f:
        conf=yaml.load(f, Loader=yaml.Loader)
        constellation=conf.get('constellation')
    with open("../../config/"+constellation+".yaml", 'r') as f:
        cstlconfig=yaml.load(f, Loader=yaml.Loader)
    """
    #TODO critère réjection End User
    liste_ues=[]
    for prenom in prenoms_sel:
        u = np.random.random()
        v = np.random.random()
        theta = 2 * np.pi * u
        phi = np.arcsin(2*v-1)
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_ues.append({
            "nom": prenom.strip(),
            "lon": str(theta*180/np.pi), #degrees
            "lat": str(phi*180/np.pi), #degrees
            "elev": str(altitude_above_msl), #altitude, meters
        })

    with open(os.path.join(this_file_path,"UEs_randomGlobe.txt"), 'w') as f:
        for i,ue in enumerate(liste_ues):
            f.write(",".join([str(i), ue["nom"], ue["lat"], ue["lon"], ue["elev"]])+'\n')
            

def create_users_randomGlobe(Nb, constellation='tas_700'):
    np.random.seed(32)

    fic_prenoms=os.path.join(this_file_path,"prenoms.txt")
    with open(fic_prenoms, 'r') as f:
        prenoms=f.readlines()[1:]
    if Nb>len(prenoms):
        raise Exception("Pas assez de prenoms, compléter le fichier")
    prenoms_sel=np.random.choice(prenoms, Nb, replace=False)

    #get the parameters of the constellation, set out of range criteria
    # Les utilisateurs possible sont tous ceux qui seront à portée de satellite au moins pour un instant  
    with open("../../config/"+constellation+".yaml", 'r') as f:
        cstlconfig=yaml.load(f, Loader=yaml.Loader)
    heightsat=cstlconfig['ALTITUDE_M']
    latsat=np.deg2rad(cstlconfig['INCLINATION_DEGREE'])
    elev_ue=np.deg2rad(cstlconfig[TYPE_OBJET]['minElevation'])
    latMaxUE = np.arccos(EARTH_RADIUS*np.cos(elev_ue)/(EARTH_RADIUS+heightsat))-elev_ue+latsat
    assert 0<=latMaxUE<=90
    
    liste_ues=[]
    for prenom in prenoms_sel:
        u = np.random.random()
        v = np.random.uniform(-np.sin(latMaxUE), np.sin(latMaxUE))
        theta = 2 * np.pi * u
        phi = np.arcsin(v)
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_ues.append({
            "nom": prenom.strip(),
            "lon": str(theta*180/np.pi), #degrees
            "lat": str(phi*180/np.pi), #degrees
            "elev": str(altitude_above_msl), #altitude, meters
        })

    with open(os.path.join(this_file_path,f"UEs_randomGlobe_{constellation.replace('_', '')}.txt"), 'w') as f:
        for i,ue in enumerate(liste_ues):
            f.write(",".join([str(i), ue["nom"], ue["lat"], ue["lon"], ue["elev"]])+'\n')
            

        
    

if __name__ =='__main__':
    #create_users_randomGlobe(100)
    create_users_randomGlobe(250)
