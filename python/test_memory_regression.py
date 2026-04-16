#!/usr/bin/env python3
"""
Simple RSS regression check for repeated classy evaluations.

Usage:
  python3 test_memory_regression.py --n 300 --fail-every 5
"""

import argparse
import resource
import time

from classy import Class, CosmoComputationError


def rss_mb():
    # macOS reports bytes, Linux reports KB for ru_maxrss.
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if raw > 10**10:
        return raw / 1024.0 / 1024.0
    return raw / 1024.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200, help="Number of evaluations")
    parser.add_argument(
        "--fail-every",
        type=int,
        default=0,
        help="Inject a likely-failing point every N iterations (0 disables)",
    )
    args = parser.parse_args()

    base = {
        "output": "tCl,pCl,lCl,mPk",
        "lensing": "yes",
        "modes": "s",
        "h": 0.6736,
        "omega_b": 0.02237,
        "omega_cdm": 0.12,
        "A_s": 2.1e-9,
        "n_s": 0.9649,
        "tau_reio": 0.0544,
        "P_k_max_h/Mpc": 2.0,
        "z_pk": 0.0,
    }

    cosmo = Class()
    t0 = time.time()
    peak = rss_mb()

    for i in range(args.n):
        pars = dict(base)
        pars["log10_G_eff_nu"] = -6.0 + 0.02 * (i % 20)

        if args.fail_every > 0 and i % args.fail_every == 0 and i > 0:
            # Deliberately inconsistent point to stress failure cleanup.
            pars["h"] = -0.7

        cosmo.set(pars)
        status = "ok"
        try:
            cosmo.compute(["lensing"])
        except CosmoComputationError:
            status = "fail"

        current = rss_mb()
        peak = max(peak, current)
        print(f"{i:04d} {status:4s} rss={current:8.2f} MB peak={peak:8.2f} MB")

    cosmo.struct_cleanup()
    dt = time.time() - t0
    print(f"Done: n={args.n}, elapsed={dt:.2f}s, peak_rss={peak:.2f} MB")


if __name__ == "__main__":
    main()

