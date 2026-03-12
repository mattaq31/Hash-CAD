from seqwalk import design

L, k = 20, 6
lib = design.max_size(L, k, alphabet="ACGT")

# sanity: lengths
assert all(len(s) == L for s in lib)

# sanity: SSM-ish check: no repeated k-mers across library (quick check on a subset)
seen = set()
for s in lib[:5000]:  # keep it fast
    for i in range(L - k + 1):
        km = s[i:i+k]
        if km in seen:
            raise RuntimeError("repeated k-mer found: " + km)
        seen.add(km)

print("sanity checks passed; sequences:", len(lib))
