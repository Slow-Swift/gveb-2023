import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from tkinter import *
from tkinter import ttk

from data_wrangler import Category

from scrollableframe import ScrollableFrame

class CategoryFrame(ttk.Frame):
    
    def __init__(self, parent, root, get_datasets, action_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.root = root
        self.action_manager = action_manager
        parent.bind("<<NotebookTabChanged>>", lambda e: self.on_tab_switched())
        
        self.categories = {}
        self.current_category = None
        self.get_datasets = get_datasets
        
        toolbar = ttk.Frame(self, borderwidth=5, relief="solid")
        category_setup = ttk.Frame(self, borderwidth=5, relief="solid")
        toolbar.grid(row=0, column=0, sticky=NSEW)
        category_setup.grid(row=1, column=0, sticky=NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self.selected_category_name = StringVar()
        self.category_name = StringVar()
        self.dataset_name = StringVar()
        
        self.category_dropdown = ttk.Combobox(toolbar, state='readonly', textvariable=self.selected_category_name, values=["- Add Category -"])
        self.category_dropdown.grid(row=0, column=0)
        self.category_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_category_selected())
        
        ttk.Button(toolbar, text="Delete Category", command=self.delete_category).grid(row=0, column=1)
        
        ttk.Label(category_setup, text="Category name:").grid(row=0, column=0, sticky=W)
        ttk.Label(category_setup, text="Dataset:").grid(row=1, column=0, sticky=W)
        name_entry = ttk.Entry(category_setup, textvariable=self.category_name)
        name_entry.bind("<Return>", self.update_category)
        name_entry.bind("<FocusOut>", self.update_category)
        self.dataset_dropdown = ttk.Combobox(category_setup, state='readonly', textvariable=self.dataset_name, values=[])
        self.dataset_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_category())
        ttk.Button(category_setup, text="Add Property", command=self.add_property).grid(row=2, column=0)
        
        name_entry.grid(row=0, column=1, sticky=W)
        self.dataset_dropdown.grid(row=1, column=1, sticky=W)
        
        self.property_frame = ScrollableFrame(category_setup)
        self.property_frame.grid(row=3, column=0, sticky=NSEW)
        category_setup.rowconfigure(3, weight=1)
        
    def on_tab_switched(self):
        self.update_dataset_dropdown()
        self.update_properties_display()
    
    def update_properties_display(self):
        for child in self.property_frame.frame.winfo_children():
            child.destroy()
            
        if not self.current_category: return
            
        primary_key = None
        fieldnames = self.current_category.data.get_fieldnames()
        if self.current_category.data:
            primary_key = self.current_category.data.primary_key
            ttk.Label(self.property_frame.frame, text=primary_key).grid(row=0, column=0, sticky=W)
            
        for i, property_name in enumerate(self.current_category.property_names):
            if property_name == primary_key: continue
            text = property_name
            if property_name not in fieldnames:
                text = f"(Missing) {property_name}"
            ttk.Label(self.property_frame.frame, text=text).grid(row=i+1, column=0, sticky=W)
            ttk.Button(self.property_frame.frame, text="Delete", command=(lambda p: lambda: self.delete_property(p))(property_name)).grid(row=i+1, column=1)
            
    def delete_property(self, property_name):
        self.current_category.property_names.remove(property_name)
        self.update_properties_display()
        
    def update_dataset_dropdown(self):
        self.dataset_dropdown.configure(values=list(self.get_datasets().keys()))
            
    def update_category_options(self):
        self.category_dropdown.configure(values=list(self.categories.keys()) + ["- Add Category -"])
        if self.current_category == None:
            self.selected_category_name.set('')
        else:
            self.selected_category_name.set(self.current_category.name)
        
    def update_category(self, e=None):
        category_name = self.category_name.get()
        dataset = self.get_datasets()[self.dataset_name.get()] if self.dataset_name.get() else None
        if self.current_category:
            if self.current_category.name != category_name and category_name in self.categories: return
            if self.current_category.name != category_name and category_name.strip():
                del self.categories[self.current_category.name]
                self.categories[category_name] = self.current_category
                self.current_category.name = category_name
                self.update_category_options()
            if dataset != self.current_category.data:  
                if self.current_category.data:
                    self.current_category.property_names.remove(self.current_category.data.primary_key)
                self.current_category.property_names.append(dataset.primary_key)
                self.current_category.data = dataset
                self.update_properties_display()
        else:
            if not category_name.strip(): return
            if category_name in self.categories: return
            
            self.current_category = Category(category_name, dataset, [dataset.primary_key] if dataset else [])
            self.action_manager.add_category(self.current_category)
            self.categories[category_name] = self.current_category
            self.update_category_options()
            
    def clear_category(self):
        self.category_name.set("")
        self.dataset_name.set("")
        self.current_category = None
        self.update_properties_display()
        
    def on_category_selected(self):
        if self.selected_category_name.get() == "- Add Category -":
            self.clear_category()
        else:
            datasets = self.get_datasets()
            self.current_category = self.categories[self.selected_category_name.get()]
            dataset_name = [key for key in datasets if datasets[key] == self.current_category.data]
            dataset_name = dataset_name[0] if len(dataset_name) > 0 else ""
            
            self.category_name.set(self.current_category.name)
            self.dataset_name.set(dataset_name)
            self.update_properties_display()
            
    def delete_category(self):
        self.action_manager.delete_category(self.current_category)
        del self.categories[self.current_category.name]
        self.clear_category()
        self.update_category_options()
    
    def add_property(self):
        if not self.current_category: return
        if not self.current_category.data: return
        
        properties = list(set(self.current_category.data.get_fieldnames()).difference(self.current_category.property_names))
        if len(properties) == 0: return
        
        add_property_dialog = Toplevel()
        add_property_frame = ttk.Frame(add_property_dialog, padding=8)
        add_property_frame.grid(row=0, column=0, sticky=NSEW)
        add_property_dialog.columnconfigure(0, weight=1)
        add_property_dialog.rowconfigure(0, weight=1)
        
        property_name = StringVar()
        def on_done():
            self.current_category.property_names.append(property_name.get())
            self.update_properties_display()
            add_property_dialog.destroy()
            
        ttk.Label(add_property_frame, text="Add Property").grid(row=0, column=0, columnspan=2, sticky=EW)
        ttk.Combobox(add_property_frame, textvariable=property_name, values=properties).grid(row=1, column=0, columnspan=2)
        ttk.Button(add_property_frame, text="Cancel", command=add_property_dialog.destroy).grid(row=2, column=0)
        ttk.Button(add_property_frame, text="Done", command=on_done).grid(row=2, column=1)
        
        for child in add_property_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)
            
        add_property_dialog.update_idletasks()
        x = self.root.winfo_x() + int(self.root.winfo_width() / 2 - add_property_dialog.winfo_width() / 2)
        y = self.root.winfo_y() + int(self.root.winfo_height() / 2 - add_property_dialog.winfo_height() / 2)
        add_property_dialog.geometry(f"+{x}+{y}")