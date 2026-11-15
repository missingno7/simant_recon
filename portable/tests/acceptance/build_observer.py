"""Build the pinned ideal-v1 DOS observer in a fresh output directory."""
import argparse
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--contract',choices=('ideal-v1',),default='ideal-v1')
    args=parser.parse_args()
    try:
        from .ideal_build import build
    except ImportError:
        from ideal_build import build
    return build(args.out)

if __name__=='__main__':main()
