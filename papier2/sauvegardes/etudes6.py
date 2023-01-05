"""
README
analyse loss logs, find out when they occur and why
"""
import os
import os, sys
import matplotlib.pyplot as plt
from matplotlib import colormaps, markers #names of colormaps
import numpy as np
import re, yaml
import pickle


DOSSIER='a-supprimer'
DOSSIER_A_EXCLURE=['slp','tcp','Ancien']
DOSSIER_A_INCLURE=['']
AFFICHE_RATIO=True

PARAMS_A_EXCLURE = []#'NuldeteriorISL', 'brstErrMdl'] #

if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')

FIC_SAUVEGARDE = __file__.removesuffix('.py')+".pickle"

dico={}
dico_labellise={} # similar to dico
dico_pertes_bole={}#buffer overflow link error
dico_pertes_emission={}
dico_ratio={}

#LABELS for packets inter-arrival
# triés par ordre pour analyse de classe
LABELS=["bon", "perteTampon", "perteEmission", "réordonnancement", "perteAutre", "mélange"]

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

def successRatio(dossier, str_variants):
	def readfic(nomfic):
		ledict={}
		with open(nomfic, 'r') as f:
			for line in f:
				valeurs=eval(line[:line.rfind(',')])
				qte_o = valeurs[10]
				deb_Mbps=valeurs[7]
				idcom=valeurs[0]
				ledict[idcom]=qte_o, deb_Mbps
		return ledict

	infic, outfic="udp_bursts_incoming.csv", "udp_bursts_outgoing.csv"
	assert infic in (fics:=os.listdir(dossier)) and outfic in fics
	dico_in=readfic(os.path.join(dossier, infic))
	dico_out=readfic(os.path.join(dossier, outfic))
	for idcom in dico_in:
		add_dico(str_variants, (idcom, dico_out[idcom][1], dico_in[idcom][1]), dico=dico_ratio)
			
def veritePertesLiens(dossier, str_variants):
	nom_fic="link.drops"
	if nom_fic not in os.listdir(dossier):
		return

	with open(os.path.join(dossier, nom_fic), "r") as fic:
		for line in fic:
			id_commodite, idseq, temps_ns= eval(line[:line.rfind(',')])
			add_dico(str_variants, id_commodite, idseq, dico=dico_pertes_bole)


def repartiteurLogBrut(dossier, str_variants):
	for nom_fic in os.listdir(dossier):
		if re.match("udp_burst_\d+_incoming.csv", nom_fic):
			################ add data in main dict
			with open(os.path.join(dossier, nom_fic), "r") as fic:
				for line in fic:
					id_commodite, idseq, temps_ns= eval(line.strip())
					add_dico(str_variants, id_commodite, (temps_ns*1e-9, idseq))
		elif re.match("udp_burst_\d+_outgoing.csv", nom_fic):
			################ add emission losses in related dict
			with open(os.path.join(dossier, nom_fic), "r") as fic:
				for line in fic:
					id_commodite, idseq, temps_ns, succes= eval(line.strip())
					if not succes:
						print("erreur", str_variants, id_commodite, idseq)
						add_dico(str_variants, id_commodite, idseq, dico=dico_pertes_emission)
	
def labellise_arrivees():
	""" copy dico, but for each commodity, deletes the 1st packet, 
	and add to each packet the time delta with the previous and a label related to this interarrival time """

	for (valparams, dic) in dico.items():
		for commodite, l_arrivees in sorted([elt for elt in dic.items()]):
			arrivees=np.array(l_arrivees)
			inter_arrivees= arrivees[1:] - arrivees[:-1]
			#diviseuria = np.mean(inter_arrivees)*10
			#inter_arrivees/=diviseuria
			#inter_arrivees[:,0].clip(min=0, max=1, out=inter_arrivees[:,0])
			for idinArr, (inArr, dseq) in enumerate(inter_arrivees):
				if dseq == 1:
					add_dico(valparams, commodite, tuple([*l_arrivees[idinArr+1], inArr, "bon"]), dico=dico_labellise)
					continue
				if dseq < 0:
					add_dico(valparams, commodite, tuple([*l_arrivees[idinArr+1], inArr, "réordonnancement"]), dico=dico_labellise)
					continue
				active_isl=dico_pertes_bole.get(valparams) and dico_pertes_bole[valparams].get(commodite)
				active_emission=dico_pertes_emission.get(valparams) and dico_pertes_emission[valparams].get(commodite)
				causes_pertes = np.zeros(int(dseq)-1, dtype=int)+LABELS.index("perteAutre") #par défaut on ne sait pas d'ou vient la perte
				for q in range(1, int(dseq)):
					if active_isl and int(arrivees[idinArr][1]+q) in dico_pertes_bole[valparams][commodite]:
						causes_pertes[q-1] = LABELS.index("perteTampon")
					elif active_emission and int(arrivees[idinArr][1]+q) in dico_pertes_emission[valparams][commodite]:
						causes_pertes[q-1] = LABELS.index("perteEmission")
					elif arrivees[idinArr][1]+q in arrivees[:, 1]:
						causes_pertes[q-1] = LABELS.index("réordonnancement")
				if all(causes_pertes==causes_pertes[0]): #toutes les pertes sont identiques
					add_dico(valparams, commodite, tuple([*l_arrivees[idinArr+1], inArr, LABELS[causes_pertes[0]]]), dico=dico_labellise)
				else:
					add_dico(valparams, commodite, tuple([*l_arrivees[idinArr+1], inArr, "mélange"]), dico=dico_labellise)

#Etude par sources
def affiche_logs_sources(display_success_rate=AFFICHE_RATIO):
	#fig.suptitle("Comparison of the median pings per source")
	markers_choisis=[m for m in markers.MarkerStyle.markers if m not in markers.MarkerStyle.filled_markers and m!=',']
	couleurs=['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']
	nbaxis=len(dico_labellise)
	fig, axs = plt.subplots(nbaxis, sharex=True, sharey=True, figsize=(10, 10))
	if not '__getitem__' in dir(axs):
		axs=np.array([axs])

	# affiche pertes
	for expCntr, (valparams, dic) in enumerate(sorted([elt for elt in dico_labellise.items()])):
		dico_listes_commodites={}
		for commodite, l_arrivees in sorted([elt for elt in dic.items()]):
			#l_arrivees : (temps, idseq, inter_arrivee, label)
			for (temps, idseq, inter_arrivee, label) in l_arrivees:
				add_dico(commodite, label, inter_arrivee, dico=dico_listes_commodites)
		
		axs[expCntr].set_title(valparams)
		labels_utilises=set()
		for commodite, donnees in dico_listes_commodites.items():
			for label, liste in donnees.items():
				indexCouleur=LABELS.index(label)
				axs[expCntr].plot([commodite]*len(liste), liste, ls='', marker=markers_choisis[indexCouleur], color=couleurs[indexCouleur], label=('' if label in labels_utilises else label)  )
				labels_utilises.add(label)
				
		axs[expCntr].legend()
		axs[expCntr].set_xlabel("ID commodité")
		axs[expCntr].set_ylabel("temps inter-arrivée (s)")

	fig.tight_layout()
	plt.savefig(os.path.join(DOSSIER, 'comparaisonv6.png'))
	plt.show()

	# affiche success ratio
	if not display_success_rate:
		return
	
	fig, axs = plt.subplots(nbaxis, sharex=True, sharey=True, figsize=(10, 10))
	if not '__getitem__' in dir(axs):
		axs=np.array([axs])
	
	for expCntr, (valparams, listexy) in enumerate(sorted([elt for elt in dico_ratio.items()])):
		nplistexy=np.array(sorted(listexy))
		axs[expCntr].fill_between(nplistexy[:, 0], nplistexy[: , 1], step='mid', label="sortant")
		axs[expCntr].fill_between(nplistexy[:, 0], nplistexy[: , 2], step="mid", label="entrant")
		axs[expCntr].legend()
		axs[expCntr].set_xlabel("ID commodité")
		#axs[expCntr, 1].set_ylabel("Ratio de succes")
		axs[expCntr].set_ylabel("Débit (Mb/s)")			
	fig.tight_layout()
	
	plt.savefig(os.path.join(DOSSIER, 'comparaisonv6-debits.png'))
	plt.show()
		

		
def remplissage_dico():
	dossiers, cles_variantes=retrouveLogsBrutRecursif()
	cleSVGDE='-'.join([DOSSIER,'|à|']+sorted(dossiers))
	global dico, dico_pertes_bole, dico_ratio, dico_labellise
	try:
		with open(FIC_SAUVEGARDE, 'rb') as f:
			lessvgdes=pickle.load(f)
		dos_svgdes, dico, dico_pertes_bole, dico_ratio, dico_labellise=lessvgdes.get(cleSVGDE)
		assert dos_svgdes == dossiers
		assert dico
	except Exception:
		dico.clear()
		dico_pertes_bole.clear()
		dico_ratio.clear()
		dico_labellise.clear()
		for i,dos in enumerate(dossiers):
			print(f"repartition données: {i}/{len(dossiers)}")
			str_params = getconfigcourante(dos, cles_variantes)
			veritePertesLiens(dos, str_params)
			repartiteurLogBrut(dos, str_params)
			successRatio(dos, str_params)
		labellise_arrivees()
		if 'lessvgdes' not in dir():# if lessvgdes is not defined
			lessvgdes={}
		lessvgdes[cleSVGDE]=(dossiers,dico, dico_pertes_bole, dico_ratio, dico_labellise)
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

if __name__=='__main__':
	remplissage_dico()
	affiche_logs_sources()

