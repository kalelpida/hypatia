import yaml, os
from .input_data import generate_users as genpos
from .input_data.constants import *

class Positionneur():
    def __init__(self, constel: str, dico_constel: dict) -> None:
        regeneres=set()
        liste=dico_constel["TYPES_OBJETS_SOL"]
        stopBoucle=iter(range(1,100))
        while liste and next(stopBoucle):
            nom_obj_sol=liste.pop(0)
            obj=dico_constel[nom_obj_sol]
            if any(dependance not in regeneres for dependance in obj.get('dependances', [])):
                liste.append(nom_obj_sol)#get back to this object later, others need to be generated first
                continue
            if not obj.get('generateur', ""):#pas de position à générer
                regeneres.add(nom_obj_sol)
                continue
            fonc =  getattr(genpos, obj['generateur'])
            fonc(Nb=obj['nombre'],constellation=constel, outfic=obj['positions']+'.csv', **{ param: obj[param] for param in obj.get('genparams', [])})
            regeneres.add(nom_obj_sol)

