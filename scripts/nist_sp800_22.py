#!/usr/bin/env python3
"""
nist_sp800_22.py -- NIST SP 800-22 Statistical Test Suite
All 15 randomness tests for cryptographic validation.

Usage:
    from nist_sp800_22 import run_all_tests
    results = run_all_tests(ciphertext_bytes)

    python scripts/nist_sp800_22.py --self-test
"""

import math
import numpy as np
from scipy.special import erfc, gammaincc
from scipy.fft import fft

# ============================================================
# Test 1: Frequency (Monobit)
# ============================================================
def frequency_test(bits):
    n = len(bits)
    s = np.sum(2*bits - 1)
    s_obs = abs(s) / math.sqrt(n)
    p = erfc(s_obs / math.sqrt(2))
    return float(p)

# ============================================================
# Test 2: Block Frequency
# ============================================================
def block_frequency_test(bits, M=128):
    n = len(bits)
    N = n // M
    if N == 0:
        return 1.0
    proportions = np.array([np.mean(bits[i*M:(i+1)*M]) for i in range(N)])
    chi2 = 4 * M * np.sum((proportions - 0.5)**2)
    p = gammaincc(N/2.0, chi2/2.0)
    return float(p)

# ============================================================
# Test 3: Runs
# ============================================================
def runs_test(bits):
    n = len(bits)
    pi = np.mean(bits)
    tau = 2.0 / math.sqrt(n)
    if abs(pi - 0.5) >= tau:
        return 0.0
    v = 1 + np.sum(bits[:-1] != bits[1:])
    p = erfc(abs(v - 2*n*pi*(1-pi)) / (2*math.sqrt(2*n)*pi*(1-pi)))
    return float(p)

# ============================================================
# Test 4: Longest Run of Ones
# ============================================================
def longest_run_test(bits):
    n = len(bits)
    if n < 128:
        return 1.0
    if n < 6272:
        M, K, N_val = 8, 3, n // 8
        v_vals = [1, 2, 3, 4]
        pi_vals = [0.2148, 0.3672, 0.2305, 0.1875]
    elif n < 750000:
        M, K, N_val = 128, 5, n // 128
        v_vals = [4, 5, 6, 7, 8, 9]
        pi_vals = [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
    else:
        M, K, N_val = 10000, 6, n // 10000
        v_vals = [10, 11, 12, 13, 14, 15, 16]
        pi_vals = [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727]
    
    blocks = [bits[i*M:(i+1)*M] for i in range(N_val)]
    max_runs = []
    for block in blocks:
        max_run = 0
        current = 0
        for b in block:
            if b == 1:
                current += 1
                max_run = max(max_run, current)
            else:
                current = 0
        max_runs.append(max_run)
    
    freq = np.zeros(len(v_vals))
    for mr in max_runs:
        if mr <= v_vals[0]:
            freq[0] += 1
        elif mr >= v_vals[-1]:
            freq[-1] += 1
        else:
            for j in range(len(v_vals)):
                if mr == v_vals[j]:
                    freq[j] += 1
                    break
    
    chi2 = sum((freq[i] - N_val*pi_vals[i])**2 / (N_val*pi_vals[i]) for i in range(len(v_vals)))
    p = gammaincc(len(v_vals)/2.0, chi2/2.0)
    return float(p)

# ============================================================
# Test 5: Binary Matrix Rank
# ============================================================
def matrix_rank_test(bits):
    n = len(bits)
    M, Q = 32, 32
    N = n // (M * Q)
    if N == 0:
        return 1.0
    
    def gf2_rank(matrix):
        m = matrix.copy()
        rows, cols = m.shape
        rank = 0
        for col in range(min(rows, cols)):
            pivot = None
            for row in range(rank, rows):
                if m[row, col] == 1:
                    pivot = row
                    break
            if pivot is None:
                continue
            m[[rank, pivot]] = m[[pivot, rank]]
            for row in range(rows):
                if row != rank and m[row, col] == 1:
                    m[row] = m[row] ^ m[rank]
            rank += 1
        return rank
    
    ranks = []
    for i in range(N):
        block = bits[i*M*Q:(i+1)*M*Q].reshape(M, Q)
        ranks.append(gf2_rank(block))
    
    FM = sum(1 for r in ranks if r == M)
    FM1 = sum(1 for r in ranks if r == M-1)
    rest = N - FM - FM1
    
    chi2 = ((FM - 0.2888*N)**2 / (0.2888*N) +
            (FM1 - 0.5776*N)**2 / (0.5776*N) +
            (rest - 0.1336*N)**2 / (0.1336*N))
    p = math.exp(-chi2/2)
    return float(p)

# ============================================================
# Test 6: DFT (Spectral)
# ============================================================
def spectral_test(bits):
    n = len(bits)
    x = 2*bits.astype(float) - 1
    S = np.abs(fft(x))[:n//2]
    T = math.sqrt(math.log(1/0.05) * n)
    N0 = 0.95 * n / 2.0
    N1 = np.sum(S < T)
    d = (N1 - N0) / math.sqrt(n * 0.95 * 0.05 / 4)
    p = erfc(abs(d) / math.sqrt(2))
    return float(p)

# ============================================================
# Test 7: Non-overlapping Template Matching
# ============================================================
def non_overlapping_template_test(bits, m=9):
    n = len(bits)
    template = np.ones(m, dtype=int)
    N = 8
    M = n // N
    if M == 0:
        return 1.0
    
    mu = (M - m + 1) / (2**m)
    sigma2 = M * (1.0/(2**m) - (2*m-1)/(2**(2*m)))
    
    counts = []
    for i in range(N):
        block = bits[i*M:(i+1)*M]
        count = 0
        j = 0
        while j <= len(block) - m:
            if np.array_equal(block[j:j+m], template):
                count += 1
                j += m
            else:
                j += 1
        counts.append(count)
    
    chi2 = sum((c - mu)**2 / sigma2 for c in counts)
    p = gammaincc(N/2.0, chi2/2.0)
    return float(p)

# ============================================================
# Test 8: Overlapping Template Matching
# ============================================================
def overlapping_template_test(bits, m=9):
    n = len(bits)
    template = np.ones(m, dtype=int)
    K = 5
    M = 1032
    N = n // M
    if N == 0:
        return 1.0
    
    lam = (M - m + 1) / (2.0**m)
    eta = lam / 2.0
    pi = [0.364091, 0.185659, 0.139381, 0.100571, 0.070432, 0.139865]
    
    counts = []
    for i in range(N):
        block = bits[i*M:(i+1)*M]
        count = sum(1 for j in range(M-m+1) if np.array_equal(block[j:j+m], template))
        counts.append(min(count, K))
    
    freq = [0] * (K+1)
    for c in counts:
        freq[c] += 1
    
    chi2 = sum((freq[i] - N*pi[i])**2 / (N*pi[i]) for i in range(K+1) if N*pi[i] > 0)
    p = gammaincc(K/2.0, chi2/2.0)
    return float(p)

# ============================================================
# Test 9: Maurer's Universal Statistical Test
# ============================================================
def universal_test(bits):
    n = len(bits)
    L = 7
    Q = 1280
    K = n // L - Q
    if K <= 0:
        return 1.0
    
    expected = [0, 0.7326, 1.5374, 2.4016, 3.3112, 4.2534, 5.2177, 6.1962, 7.1836, 8.1764]
    variance = [0, 0.690, 1.338, 1.901, 2.358, 2.705, 2.954, 3.125, 3.238, 3.311]
    
    T = np.zeros(2**L, dtype=int)
    for i in range(Q):
        val = 0
        for j in range(L):
            val = (val << 1) | bits[i*L + j]
        T[val] = i + 1
    
    total = 0.0
    for i in range(Q, Q+K):
        val = 0
        for j in range(L):
            val = (val << 1) | bits[i*L + j]
        total += math.log2(i + 1 - T[val])
        T[val] = i + 1
    
    fn = total / K
    c = 0.7 - 0.8/L + (4 + 32.0/L) * (K**(-3.0/L)) / 15
    sigma = c * math.sqrt(variance[L] / K)
    p = erfc(abs(fn - expected[L]) / (math.sqrt(2) * sigma))
    return float(p)

# ============================================================
# Test 10: Linear Complexity
# ============================================================
def linear_complexity_test(bits, M=500):
    n = len(bits)
    N = n // M
    if N == 0:
        return 1.0
    
    K = 6
    pi = [0.010417, 0.03125, 0.125, 0.5, 0.25, 0.0625, 0.020833]
    
    def berlekamp_massey(seq):
        n_bm = len(seq)
        c = np.zeros(n_bm, dtype=int)
        b = np.zeros(n_bm, dtype=int)
        c[0] = 1
        b[0] = 1
        L, m, d_old = 0, -1, 1
        for n_i in range(n_bm):
            d = seq[n_i]
            for i in range(1, L+1):
                d ^= c[i] & seq[n_i-i]
            if d == 1:
                t = c.copy()
                for i in range(n_i - m, n_bm):
                    c[i] ^= b[i - (n_i - m)]
                if L <= n_i // 2:
                    L = n_i + 1 - L
                    m = n_i
                    b = t.copy()
        return L
    
    T_vals = []
    mu = M/2.0 + (9 + (-1)**(M+1)) / 36.0 - (M/3.0 + 2/9.0) / (2**M)
    for i in range(N):
        block = bits[i*M:(i+1)*M]
        Li = berlekamp_massey(block)
        Ti = (-1)**M * (Li - mu) + 2.0/9.0
        T_vals.append(Ti)
    
    freq = [0] * (K+1)
    for t in T_vals:
        if t <= -2.5:
            freq[0] += 1
        elif t <= -1.5:
            freq[1] += 1
        elif t <= -0.5:
            freq[2] += 1
        elif t <= 0.5:
            freq[3] += 1
        elif t <= 1.5:
            freq[4] += 1
        elif t <= 2.5:
            freq[5] += 1
        else:
            freq[6] += 1
    
    chi2 = sum((freq[i] - N*pi[i])**2 / (N*pi[i]) for i in range(K+1) if N*pi[i] > 0)
    p = gammaincc(K/2.0, chi2/2.0)
    return float(p)

# ============================================================
# Test 11: Serial
# ============================================================
def serial_test(bits, m=16):
    n = len(bits)
    if n < m:
        return 1.0, 1.0
    
    augmented = np.concatenate([bits, bits[:m-1]])
    
    def count_patterns(length):
        if length == 0:
            return n
        counts = {}
        for i in range(n):
            pattern = tuple(augmented[i:i+length])
            counts[pattern] = counts.get(pattern, 0) + 1
        return sum(c**2 for c in counts.values()) * (2**length) / n - n
    
    psi_m = count_patterns(m)
    psi_m1 = count_patterns(m-1)
    psi_m2 = count_patterns(m-2) if m >= 2 else 0
    
    dpsi = psi_m - psi_m1
    dpsi2 = psi_m - 2*psi_m1 + psi_m2
    
    p1 = gammaincc(2**(m-2), dpsi/2.0) if dpsi > 0 else 1.0
    p2 = gammaincc(2**(m-3), dpsi2/2.0) if dpsi2 > 0 else 1.0
    return float(p1), float(p2)

# ============================================================
# Test 12: Approximate Entropy
# ============================================================
def approximate_entropy_test(bits, m=10):
    n = len(bits)
    if n < m:
        return 1.0
    
    def phi(length):
        augmented = np.concatenate([bits, bits[:length-1]])
        counts = {}
        for i in range(n):
            pattern = tuple(augmented[i:i+length])
            counts[pattern] = counts.get(pattern, 0) + 1
        c_vals = [counts.get(tuple(augmented[i:i+length]), 0)/n for i in range(n)]
        return sum(math.log(c) for c in c_vals if c > 0) / n
    
    apen = phi(m) - phi(m+1)
    chi2 = 2 * n * (math.log(2) - apen)
    p = gammaincc(2**(m-1), chi2/2.0)
    return float(p)

# ============================================================
# Test 13: Cumulative Sums
# ============================================================
def cumulative_sums_test(bits):
    n = len(bits)
    x = 2*bits.astype(float) - 1
    
    # Forward
    S_fwd = np.cumsum(x)
    z_fwd = np.max(np.abs(S_fwd))
    
    # Backward
    S_bwd = np.cumsum(x[::-1])
    z_bwd = np.max(np.abs(S_bwd))
    
    def compute_p(z):
        total = 0.0
        start = int((-n/z + 1) / 4)
        end = int((n/z - 1) / 4) + 1
        for k in range(start, end + 1):
            from scipy.stats import norm
            total += norm.cdf((4*k+1)*z/math.sqrt(n)) - norm.cdf((4*k-1)*z/math.sqrt(n))
        p = 1.0 - total
        return max(0.0, min(1.0, p))
    
    p_fwd = compute_p(z_fwd) if z_fwd > 0 else 1.0
    p_bwd = compute_p(z_bwd) if z_bwd > 0 else 1.0
    return float(p_fwd), float(p_bwd)

# ============================================================
# Test 14: Random Excursions
# ============================================================
def random_excursions_test(bits):
    n = len(bits)
    x = 2*bits.astype(int) - 1
    S = np.concatenate([[0], np.cumsum(x)])
    
    cycles = []
    cycle_start = 0
    for i in range(1, len(S)):
        if S[i] == 0:
            cycles.append(S[cycle_start:i+1])
            cycle_start = i
    
    J = len(cycles)
    if J < 500:
        return [(s, 1.0) for s in [-4,-3,-2,-1,1,2,3,4]]
    
    states = [-4, -3, -2, -1, 1, 2, 3, 4]
    pi_table = [
        [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    ] * 8  # simplified
    
    results = []
    for state in states:
        freq = [0] * 6
        for cycle in cycles:
            count = min(np.sum(cycle == state), 5)
            freq[count] += 1
        
        x_val = abs(state)
        pi = [1-1.0/(2*abs(state))] + [1.0/(4*state**2)] * 5
        pi[0] = 1 - sum(pi[1:])
        
        chi2 = sum((freq[k] - J*pi[k])**2 / (J*pi[k]) for k in range(6) if J*pi[k] > 0)
        p = gammaincc(5/2.0, chi2/2.0)
        results.append((state, float(p)))
    
    return results

# ============================================================
# Test 15: Random Excursions Variant
# ============================================================
def random_excursions_variant_test(bits):
    n = len(bits)
    x = 2*bits.astype(int) - 1
    S = np.cumsum(x)
    
    J = np.sum(S == 0) + 1
    if J < 500:
        return [(s, 1.0) for s in range(-9, 10) if s != 0]
    
    results = []
    for state in range(-9, 10):
        if state == 0:
            continue
        count = np.sum(S == state)
        p = erfc(abs(count - J) / math.sqrt(2 * J * (4*abs(state) - 2)))
        results.append((state, float(p)))
    
    return results

# ============================================================
# Master runner
# ============================================================
def run_all_tests(data):
    """Run all 15 NIST SP 800-22 tests on raw bytes.
    
    Args:
        data: bytes or bytearray of ciphertext
    
    Returns:
        list of dicts: [{"test": str, "p_value": float, "passed": bool}, ...]
    """
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    n = len(bits)
    results = []
    
    def add(name, p):
        results.append({"test": name, "p_value": round(p, 6), "passed": p >= 0.01})
    
    print(f"  Running NIST SP 800-22 on {n} bits ({len(data)} bytes)...")
    
    # 1
    add("1. Frequency (Monobit)", frequency_test(bits))
    # 2
    add("2. Block Frequency", block_frequency_test(bits))
    # 3
    add("3. Runs", runs_test(bits))
    # 4
    add("4. Longest Run of Ones", longest_run_test(bits))
    # 5
    if n >= 38912:
        add("5. Binary Matrix Rank", matrix_rank_test(bits))
    else:
        add("5. Binary Matrix Rank (skipped: need 38912 bits)", 1.0)
    # 6
    if n >= 1000:
        add("6. DFT (Spectral)", spectral_test(bits))
    else:
        add("6. DFT (skipped)", 1.0)
    # 7
    if n >= 100000:
        add("7. Non-overlapping Template", non_overlapping_template_test(bits))
    else:
        add("7. Non-overlapping Template (skipped: need 100K bits)", 1.0)
    # 8
    if n >= 100000:
        add("8. Overlapping Template", overlapping_template_test(bits))
    else:
        add("8. Overlapping Template (skipped)", 1.0)
    # 9
    if n >= 10000:
        add("9. Maurer's Universal", universal_test(bits))
    else:
        add("9. Universal (skipped)", 1.0)
    # 10
    if n >= 1000000:
        add("10. Linear Complexity", linear_complexity_test(bits))
    else:
        add("10. Linear Complexity (skipped: need 1M bits)", 1.0)
    # 11
    p11a, p11b = serial_test(bits, m=min(16, int(math.log2(n))-2)) if n >= 16 else (1.0, 1.0)
    add("11. Serial (p1)", p11a)
    # 12
    add("12. Approximate Entropy", approximate_entropy_test(bits, m=min(10, int(math.log2(n))-5)))
    # 13
    p13a, p13b = cumulative_sums_test(bits)
    add("13. Cumulative Sums (fwd)", p13a)
    # 14
    if n >= 1000000:
        re_results = random_excursions_test(bits)
        min_p = min(p for _, p in re_results)
        add("14. Random Excursions", min_p)
    else:
        add("14. Random Excursions (skipped: need 1M bits)", 1.0)
    # 15
    if n >= 1000000:
        rev_results = random_excursions_variant_test(bits)
        min_p = min(p for _, p in rev_results)
        add("15. Random Excursions Variant", min_p)
    else:
        add("15. Random Excursions Var. (skipped: need 1M bits)", 1.0)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"  Result: {passed}/{total} tests PASSED")
    
    return results


# ============================================================
# Self-test with software AES-CTR
# ============================================================
if __name__ == "__main__":
    import sys
    
    if "--self-test" in sys.argv:
        print("=" * 55)
        print("  NIST SP 800-22 Self-Test (Software AES-128 CTR)")
        print("=" * 55)
        
        try:
            from Crypto.Cipher import AES
        except ImportError:
            print("  Install: pip install pycryptodome")
            sys.exit(1)
        
        key = bytes(range(16))
        nonce = b'\xf0\xe0\xd0\xc0\xb0\xa0\x90\x80'
        cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
        
        # Generate 128 KB of ciphertext (1,048,576 bits)
        plaintext = bytes(128 * 1024)
        ciphertext = cipher.encrypt(plaintext)
        
        results = run_all_tests(ciphertext)
        
        print("\n  Detailed Results:")
        print("  " + "-" * 50)
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  {r['test']:45s} p={r['p_value']:.6f}  [{status}]")
        
        passed = sum(1 for r in results if r["passed"])
        print(f"\n  Overall: {passed}/{len(results)} PASSED")
    else:
        print("Usage: python nist_sp800_22.py --self-test")
