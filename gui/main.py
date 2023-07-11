from tkinter import *
from tkinter import ttk
from tkinter import font

from dataframe import DatasetFrame

root = Tk()
root.title('Data Loading')
root.geometry("800x800")

font.nametofont("TkDefaultFont").configure(size=15)

notebook = ttk.Notebook(root)
notebook.grid(row=0, column=0, sticky=NSEW)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

dataset_frame = DatasetFrame(notebook, root=root)
category_frame = ttk.Frame(notebook)
relationship_frame = ttk.Frame(notebook)

dataset_frame.grid(row=0, column=0, sticky=NSEW)
category_frame.grid(row=0, column=0, sticky=NSEW)
relationship_frame.grid(row=0, column=0, sticky=NSEW)

notebook.add(dataset_frame, text="Datesets")
notebook.add(category_frame, text="Categories")
notebook.add(relationship_frame, text="Relationships")

root.mainloop()