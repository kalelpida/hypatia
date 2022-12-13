#generate X users spread uniformly on Earth
import numpy as np
import os


def create_users(Nb):
    fic_prenoms=os.path.join(os.path.dirname(os.path.abspath(__file__)),"prenoms.txt")
    with open(fic_prenoms, 'r') as f:
        prenoms=f.readlines()
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
    liste_prenoms=[]
    for prenom in prenoms_sel:
        u = np.random()
        v = np.random()
        theta = 2 * np.pi * u
        phi = np.arccos(2*v-1)
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_prenoms.append({
            "name": prenom,
            "latitude_degrees_str": str(theta*180/np.pi),
            "longitude_degrees_str": str(phi*180/np.pi),
            "elevation_m_float": altitude_above_msl,
        })
        
    return liste_prenoms


