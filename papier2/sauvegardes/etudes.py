import os, sys
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize as opt
import sys

DOSSIER='svgde_global'
DOSSIER_A_EXCLURE=['slp','tcp','Ancien']
DOSSIER_A_INCLURE=['isls3', 'isls4', 'isls7', 'isls8']
if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')
	print(f"étude de : {DOSSIER}")

dico={}
algos_ininteressants=[]
#cmap=plt.get_cmap('rainbow')
#dico_couleurs={cle:cmap(i/len(dico)) for i,cle in enumerate(dico.keys())}

ALPHA=0.2
nbvaleurs=0
def analyse(file):
	""" remplir le dictionnaire avec les valeurs des simulations """
	with open(file,"r") as f:
		for line in f:
			if 'udp' not in line:
				continue
			if "pas de donnees" in line:
				continue
			if any([motif in line for motif in DOSSIER_A_EXCLURE]):
				continue
			if not any([motif in line for motif in DOSSIER_A_INCLURE]):
				continue
			nomfic=file
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


fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)
fig.suptitle("plots for differents algos")

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
		
def optimise_data(x, y, nomalgo):
	# This is the function we are trying to fit to the data.
	def func(x, a, b):
		return 1 - a * np.exp(-b * x)
	def func2(x, a, b):
		return 1- 1/(a*x+ b)
	# The actual curve fitting happens here
	try:
		optimizedParameters, pcov = opt.curve_fit(func, x, y)
	except Exception:
		print(f"echec optimisation exponentielle pour {nomalgo}") 
		optimizedParameters, pcov = opt.curve_fit(func2, x, y)
		return func2, optimizedParameters, pcov
	else:
		# Use the optimized parameters to plot the best fit
		return func, optimizedParameters, pcov
	
	
	

couleurs=['tab:blue', "tab:orange", "tab:green", "tab:red"]
dico_couleurs={algo:couleur for algo,couleur in zip(dico.keys(),couleurs)}

for i,(algo,val) in enumerate(dico.items()):
	valeurs_algo={}
	for seed,listexy in val.items():
		x=[listexy[i][0] for i in range(len(listexy))]
		y=[listexy[i][1] for i in range(len(listexy))]
		axs[i%2, i//2].plot(x,y,color=dico_couleurs[algo],marker="*", linestyle='', alpha=ALPHA)
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
	#axs[i%2, i//2].errorbar(X, moy, 2*std, color=dico_couleurs[algo], label=algo)
	foptim,args_optim, pcov=optimise_data(np.array(X),moy, algo)
	Xfit=np.linspace(X[0],X[-1],100)
	Yfit=foptim(Xfit,*args_optim)
	axs[i%2, i//2].plot(Xfit, Yfit, color=dico_couleurs[algo])
	if not float('inf') in pcov:
		perr = np.sqrt(np.diag(pcov))
		axs[i%2, i//2].fill_between(Xfit, foptim(Xfit,*(args_optim-2*perr)), foptim(Xfit,*(args_optim+2*perr)),color=dico_couleurs[algo], alpha=ALPHA)
	axs[i%2, i//2].set_title(nom_algo(algo))

fig.text(0.5, 0.01, 'ISL (Mb/s)', ha='center', fontsize=12)
fig.text(0.01, 0.5, 'ratio arrived/sent', va='center', rotation='vertical', fontsize=12)	
fig.tight_layout(pad=3)



#plt.legend()
nomfic="comparisonv"+''.join(DOSSIER_A_INCLURE)
plt.savefig(DOSSIER+'/'+nomfic+".png")
plt.show()
print("nbvaleurs:",nbvaleurs/4, "par courbe en moyenne")
			
