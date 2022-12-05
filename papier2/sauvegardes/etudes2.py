import os, sys
import matplotlib.pyplot as plt
import numpy as np

DOSSIER='.'
DOSSIER_A_EXCLURE=['slp','tcp','Ancien']
DOSSIER_A_INCLURE=['']
if len(sys.argv)>1:
	DOSSIER=sys.argv[1].strip('/')

print(f"étude de : {DOSSIER}")	

algos_ininteressants=['isls5-slp', 'isls6-slp']
dico={}

#ALGOS=sorted(['isls']+[f'isls{i}' for i in range(2,7)], key = lambda x: len(x), reverse=True)#('isls2d', 'isls2e', 'isls2b', 'isls2c', 'isls2', 'isls')
#print(f"algos: {ALGOS}")
#dico={'isls':{},'isls2':{},'isls2b':{},'isls2c':{}, 'isls2d':{}, 'isls2e':{}}
#dico={algo:{} for algo in ALGOS}
#cmap=plt.get_cmap('rainbow')
#dico_couleurs={cle:cmap(i/len(dico)) for i,cle in enumerate(dico.keys())}

ALPHA=0.2
nbvaleurs=0
def analyse(fic):
	""" remplir le dictionnaire avec les valeurs des simulations """
	with open(fic,"r") as f:
		for line in f:
			if 'udp' not in line:
				continue
			if "pas de donnees" in line:
				continue
			if any([motif in line for motif in DOSSIER_A_EXCLURE]):
				continue
			if any([motif not in line for motif in DOSSIER_A_INCLURE]):
				continue
			nomfic=fic
			if '/' in nomfic:
				nomfic=nomfic.split('/')[-1]
			seed=int(nomfic.strip(".seedtxt"))
			isl=float(line.split('Mbps')[0].split('_')[-2])
			ratio=eval(line.split("qtes: ")[-1].split('Mb')[0])
			algo = line.split("one_only_over_")[1].split(" ,")[0].split('-')[0]
			if algo in algos_ininteressants:
				continue
			if algo not in dico:
				dico[algo]={}
			if seed in dico[algo]:
				dico[algo][seed].append((isl,ratio))
			else:
				dico[algo][seed]=[(isl,ratio)]
		

tous=os.listdir(DOSSIER)
for glob in tous:
	glob=DOSSIER+'/'+glob
	if glob.startswith("seed"):
		analyse(glob)
	elif os.path.isdir(glob):
		subglobs=os.listdir(glob)
		for subglob in subglobs:
			if subglob.startswith("seed"):
				analyse('/'.join([glob,subglob]))

couleurs=['tab:blue', "tab:orange", "tab:green", "tab:red", "tab:purple", 'tab:brown', 'tab:pink', 'tab:gray', "tab:olive", 'tab:cyan']
dico_couleurs={algo:couleur for algo,couleur in zip(dico.keys(),couleurs)}

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

def plot_ratios():
	#plot ratios according to ISL capacity
	global nbvaleurs
	plt.figure(figsize=(10, 10))
	for i,(algo,val) in enumerate(dico.items()):
		valeurs_algo={}
		for seed,listexy in val.items():
			x=[listexy[i][0] for i in range(len(listexy))]
			y=[listexy[i][1] for i in range(len(listexy))]
			plt.plot(x,y,color=dico_couleurs[algo],marker="*", linestyle='', alpha=ALPHA)
			nbvaleurs+=len(listexy)
			for xy in listexy:
				x,y=xy
				if x in valeurs_algo:
					valeurs_algo[x].append(y)
				else:
					valeurs_algo[x]=[y]
		X=sorted(valeurs_algo.keys())
		moy=np.array([np.mean(valeurs_algo[x]) for x in X])
		std=np.array([np.std(valeurs_algo[x]) for x in X])
		plt.errorbar(X, moy, 2*std, color=dico_couleurs[algo], label=nom_algo(algo))
	plt.xlabel('ISL (Mb/s)')
	plt.ylabel('ratio arrived/sent')
	


def plot_seed():
	#plot values according to seeds
	global nbvaleurs
	plt.figure(figsize=(10, 10))
	for i,(algo,val) in enumerate(dico.items()):
		dicoISL={}		
		for seed,listexy in val.items():
			x=[listexy[i][0] for i in range(len(listexy))]
			y=[listexy[i][1] for i in range(len(listexy))]
			for capaIsl, ratio in listexy:
				if capaIsl not in dicoISL:
					dicoISL[capaIsl]=[[],[]]#seeds, ratios
				dicoISL[capaIsl][0].append(seed)
				dicoISL[capaIsl][1].append(ratio)
		for capa, listesSeedsRatios in dicoISL.items():
			plt.plot(listesSeedsRatios[0],listesSeedsRatios[1],color=dico_couleurs[algo],marker="*", linestyle='', alpha=ALPHA, label=f"{nom_algo(algo)}-{capa}Mbs")
		nbvaleurs+=len(listexy)
	plt.xlabel('seed number')
	plt.ylabel('ratio arrived/sent')

		
plot_ratios()
#plot_seed()
plt.legend()

	


plt.tight_layout()
#plt.legend()
nomfic="comparisonv2"+''.join(DOSSIER_A_INCLURE)
plt.savefig(DOSSIER+'/'+nomfic+".png")
plt.show()
print("nbvaleurs:",nbvaleurs/len(dico), "par courbe en moyenne")
			
