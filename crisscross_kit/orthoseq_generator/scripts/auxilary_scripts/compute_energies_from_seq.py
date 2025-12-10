import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc


seq1= "CTGGATG"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='total',Use_Library=False)
print(test_result_total)
test_result_min = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='minimum',Use_Library=False)

seq1= "ATGATTA"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='total',Use_Library=False)
print(test_result_total)
test_result_min = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='minimum',Use_Library=False)


seq1= "GGTCGTA"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='total',Use_Library=False)
print(test_result_total)
test_result_min = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='minimum',Use_Library=False)

seq1= "AGCTTAG"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='total',Use_Library=False)
print(test_result_total)
test_result_min = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='minimum',Use_Library=False)

seq1= "GATAGCC"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='total',Use_Library=False)
print(test_result_total)
test_result_min = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='minimum',Use_Library=False)

seq1= "ATTACTA"
seq2= sc.reverse_complement(seq1)
seq1="TT" + seq1
seq2="TT" + seq2
print(seq1)
print(seq2)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='total',Use_Library=False)
print(test_result_total)
test_result_min = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='minimum',Use_Library=False)


print("in library:")

seqA= "TAGAAGC"
seqAP= sc.reverse_complement(seqA)
seqA= "TT" + seqA
seqAP= "TT" + seqAP



seqB= "GCTTAGT"
seqBP= sc.reverse_complement(seqB)
seqB= "TT" + seqB
seqBP= "TT" + seqBP


test_result_total = sc.nupack_compute_energy_precompute_library_fast(seqA,seqB,type='total',Use_Library=False)
print(seqA, seqB, test_result_total)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seqAP,seqBP,type='total',Use_Library=False)
print(seqAP, seqBP, test_result_total)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seqA,seqBP,type='total',Use_Library=False)
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


test_result_total = sc.nupack_compute_energy_precompute_library_fast(seqA,seqB,type='total',Use_Library=False)
print(seqA, seqB, test_result_total)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seqAP,seqBP,type='total',Use_Library=False)
print(seqAP, seqBP, test_result_total)

test_result_total = sc.nupack_compute_energy_precompute_library_fast(seqA,seqBP,type='total',Use_Library=False)
print(seqA, seqBP, test_result_total)


test_result_min = sc.nupack_compute_energy_precompute_library_fast(seq1,seq2,type='minimum',Use_Library=False)


