"""
Remove a previously-ingested PDF's chunks from the vector + keyword
index, without needing to delete and rebuild everything.

Usage:
    cd backend
    python -m scripts.remove_document                  # lists indexed files
    python -m scripts.remove_document booklet_2083.pdf  # removes that file's chunks
"""

import sys

from app.retrieval.vector_store import get_vector_store


def main() -> None:
    store = get_vector_store()

    if len(sys.argv) < 2:
        sources = store.indexed_sources()
        if not sources:
            print("Nothing is indexed yet.")
            return
        print("Indexed files (pass one of these as an argument to remove it):\n")
        for name in sources:
            print(f"  {name}")
        return

    filename = sys.argv[1]
    removed = store.delete_by_source(filename)

    if removed == 0:
        print(f"No chunks found for '{filename}'. Check the exact filename with:")
        print("  python -m scripts.remove_document")
    else:
        print(f"Removed {removed} chunk(s) for '{filename}'.")
        print("Note: this only removes it from the index - the PDF itself is")
        print("still in data/raw/. Delete it there too if you don't want it")
        print("picked up again next time you run scripts.ingest.")


if __name__ == "__main__":
    main()
