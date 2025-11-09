import argparse
from src.doc_hub.core.incremental_indexer import IncrementalIndexer
from src.doc_hub.core.duplicate_detector import DuplicateDetector

def main():
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+")
    p.add_argument("--drop-removed", action="store_true")
    p.add_argument("--find-duplicates", action="store_true")
    args = p.parse_args()
    idx = IncrementalIndexer(args.paths)
    idx.reindex()
    if args.drop_removed:
        idx.drop_removed()
    if args.find_duplicates:
        dd = DuplicateDetector(args.paths)
        out_path, groups = dd.find_duplicates()
        print("Duplicate report:", out_path, "groups:", groups)

if __name__ == "__main__":
    main()
