import csv

# Load the stores
stores = {}
with open('../data/storefronts-inventory.csv', 'r', encoding='utf-8-sig') as stores_in:
    store_rows = csv.DictReader(stores_in,quoting=csv.QUOTE_MINIMAL, delimiter=';')
    
    fieldnames = store_rows.fieldnames
    for store_row in store_rows:
        sid = int(store_row['ID'])
        if sid in stores:
            old_year = int(stores[sid]['Year recorded'])
            new_year = int(store_row['Year recorded'])
            
            if (new_year > old_year):
                stores[sid] = store_row
        else:
            stores[sid] = store_row
        

        
with open('../data/storefronts-inventory_new.csv', 'w', newline='', encoding='utf-8-sig') as streetOutput:
    writer = csv.DictWriter(f=streetOutput, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL) # type: ignore
    writer.writeheader()
    writer.writerows(list(stores.values()))