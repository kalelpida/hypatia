# The MIT License (MIT)
#
# Copyright (c) 2020 ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os

def calcul_ISL_utilisation(nom_doss):
    """ get the most used ISLs"""

    emplacement_fics=os.path.join('data', nom_doss, 'data')

    nx_calcs=os.listdir(emplacement_fics)
    nx_paths=[os.path.join(emplacement_fics,nom) for nom in nx_calcs if nom.startswith('networkx_path')]
    dico_compteur_ISL={}
    for fic in nx_paths:
        with open(fic, 'r') as f:
            ligne0=f.readline()
            ligne0.removeprefix('0,')
            listeSats=ligne0.split('-')[1:-1]
            satsId=[int(sat) for sat in listeSats]
            for i in range(len(listeSats)-1):
                paire=min(satsId[i:i+2]), max(satsId[i:i+2])
                if paire in listeSats:
                    dico_compteur_ISL[paire]+=1
                else:
                    dico_compteur_ISL[paire]=1

    return sorted(dico_compteur_ISL.items(), key= lambda x: x[1])

def casseISLs(dico):
    
    if not (params:=dico.get('deteriorISL')):
        return 
    
    cstl=dico['constellation']
    nom_doss='_'.join([cstl, dico['isls'], dico['sol'], dico['algo']])

    duree=dico['duree']
    pas=dico['pas']
    
    sel=params.get('sel', 'topUtil10')
    erreur=params.get('errRate', "0.1")
    listeUtilISL=calcul_ISL_utilisation(os.path.join(nom_doss, f"{pas}ms_for_{duree}s", "manual"))
    if sel.startswith('topUtil'):
        nb=int(sel.removeprefix('topUtil'))
        liens_compromis_int=listeUtilISL[:nb]
        liens_compromis_str=[]
        for l in liens_compromis_int:
            liens_compromis_str.append('{} {}'.format(*l[0]))
            liens_compromis_str.append(f'{l[0][1]} {l[0][0]}')

    ficISL=os.path.join("../satellite_networks_state/gen_data/",nom_doss, "isls.txt")
    assert os.path.isfile(ficISL)
    vrai_lignes=[]
    str_vereuse=" recvErrRate:"+str(erreur)+" trackLinkDrops\n"
    with open(ficISL, 'r') as f:
        lignes=f.readlines()
    for ligne in lignes:
        if any(ligne.startswith(l) for l in liens_compromis_str):
            vrai_lignes.append(ligne.strip()+ str_vereuse)
        else:
            vrai_lignes.append(ligne)
    with open(ficISL, 'w') as f:
        f.writelines(vrai_lignes)
    
    


