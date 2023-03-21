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

def calcul_ISL_utilisation(nom_doss, commodites):
    """ get the most used ISLs"""

    emplacement_fics=os.path.join('data', nom_doss, 'data')
    dico_coms={(src, dst) for (src, dst, deb) in commodites}
    nx_calcs=os.listdir(emplacement_fics)
    nx_paths=[os.path.join(emplacement_fics,nom) for nom in nx_calcs if nom.startswith('networkx_path')]
    dico_compteur_ISL={}
    for fic in nx_paths:
        with open(fic, 'r') as f:
            ligne0=f.readline()
            ligne0=ligne0.removeprefix('0,')
            lsplit=ligne0.split('-')
            solsrc, soldst=int(lsplit[0]), int(lsplit[-1])
            if (solsrc, soldst) not in dico_coms:
                continue
            listeSats=lsplit[1:-1]
            satsId=[int(sat) for sat in listeSats]
            for i in range(len(listeSats)-1):
                paire=min(satsId[i:i+2]), max(satsId[i:i+2])
                if paire in dico_compteur_ISL:
                    dico_compteur_ISL[paire]+=1
                else:
                    dico_compteur_ISL[paire]=1
    
    return sorted(dico_compteur_ISL.items(), key= lambda x: (x[1], x[0])) #name of satellites is added for reproducibility

def casseISLs(dico):
    
    if not (params:=dico.get('deteriorISL')):
        return 
    
    cstl=dico['constellation']
    nom_doss='_'.join([cstl, dico['isls'], dico['sol'], dico['algo']])

    duree=dico['duree']
    pas=dico['pas']
    
    #get commodities list
    with open("../satellite_networks_state/commodites.temp","r") as f_comms:
            list_comms = eval(f_comms.readline())

    liens_compromis_str=[]
    ajout_str_isl=""
    if erreur:=params.get('errModel', ""):
        ajout_str_isl+=" "+erreur+" trackLinkDrops"

        sel=params.get('sel', '')
        if sel.startswith('topUtil'):
            listeUtilISL=calcul_ISL_utilisation(os.path.join(nom_doss, f"{pas}ms_for_{duree}s", "manual"), list_comms)
            nb=int(sel.removeprefix('topUtil'))
            liens_compromis_int=listeUtilISL[:nb]
            for l in liens_compromis_int:
                liens_compromis_str.append((l[0][0], '{} {} '.format(*l[0])))

    #print("generation des liens compromis :", liens_compromis_str)
    if not liens_compromis_str or not ajout_str_isl:
        #nothing to do, exit
        return
    ficISL=os.path.join("../satellite_networks_state/gen_data/",nom_doss, "isls.txt")
    assert os.path.isfile(ficISL)
    vrai_lignes=[]
    
    with open(ficISL, 'r') as f:
        lignes=f.readlines()
    for ligne in lignes:
        modif=False
        ligneval0=int(ligne[:ligne.find(' ')])
        for lv0, l in liens_compromis_str:
            if ligne.startswith(l):
                vrai_lignes.append(ligne.rstrip() + ajout_str_isl + "\n")
                modif=True
                break
            if ligneval0 < lv0:
                break
        if not modif:
            vrai_lignes.append(ligne)
    with open(ficISL, 'w') as f:
        f.writelines(vrai_lignes)


    #just to keep a trace of the changes, write it as comments in the config file of the simulation
    groupes=dico['protocoles']
    all_protocols_name=[]
    for groupe in groupes.values():
        all_protocols_name.append(groupe['nom'])
    protocols_name= '_and_'.join(sorted(set(all_protocols_name)))
    run_dir = "../ns3_experiments/runs/run_loaded_tm_pairing_{}_Mbps_for_{}s_with_{}_{}".format( dico['debit-if-isl'], dico['duree'], protocols_name, dico['algo'])
    assert os.path.isfile( fic_config_ns3:=os.path.join(run_dir,"config_ns3.properties"))
    with open(fic_config_ns3, 'a') as f:
        f.write("######### Liens compromis, paramètres:"+ajout_str_isl+"\n")
        for _, l in liens_compromis_str:
            f.write("# "+l+"\n") 

