#!/bin/python
"""
README
new way of handling data
A first database contains the different parameters explored in each experiment, and the 'variant' string for a given experiment
Then, a dict keyed with these same 'variants' string contains the database for each experiment
"""
import os, sys
import re, yaml
import pickle
import pandas as pd


DOSSIER='one-station-paramel50'
if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')

FIC_SAUVEGARDE = os.path.join(DOSSIER, os.path.basename(__file__).removesuffix('.py')+".pickle")

df_variants=pd.DataFrame()
dico_bdds={}

global NB_SATS
global NB_STATIONS # ground stations, not UEs
def set_globale(nom, valeur):
	if nom in globals() and valeur != globals()[nom]:
		raise Exception(f"redéfinition de {nom}")
	else:
		globals()[nom]= valeur

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

#cmap=plt.get_cmap('rainbow')
#dico_couleurs={cle:cmap(i/len(dico)) for i,cle in enumerate(dico.keys())}


def retrouveLogsBrutRecursif(chemin_initial=DOSSIER):#,'2022-05-06'}):
	print(f"étude de : {chemin_initial}")
	trouves=[]
	aChercher=[chemin_initial]
	cles_variantes=[]
	while aChercher:
		nom=aChercher.pop()
		if "logs_ns3" in nom:
			trouves.append(nom)
		else:
			for glob in os.listdir(nom):
				x=os.path.join(nom,glob)  
				if os.path.isdir(x):
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
		constel_nom=dico_config.get('constellation')
		os.path.abspath
	chemin_config=re.search('.*papier2', os.path.abspath(__file__)).group(0)
	with open(os.path.join(chemin_config,  'config', constel_nom+".yaml"), 'r') as f:
		dico_constel=yaml.load(f, Loader=yaml.Loader)
	nbsats=dico_constel.get('NUM_ORBS')*dico_constel.get('NUM_SATS_PER_ORB')
	set_globale('NB_SATS', nbsats)
	set_globale('NB_STATIONS', dico_constel['gateway']['nombre'])

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
	return '::'.join(liste_variants), liste_variants


def lecture(dossier, str_variants):
	infos_reduites=["instant", "noeud", "commId", "seqNum", "offset", "taille", "TCP", "retour", "info"]
	infos_completes=["instant", "src", "dst", "commId", "seqNum", "offset", "taille", "dureeTx", "TCP", "retour", "info"]
	dico_bdds[str_variants]=[]
	dico_bdds[str_variants].append(pd.read_csv(os.path.join(dossier, 'link.rx'), names=infos_reduites))
	dico_bdds[str_variants].append(pd.read_csv(os.path.join(dossier, 'link.tx'), names=infos_completes))
	dico_bdds[str_variants].append(pd.read_csv(os.path.join(dossier, 'link.drops'), names=infos_reduites))



def remplissage_dico():
	global dico_bdds, df_variants
	dossiers, cles_variantes=retrouveLogsBrutRecursif()
	df_variants_columns=["dossier"]+cles_variantes+["str_variant"]
	df_variants_data=[]
	try:
		#raise Exception("show must go on")
		with open(FIC_SAUVEGARDE, 'rb') as f:
			globales, df_variants, dico_bdds=pickle.load(f)
		assert globales['SOUS_DOSSIERS'] == dossiers
	except Exception:
		for i,dos in enumerate(dossiers):
			print(f"repartition données: {i}/{len(dossiers)}")
			str_params, liste_variants = getconfigcourante(dos, cles_variantes)
			df_variants_data.append([dos]+liste_variants+[str_params])
			lecture(dos, str_params)
		df_variants=pd.DataFrame(df_variants_data, columns=df_variants_columns)
		globales={'NB_SATS':NB_SATS, 'SOUS_DOSSIERS':dossiers, "NB_STATIONS":NB_STATIONS}
		with open(FIC_SAUVEGARDE, 'wb') as f:
			pickle.dump((globales, df_variants, dico_bdds), f)
	"""
	finally:
		for param in PARAMS_A_EXCLURE:
			for valparams in list(dico.keys()):
				if param in valparams:
					del dico[valparams]
	"""

if __name__=='__main__':
	remplissage_dico()

