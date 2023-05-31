#generate X users spread uniformly on Earth
import numpy as np
import matplotlib.pyplot as plt
import os, sys, csv
import yaml
from constants import *
import scipy

TYPE_OBJET='ue'
PROTECTION_DEG=7 # marge pour les zones non couvertes

this_file_path=os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(this_file_path,"../../../satgenpy"))
import satgen
            

def create_users_randomGlobe(Nb, constellation='kuiper_630'):
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
    plt.subplot(projection='3d')
    for prenom in prenoms_sel:
        u = np.random.random()
        v = np.random.uniform(-np.sin(latMaxUE), np.sin(latMaxUE))
        theta = 2 * np.pi * u
        phi = np.arcsin(v)
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        plt.plot(*xyz(phi, theta), '.')
        liste_ues.append({
            "nom": prenom.strip(),
            "lon": str(theta*180/np.pi), #degrees
            "lat": str(phi*180/np.pi), #degrees
            "elev": str(altitude_above_msl), #altitude, meters
        })
    plt.show()
    with open(os.path.join(this_file_path,f"os_randomGlobe_{constellation.replace('_', '')}.txt"), 'w') as f:
        for i,ue in enumerate(liste_ues):
            f.write(",".join([str(i), ue["nom"], ue["lat"], ue["lon"], ue["elev"]])+'\n')
            

def create_users_villesGlobe(Nb, constellation='kuiper_630', ficVille='os_cities_by_estimated_2025_pop_300k_UN.csv'):
    np.random.seed(32)

    fic_prenoms=os.path.join(this_file_path,"prenoms.txt")
    with open(fic_prenoms, 'r') as f:
        prenoms=f.readlines()[1:]
    if Nb>len(prenoms):
        raise Exception("Pas assez de prenoms, compléter le fichier")
    prenoms_sel=np.random.choice(prenoms, Nb, replace=False)

    #get the parameters of the constellation, set out of range criteria
    # Les utilisateurs sont tous ceux qui seront potentiellement à portée d'un satellite au moins pour un instant 
    # dans main_net_helper, cette valeur est majorée par le K_FACTOR 
    with open("../../config/"+constellation+".yaml", 'r') as f:
        cstlconfig=yaml.load(f, Loader=yaml.Loader)
    heightsat=cstlconfig['ALTITUDE_M']
    latsat=np.deg2rad(cstlconfig['INCLINATION_DEGREE'])
    elev_ue=np.deg2rad(cstlconfig[TYPE_OBJET]['minElevation']+PROTECTION_DEG) # avoid users out of bounds
    latMaxUE_rad = np.arccos(EARTH_RADIUS*np.cos(elev_ue)/(EARTH_RADIUS+heightsat))-elev_ue+latsat
    assert 0<=latMaxUE_rad<=np.pi/2
    
    #generate users close to cities
    Nb_proches_villes=int(Nb*0.9)
    #get the cities
    villes=satgen.read_ground_stations_basic(ficVille)
    #"gid",  "name", "latitude_degrees", "longitude_degrees", "elevation_m","population_k": int
    villes_pos=[np.radians([float(ville["latitude_degrees"]), float(ville["longitude_degrees"])]) for ville in villes]
    villes_probas=np.array([ville['population_k'] for ville in villes])
    villes_choisies = np.random.choice(list(range(len(villes))), size=Nb_proches_villes, p=villes_probas/sum(villes_probas))
    liste_ues=[]
    ectype= np.radians(3) # ~ ecart-type de la distribution
    kappa=1/2/(ectype**2)
    plt.subplot(projection='3d')
    for prenom, idville in zip(prenoms_sel[:Nb_proches_villes], villes_choisies):
        latrad=np.pi
        iters=0
        while latrad> latMaxUE_rad:
            latlonrad=kent_randomgen(*villes_pos[idville], kappa=kappa, latmax=latMaxUE_rad)
            latrad=latlonrad[0]
            lat, lon = np.degrees(latlonrad)
            iters+=1
            if iters> 10:
                raise Exception("trop de points aux pôles")
        
        plt.plot(*xyz(*latlonrad), '.')
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_ues.append({
            "nom": prenom.strip(),
            "lon": str(lon), #degrees
            "lat": str(lat), #degrees
            "elev": str(altitude_above_msl), #altitude, meters
        })

    #generate other random users
    koeff=Nb/(Nb-Nb_proches_villes)
    for i, prenom in enumerate(prenoms_sel[Nb_proches_villes:]):
        theta = np.random.uniform(0, 2*np.pi)
        phi =  np.arcsin(np.random.uniform(-np.sin(latMaxUE_rad), np.sin(latMaxUE_rad)))

        plt.plot(*xyz(phi, theta), '.')
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_ues.insert(int(i*koeff), {
            "nom": prenom.strip(),
            "lon": str(np.degrees(theta)), #degrees
            "lat": str(np.degrees(phi)), #degrees
            "elev": str(altitude_above_msl), #altitude, meters
        })
    plt.show()
    #raise Exception("data not written, comment out this exception to generate users")
    with open(os.path.join(this_file_path,f"os_villesGlobe_{constellation.replace('_', '')}.txt"), 'w') as f:
        for i,ue in enumerate(liste_ues):
            f.write(",".join([str(i), ue["nom"], ue["lat"], ue["lon"], ue["elev"]])+'\n')


def create_users_villeschoisies(Nb, constellation='kuiper_630', ficVille='os_Lille.csv'):
    np.random.seed(32)

    fic_prenoms=os.path.join(this_file_path,"prenoms.txt")
    with open(fic_prenoms, 'r') as f:
        prenoms=f.readlines()[1:]
    if Nb>len(prenoms):
        raise Exception("Pas assez de prenoms, compléter le fichier")
    prenoms_sel=np.random.choice(prenoms, Nb, replace=False)

    #get the parameters of the constellation, set out of range criteria
    # Les utilisateurs sont tous ceux qui seront potentiellement à portée d'un satellite au moins pour un instant 
    # dans main_net_helper, cette valeur est majorée par le K_FACTOR 
    with open("../../config/"+constellation+".yaml", 'r') as f:
        cstlconfig=yaml.load(f, Loader=yaml.Loader)
    heightsat=cstlconfig['ALTITUDE_M']
    latsat=np.deg2rad(cstlconfig['INCLINATION_DEGREE'])
    elev_ue=np.deg2rad(cstlconfig[TYPE_OBJET]['minElevation']+PROTECTION_DEG) # avoid users out of bounds
    latMaxUE_rad = np.arccos(EARTH_RADIUS*np.cos(elev_ue)/(EARTH_RADIUS+heightsat))-elev_ue+latsat
    assert 0<=latMaxUE_rad<=np.pi/2
    
    #generate users close to cities
    Nb_proches_villes=int(Nb*0.8)
    #get the cities
    villes=satgen.read_ground_stations_basic(ficVille)
    #"gid",  "name", "latitude_degrees", "longitude_degrees", "elevation_m","population_k": int
    villes_pos=[np.radians([float(ville["latitude_degrees"]), float(ville["longitude_degrees"])]) for ville in villes]
    villes_probas=np.array([ville['population_k'] for ville in villes])
    villes_choisies = np.random.choice(list(range(len(villes))), size=Nb_proches_villes, p=villes_probas/sum(villes_probas))
    liste_ues=[]
    ectype= np.radians(10) # ~ ecart-type de la distribution
    kappa=1/2/(ectype**2)
    plt.subplot(projection='3d')
    for prenom, idville in zip(prenoms_sel[:Nb_proches_villes], villes_choisies):
        latrad=np.pi
        iters=0
        while latrad> latMaxUE_rad:
            latlonrad=kent_randomgen(*villes_pos[idville], kappa=kappa, latmax=latMaxUE_rad)
            latrad=latlonrad[0]
            lat, lon = np.degrees(latlonrad)
            iters+=1
            if iters> 10:
                raise Exception("trop de points aux pôles")
        
        plt.plot(*xyz(*latlonrad), '.')
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_ues.append({
            "nom": prenom.strip(),
            "lon": str(lon), #degrees
            "lat": str(lat), #degrees
            "elev": str(altitude_above_msl), #altitude, meters
        })


    #generate other random users
    koeff=Nb/(Nb-Nb_proches_villes)
    for i, prenom in enumerate(prenoms_sel[Nb_proches_villes:]):
        theta = np.random.uniform(0, 2*np.pi)
        phi =  np.arcsin(np.random.uniform(-np.sin(latMaxUE_rad), np.sin(latMaxUE_rad)))

        plt.plot(*xyz(phi, theta), '.')
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_ues.insert(int(i*koeff), {
            "nom": prenom.strip(),
            "lon": str(np.degrees(theta)), #degrees
            "lat": str(np.degrees(phi)), #degrees
            "elev": str(altitude_above_msl), #altitude, meters
        })
    plt.show()
    #raise Exception("data not written, comment out this exception to generate users")
    with open(os.path.join(this_file_path,f"os_{len(villes)}villes_{constellation.replace('_', '')}.txt"), 'w') as f:
        for i,ue in enumerate(liste_ues):
            f.write(",".join([str(i), ue["nom"], ue["lat"], ue["lon"], ue["elev"]])+'\n')


def kent_pdf(prodscal, kappa):
    return np.exp(kappa*prodscal)*kappa/4/np.pi/np.sinh(kappa)

def kent_randomgen(lat, lon, kappa, latmax):
    """
    lon, lat, latmax in rads
    Generate random vector from Kent distribution (FB5), based on the vonMisesFisher. 
    Did not find any better solution
    """
    lat_accept=False
    maxpdf=(np.exp(kappa)*kappa/4/np.pi/np.sinh(kappa))
    slatmax=np.sin(latmax)
    sl, sL, cl, cL = np.sin(lon), np.sin(lat), np.cos(lon), np.cos(lat)
    vec_central=np.array([cl*cL, sl*cL, sL])
    while not lat_accept:
        latobj, lonobj=np.arcsin(np.random.uniform(-slatmax, slatmax)), np.random.uniform(-np.pi, np.pi)#random from 3D sphere
        slobj, sLobj, clobj, cLobj = np.sin(lonobj), np.sin(latobj), np.cos(lonobj), np.cos(latobj)
        prodscal=np.dot(vec_central, np.array([clobj*cLobj, slobj*cLobj, sLobj]))
        u=np.random.random()*maxpdf
        lat_accept = u<kent_pdf(prodscal, kappa)
    assert -np.pi/2<latobj<np.pi/2
    return [latobj, lonobj]

def zone_randomgen(lat, lon, dmax_km, dmin_km=50):
    """
    lon, lat in rads
    dmax, dmin in km
    """
    assert dmax_km>dmin_km>0
    sl, sL, cl, cL = np.sin(lon), np.sin(lat), np.cos(lon), np.cos(lat)
    vec_central=np.array([cl*cL, sl*cL, sL])
    vec_normal=np.array([-cl*sL, -sl*sL, cL]) #vecteur normal au précédent
    vec_orth=np.array([-sl, cl, 0]) # vecteur normal aux deux précédents
    #choix de la direction d'écartement depuis le vecteur d'origine
    theta= np.random.uniform(-np.pi, np.pi)
    vec_tournant = np.cos(theta)*vec_normal+np.sin(theta)*vec_orth
    #choix de la distance d'écartement depuis l'origine
    if dmax_km*180/np.pi/EARTH_RADIUS>10:
        raise Exception("trop loin, changer la distribution (ajouter un sinus.. )")
    phi=np.sqrt(np.random.uniform(dmin_km**2, dmax_km**2))/EARTH_RADIUS# uniforme sur la Terre aplatie localement
    nv_vec=np.sin(phi)*vec_tournant+np.cos(phi)*vec_central
    latobj, lonobj = np.arcsin(nv_vec[2]), np.arccos(nv_vec[0]/(1-nv_vec[2]**2)**0.5)
    assert -np.pi/2<latobj<np.pi/2
    return [latobj, lonobj]

def ramene_pi(x):
    while x > np.pi:
        x-=2*np.pi
    while x <= -np.pi:
        x+=2*np.pi
    return x

def xyz(lat, lon):
    clt, slt = np.cos(lat), np.sin(lat)
    cln, sln = np.cos(lon), np.sin(lon)
    return [clt*cln], [clt*sln], [slt]

def test_distrib():
    lon, lat = np.pi/6, np.pi/3
    latmax=np.radians(80)
    kappa = 5
    u = [xyz(*kent_randomgen(lat, lon, kappa, latmax)) for _ in range(1000)]
    print(np.mean(np.reshape(u, (-1, len(u[0]))), axis=0))
    plt.figure(figsize=(20, 10))
    plt.subplot(121, projection='3d')
    for elt in u:
        plt.plot(*elt, ',')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('kent perso')

    plt.subplot(122)
    s = np.random.vonmises(lon, kappa, 200)
    x=np.cos(s)
    y=np.sin(s)
    plt.plot(x, y,',')
    plt.title('vMF')
    plt.show()


def create_voisins_villeschoisies(Nb, ficVille='os_Lille.csv'):
    np.random.seed(32)

    fic_communes=os.path.join(this_file_path,"villes_villages.txt")
    with open(fic_communes, 'r') as f:
        villages=f.readlines()[1:]
    if Nb>len(villages):
        raise Exception("Pas assez de prenoms, compléter le fichier")
    prenoms_sel=np.random.choice(villages, Nb, replace=False)
    
    #get the cities
    villes=satgen.read_ground_stations_basic(ficVille)
    #"gid",  "name", "latitude_degrees", "longitude_degrees", "elevation_m","population_k": int
    villes_pos=[np.radians([float(ville["latitude_degrees"]), float(ville["longitude_degrees"])]) for ville in villes]
    villes_probas=np.array([float(ville['population_k']) for ville in villes])
    villes_choisies = np.random.choice(list(range(len(villes))), size=Nb, p=villes_probas/sum(villes_probas))
    nomvillefic=villes[villes_choisies[0]]['name']
    villes_choisies.sort()
    liste_emplacements=[]
    plt.subplot(projection='3d')
    for gid, (prenom, idville) in enumerate(zip(prenoms_sel, villes_choisies)):
        latlonrad=zone_randomgen(*villes_pos[idville], dmax_km=700, dmin_km=50)
        lat, lon = np.degrees(latlonrad)
        plt.plot(*xyz(*latlonrad), '.')
        plt.plot(*xyz(*villes_pos[idville]), '.', color='k')
        #altitude normal law around 200m+/-
        altitude_above_msl=np.random.rayleigh(1.6)*100-30#aucune idée si c'est vrai, mais ça fera l'affaire
        liste_emplacements.append({
            'gid': gid,
            "name": prenom.strip(),
            "longitude_degrees": lon, #degrees
            "latitude_degrees": lat, #degrees
            "elevation_m": altitude_above_msl, #altitude, meters
            "maitre": idville
        })
    plt.show()
    #raise Exception("data not written, comment out this exception to generate emplacements")
    with open(os.path.join(this_file_path,f"os_{Nb}emplacements_{nomvillefic}.csv"), 'w') as f:
        champs = ['gid', 'name', 'latitude_degrees', 'longitude_degrees', 'elevation_m', 'maitre']
        ecrivain = csv.DictWriter(f, fieldnames=champs)
        ecrivain.writeheader()
        ecrivain.writerows(liste_emplacements)

if __name__ =='__main__':
    #create_users_randomGlobe(100)
    #test_distrib()
    #create_users_randomGlobe(250)
    #create_users_villesGlobe(1000)
    #create_users_villeschoisies(1000)
    create_voisins_villeschoisies(100)

