import json

def load_library():
    with open("data/library_books.json", "r") as f:
        return json.load(f)

def search_books(keyword):
    library = load_library()
    results = [book for book in library if keyword.lower() in book["title"].lower()]
    return results if results else "No books found."
