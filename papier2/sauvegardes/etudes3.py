"""
README
print raw results from ns3 simulation runs. 
For each simulation, calculates the sum of the results of all commodities.
"""
import os
import os, sys
import matplotlib.pyplot as plt
import numpy as np

DOSSIER='svgde_global'
DOSSIER_A_EXCLURE=['slp','tcp','Ancien']
DOSSIER_A_INCLURE=['isls3', 'isls4', 'isls7', 'isls8']
if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')
	print(f"étude de : {DOSSIER}")


FIC_RES="fichier_resultats"
RECIPROQUE=False #""" considérer les chemins A->B et B->A comme la même mesure """
dico={}#'isls':{},'isls2':{},'isls2b':{},'isls2c':{}, 'isls2d':{}, 'isls2e':{}}


LISTE_COULEURS=['Oranges','Purples']*3#,'Greens', 'Blues', 'RdBu', 'PiYG']


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
#cmap=plt.get_cmap('rainbow')
#dico_couleurs={cle:cmap(i/len(dico)) for i,cle in enumerate(dico.keys())}


def retrouveLogsBrutRecursif(chemin_initial=DOSSIER):#,'2022-05-06'}):
	trouves=[]
	aChercher=[chemin_initial]
	while aChercher:
		nom=aChercher.pop()
		if "logs_ns3" in nom  and any([motif in nom for motif in DOSSIER_A_INCLURE]):
			trouves.append(nom)
		else:
			for glob in os.listdir(nom):
				x=os.path.join(nom,glob)  
				if os.path.isdir(x)  and all([not motif in x for motif in DOSSIER_A_EXCLURE]):
					aChercher.append(x)
	return trouves



def repartiteurLogBrut(dossier, reciproque=RECIPROQUE):
	chemin_udp="udp_bursts_incoming.csv","udp_bursts_outgoing.csv"
	import re
	result=re.search('_(isls[^/-]*)',dossier)# cherche les chaines de caractères contenant isls, après _ et avant /
	assert len(result.groups())==1
	cle,=result.groups()
	if cle not in dico:
		dico[cle]={}
	x=os.path.join(dossier,chemin_udp[0])
	y=os.path.join(dossier,chemin_udp[1])
	if not (os.path.isfile(x) and os.path.isfile(y)):
		print(dossier,"pas de donnees")
		return
	debitISL=dossier.split("pairing_")[1].split('_')[0]
	with open(x, "r") as infic,\
	open(y, "r") as outfic:
		outlines=outfic.readlines()
		inlines=infic.readlines()
		for i,inline in enumerate(inlines):
			resi=eval(inline)
			reso=eval(outlines[i])
			#qteem=reso[10]/125000
			#qterec=resi[10]/125000
			ratio=resi[10]/reso[10]
			n1,n2=resi[1],resi[2]
			if reciproque:
				n1,n2=min(n1,n2),max(n1,n2)
			if (n1,n2) in dico[cle]:
				if debitISL in dico[cle][(n1,n2)]:
					dico[cle][(n1,n2)][debitISL].append(ratio)
				else:
					dico[cle][(n1,n2)][debitISL]=[ratio]
			else:
				dico[cle][(n1,n2)]={debitISL:[ratio]}
		
#Etude par commodités
def enregistreur_logs(reciproque=RECIPROQUE):
	for algo,dic in dico.items():
		lignes=[]
		ratios={}
		nb_mesures={}
		lignes.append('src/dst  [débitISL: moyenne, mesures, ecart-type] ..\n')
		for srcdst,di in dic.items():
			caracs=''
			for isl,vals in di.items():
				caracs+=f'\t  {isl}: {np.mean(vals):.2f}, {len(vals)}, {np.std(vals):.2f}'
				if not isl in nb_mesures:
					nb_mesures[isl]=0
					ratios[isl]=[]
				ratios[isl].append(np.mean(vals))
				nb_mesures[isl]+=len(vals)
			lignes.append('{},{} {}\n'.format(*srcdst,caracs))
		if reciproque:
			methode='aller-retour'
		else:
			methode='simple'
		caracs=''
		for isl in sorted(ratios.keys(),key=lambda x:int(x)):
			vals=ratios[isl]
			caracs+=f'\t  {isl}Mb/s: moyenne des rapports {np.mean(vals):.2f}, écart-type de {np.std(vals):.2f} pour {len(vals)} mesures répétées {nb_mesures[isl]/len(vals):.1f} fois chacune\n'
			
		lignes.insert(0, f"global: {len(dic)} débits {methode} mesurés\n"
						f"{caracs}")

		with open("{}_{}.txt".format(FIC_RES,algo),"w") as f:
			f.writelines(lignes)


#Etude par sources
def affiche_logs_sources(reciproque=RECIPROQUE):
	kCOMP=2
	nombre_algos=len(dico)//kCOMP

	for i in range(int(nombre_algos**0.5), 0, -1):
		if nombre_algos%i==0:
			placement=(nombre_algos//i,i)
			break
	fig, axs = plt.subplots(*placement, sharex=True, sharey=True, figsize=(5*kCOMP*placement[1], 5*placement[0]))
	axs=np.reshape(axs,placement)
	fig.suptitle("Comparison of the median throughput ratios per source")
	cmaps = [plt.get_cmap(nom) for nom in LISTE_COULEURS] 
	assert RECIPROQUE==False
	for i_algo,(algo,dic) in enumerate(sorted(dico.items())):#[elt for elt in dico.items() if elt[0]=='isls' or elt[0]=='isls2']):
		
		lignes=[]
		quantiles=[0.05,0.5]
		lignes.append(f'src  [débitISL: mesures, quantiles {quantiles}] ..\n')
		sources={}

		for srcdst in dic.keys():
			if (src:=srcdst[0]) not in sources:
				sources[src]={}
			for isl,vals in dic[srcdst].items():
				if isl not in sources[src]:
					sources[src][isl]=[]
				sources[src][isl].append(np.mean(vals))
		x,y=[],{}
		colors=cmaps[(i_algo//placement[0])%kCOMP](np.linspace(1,0,len(dic[srcdst]),endpoint=False))
		for src in sorted(sources):
			caracs=''
			for isl in sources[src]:	
				vals=sources[src][isl]	
				caracs+=('\t  {}: {}, '+','.join(['{:.2f}']*len(quantiles))).format(isl,len(vals),*np.quantile(vals,quantiles))
				if not isl in y:
					y[isl]=[]
				y[isl].append(np.median(vals))
			lignes.append('{} {}\n'.format(src,caracs))
			x.append(src)
		for numcolor,isl in enumerate(sorted(y)):
			axs[i_algo%placement[0],i_algo//placement[0]//kCOMP].step(range(len(y[isl])),sorted(y[isl]), where='mid', color=colors[numcolor], label=f'{nom_algo(algo)}-'*(kCOMP>1)+f"{isl}Mb/s")
			#axs[i_algo%2,i_algo//2].step(x, y[isl], where='mid', label=isl)
		if kCOMP==1:
			axs[i_algo%placement[0],i_algo//placement[0]//kCOMP].set_title(f'{nom_algo(algo)} algorithm')
		axs[i_algo%placement[0],i_algo//placement[0]//kCOMP].legend()
		#with open("{}_{}_sources.txt".format(FIC_RES,algo),"w") as f:
		#	f.writelines(lignes)	
	fig.text(0.5, 0.01, 'sorted source stations', ha='center', fontsize=12)
	fig.text(0.01, 0.5, 'ratio received/sent', va='center', rotation='vertical', fontsize=12)	
	fig.tight_layout(pad=3)
	
	nomfic="comparisonv3"+''.join(DOSSIER_A_INCLURE)
	plt.savefig(DOSSIER+'/'+nomfic+".png")
	plt.show()	


dossiers=retrouveLogsBrutRecursif()
#print(dossiers)
for dos in dossiers:
	repartiteurLogBrut(dos)
enregistreur_logs()
affiche_logs_sources()
