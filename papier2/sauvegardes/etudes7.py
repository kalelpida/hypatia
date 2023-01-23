"""
README
etude sur le croisement de flux
"""
import os
import os, sys
import matplotlib.pyplot as plt
from matplotlib import colormaps, markers #names of colormaps
import numpy as np
import re, yaml
import pickle

ROUTAGE_UNIQUE='' #'routes communes' # set to '' to disable
DOSSIER='reunion230123sc'
DOSSIER_A_EXCLURE=['slp','tcp','Ancien']
DOSSIER_A_INCLURE=['']
AFFICHE_RATIO=True

PARAMS_A_EXCLURE = []#'NuldeteriorISL', 'brstErrMdl'] #

if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')

FIC_SAUVEGARDE = __file__.removesuffix('.py')+".pickle"

dico={}
dict_commodites={}
dico_sacs={}
duree_simu=None

def nom_algo(algo):
	if algo=='isls':
		return 'SP'
	elif algo=='isls2':
		return 'UMCF/1-nearest'
	if algo=='isls3':
		return 'SP/3-nearest'
	elif algo=='isls4':
		return 'UMCF/3-nearest'
	else:
		return algo


def add_dico(*args, dico=dico):
	n=len(args)
	assert n>=2
	dic=dico
	for k in range(n-2):
		if args[k] not in dic:
			dic[args[k]]={}
		dic=dic[args[k]]
	if args[n-2] not in dic:
		dic[args[n-2]]=[]
	dic[args[n-2]].append(args[-1])
	

#cmap=plt.get_cmap('rainbow')
#dico_couleurs={cle:cmap(i/len(dico)) for i,cle in enumerate(dico.keys())}


def retrouveLogsBrutRecursif(chemin_initial=DOSSIER):#,'2022-05-06'}):
	print(f"étude de : {chemin_initial}")
	trouves=[]
	aChercher=[chemin_initial]
	cles_variantes=[]
	while aChercher:
		nom=aChercher.pop()
		if "manual/data" in nom and any([motif in nom for motif in DOSSIER_A_INCLURE]):
			trouves.append(nom)
			continue
		
		for glob in os.listdir(nom):
			x=os.path.join(nom,glob) 
			if glob=="variations.txt":
				if cles_variantes:
					raise Exception("erreur: cle variantes déjà définies, résoudre la fusion des configurations/données")
				with open(x, 'r') as f:
					cles_variantes=eval(f.readline())
			elif os.path.isdir(x) and all([not motif in x for motif in DOSSIER_A_EXCLURE]):
				aChercher.append(x)
	return trouves, sorted(cles_variantes)

def getconfigcourante(dossier, cles_variantes):
	global duree_simu
	chemin, =re.search('(.*svgde_[^/]*20\d{2}-\d{2}-\d{2}-\d{4}_\d+/)',dossier).groups()#all before the config_name
	with open(os.path.join(chemin,  "courante.yaml"), 'r') as f:
		dico_config=yaml.load(f, Loader=yaml.Loader)

	#specifique: duree simu identique pour tous
	if duree_simu is None:
		duree_simu=dico_config['duree']
	assert duree_simu==dico_config['duree']

	liste_variants=[]
	for cle in cles_variantes:
		valeur =  dico_config[cle]
		if not valeur:
			liste_variants.append('Nul'+cle)
		elif type(valeur) is dict:
			liste_variants.append("-".join(f"{nom}:{val}" for nom, val in valeur.items()))
		elif "__iter__" in dir(valeur):
			liste_variants.append("-".join(str(u) for u in valeur))
		else:
			liste_variants.append(str(valeur))
	cle='::'.join(liste_variants)
	if ROUTAGE_UNIQUE:
		maj_liste_commodites(os.path.join(chemin,  "commodites.temp"), ROUTAGE_UNIQUE) 
	else:
		maj_liste_commodites(os.path.join(chemin,  "commodites.temp"), cle) 
	return cle

def maj_liste_commodites(chemin, cle):
	global dict_commodites
	with open(chemin, "r") as f:
		coms=f.readlines()
	coms=eval(coms[0])
	commodites={}
	for idcom, (src, dst, ratio) in enumerate(coms):
		commodites[(src, dst)]=idcom
	if cle in dict_commodites:
		assert commodites == dict_commodites[cle]
	else:
		dict_commodites[cle] = commodites


def repartiteurLogBrut(dossier, str_variants):
	"""fill in dico with all links used by commodites, at any interval"""

	for nom_fic in os.listdir(dossier):
		if re.match("networkx_path_\d+_to_\d+.txt", nom_fic):
			################ add data in main dict
			with open(os.path.join(dossier, nom_fic), "r") as fic:
				liens_precedents=set()
				for line in fic:
					#4000000000,756-434-407-406-405-431-767
					temps, str_nds = line.split(',')
					temps_ns=int(temps)
					nds=str_nds.split('-')
					depart, fin=int(nds[0]), int(nds[-1])
					if (depart, fin) not in dict_commodites[str_variants]:
						#ancien lien penser à supprimer les vieilles simulations
						break
					numcom=dict_commodites[str_variants][(depart, fin)] 
					#interface ISL
					liens = set([(int(nd), int(nds[i+2])) for i, nd in enumerate(nds[1:-2])])
					#interfaces GSL stations
					liens.add(depart)
					#liens.add(fin) # non limitant
					#lien dernier satellite.
					liens.add(int(nds[-2]))
					# donnée finale: interface (debut_activation, fin_activation, debut_reactivation, fin_react...)
					for lien in liens.symmetric_difference(liens_precedents):
						#créer nouveau liens si dans liens-liens_precedents
						#supprimer anciens lien si dans liens_precedents-liens
						add_dico(str_variants, lien, dict_commodites[str_variants][(depart, fin)], temps_ns )
					liens_precedents = liens

def temps_total_commun(*temps):
	#assert len(temps) > 2
	assert all(len(liste) for liste in temps)
	tt=0
	indicesAB=np.ones(len(temps))
	etatsAB=np.zeros(len(temps)) #0=pas utilisation, 1=utilisation
	fonctionnait=False
	precedent=0
	actuel=0
	tempsAB=np.array([liste[0] for liste in temps])
	while any(indicesAB):
		actuel=min(tempsAB[indicesAB>0])
		for i,instant in enumerate(tempsAB):
			if instant==actuel:#changement d'etat
				etatsAB[i] = 1-etatsAB[i]
				if len(temps[i]) > indicesAB[i] > 0:#etape suivante
					tempsAB[i]=temps[i][indicesAB[i]]
					indicesAB[i]+=1
					assert tempsAB[i]>actuel
				else:
					indicesAB[i] = 0			
		if fonctionnait:
			tt+=actuel-precedent
		fonctionnait = all(etatsAB)
		precedent=actuel
	tt*=1e-9
	if fonctionnait:
		tt+=duree_simu-actuel*1e-9
	return tt

def temps_total_parties(*temps):
	if len(temps) < 2:
		return {}
	assert all(len(liste) for liste in temps)
	tt_parties={}
	indicesAB=np.ones(len(temps), dtype=np.uint32)
	etatsAB=np.zeros(len(temps)) #0=pas utilisation, 1=utilisation
	fonctionnaient=()
	precedent=0
	actuel=0
	tempsAB=np.array([liste[0] for liste in temps])
	while any(indicesAB):
		actuel=min(tempsAB[indicesAB>0])
		for i,instant in enumerate(tempsAB):
			if instant==actuel:#changement d'etat
				etatsAB[i] = 1-etatsAB[i]
				if len(temps[i]) > indicesAB[i] > 0:#etape suivante
					tempsAB[i]=temps[i][indicesAB[i]]
					indicesAB[i]+=1
					assert tempsAB[i]>actuel
				else:
					indicesAB[i] = 0			
		if len(fonctionnaient)>1:
			if fonctionnaient in tt_parties:
				tt_parties[fonctionnaient]+=actuel-precedent
			else:
				tt_parties[fonctionnaient] = actuel-precedent
		fonctionnaient = tuple(np.where(etatsAB)[0])
		precedent=actuel

	if len(fonctionnaient)>1:
		if fonctionnaient in tt_parties:
			tt_parties[fonctionnaient]+=duree_simu*1e9-actuel
		else:
			tt_parties[fonctionnaient] = duree_simu*1e9-actuel
	for elt in tt_parties:
		tt_parties[elt]*=1e-9
	return tt_parties


def matrice_correlation():
	#nombre de liens communs à deux flux
	from sklearn import metrics
	nbcoms=len(dict_commodites)
	correlation_flux=np.zeros((nbcoms, nbcoms))
	for experience, dic in dico.items():
		for lien, dict_coms in dic.items():
			coms=list(dict_coms.keys())
			for num, com in enumerate(coms):
				for numautre in range(0, num):
					correlation_flux[coms[num], coms[numautre]] = temps_total_commun(dict_coms[coms[num]], dict_coms[coms[numautre]])
					correlation_flux[coms[numautre], coms[num]] = correlation_flux[coms[num], coms[numautre]]
		print(np.where(correlation_flux==6))
		disp = metrics.ConfusionMatrixDisplay(correlation_flux)
		disp.plot()
		plt.show()


def sac_de_noeuds():
	"""renvoie les ensembles des commodités liées
	"""
	global dico_sacs
	if dico_sacs:
		return dico_sacs
	
	for experience, dic in dico.items():
		sacs=[]
		for lien, dict_coms in dic.items():
			ensembles=temps_total_parties(*list(dict_coms.values()))
			idComs=np.array(list(dict_coms.keys()))
			for ens in ensembles:
				a=set(idComs[list(ens)])
				opfinie=False
				# ensemble deja connu
				for elt in sacs:
					if a.issubset(elt):
						opfinie=True
						break
				if opfinie:
					continue
				# ensemble aggrégateur
				x=len(sacs)
				i=0
				while i<x:
					if sacs[i].issubset(a):
						sacs.pop(i)
						x-=1
					else:
						i+=1
				sacs.append(a)	
		dico_sacs[experience]=sacs	
	return dico_sacs

def cdf_sac_de_noeuds():
	for valparams, sacs in dico_sacs.items():
		groupes={}
		for sac in sacs:
			if len(sac) in groupes:
				groupes[len(sac)]+=1
			else:
				groupes[len(sac)]=1
		npvecs=np.array([(taillegroupe, nbgroupes) for (taillegroupe, nbgroupes) in sorted(groupes.items())])
		plt.figure(figsize=(10, 5))
		plt.title(valparams)
		plt.plot(npvecs[:, 0], npvecs[:, 1], '-*')
		plt.xlabel("taille d'un groupe de commodites")
		plt.ylabel("nombre de groupes")
		plt.tight_layout()
		plt.savefig(os.path.join(DOSSIER, f'comparaisonv7-{valparams}.png'))
		plt.show()

def remplissage_dico():
	dossiers, cles_variantes=retrouveLogsBrutRecursif()
	cleSVGDE='-'.join([DOSSIER,'|à|']+sorted(dossiers))
	global dico, dict_commodites, dico_sacs, duree_simu
	try:
		with open(FIC_SAUVEGARDE, 'rb') as f:
			lessvgdes=pickle.load(f)
		dos_svgdes, dico, dico_sacs, duree_simu, dict_commodites=lessvgdes.get(cleSVGDE)
		assert dos_svgdes == dossiers
		assert dico
	except Exception:
		dico.clear()
		dico_sacs.clear()
		if ROUTAGE_UNIQUE:
			print(f"Routage unique, seul le dossier {dossiers[0]} est utilisé")
			str_params = getconfigcourante(dossiers[0], cles_variantes)# pour mettre à jour commodités
			repartiteurLogBrut(dossiers[0], ROUTAGE_UNIQUE)
		else:
			for i,dos in enumerate(dossiers):
				print(f"repartition données: {i}/{len(dossiers)}")
				str_params = getconfigcourante(dos, cles_variantes)
				repartiteurLogBrut(dos, str_params)
		if 'lessvgdes' not in dir():# if lessvgdes is not defined
			lessvgdes={}
		sac_de_noeuds()# update dico_sacs
		lessvgdes[cleSVGDE]=(dossiers,dico, dico_sacs, duree_simu, dict_commodites)
		with open(FIC_SAUVEGARDE, 'wb') as f:
			pickle.dump(lessvgdes, f)
	finally:
		for param in PARAMS_A_EXCLURE:
			for valparams in list(dico.keys()):
				if param in valparams:
					del dico[valparams]
	

#ALGOS=['isls2', 'isls4', 'isls3', 'isls5', 'isls6', 'isls']#sorted(['isls']+[f'isls{i}' for i in range(2,7)], key = lambda x: len(x), reverse=True)#('isls2d', 'isls2e', 'isls2b', 'isls2c', 'isls2', 'isls')
#ALGOS=list(dico.keys())
#if len(LISTE_COULEURS)<len(ALGOS):
#	LISTE_COULEURS=np.random.choice(colormaps, len(ALGOS), replace=False)


#enregistreur_logs()

def test():
	global duree_simu
	duree_simu=9
	tempsA=[0, 1, 2, 7, 8]
	tempsB=[0, 2, 3, 6, 8]
	print(temps_total_commun([tempsA.copy(), tempsB.copy()]))
	print(tempsB, tempsA)

def main():
	remplissage_dico()
	return sac_de_noeuds()

if __name__=='__main__':
	remplissage_dico()
	#print("dico", dico)
	#print("commodites", dict_commodites)
	#matrice_correlation()
	print(sac_de_noeuds())
	cdf_sac_de_noeuds()
