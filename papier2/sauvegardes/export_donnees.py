"""
README
just save the 
"""
import os, sys
from etudes6 import *

if __name__=='__main__':
	remplissage_dico()
	fic_export = __file__.removesuffix('.py')+".pickle"
	with open(FIC_SAUVEGARDE, 'rb') as f_from, open(fic_export, 'wb') as f_export:
		f_export.writelines(f_from.readlines())
	


#ALGOS=['isls2', 'isls4', 'isls3', 'isls5', 'isls6', 'isls']#sorted(['isls']+[f'isls{i}' for i in range(2,7)], key = lambda x: len(x), reverse=True)#('isls2d', 'isls2e', 'isls2b', 'isls2c', 'isls2', 'isls')
#ALGOS=list(dico.keys())
#if len(LISTE_COULEURS)<len(ALGOS):
#	LISTE_COULEURS=np.random.choice(colormaps, len(ALGOS), replace=False)


#enregistreur_logs()
