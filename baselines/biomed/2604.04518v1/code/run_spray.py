"""Run SpRAy group-label derivation for multiple datasets/layers.

Usage:
    python run_spray.py <dataset> <poison> <layer>
"""
import sys

from spray import main

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
