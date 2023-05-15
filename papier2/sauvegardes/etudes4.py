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
import pickle

DOSSIER='.'
DOSSIER_A_EXCLURE=['slp','tcp','Ancien']
DOSSIER_A_INCLURE=['isls3', 'isls4', 'isls7', 'isls8']
if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')

FIC_RES="fichier_resultats_pings"
RECIPROQUE=False #""" considérer les chemins A->B et B->A comme la même mesure """

LISTE_COULEURS=['Oranges','Purples']*3#,'Greens', 'Blues', 'RdBu', 'PiYG']

dico={}#algo:{} for algo in ALGOS}



def nom_algo(algo):
	if algo=='isls':
		return 'SP/1-nearest'
	elif algo=='isls2':
		return 'UMCF/1-nearest'
	if algo=='isls3':
		return 'SP/3-nearest'
	elif algo=='isls4':
		return 'UMCF/3-nearest'
	else:
		return algo


def add_dico(*args):
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
	while aChercher:
		nom=aChercher.pop()
		if "logs_ns3" in nom and any([motif in nom for motif in DOSSIER_A_INCLURE]):
			trouves.append(nom)
		else:
			for glob in os.listdir(nom):
				x=os.path.join(nom,glob)  
				if os.path.isdir(x) and all([not motif in x for motif in DOSSIER_A_EXCLURE]):
					aChercher.append(x)
	return trouves


def repartiteurLogBrut(dossier, reciproque=RECIPROQUE):
	chemin_pingmesh="pingmesh.csv"
	import re
	res_algo=re.search('_(isls[^/-]*)',dossier)# cherche les chaines de caractères contenant isls, après _ et avant /
	if res_algo is None:
		return
	cle,=res_algo.groups()
	res_nomgraine=re.search('svgde_[^/]*20\d{2}-\d{2}-\d{2}-\d{4}_(\d+)',dossier)#nom typique: blabla1/svgde_[infos?]date_graine/blabla2
	if res_nomgraine is None:
		return
	graine,=res_nomgraine.groups()
	if cle not in dico:
		dico[cle]={}
	y=os.path.join(dossier,"udp_bursts_outgoing.csv")
	x=os.path.join(dossier,chemin_pingmesh)
	################# get commodities for current simulation
	if not (os.path.isfile(y) and os.path.isfile(x)):
		#print(x,dossier,"pas de donnees")
		return
	commodites=set()

	with open(y,'r') as fic:
		for line in fic:
			donnees=eval(line)
			src,dst=donnees[1:3]
			commodites.add((src,dst))	

	################ add data in main dict
	debitISL=dossier.split("pairing_")[1].split('_')[0]
	with open(x, "r") as fic:
		for line in fic:
			data_split = line.strip().split(',')
			reply_arrived_str = data_split[-1]
			if reply_arrived_str != "YES":
				#there is no data
				continue
			from_node_id, to_node_id, j, sendRequestTimestamps, replyTimestamps, receiveReplyTimestamps, \
                        latency_to_there_ns, latency_from_there_ns, rtt_ns = eval(','.join(data_split[:-1]))
			
			# select ping pairs. To study only pings on commodities,
			# the test should be like "if (n1,n2) not in commodites: continue""
			if (from_node_id, to_node_id) not in commodites:
				continue
			
			if reciproque:
				add_dico(cle, debitISL, graine, min(from_node_id, to_node_id), rtt_ns*1e-9)
			else:
				add_dico(cle, debitISL, graine, from_node_id, latency_to_there_ns*1e-9)
				add_dico(cle, debitISL, graine, to_node_id, latency_from_there_ns*1e-9)
	


#Etude par sources
def affiche_logs_sources(reciproque=RECIPROQUE):
	#fig, this_ax = plt.subplots()
	nbaxis=len(dico)//2
	fig, axs = plt.subplots(nbaxis, sharex=True, sharey=True, figsize=(10, 10))
	#fig.suptitle("Comparison of the median pings per source")
	cmaps = [plt.get_cmap(nom) for nom in LISTE_COULEURS] 
	for i_algo,(algo,dic) in enumerate(sorted([elt for elt in dico.items()])):

		colors=cmaps[i_algo//nbaxis](np.linspace(1,0,len(dic),endpoint=False))
		for nb, isl in enumerate(sorted(dic, key= lambda val:int(val))):
			#this_ax.step(range(len(y[isl])),sorted(y[isl]), where='mid', color=colors[nb], marker=("2" if algo=='isls' else " "), label=f"{nom_algo(algo)}@ISL {isl}Mb/s")
			#this_ax.legend()
			#récupérer les mesures pour chaque graine, 
			#trier les mesures par distance
			#compléter les RTTs manquants comme des échecs
			mesures_par_graines=[]
			for graine, di in dic[isl].items():
				mesures_triees=[]
				for src,mes in di.items():
					mesures_triees.append(np.median(mes))
				mesures_par_graines.append(sorted(mesures_triees))

			n=max(len(mpg) for mpg in mesures_par_graines)
			for liste in mesures_par_graines:
				while len(liste)<n:
					liste.append(0)
			
			# pour chaque graine, choisir la médiane des valeurs
			valeurs=np.array(mesures_par_graines)


			axs[i_algo%nbaxis].step(range(valeurs.shape[1]), [np.median(valeurs[:, i]) for i in range(valeurs.shape[1])], where='mid', color=colors[nb], label=f"{nom_algo(algo)}@ISL {isl}Mb/s")
			axs[i_algo%nbaxis].legend()
			#axs[i_algo%2,i_algo//2].step(x, y[isl], where='mid', color=colors[nb], label=isl)


	fig.text(0.5, 0.01, 'sorted source stations', ha='center', fontsize=12)
	fig.text(0.01, 0.5, 'median measured latency (s)', va='center', rotation='vertical', fontsize=12)	
	fig.tight_layout(pad=3)
	
	nomfic="comparisonv4"+''.join(DOSSIER_A_INCLURE)
	plt.savefig(DOSSIER+'/'+nomfic+".png")
	plt.show()	


dossiers=retrouveLogsBrutRecursif()
cleSVGDE='-'.join(sorted(DOSSIER_A_EXCLURE, reverse=True)+['|ç|',DOSSIER,'|à|']+sorted(DOSSIER_A_INCLURE))
try:
	with open("etudes4.pickle", 'rb') as f:
		lessvgdes=pickle.load(f)
	dos_svgdes, dico=lessvgdes.get(cleSVGDE)
	assert dos_svgdes == dossiers
	assert dico
except Exception:
	for i,dos in enumerate(dossiers):
		print(f"repartition données: {i}/{len(dossiers)}")
		repartiteurLogBrut(dos)
	if 'lessvgdes' not in dir():# if lessvgdes is not defined
		lessvgdes={}
	lessvgdes[cleSVGDE]=(dossiers,dico)
	with open("etudes4.pickle", 'wb') as f:
		pickle.dump(lessvgdes, f)
	

#ALGOS=['isls2', 'isls4', 'isls3', 'isls5', 'isls6', 'isls']#sorted(['isls']+[f'isls{i}' for i in range(2,7)], key = lambda x: len(x), reverse=True)#('isls2d', 'isls2e', 'isls2b', 'isls2c', 'isls2', 'isls')
ALGOS=list(dico.keys())
print(f"algos: {ALGOS}")
if len(LISTE_COULEURS)<len(ALGOS):
	LISTE_COULEURS=np.random.choice(colormaps, len(ALGOS), replace=False)


#enregistreur_logs()
affiche_logs_sources()

