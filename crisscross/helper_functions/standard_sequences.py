from crisscross.helper_functions import revcom

simpsons = {
    'Bart': 'GTGTAGGTATGAAGGTATAGA',
    'Edna': 'TGAGTGAAAAGTTGATAGTGG',
    'Flanders': 'GGTTGGAATTGGTAATAAGAG',
    'Homer': 'AGGAAAGATATTAGGGGTTGT',
    'Krusty': 'GAAGTTAGAGTTGAGAGTTGA',
    'Lisa': 'GGGGTTAGTTAGGAGAAAATT',
    'Marge': 'AGATTGATTAGAGGGAATGGT',
    'Nelson': 'TGATGGGAGAGAGATGTAATT',
    'Patty': 'GGGAAGAATGATATAGTGTGT',
    'Quimby': 'GGATTTAATGGATGAAGTAGG',
    'Smithers': 'GATGAGGTGTATAAGTGAGAT',
    'Wiggum': 'GAATGTGTAAGGAGAATTTGG'
}

in_dwarves = {
    'Fili': 'GAGACGATGTTGACCTTAACC',
    'Kili': 'GGCTGAAAATCTCCTGACATG',
    'Dwalin': 'GCTACTCACTCAGATAGGGTA',
    'Balin': 'CCATCTTGTCATAACGGGAAG',
    'Oin': 'ACTATATCGGTCGGAAACTGC',
    'Gloin': 'AACGAGGACTCTTGGACTCTA',
    'Ori': 'GTTTCTCCAAAAGCACTAGGG',
    'Dori': 'CGAATTAGGAATACCGTGTCC',
    'Nori': 'CGATCCTGATGTACGAAAGTC',
    'Bifur': 'CCTGGAACACTTGCTAATGAG',
    'Bofur': 'CGTGTAGCCAATTAGACTGAC',
    'Bombur': 'TCTAACTTACAGAGCATGGCG'
}

simpsons_anti = {k: revcom(v) for k, v in simpsons.items()}
in_dwarves_anti = {k: revcom(v) for k, v in in_dwarves.items()}
