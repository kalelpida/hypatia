fics=$(find ../../papier2/sauvegardes/svgde_paths_hypatia_graine2_pas2s_for_8s/data10Mbps -type f -regex ".*over_isls3m4/.*" -name "networkx_path_*.txt" | sort)
#fics=$(find ../../papier2/sauvegardes/svgde_paths_hypatia_graine2_pas2s_for_8s/ -type f -name "networkx_path_*.txt" | sort)

for fic in $fics; do 
	python visualize_path.py $fic
done
