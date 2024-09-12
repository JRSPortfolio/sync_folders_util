import tkinter as tk
from tkinter import ttk, filedialog
from tkcalendar import Calendar
from datetime import datetime
from sf_folder_file_actions import sync_folders, validate_folder_path, export_logs_to_txt, export_logs_to_csv
from database.sf_crud import (register_folder_pair, check_duplicated_folder_pairs, get_existing_folder_pairs, set_sync_schedule,
                              check_existing_schedule, get_sync_logs, get_schedules)
from database.db_url_session import session

class SF_MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title('Folders Synchronization Utility')
        self.geometry('900x900')
        
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)
        self.grid_rowconfigure(6, weight = 1)
        
        self.set_main_options_layout()
        self.viewing_layout()
        
    def set_main_options_layout(self):
        def update_path_labels(event):
            folder_pairs = get_existing_folder_pairs(session)
            index = self.set_sync_folders_combobox.current()
            self.displayed_source = folder_pairs[index][0]
            self.displayed_replica = folder_pairs[index][1]
            self.selected_source_folder_label.config(text = f'Source: {self.displayed_source}')
            self.selected_replica_folder_label.config(text = f'Replica: {self.displayed_replica}')
        
        pairs = self.get_folder_pairs_description()
                
        self.set_schedule_button = tk.Button(self, text = 'Set Synchronization Schedule', width = 25, height = 2, command = self.set_sync_schedule_layout)
        self.view_schedule_button = tk.Button(self, text = 'View Schedule Synchronization', width = 25, height = 2, command = self.set_view_schedules_layout)
        self.view_logs_button = tk.Button(self, text = 'View Synchronization Logs', width = 25, height = 2, command = self.set_sync_logs_layout)
        self.set_folders_button = tk.Button(self, text = 'Set Synchronization Folders', width = 25, height = 2, command = self.set_source_replica_folders_layout)
        self.sync_button = tk.Button(self, text = 'Synchronize Folders', width = 25, height = 2, command = self.sync_folders_action)
        self.set_sync_folders_combobox = ttk.Combobox(self, values = pairs, width = 30, height = 2)
        self.selected_source_folder_label = tk.Label(self, text = 'Source:', height = 1)
        self.selected_replica_folder_label = tk.Label(self, text = 'Replica:', height = 1)
        
        self.set_schedule_button.grid(row = 0, column = 0, padx = 40, pady = 30)
        self.view_schedule_button.grid(row = 0, column = 1, padx = 40, pady = 10)
        self.view_logs_button.grid(row = 1, column = 0, padx = 40, pady = 10)
        self.set_folders_button.grid(row = 1, column = 1, padx = 40, pady = 10)
        self.sync_button.grid(row = 2, column = 0, pady = 30)
        self.set_sync_folders_combobox.grid(row = 2, column = 1, pady = 10)
        self.selected_source_folder_label.grid(row = 3, column = 0, columnspan = 2, padx = 40)
        self.selected_replica_folder_label.grid(row = 4, column = 0, columnspan = 2, padx = 40)

        self.close_button_canvas = tk.Canvas(self)
        self.close_button = tk.Button(self.close_button_canvas, text = 'Close', width = 25, height = 2, command = self.close_window)
        self.close_button_canvas.grid(row = 6, column = 0, columnspan = 2, padx = 40, pady = 20, sticky = 'S')
        self.close_button.grid(row = 0, column = 0, padx = 40, pady = 0, sticky = 'S')
        
        self.set_sync_folders_combobox.bind("<<ComboboxSelected>>", update_path_labels)
        
    def get_folder_pairs_description(self):
        folder_pairs = get_existing_folder_pairs(session)
        pairs = []
        for pair in folder_pairs:
            pairs.append(f'{pair[0]}|||{pair[1]}')
        return pairs
        
    def sync_folders_action(self):
        if self.set_sync_folders_combobox.get() == '':
            pass
        else:
            sync_folders(self.displayed_source, self.displayed_replica, session, scheduled = False)
            self.set_sync_folders_combobox.set('')    
            self.selected_source_folder_label.config(text = 'Source:')
            self.selected_replica_folder_label.config(text = 'Replica:')
            self.displayed_source = ''
            self.displayed_replica = ''
                 
    def close_window(self):
        self.destroy()
        
    def viewing_layout(self):
        self.viewing_layout_canvas = tk.Canvas(self)
        self.viewing_layout_canvas.grid(row = 5, column = 0, columnspan = 2, padx = 0, pady = (80, 10), sticky = 'nsew')
        self.viewing_layout_canvas.grid_columnconfigure(0, weight = 1)
        
    def clean_viewing_layout(self):
        self.viewing_layout_canvas.destroy()
        self.viewing_layout()
        
    def set_source_replica_folders_layout(self):
        self.clean_viewing_layout()
        
        self.view_paired_folders_button = tk.Button(self.viewing_layout_canvas, text = 'View Paired Folders', width = 20, height = 1, command = self.view_paired_folders_layout)
        self.set_folders_pair_button = tk.Button(self.viewing_layout_canvas, text = 'Set Folders Pair', width = 20, height = 1, command = self.set_folders_pair_layout)
        
        self.view_paired_folders_button.grid(row = 0, column = 0, padx = 40, pady = 20, sticky = "ns")
        self.set_folders_pair_button.grid(row = 1, column = 0, padx = 40, pady = 20, sticky = "ns")
        
    def view_paired_folders_layout(self):
        self.clean_viewing_layout()
        treeview_columns = ('Source Folder', 'Replica Folder')
        
        self.paired_folders_treeview = ttk.Treeview(self.viewing_layout_canvas, columns = treeview_columns, show = 'headings')
        self.paired_folders_treeview.grid(row = 0, column = 0, sticky = 'nsew', padx = 20)
        
        for col in treeview_columns:
            self.paired_folders_treeview.column(col, width = 130, anchor = tk.W)
            
        self.paired_folders_treeview.heading('Source Folder', text = 'Source Folder', anchor = tk.CENTER)
        self.paired_folders_treeview.heading('Replica Folder', text = 'Replica Folder', anchor = tk.CENTER)
        
        pairs = get_existing_folder_pairs(session)
        for pair in pairs:
            self.paired_folders_treeview.insert('', tk.END, values = (pair[0], pair[1]))
        
    def set_folders_pair_layout(self):
        self.clean_viewing_layout()
        for i in range(3):
            self.viewing_layout_canvas.grid_columnconfigure(i, weight = 1)
        
        self.set_folders_pair_layout_source_label = tk.Label(self.viewing_layout_canvas, text = 'Source:', width = 8)
        self.set_folders_pair_layout_replica_label = tk.Label(self.viewing_layout_canvas, text = 'Replica:', width = 8)
        self.set_folders_pair_layout_source_entry = tk.Entry(self.viewing_layout_canvas, width = 50)
        self.set_folders_pair_layout_replica_entry = tk.Entry(self.viewing_layout_canvas, width = 50)
        self.set_folders_pair_layout_source_button = tk.Button(self.viewing_layout_canvas, text = 'Search', width = 8, command = self.select_source_folder_path)
        self.set_folders_pair_layout_replica_button = tk.Button(self.viewing_layout_canvas, text = 'Search', width = 8, command = self.select_replica_folder_path)
        self.set_folders_pair_layout_select_button = tk.Button(self.viewing_layout_canvas, text = 'Select', width = 8, command = self.register_folders_pair_in_db)
        
        self.set_folders_pair_layout_source_label.grid(row = 0, column = 0, padx = 5, pady = 10)
        self.set_folders_pair_layout_source_entry.grid(row = 0, column = 1, padx = 5, pady = 10)
        self.set_folders_pair_layout_source_button.grid(row = 0, column = 2, padx = 5, pady = 10)
        self.set_folders_pair_layout_replica_label.grid(row = 1, column = 0, padx = 5, pady = 10)
        self.set_folders_pair_layout_replica_entry.grid(row = 1, column = 1, padx = 5, pady = 10)
        self.set_folders_pair_layout_replica_button.grid(row = 1, column = 2, padx = 5, pady = 10)
        self.set_folders_pair_layout_select_button.grid(row = 2, column = 1, pady = 20)

    def open_file_explorer(self):
        path = filedialog.askdirectory(title = 'Select Directory')
        return path
    
    def select_source_folder_path(self):
        self.selected_source_path = self.open_file_explorer()
        self.set_folders_pair_layout_source_entry.insert(0, self.selected_source_path)
    
    def select_replica_folder_path(self):
        self.selected_replica_path = self.open_file_explorer()
        self.set_folders_pair_layout_replica_entry.insert(0, self.selected_replica_path)
    
    def validate_folder_paths(self, source: str, replica: str):
        if validate_folder_path(source) == False:
            title = f'Invalid {source} path'
            message = f'The path for {source} in not valid.'
            self.set_message_window(title, message)
            self.set_folders_pair_layout_source_entry.delete(0, 'end')
            return False
        if validate_folder_path(replica) == False:
            title = f'Invalid {replica} path'
            message = f'The path for {replica} in not valid.'
            self.set_message_window(title, message)
            self.set_folders_pair_layout_replica_entry.delete(0, 'end')
            return False
        else:
            return True
        
    def set_message_window(self, title: str, message: str):
        def close_invalid_folder_message():
            self.message_window.destroy()
        
        self.message_window = tk.Toplevel(self)
        self.message_window.title(title)
        
        self.message_window_label = tk.Label(self.message_window, text = message)
        self.message_window_button = tk.Button(self.message_window, text = 'Close', command = close_invalid_folder_message)
        
        self.message_window_label.pack()
        self.message_window_button.pack(pady = 20)
            
    def register_folders_pair_in_db(self):
        source = self.set_folders_pair_layout_source_entry.get()
        replica = self.set_folders_pair_layout_replica_entry.get()
        if self.validate_folder_paths(source, replica):
            if check_duplicated_folder_pairs(session, source, replica):
                title = 'Existing folder pair'
                message = f'Already existist a folder pair with {source} as Source folder and\n{replica} as Replica folder'
                self.set_message_window(title, message)
                self.set_folders_pair_layout_source_entry.delete(0, 'end')
                self.set_folders_pair_layout_replica_entry.delete(0, 'end')
            else:
                title = 'Folder pair registered'
                message = f'Registered folder pair of {source} as Source folder and\n{replica} as Replica folder'
                register_folder_pair(session, source, replica)
                self.set_message_window(title, message)
                self.set_folders_pair_layout_source_entry.delete(0, 'end')
                self.set_folders_pair_layout_replica_entry.delete(0, 'end')
        
        self.update_pairs_combobox()
                
    def update_pairs_combobox(self):
        pairs = self.get_folder_pairs_description()  
        self.set_sync_folders_combobox['values'] = pairs
        
    def set_sync_schedule_layout(self):
        self.clean_viewing_layout()
        
        folder_pairs = get_existing_folder_pairs(session)
        pairs = []
        for pair in folder_pairs:
            pairs.append(f'{pair[0]}|||{pair[1]}')
        
        for i in range(3):
            self.viewing_layout_canvas.grid_columnconfigure(i, weight = 1)
        
        self.daily_checkbox_var = tk.IntVar()
        self.interval_checkbox_var = tk.IntVar()
        
        self.set_schedule_daily_checkbutton = tk.Checkbutton(self.viewing_layout_canvas, text = 'Daily', variable = self.daily_checkbox_var,
                                                          command = self.daily_checkbutton_state)
        self.set_schedule_interval_checkbutton = tk.Checkbutton(self.viewing_layout_canvas, text = 'Time Interval',variable = self.interval_checkbox_var,
                                                             command = self.interval_checkbutton_state)
        self.set_schedule_date_label = tk.Label(self.viewing_layout_canvas, text = 'Date:', width = 8)
        self.set_schedule_date_entry = tk.Entry(self.viewing_layout_canvas, width = 14)
        self.set_schedule_date_button = tk.Button(self.viewing_layout_canvas, text = 'Search', width = 8, command = self.set_sync_schedule_date)
        self.set_schedule_time_label = tk.Label(self.viewing_layout_canvas, text = 'Time:', width = 8)
        self.set_schedule_time_frame = tk.Frame(self.viewing_layout_canvas, width = 10)
        self.set_schedule_hour_spinbox = tk.Spinbox(self.set_schedule_time_frame, from_ = 0, to = 23, width = 2)
        self.set_schedule_separator_label = tk.Label(self.set_schedule_time_frame, text= ' : ', width = 2)
        self.set_schedule_minute_spinbox = tk.Spinbox(self.set_schedule_time_frame, from_ = 0, to = 59, width = 2)
        self.set_schedule_folders_combobox_label = tk.Label(self.viewing_layout_canvas, text = 'Source|||Replica:', width = 12)
        self.set_schedule_folders_combobox = ttk.Combobox(self.viewing_layout_canvas, values = pairs, width = 100)
        self.set_schedule_select_button = tk.Button(self.viewing_layout_canvas, text = 'Select', width = 10, height = 2, command = self.set_sync_schedule)
        
        self.set_schedule_daily_checkbutton.grid(row = 0, column = 0, pady = 5)
        self.set_schedule_interval_checkbutton.grid(row = 0, column = 1, pady = 5)
        self.set_schedule_date_label.grid(row = 1, column = 0, pady = 5)
        self.set_schedule_date_entry.grid(row = 1, column = 1, pady = 5)
        self.set_schedule_date_button.grid(row = 1, column = 2, pady = 5, sticky = 'w')
        self.set_schedule_time_label.grid(row = 2, column = 0, pady = 5)
        self.set_schedule_time_frame.grid(row = 2, column = 1, pady = 5)
        self.set_schedule_hour_spinbox.pack(side = tk.LEFT)
        self.set_schedule_separator_label.pack(side = tk.LEFT)
        self.set_schedule_minute_spinbox.pack(side = tk.LEFT)
        self.set_schedule_folders_combobox_label.grid(row = 3, column = 0, pady = 5)
        self.set_schedule_folders_combobox.grid(row = 3, column = 1, columnspan = 3, pady = 5)
        self.set_schedule_select_button.grid(row = 4, column = 1, columnspan = 3, pady = 20)
        
        self.set_schedule_date_entry.insert(0, 'DD/MM/YYYY')
        
    def set_sync_schedule(self):
        daily_status = self.daily_checkbox_var.get()
        interval_status = self.interval_checkbox_var.get()
        if daily_status == 0 and interval_status == 0:
            string_date = self.set_schedule_date_entry.get()
            date = datetime.strptime(string_date, '%d/%m/%Y').day
        else:
            date = None
        string_time = f'{self.set_schedule_hour_spinbox.get()}:{self.set_schedule_minute_spinbox.get()}'
        time = datetime.strptime(string_time, '%H:%M').time()
        source = self.set_schedule_folders_combobox.get().split('|||')[0]
        replica = self.set_schedule_folders_combobox.get().split('|||')[1]
        
        if check_existing_schedule(session, source, replica):
            title = 'Existing Schedule'
            message = f'Already exists a synchronization schedule for the folders\nSource: {source}\nReplica: {replica}'
            self.set_message_window(title, message)
            self.clean_schedule_layout()
        else:
            if daily_status == 0 and interval_status == 0:
                interval = None
            elif daily_status == 1:
                interval = None
            elif interval_status == 1:
                interval = time
                time = None
            set_sync_schedule(session, date, time, interval, source, replica)
            title = 'Schedule Registered'
            message = f'Registered synchronization schedule for the folders\nSource: {source}\nReplica: {replica}'
            self.set_message_window(title, message)
            self.clean_schedule_layout()
            
    def set_sync_schedule_date(self):
        self.display_calendar_window(self.get_sync_schedule_date)
        
    def display_calendar_window(self, date_type):        
        self.calendar_window = tk.Toplevel(self)
        self.calendar_window.title('Select Date')
        
        self.select_date_calendar = Calendar(self.calendar_window, selectmode = 'day', year = datetime.today().date().year,
                                             month = datetime.today().date().month, day = datetime.today().date().day)
        self.select_date_calendar_button = tk.Button(self.calendar_window, text = 'Select', width = 8, command = date_type)
        
        self.select_date_calendar.pack(padx = 30, pady = 10)
        self.select_date_calendar_button.pack(pady = 10)
    
    def get_sync_schedule_date(self):
        self.set_schedule_date_entry.delete(0, 'end')
        calendar_date = self.select_date_calendar.get_date()
        date = datetime.strptime(calendar_date, '%m/%d/%y')
        return_date = date.strftime('%d/%m/%Y')
        
        self.set_schedule_date_entry.insert(0, return_date)
        self.calendar_window.destroy()
        
    def schedule_date_change_states(self):
        if self.daily_checkbox_var.get() == 1 or self.interval_checkbox_var.get() == 1:
            self.set_schedule_date_label.config(state = 'disabled')
            self.set_schedule_date_entry.config(state = 'disabled')
            self.set_schedule_date_button.config(state = 'disabled')
            
        if self.daily_checkbox_var.get() == 0 and self.interval_checkbox_var.get() == 0:
            self.set_schedule_date_label.config(state = 'normal')
            self.set_schedule_date_entry.config(state = 'normal')
            self.set_schedule_date_button.config(state = 'normal')
            
    def daily_checkbutton_state(self):
        if self.daily_checkbox_var.get() == 1:
            self.interval_checkbox_var.set(0)
        self.schedule_date_change_states()
    
    def interval_checkbutton_state(self):
        if self.interval_checkbox_var.get() == 1:
            self.daily_checkbox_var.set(0)
        self.schedule_date_change_states()
        
    def clean_schedule_layout(self):
        self.daily_checkbox_var.set(0)
        self.interval_checkbox_var.set(0)
        self.set_schedule_date_entry.delete(0, 'end')
        self.set_schedule_date_entry.insert(0, 'DD/MM/YYYY')
        self.set_schedule_hour_spinbox.delete(0, tk.END)
        self.set_schedule_hour_spinbox.insert(0, 0)
        self.set_schedule_minute_spinbox.delete(0, tk.END)
        self.set_schedule_minute_spinbox.insert(0, 0)
        self.set_schedule_folders_combobox.set('')
        self.schedule_date_change_states()
    
    def set_sync_logs_layout(self):
        self.clean_viewing_layout()
        
        pairs = self.get_folder_pairs_description()
            
        self.logs_options_layout_canvas = tk.Canvas(self.viewing_layout_canvas)
        self.logs_options_layout_canvas.grid(row = 0, column = 0, sticky = 'n')
        
        self.logs_export_layout_canvas = tk.Canvas(self.viewing_layout_canvas)
        self.logs_export_layout_canvas.grid(row = 2, column = 0, sticky = 's')
        
        self.all_logs_checkbox_var = tk.IntVar()
        
        self.show_all_logs_checkbutton = tk.Checkbutton(self.logs_options_layout_canvas, text = 'All Logs', variable = self.all_logs_checkbox_var,
                                                          command = self.all_logs_checkbutton_state)
        self.folder_pair_logs_selection = ttk.Combobox(self.logs_options_layout_canvas, values = pairs, width = 100)
        self.logs_date_entry = tk.Entry(self.logs_options_layout_canvas, width = 14)
        self.logs_chose_date_button = tk.Button(self.logs_options_layout_canvas, text = 'Date', command = self.set_viewing_logs_date)
        self.logs_viewing_button = tk.Button(self.logs_options_layout_canvas, text = 'Display', command = self.display_logs_in_treeview)
        
        self.logs_filetype_combobox_label = tk.Label(self.logs_export_layout_canvas, text = 'Log filetype: ', width = 12)
        self.logs_filetype_combobox = ttk.Combobox(self.logs_export_layout_canvas, values = ['txt', 'csv'], width = 14)
        self.logs_export_filename_label = tk.Label(self.logs_export_layout_canvas, text = 'Log filename (Blank for default)', width = 25)
        self.logs_export_filename_entry = tk.Entry(self.logs_export_layout_canvas, width = 14)
        self.logs_export_button = tk.Button(self.logs_export_layout_canvas, text = 'Export Logs to file', command = self.export_logs_to_file)
        
        self.show_all_logs_checkbutton.grid(row = 0, column = 0, padx = 5, pady = 5)
        self.folder_pair_logs_selection.grid(row = 0, column = 1, padx = 5, pady = 5)
        self.logs_date_entry.grid(row = 0, column = 2, padx = 5, pady = 5)
        self.logs_chose_date_button.grid(row = 0, column = 3, padx = 5, pady = 5)
        self.logs_viewing_button.grid(row = 1, column = 1, pady = (2, 20))
        
        self.logs_filetype_combobox_label.grid(row = 0, column = 0, padx = (50, 5) , pady = 30)
        self.logs_filetype_combobox.grid(row = 0, column = 1, padx = (5, 50), pady = 30)
        self.logs_export_filename_label.grid(row = 0, column = 2, padx = (50, 5), pady = 30)
        self.logs_export_filename_entry.grid(row = 0, column = 3, padx = (5, 50), pady = 30)
        self.logs_export_button.grid(row = 0, column = 4, padx = (50, 50), pady = 30)
        
        self.logs_date_entry.insert(0, 'DD/MM/YYYY')
        
        self.set_log_viewing_treeview()
        
    def export_logs_to_file(self):
        filename = self.logs_export_filename_entry.get().strip()
        if filename == '':
            filename = datetime.now().strftime('%d%m%Y_%H%M')
        
        filetype = self.logs_filetype_combobox.get()
        
        if filetype == 'txt':
            export_logs_to_txt(filename)
            title = 'Log file created'
            message = f'Created log file named {filename}.txt'
            self.set_message_window(title, message)
        elif filetype == 'csv':
            export_logs_to_csv(filename)
            title = 'Log file created'
            message = f'Created log file named {filename}.csv'
            self.set_message_window(title, message)
        else:
            title = 'No file type selected'
            message = 'No file type was selected'
            self.set_message_window(title, message)
            
            
        self.logs_export_filename_entry.delete(0, 'end')
        
    def set_log_viewing_treeview(self):
        treeview_columns = ('Source', 'Replica', 'File', 'Operation', 'Scheduled')
        
        self.log_viewing_treeview = ttk.Treeview(self.viewing_layout_canvas, columns = treeview_columns, show = 'headings')
        self.log_viewing_treeview.grid(row = 1, column = 0, sticky = 'nsew')
        
        for col in treeview_columns[:3]:
            self.log_viewing_treeview.heading(col, text = col, anchor = tk.CENTER)
            self.log_viewing_treeview.column(col, width = 200, anchor = tk.W)
            
        for col in treeview_columns[3:]:
            self.log_viewing_treeview.heading(col, text = col, anchor = tk.CENTER)
            self.log_viewing_treeview.column(col, width = 50, anchor = tk.CENTER)
                          
    def display_logs_in_treeview(self):
        self.log_viewing_treeview.destroy()
        self.set_log_viewing_treeview()
        
        string_date = self.logs_date_entry.get()
        try:
            date = datetime.strptime(string_date, '%d/%m/%Y').date()
        except:
            date = None

        if self.all_logs_checkbox_var.get() == 1:
            logs = get_sync_logs(session, source = None, replica = None, date = None)
        elif date and self.folder_pair_logs_selection.get() != '':
            source = self.folder_pair_logs_selection.get().split('|||')[0]
            replica = self.folder_pair_logs_selection.get().split('|||')[1]
            logs = get_sync_logs(session, source, replica, date)
        elif self.folder_pair_logs_selection.get() != '':
            source = self.folder_pair_logs_selection.get().split('|||')[0]
            replica = self.folder_pair_logs_selection.get().split('|||')[1]
            logs = get_sync_logs(session, source, replica, date = None)
        elif date:
            logs = get_sync_logs(session, source = None, replica = None, date = date)
        else:
            logs = 0
        
        if logs != 0:
            for row in range(len(logs['source'])):
                self.log_viewing_treeview.insert('', tk.END, values = (logs['source'][row], logs['replica'][row], logs['file'][row], logs['operation'][row], logs['scheduled'][row]))
            
    def all_logs_checkbutton_state(self):
        if self.all_logs_checkbox_var.get() == 1:
            self.folder_pair_logs_selection.config(state = 'disabled')
            self.logs_date_entry.config(state = 'disabled')
            self.logs_chose_date_button.config(state = 'disabled')
            self.logs_date_entry.delete(0, 'end')
            self.logs_date_entry.insert(0, 'DD/MM/YYYY')
            
        if self.all_logs_checkbox_var.get() == 0:
            self.folder_pair_logs_selection.config(state = 'normal')
            self.logs_date_entry.config(state = 'normal')
            self.logs_chose_date_button.config(state = 'normal')
            self.logs_date_entry.delete(0, 'end')
            self.logs_date_entry.insert(0, 'DD/MM/YYYY')
            
    def set_viewing_logs_date(self):
        self.display_calendar_window(self.get_viewing_logs_date)
    
    def get_viewing_logs_date(self):
        self.logs_date_entry.delete(0, 'end')
        calendar_date = self.select_date_calendar.get_date()
        date = datetime.strptime(calendar_date, '%m/%d/%y')
        return_date = date.strftime('%d/%m/%Y')
        
        self.logs_date_entry.insert(0, return_date)
        self.calendar_window.destroy()
    
    def set_view_schedules_layout(self):
        def set_schedule_label(type, schedule):
            if type == 'monthly':
                text = f'Monthly every {schedule[0]} day at {schedule[1].strftime('%H:%M')}'
            elif type == 'daily':
                text = f'Daily at {schedule.strftime('%H:%M')}'
            else:
                text = f'Every {schedule.strftime('%H:%M')}'
            return text
            
        self.clean_viewing_layout()
        schedules = get_schedules(session)
        
        for i in range(len(schedules['source'])):
            schedule_label_text = set_schedule_label(schedules['schedule_type'][i], schedules['schedule'][i])
            source_label = tk.Label(self.viewing_layout_canvas, text = f'Source: {schedules['source'][i]}')
            replica_label = tk.Label(self.viewing_layout_canvas, text = f'Replica: {schedules['replica'][i]}')
            schedule_label = tk.Label(self.viewing_layout_canvas, text = schedule_label_text)
            separator = ttk.Separator(self.viewing_layout_canvas, orient = 'horizontal')
            
            source_label.pack(pady = 0)
            replica_label.pack(pady = 0)
            schedule_label.pack(pady = 0)
            separator.pack(fill = 'x', pady = 1)