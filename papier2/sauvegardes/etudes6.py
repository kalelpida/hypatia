"""
README
makes computations on pingmesh data
print
"""
import os
import os, sys
import matplotlib.pyplot as plt
from matplotlib import colormaps #names of colormaps
import numpy as np
import re, yaml
import pickle


DOSSIER='experienceBursty'
DOSSIER_A_EXCLURE=['slp','tcp','Ancien']
DOSSIER_A_INCLURE=['']


PARAMS_A_EXCLURE = []#'NuldeteriorISL', 'brstErrMdl'] #

if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')

FIC_SAUVEGARDE = __file__.removesuffix('.py')+".pickle"

dico={}
dico_pertes_isl={}


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
	assert n>2
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
		if "logs_ns3" in nom and any([motif in nom for motif in DOSSIER_A_INCLURE]):
			trouves.append(nom)
		else:
			for glob in os.listdir(nom):
				x=os.path.join(nom,glob)  
				if os.path.isdir(x) and all([not motif in x for motif in DOSSIER_A_EXCLURE]):
					aChercher.append(x)
				elif glob=="variations.txt":
					if cles_variantes:
						raise Exception("erreur: cle variantes déjà définies, résoudre la fusion des configurations/données")
					with open(x, 'r') as f:
						cles_variantes=eval(f.readline())
	return trouves, sorted(cles_variantes)

def getconfigcourante(dossier, cles_variantes):
	chemin, =re.search('(.*svgde_[^/]*20\d{2}-\d{2}-\d{2}-\d{4}_\d+/)',dossier).groups()#all before the config_name
	with open(os.path.join(chemin,  "courante.yaml"), 'r') as f:
		dico_config=yaml.load(f, Loader=yaml.Loader)
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
	return '::'.join(liste_variants)
			
def veritePertesISLs(dossier, str_variants):
	for nom_fic in os.listdir(dossier):
		if not re.match("link_\d+-\d+.drops", nom_fic):
			continue

		with open(os.path.join(dossier, nom_fic), "r") as fic:
			for line in fic:
				id_commodite, idseq, temps_ns= eval(line.strip())
				add_dico(str_variants, id_commodite, idseq, dico=dico_pertes_isl)


def repartiteurLogBrut(dossier, str_variants):
	for nom_fic in os.listdir(dossier):
		if not re.match("udp_burst_\d+_incoming.csv", nom_fic):
			continue

		################ add data in main dict
		with open(os.path.join(dossier, nom_fic), "r") as fic:
			for line in fic:
				id_commodite, idseq, temps_ns= eval(line.strip())
				add_dico(str_variants, id_commodite, (temps_ns*1e-9, idseq))
	


#Etude par sources
def affiche_logs_sources():
	#fig.suptitle("Comparison of the median pings per source")
	realites=["bon", "perteISL", "perteAutre", "mélange"]
	markers='.+x1'
	couleurs=['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']
	nbaxis=len(dico)
	fig, axs = plt.subplots(nbaxis, sharex=True, sharey=True, figsize=(10, 10))
	if not '__getitem__' in dir(axs):
		axs=[axs]
	for expCntr, (valparams, dic) in enumerate(sorted([elt for elt in dico.items()])):
		dico_listes_commodites={}
		for commodite, l_arrivees in sorted([elt for elt in dic.items()]):
			arrivees=np.array(l_arrivees)
			inter_arrivees= arrivees[1:] - arrivees[:-1]
			#diviseuria = np.mean(inter_arrivees)*10
			#inter_arrivees/=diviseuria
			#inter_arrivees[:,0].clip(min=0, max=1, out=inter_arrivees[:,0])
			dico_listes_commodites[commodite] = {realite:[] for realite in realites}
			for idinArr, (inArr, dseq) in enumerate(inter_arrivees):
				if dseq == 1:
					dico_listes_commodites[commodite]["bon"].append((inArr))
				elif not dico_pertes_isl.get(valparams) or not dico_pertes_isl[valparams].get(commodite):
					#les pertes ne sont pas activées dans la configuration valparams ou pour la commodite
					dico_listes_commodites[commodite]["perteAutre"].append((inArr))
				else:
					causes_pertes = [int(arrivees[idinArr][1]+q) in dico_pertes_isl[valparams][commodite] for q in range(1, int(dseq))]
					if all(causes_pertes):
						dico_listes_commodites[commodite]["perteISL"].append((inArr))
					elif any(causes_pertes):
						dico_listes_commodites[commodite]["mélange"].append((inArr))
					else:
						dico_listes_commodites[commodite]["perteAutre"].append((inArr))

					
		
		axs[expCntr].set_title(valparams)
		for commodite, donnees in dico_listes_commodites.items():
			for label, liste in donnees.items():
				indexCouleur=realites.index(label)
				axs[expCntr].plot([commodite]*len(liste), liste, ls='', marker=markers[indexCouleur], color=couleurs[indexCouleur], label=label*(commodite==0) )
				
		axs[expCntr].legend()
		axs[expCntr].set_xlabel("ID commodité")
		axs[expCntr].set_ylabel("temps inter-arrivée (s)")
	fig.tight_layout()
	
	plt.savefig(os.path.join(DOSSIER, 'comparaisonv6.png'))
	plt.show()
		

			


		

		

dossiers, cles_variantes=retrouveLogsBrutRecursif()
cleSVGDE='-'.join(sorted(DOSSIER_A_EXCLURE, reverse=True)+['|ç|',DOSSIER,'|à|']+sorted(DOSSIER_A_INCLURE))
try:
	with open(FIC_SAUVEGARDE, 'rb') as f:
		lessvgdes=pickle.load(f)
	dos_svgdes, dico, dico_pertes_isl=lessvgdes.get(cleSVGDE)
	assert dos_svgdes == dossiers
	assert dico
except Exception:
	dico.clear()
	dico_pertes_isl.clear()
	for i,dos in enumerate(dossiers):
		print(f"repartition données: {i}/{len(dossiers)}")
		str_params = getconfigcourante(dos, cles_variantes)
		veritePertesISLs(dos, str_params)
		repartiteurLogBrut(dos, str_params)
	if 'lessvgdes' not in dir():# if lessvgdes is not defined
		lessvgdes={}
	lessvgdes[cleSVGDE]=(dossiers,dico, dico_pertes_isl)
	with open(FIC_SAUVEGARDE, 'wb') as f:
		pickle.dump(lessvgdes, f)
	

#ALGOS=['isls2', 'isls4', 'isls3', 'isls5', 'isls6', 'isls']#sorted(['isls']+[f'isls{i}' for i in range(2,7)], key = lambda x: len(x), reverse=True)#('isls2d', 'isls2e', 'isls2b', 'isls2c', 'isls2', 'isls')
#ALGOS=list(dico.keys())
#if len(LISTE_COULEURS)<len(ALGOS):
#	LISTE_COULEURS=np.random.choice(colormaps, len(ALGOS), replace=False)


#enregistreur_logs()
for param in PARAMS_A_EXCLURE:
	for valparams in list(dico.keys()):
		if param in valparams:
			del dico[valparams]
affiche_logs_sources()

