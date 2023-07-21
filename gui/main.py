from tkinter import *
from tkinter import ttk
from tkinter import font

from dataframe import DatasetFrame
from categoryframe import CategoryFrame

from action_manager import ActionManager

_get_datasets = lambda: []
get_datasets = lambda: _get_datasets()

action_manager = ActionManager(get_datasets)
action_manager.load_file("cleanup.txt")
datasets = action_manager.apply_actions()

root = Tk()
root.title('Data Loading')
root.geometry("800x800")

font.nametofont("TkDefaultFont").configure(size=15)

notebook = ttk.Notebook(root)
notebook.grid(row=0, column=0, sticky=NSEW)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

dataset_frame = DatasetFrame(notebook, root, datasets, action_manager)
_get_datasets = dataset_frame.get_datasets
category_frame = CategoryFrame(notebook, root, get_datasets)
relationship_frame = ttk.Frame(notebook)

dataset_frame.grid(row=0, column=0, sticky=NSEW)
category_frame.grid(row=0, column=0, sticky=NSEW)
relationship_frame.grid(row=0, column=0, sticky=NSEW)

notebook.add(dataset_frame, text="Datesets")
notebook.add(category_frame, text="Categories")
notebook.add(relationship_frame, text="Relationships")

root.mainloop()

action_manager.save_actions("cleanup.txt")