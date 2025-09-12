import numpy as np, eqcorr2d

# small inputs for debugging
A_dbg = [np.array([[1,2,3]], dtype=np.uint8, order='C')]
B_dbg = [np.array([[2,3]],    dtype=np.uint8, order='C')]

# histogram path
hist_c, full = eqcorr2d.compute(A_dbg, B_dbg, 1,0,1,0, 1,0,0)
print("hist shape:", hist_c.shape, "full is", full)

# full maps path
_, full_dbg = eqcorr2d.compute(A_dbg, B_dbg, 1,0,1,0, 0,1,1)
if full_dbg is not None:
    t = full_dbg[0][0]
    print("tuple len:", len(t))
    print("out0 shape:", None if t[0] is None else t[0].shape)      # expect (1, 4) for 1×3 vs 1×2
    print("out180 shape:", None if t[2] is None else t[2].shape)
else:
    print("full_dbg is None (per_pair_full likely off).")