import os
import pandas as pd
dos_experience="papaver4/svgde_2023-09-02-1921_3_3978748"
pas_temps=2e9 #ns
def cree_db(dos_exp):
	infos=[]
	for fic in os.scandir(os.path.join(dos_exp, 'paths')):
		if (not fic.name.startswith("paths_")) or (not fic.name.endswith('.txt')):
			print("skip", fic.path)
			continue
		instant=fic.name.rstrip('.txt')
		instant=int(instant[instant.rfind('_')+1:])
		with open(fic.path) as f:
			lignes=f.readlines()
		for ligne in lignes:
			paire, temps, chem = eval(ligne)
			src, dst=paire
			chem=str(chem)
			infos.append((instant,src, dst,chem))
	return pd.DataFrame.from_records(infos, columns=['instant', 'src', 'dst', "chemin"])
 
def communs(df):
	for (src, dst, _), bdd in df.groupby(by=['src', 'dst', 'chemin']):
		if bdd.shape[0]==1:
			continue
		if bdd.shape[0]-1!=(bdd['instant'].max()-bdd['instant'].min())/pas_temps:
			print(src, dst,"\n", bdd, "\n\n")
bdd=cree_db(dos_experience)
communs(bdd)
