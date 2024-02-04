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

simpsons_anti = {k: revcom(v) for k, v in simpsons.items()}
