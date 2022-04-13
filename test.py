with open('storage.json') as f:
    storage = json.load(f)
    
with open('storage.json', 'w') as f:
    json.dump(storage, f)