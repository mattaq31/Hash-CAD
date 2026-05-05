import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc


seq1= "CTGGATG"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.compute_nupack_energy(seq1,seq2,type='total')
print(test_result_total)
test_result_min = sc.compute_nupack_energy(seq1,seq2,type='minimum')

seq1= "ATGATTA"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.compute_nupack_energy(seq1,seq2,type='total')
print(test_result_total)
test_result_min = sc.compute_nupack_energy(seq1,seq2,type='minimum')


seq1= "GGTCGTA"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.compute_nupack_energy(seq1,seq2,type='total')
print(test_result_total)
test_result_min = sc.compute_nupack_energy(seq1,seq2,type='minimum')

seq1= "AGCTTAG"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.compute_nupack_energy(seq1,seq2,type='total')
print(test_result_total)
test_result_min = sc.compute_nupack_energy(seq1,seq2,type='minimum')

seq1= "GATAGCC"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.compute_nupack_energy(seq1,seq2,type='total')
print(test_result_total)
test_result_min = sc.compute_nupack_energy(seq1,seq2,type='minimum')

seq1= "ATTACTA"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.compute_nupack_energy(seq1,seq2,type='total')
print(test_result_total)
test_result_min = sc.compute_nupack_energy(seq1,seq2,type='minimum')


print("in library:")

seqA= "TAGAAGC"
seqAP= sc.reverse_complement(seqA)
seqA= "TT" + seqA
seqAP= "TT" + seqAP



seqB= "GCTTAGT"
seqBP= sc.reverse_complement(seqB)
seqB= "TT" + seqB
seqBP= "TT" + seqBP


test_result_total = sc.compute_nupack_energy(seqA,seqB,type='total')
print(seqA, seqB, test_result_total)

test_result_total = sc.compute_nupack_energy(seqAP,seqBP,type='total')
print(seqAP, seqBP, test_result_total)

test_result_total = sc.compute_nupack_energy(seqA,seqBP,type='total')
print(seqA, seqBP, test_result_total)

print("not in library:")

seqA= "TAGAAGC"
seqAP= sc.reverse_complement(seqA)
seqA= "TT" + seqA
seqAP= "TT" + seqAP



seqB= "AGCTTAG"
seqBP= sc.reverse_complement(seqB)
seqB= "TT" + seqB
seqBP= "TT" + seqBP


test_result_total = sc.compute_nupack_energy(seqA,seqB,type='total')
print(seqA, seqB, test_result_total)

test_result_total = sc.compute_nupack_energy(seqAP,seqBP,type='total')
print(seqAP, seqBP, test_result_total)

test_result_total = sc.compute_nupack_energy(seqA,seqBP,type='total')
print(seqA, seqBP, test_result_total)


test_result_min = sc.compute_nupack_energy(seq1,seq2,type='minimum')


