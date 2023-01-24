# Ce qui a changé

Ce dossier a été remanié de Hypatia pour lancer des simulations. Les appels à des lignes de commande bash le rendait facile à distribuer, tout cela a été modifié pour le rendre plus simple à déboguer. Au lieu de distribuer le code, on préférera lancer des expériences différentes sur des machines différentes.	

# Résumé de hypatia

+ hypatia/ns3+sat+sim contient le simulateur ns3 + des modules spécifiques dans contrib
	+ le fichier principal est hypatia/ns3+sat+sim/simulator/scratch/main_satnet/main_satnet.cc
+ hypatia/paper2 contient les scripts de configuration de la topologie et de ns3, ainsi que les résultats lorsque le script a été correctement executé
+ hypatia/satgenpy contient la génération des constellations, du routage, et des outils d'analyse.
+ hypatia/satviz permet de générer les visualisations 3D avec Cesium
	+ À noter pour césium: il faut créer un compte sur https://cesium.com/ion/signup/tokens pour récupérer un token
	+  copier le token dans hypatia/satviz/static_html/top.html
	+  modifier les fichiers à analyser des scripts de hypatia/satviz/scripts et les exécuter
	+  ouvrir les fichiers générés dans hypatia/satviz/viz_output.
		+  dans certains cas, Firefox refuse par défaut de télécharger le javascript permettant de visualiser. Solution temporaire: ouvrir la console dans "outils de développement" : une erreur est levée sur le fichier https://cesiumjs.org/releases/1.57/Build/Cesium/Cesium.js Il suffit d'accepter de le télécharger malgré les risques de sécurité (partage du jeton cesium)


# Démarrage rapide

étapes:
 + Installer hypatia comme prévu avec `hypatia_install_dependencies.sh` et `hypatia_build.sh` à la racine du projet. 
 + Les calculs de MultiCommodity Network Flow ont besoin de Gurobi. Gurobi propose des licenses académiques. Gurobipy ne suffit pas, il faut télécharger la librairie Gurobi Optimizer, et activer les fonctionnalités avec une license Gurobi.
 + configurer les expériences à mener dans `config/campagne.yaml`.
	+ Ce fichier décrit l'ensemble des expérience à mener. Le script d'exécution sélectionne une valeur pour chaque clé et génère un fichier `config/courante.yaml` qui contient les paramètres choisis pour la simulation.
	+ ce fichier décrit aussi les fichiers qui seront sauvegardés à la fin.
 + Exécuter le script d'exécution (`paper3.py`) pour lancer les simulations une à une, et sauvegarder chaque campagne dans un dossier du même nom.
 + récupérer les résultats
	+ Après chaque expérience, si toutes les `actions` de la campagne ont été activées, on retrouve
		+ dans satgenpy_analysis/data les routes calculées et l'estimation des RTT par networkx
		+ dans ns3_experiments/traffic_matrix_load/runs les traces réseau
	+ En fonction de la configuration les `sources` de l'expérience sont copiées dans un dossier dans sauvegarde/nom_campagne
+ analyser les résultats
	+ cela peut se faire avec les scripts `sauvegardes/étudesX.py` qui permettent de visualiser les performances des flux et autres
	+ pour des visuels césium, se reporter à `../satviz/` 