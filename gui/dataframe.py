import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from data_wrangler import Dataset

from confirm_dialog import ConfirmDialog


class DatasetFrame(ttk.Frame):
    
    def __init__(self, parent, root, datasets, action_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.action_manager = action_manager
        self.datasets = datasets
        self.root = root
        
        self.selected_dataset_name = StringVar()
        self.selected_dataset = None
        
        toolbar = ttk.Frame(self, borderwidth=5, relief="solid")
        dataframe = ttk.Frame(self, borderwidth=5, relief="solid")
        toolbar.grid(row=0, column=0, sticky=NSEW)
        dataframe.grid(row=1, column=0, sticky=NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        dataframe.columnconfigure(0, weight=1)
        dataframe.rowconfigure(0, weight=1)
        s = ttk.Style()
        s.configure("Treeview", rowheight=30)
        s.configure("Treeview.Heading", font=('TkDefaultFont',18))
        
        ttk.Button(toolbar, text="Add Dataset", command=self.add_dataset_clicked).grid(row=0,column=0)
        self.datasetDropdown = ttk.Combobox(toolbar, state="readonly", textvariable=self.selected_dataset_name, values=[])
        self.datasetDropdown.grid(row=0, column=1)
        self.datasetDropdown.bind("<<ComboboxSelected>>", lambda e: self.dataset_selected())
        self.delete_dataset_btn = ttk.Button(toolbar, text="Delete Dataset", command=self.delete_dataset)
        self.delete_dataset_btn.grid(row=0, column=3)
        self.update_delete_dataset_btn()
        
        self.table = ttk.Treeview(dataframe, show="headings", columns=[], height=15)
        self.table.grid(row=0, column=0, sticky=NSEW)
        
        self.tableVScroll = ttk.Scrollbar(dataframe, orient=VERTICAL, command=self.table.yview)
        self.tableVScroll.grid(row=0, column=1, sticky=NS)
        
        self.tableHScroll = ttk.Scrollbar(dataframe, orient=HORIZONTAL, command=self.table.xview)
        self.tableHScroll.grid(row=1, column=0, sticky=EW)
        
        self.table.configure(yscrollcommand=self.tableVScroll.set)
        self.table.configure(xscrollcommand=self.tableHScroll.set)
        self.table.bind("<ButtonPress-3>", self.on_table_right_clicked)
        
        self.header_menu = Menu(self)
        
        self.update_dataset_options()
        
    def get_datasets(self):
        return self.datasets
        
    def update_header_menu(self):
        column_name = self.columns[self.selected_column_index]
        
        self.header_menu.delete(0, END)
        self.header_menu.add_command(label="Rename Column", command=self.rename_column)
        
        if column_name != self.selected_dataset.primary_key:
            self.header_menu.add_command(label="Delete Column", command=self.delete_column)
            self.header_menu.add_command(label="Set Primary Key", command=self.set_primary_key)
        
        self.header_menu.add_command(label="Change Type", command=self.change_column_type)
        
    def update_delete_dataset_btn(self):
        if self.selected_dataset:
            self.delete_dataset_btn.state(['!disabled'])
        else:
            self.delete_dataset_btn.state(['disabled'])
            
    def change_column_type(self):
        column_index = self.selected_column_index
        type_dialog = Toplevel()
        type_frame = ttk.Frame(type_dialog, padding=8)
        type_frame.grid(row=0, column=0, sticky=NSEW)
        type_dialog.columnconfigure(0, weight=1)
        type_dialog.rowconfigure(0, weight=1)
        
        type_variable = StringVar()
        def on_done():
            type_dialog.destroy()
            type_conversion = {'int': int, 'float': float, 'str': str, 'bool': bool}[type_variable.get()]
            if self.selected_dataset.try_convert_property(self.columns[column_index], type_conversion):
                self.dataset_selected()
            self.action_manager.add_action(self.selected_dataset_name.get(), "convert", self.columns[column_index], type_variable.get())
            type_dialog.destroy()
            
        type_variable.set(str(self.selected_dataset.get_types()[column_index]).split("'")[1])
        values = ['int', 'float', 'str', 'bool']
        type_dropdown = ttk.Combobox(type_frame, state="readonly", textvariable=type_variable, values=values)
        type_dropdown.grid(row=0, column=0, columnspan=2, sticky=EW)
        
        ttk.Button(type_frame, text="Cancel", command=type_dialog.destroy).grid(row=1, column=0)
        ttk.Button(type_frame, text="Done", command=on_done).grid(row=1, column=1)
            
        for child in type_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)
            
        type_dialog.update_idletasks()
        x = self.root.winfo_x() + int(self.root.winfo_width() / 2 - type_dialog.winfo_width() / 2)
        y = self.root.winfo_y() + int(self.root.winfo_height() / 2 - type_dialog.winfo_height() / 2)
        type_dialog.geometry(f"+{x}+{y}")
            
    def clear_dataset_display(self):
        self.selected_dataset = None
        self.selected_dataset_name.set('')
        
        for row in self.table.get_children():
            self.table.delete(row)
            
        self.table.configure(columns=[])
        
    def update_dataset_options(self):
        self.datasetDropdown.configure(values=list(self.datasets.keys()))
        
    def on_table_right_clicked(self, e):
        if not self.selected_dataset: return
        
        self.selected_column_index = int(self.table.identify_column(e.x)[1:]) - 1
        row_name = self.table.identify_row(e.y)
        if row_name:
            self.selected_row_index = int(row_name) - 1
        else:
            self.selected_row_index = -2
            
        if self.table.identify_region(e.x, e.y) == "heading" or self.selected_row_index == -1:
            self.update_header_menu()
            self.header_menu.post(e.x_root, e.y_root)
        
            
    def set_primary_key(self):
        self.action_manager.add_action(self.selected_dataset_name.get(), "set_primary_key", self.columns[self.selected_column_index])
        self.selected_dataset.set_primary_key(self.columns[self.selected_column_index])
        self.dataset_selected()
            
    def update_columns(self):
        self.table.configure(columns=self.columns)
        for column in self.columns:
            self.table.column(column, width=200, minwidth=200, stretch=True)
            self.table.heading(column, text=f'{column}')
        
    def dataset_selected(self):
        self.selected_dataset = self.datasets[self.selected_dataset_name.get()]
        self.columns = self.selected_dataset.get_fieldnames()
        
        for row in self.table.get_children():
            self.table.delete(row)
        
        self.update_columns()
            
        type_names = [str(t).split("'")[1] for t in self.selected_dataset.get_types()]
        id = 0
        self.table.insert('', END, id=id, values=type_names, tags=('types'))
        for row in self.selected_dataset:
            id += 1
            self.table.insert('', END, id=id, values=[row[key] for key in self.columns])
            
    def rename_column(self):
        rename_dialog = Toplevel()
        rename_frame = ttk.Frame(rename_dialog, padding=8)
        rename_frame.grid(row=0, column=0, sticky=NSEW)
        rename_dialog.columnconfigure(0, weight=1)
        rename_dialog.rowconfigure(0, weight=1)
        
        name = StringVar(value=self.columns[self.selected_column_index])
        def on_done_rename():
            old_columns = self.columns.copy()
            old_columns.pop(self.selected_column_index)
            if name.get() in old_columns: return
            
            self.action_manager.add_action(self.selected_dataset_name.get(), "rename", self.columns[self.selected_column_index], name.get())
            self.selected_dataset.rename(self.columns[self.selected_column_index], name.get())
            self.columns[self.selected_column_index] = name.get()
            self.update_columns()
            rename_dialog.destroy()
        
        ttk.Label(rename_frame, text="Rename Column", anchor='center').grid(row=0, column=0, columnspan=2, sticky=EW)
        ttk.Entry(rename_frame, textvariable=name).grid(row=1, column=0, columnspan=2)
        ttk.Button(rename_frame, text="Cancel", command=rename_dialog.destroy).grid(row=3, column=0)
        ttk.Button(rename_frame, text="Done", command=on_done_rename).grid(row=3, column=1)
            
        for child in rename_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)
            
        rename_dialog.update_idletasks()
        x = self.root.winfo_x() + int(self.root.winfo_width() / 2 - rename_dialog.winfo_width() / 2)
        y = self.root.winfo_y() + int(self.root.winfo_height() / 2 - rename_dialog.winfo_height() / 2)
        rename_dialog.geometry(f"+{x}+{y}")
    
    def delete_column(self):
        column_name = self.columns[self.selected_column_index]
        self.selected_dataset.drop(self.columns[self.selected_column_index])    
        self.action_manager.add_action(self.selected_dataset_name.get(), "drop", column_name)
        self.dataset_selected()
        
    def delete_dataset(self):
        dataset_name = self.selected_dataset_name.get()
        def on_delete_confirmed():
            del self.datasets[dataset_name]
            self.action_manager.delete_dataset(dataset_name)
            
            if len(self.datasets) == 0:
                self.clear_dataset_display()
            else:
                self.selected_dataset_name.set(next(iter(self.datasets)))
                self.dataset_selected()
                
            self.update_dataset_options()
        
        ConfirmDialog(f"Are you sure you want to delete {dataset_name}?", on_delete_confirmed, self.root)
        
    def add_dataset_clicked(self):
        filename = filedialog.askopenfilename(title="Select CSV File", filetypes=[('csv files', '*.csv')])
        if filename and filename.endswith('.csv'):
            with open(filename, encoding='utf-8-sig') as f:
                line = f.readline()
                
            popup = Toplevel()
            popup_frame = ttk.Frame(popup, padding=8)
            popup_frame.grid(row=0, column=0, sticky=(N, W, E, S))
            popup.columnconfigure(0, weight=1)
            popup.rowconfigure(0, weight=1)
            
            name = StringVar(value=filename.split('/')[-1].split('.')[0].capitalize())
            delimiter = StringVar(value=',')
            
            def on_delimiter_selected():
                if name.get() in self.datasets:
                    return
                
                popup.destroy()
                dataset = Dataset.load_file(filename, delimiter=delimiter.get(), use_literal_eval=True)
                if not dataset:
                    print("Could not load dataset")
                    return
                
                self.action_manager.add_dataset(name.get(), filename, delimiter.get())
                self.datasets[name.get()] = dataset
                self.update_dataset_options()
                self.selected_dataset_name.set(name.get())
                self.dataset_selected()
                self.update_delete_dataset_btn()
                
            ttk.Label(popup_frame, text="Name: ", anchor=E).grid(row=0, column=0, sticky=E)
            ttk.Entry(popup_frame, width=5, textvariable=name).grid(row=0, column=1, sticky=EW)
            ttk.Label(popup_frame, text="Delimiter: ", anchor='e').grid(row=1, column=0, sticky=EW)
            ttk.Entry(popup_frame, width=5, textvariable=delimiter).grid(row=1, column=1, sticky=W)
            ttk.Label(popup_frame, text=f"Sample Line: {line[:65]}", wraplength=300).grid(row=2, column=0, columnspan=2)
            ttk.Button(popup_frame, text="Cancel", command=popup.destroy).grid(row=3, column=0)
            ttk.Button(popup_frame, text="Done", command=on_delimiter_selected).grid(row=3, column=1)
            
            for child in popup_frame.winfo_children():
                child.grid_configure(padx=5, pady=5)
            
            popup.update_idletasks()
            x = self.root.winfo_x() + int(self.root.winfo_width() / 2 - popup.winfo_width() / 2)
            y = self.root.winfo_y() + int(self.root.winfo_height() / 2 - popup.winfo_height() / 2)
            popup.geometry(f"+{x}+{y}")
