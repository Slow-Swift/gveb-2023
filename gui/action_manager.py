import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from data_wrangler import Dataset
from data_wrangler import Category

from loader import Action

class ActionManager():
    
    def __init__(self, get_datasets):
        self.lines = []
        self.actions = []
        self.categories : list[Category] = []
        self.get_datasets = get_datasets
    
    def add_dataset(self, name, filename, delimiter):
        if ' ' in filename:
            filename = f'"{filename}"'
            
        new_action = f"Dataset {name} {filename} -delimiter {delimiter}"
        self.actions.append(new_action)
        self.lines.append(new_action)
        
    def add_category(self, category: Category):
        self.categories.append(category)
        
    def delete_category(self, category):
        self.categories.remove(category)
        
    def delete_dataset(self, name):
        self.actions.append(f"Drop {name}")
        
    def add_action(self, dataset_name, action, *args):
        new_action = f"Action {dataset_name} {action} {' '.join(args)}"
        self.actions.append(new_action)
        self.lines.append(new_action)
        
    def apply_actions(self):
        datasets = {}
        for line in self.actions:
            parts = line.split()
            match parts[0]:
                case "Dataset":
                    name = parts[1]
                    datasets[name] = self.load_dataset(parts)
                case "Drop":
                    name = parts[1]
                    if name in datasets:
                        del datasets[name]
                case "Action":
                    name = parts[1]
                    if name not in datasets:
                        print(f"ERROR: Dataset not loaded: {name}")
                        continue
                    Action(*parts[2:]).apply(datasets[name])
                case _:
                    print(f"ERROR: Invalid line: {line}")
        return datasets
                    
    def load_dataset(self, parts):
        # Get the filename
        filename = parts[2]
        if filename.startswith('"'):
            for i in range(3, len(parts)):
                filename += ' ' + parts[i]
                if filename.endswith('"'):
                    filename.strip('"')
                    break
          
        # Get the delimiter
        delimiter = ','
        if '-delimiter' in parts:
            delimiter = parts[parts.index('-delimiter') + 1]
        dataset = Dataset.load_file(filename, delimiter=delimiter, use_literal_eval=True)
        return dataset
    
    def save_categories(self, file):
        datasets = self.get_datasets()
        for category in self.categories:
            dataset_name = [key for key in datasets if datasets[key] == self.current_category.data]
            properties = ' '.join(category.property_names)
            file.write(f"Category {category.name} {dataset_name} {properties}")
        
    def load_file(self, filename):
        with open(filename) as f:
            for line in f:
                self.lines.append(line)
                
                line = line.strip()
                if not line: continue
                if line.startswith("//"): continue
                if '//' in line:
                    line = line[:line.index('//')]
                self.actions.append(line)
        
    def save_actions(self, filename):
        with open(filename, 'w', newline='\n') as f:
            f.writelines(action + '\n' for action in self.actions)
            self.save_categories(f)