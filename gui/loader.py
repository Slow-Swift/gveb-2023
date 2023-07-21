import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from data_wrangler import Dataset

class Action():
    
    methods = {
        "drop": Dataset.drop,
        "rename": Dataset.rename,
        "set_primary_key": Dataset.set_primary_key,
        "convert": Dataset.convert_property
    }
    
    types = {
        'int': int,
        'float': float,
        'str': str,
        'bool': bool
    }
    
    def __init__(self, action_name, *args):
        if action_name not in Action.methods: return
        self._method = Action.methods[action_name]
        self._args = list(args)
        
        if action_name == "convert":
            self._args[1] = Action.types[self._args[1]]
        
    
    def apply(self, dataset):
        self._method(dataset, *self._args)

# def load(filename):
#     datasets = {}
    
#     with open(filename) as f:
#         for line in f:
#             line = line.strip()
#             if not line: continue
#             if line.startswith("//"): continue
            
#             if '//' in line:
#                 line = line[:line.index('//')]
#             parts = line.split()
            
#             match parts[0]:
#                 case "Dataset":
#                     name = parts[1]
#                     datasets[name] = load_dataset(parts)
#                 case "Action":
#                     name = parts[1]
#                     if name not in datasets:
#                         print(f"ERROR: Dataset not loaded: {name}")
#                         continue
#                     Action(*parts[2:]).apply(datasets[name])
#                 case _:
#                     print(f"ERROR: Invalid line: {line}")
#     return datasets
                    
# def load_dataset(parts):
#     # Get the filename
#     filename = parts[2]
#     if filename.startswith('"'):
#         for i in range(3, len(parts)):
#             filename += ' ' + parts[i]
#             if filename.endswith('"'):
#                 filename.strip('"')
#                 break
            
#     # Get the delimiter
#     delimiter = ','
#     if '-delimiter' in parts:
#         delimiter = parts[parts.index('-delimiter') + 1]
#     dataset = Dataset.load_file(filename, delimiter=delimiter, use_literal_eval=True)
#     return dataset
                    
# datasets = load('cleanup.txt')
# print(datasets["Junctions"].get_fieldnames())
# print(datasets["Junctions"].get_types())