#!/bin/python
"""
README
new way of handling data
A first database contains the different parameters explored in each experiment, and the 'variant' string for a given experiment
Then, a dict keyed with these same 'variants' string contains the database for each experiment
"""
import os, sys
import re, yaml, csv
import pickle
import pandas as pd


DOSSIER='convallaria'
if len(sys.argv)==2:
	DOSSIER=sys.argv[1].strip('/')

FIC_SAUVEGARDE = os.path.join(DOSSIER, os.path.basename(__file__).removesuffix('.py')+".pickle")

df_variants=pd.DataFrame()
dico_bdds={}
dico_locales={}

global NB_SATS
global NB_STATIONS # ground stations, not UEs

def set_globale(nom, valeur):
	if nom in globals() and valeur != globals()[nom]:
		raise Exception(f"redéfinition de {nom}")
	else:
		globals()[nom]= valeur

def set_locale(cle, nom, valeur):
	if cle in dico_locales and nom in dico_locales[cle] and valeur != globals()[nom]:
		raise Exception(f"redéfinition de {nom}")
	elif cle in dico_locales:
		dico_locales[cle][nom]=valeur
	else:
		dico_locales[cle] = {nom: valeur}

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
					cles_variantes+=['graine']*(len(cles_variantes)==0)#il faut un str_variant non nul
	return trouves, sorted(cles_variantes)

def getcomInfos(dossier, cle):
	chemin=os.path.dirname(dossier)
	tcpcoms=os.path.join(chemin, "tcp_flow_schedule.csv")
	if os.path.isfile(tcpcoms):
		dico_tcp={}
		with open(tcpcoms, 'r') as f:
			rdr = csv.reader(f, delimiter=',')
			for ligne in rdr:
				idcom, groupe = ligne[0], ligne[6]
				dico_tcp[idcom]=groupe
		set_locale(cle, 'COMS_TCP', dico_tcp)
	udpcoms=os.path.join(chemin, "udp_burst_schedule.csv")
	if os.path.isfile(udpcoms):
		dico_udp={}
		with open(udpcoms, 'r') as f:
			rdr = csv.reader(f, delimiter=',')
			for ligne in rdr:
				idcom, groupe = ligne[0], ligne[7]
				dico_udp[idcom]=groupe
		set_locale(cle, 'COMS_UDP', dico_udp)
	
def getconfigcourante(dossier, cles_variantes, num=0):
	chemin, =re.search('(.*svgde_[^/]*20\d{2}-\d{2}-\d{2}-\d{4}_\d+/)',dossier).groups()#all before the config_name
	with open(os.path.join(chemin,  "courante.yaml"), 'r') as f:
		dico_config=yaml.load(f, Loader=yaml.Loader)
		constel_nom=dico_config.get('constellation')
	chemin_config=os.path.dirname(chemin)
	with open(os.path.join(chemin_config, constel_nom+".yaml"), 'r') as f:
		dico_constel=yaml.load(f, Loader=yaml.Loader)
	liste_variants=[]
	for cle in cles_variantes:
		valeur =  dico_config[cle]
		if not valeur:
			liste_variants.append('Nul'+cle[:5])
		elif type(valeur) is dict:
			liste_variants.append("-".join(f"{nom}:{val}" if type(val) != dict else f"{nom}:val{num}" for nom, val in valeur.items() ))
		elif "__iter__" in dir(valeur):
			liste_variants.append("-".join(str(u) for u in valeur)+cle[:5])
		else:
			liste_variants.append(str(valeur)+cle[:5])
	str_variants= '::'.join(liste_variants)
	nbsats=dico_constel.get('NUM_ORBS')*dico_constel.get('NUM_SATS_PER_ORB')
	set_globale('NB_SATS', nbsats)
	set_globale('NB_STATIONS', dico_constel['gateway']['nombre'])
	set_globale('TYPES_OBJETS', set(dico_constel['TYPES_OBJETS_SOL']+['satellite']))#just assert we compare similar experiments. For now
	set_locale(str_variants, 'types_objets', set(dico_constel['TYPES_OBJETS_SOL']+['satellite'])) # maybe this one will be used
	return str_variants, liste_variants

def lecture(dossier, str_variants):
	global dico_bdds
	dico_bdds[str_variants]=[]
	dico_bdds[str_variants].append(pd.read_csv(os.path.join(dossier, 'link.rx')))
	dico_bdds[str_variants].append(pd.read_csv(os.path.join(dossier, 'link.tx')))
	dico_bdds[str_variants].append(pd.read_csv(os.path.join(dossier, 'link.drops')))
	fics_progress=[]
	fics_cwnd=[]
	fics_rtt=[]
	for fic in os.listdir(dossier):
		if re.match('tcp_flow_\d+_progress.csv', fic):
			fics_progress.append(fic)
		elif re.match('tcp_flow_\d+_cwnd.csv', fic):
			fics_cwnd.append(fic)
		elif re.match('tcp_flow_\d+_rtt.csv', fic):
			fics_rtt.append(fic)
	df_suivi=pd.concat([pd.read_csv(os.path.join(dossier, fic)) for fic in fics_progress] if fics_progress else [pd.DataFrame()], ignore_index=True)
	dico_bdds[str_variants].append(df_suivi)
	df_suivi=pd.concat([pd.read_csv(os.path.join(dossier, fic)) for fic in fics_cwnd] if fics_cwnd else [pd.DataFrame()], ignore_index=True)
	dico_bdds[str_variants].append(df_suivi)
	df_suivi=pd.concat([pd.read_csv(os.path.join(dossier, fic)) for fic in fics_rtt] if fics_rtt else [pd.DataFrame()], ignore_index=True)
	dico_bdds[str_variants].append(df_suivi)



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
			str_params, liste_variants = getconfigcourante(dos, cles_variantes, i)
			getcomInfos(dos, str_params)
			df_variants_data.append([dos]+liste_variants+[str_params])
			lecture(dos, str_params)
		df_variants=pd.DataFrame(df_variants_data, columns=df_variants_columns)
		globales={'NB_SATS':NB_SATS, 'SOUS_DOSSIERS':dossiers, "NB_STATIONS":NB_STATIONS, 'locales': dico_locales}
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

