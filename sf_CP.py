import os
import threading
from sf_GUI import SF_MainWindow
from database.db_url_session import session
from sf_folder_file_actions import (sync_folders, print_message, entry_message, clean_screen, pause, validate_date,
                               validate_time, export_logs_to_txt, export_logs_to_csv, start_sync_schedules)
from database.sf_crud import (check_duplicated_folder_pairs, register_folder_pair, get_existing_folder_pairs,
                              get_sync_logs, get_schedules, set_sync_schedule, check_existing_schedule)
from datetime import datetime
    
def main_menu():
    scheduler = start_sync_schedules()
    
    while True:
        clean_screen()
        print_message('OPTIONS:')
        print_message('1 - Synchronization Folders Options')
        print_message('2 - Synchronization Logs Options')
        print_message('3 - Schedules Options')
        print_message('4 - Synchronize Folders')
        print_message('5 - Launch GUI')
        print_message('C - Close')
        print()
        
        selection = entry_message('Option: ').strip().upper()
        match selection:
            case '1':
                sync_folders_options_menu()
            case '2':
                sync_logs_options_menu()
            case '3':
                schedules_options_menu()
            case '4':
                sync_folders_action_menu()
            case '5':
                launch_GUI()
            case 'C':
                break
            case other:
                print_message(f'{other} is not a valid option.')
                print()
                pause()
                
    scheduler.shutdown()
                
def launch_GUI():
    def run_gui():
        window = SF_MainWindow()
        window.mainloop()
        
    gui_thread = threading.Thread(target = run_gui)
    gui_thread.start()
                
def sync_folders_options_menu():
    while True:
        clean_screen()
        print_message('SYNCHRONAZATION FOLDER OPTIONS:')
        print_message('1 - Register Folder Pair')
        print_message('2 - List Folder Pairs')
        print_message('M - Main Menu')
        print()
        
        selection = entry_message('Option: ').strip().upper()
        match selection:
            case '1':
                option_register_folder_pair()
            case '2':
                list_folder_pairs()
            case 'M':
                break
            case other:
                print_message(f'{other} is not a valid option.')
                print()
                pause()
                
def option_register_folder_pair():
    source = entry_message('Insert Source folder path:\n')
    replica = entry_message('Insert Replica folder path:\n')
    if os.path.isdir(source) and os.path.isdir(replica):
        if not check_duplicated_folder_pairs(session, source, replica):
            register_folder_pair(session, source, replica)
            print_message(f'Registered {source} as Source folder and {replica} as Replica folder')
            print()
            pause()
        else:
            print_message('Folder pair was already registered.')
            print()
            pause()
    else:
        print_message('Inserted an invalid folder path.')
        print()
        pause()

def list_folder_pairs():
    pairs = get_existing_folder_pairs(session)
    for pair in pairs:
        print_message(f'Source: {pair[0]} --- Replica: {pair[1]}')
    pause()
    
def sync_logs_options_menu():
    while True:
        clean_screen()
        print_message('SYNCHRONAZATION LOGS OPTIONS:')
        print_message('1 - List all logs')
        print_message('2 - List logs from a date')
        print_message('3 - List logs of specific pair')
        print_message('4 - List logs from a date and pair')
        print_message('5 - Export logs to file')
        print_message('M - Main Menu')
        print()
        
        selection = entry_message('Option: ').strip().upper()
        match selection:
            case '1':
                list_all_logs()
            case '2':
                list_logs_date()
            case '3':
                list_logs_pair()
            case '4':
                list_logs_pair_date()
            case '5':
                export_logs_menu()
            case 'M':
                break
            case other:
                print_message(f'{other} is not a valid option.')
                print()
                pause()

def print_logs(logs):
    for i in range(len(logs['source'])):
        if logs['scheduled'][i]:
            scheduled = 'Scheduled'
        else:
            scheduled = 'Not Scheduled'
        print_message(f'Source: {logs['source'][i]}  ---  Replica: {logs['replica'][i]}')
        print_message(f'Object: {logs['file'][i]}  --- {logs['operation'][i]}')
        print_message(f'{scheduled} --- Previous Synchronization: {logs['interval'][i]}')
        print()
    pause()
        
def list_all_logs():
    logs = get_sync_logs(session, source = None, replica = None, date = None)
    print_logs(logs)
    
def date_selection_option():
    date_string = entry_message('Insert date (DD/MM/YYYY): ').strip()
    if validate_date(date_string):
        date = datetime.strptime(date_string, '%d/%m/%Y')
        return date
    else:
        print_message('Inserted date was not valid.')
        pause()
        return None
        
def list_logs_date():
    date = date_selection_option()
    if date:
        logs = get_sync_logs(session, source = None, replica = None, date = date)
        print_logs(logs)
        
def pair_selection_option():
    pairs = get_existing_folder_pairs(session)
    print_message('Select the folder pair:')
    
    option_num = 1
    for pair in pairs:
        print_message(f'{option_num} - Source: {pair[0]} --- Replica: {pair[1]}')
        option_num += 1
    
    selection = entry_message('Option: ').strip().upper()

    if selection.isdigit():
        if int(selection) > option_num - 1:
            print_message('Not a valid option.')
            pause()
            return None, None
        else:
            index = int(selection) - 1
            source = pairs[index][0]
            replica = pairs[index][1]
            return source, replica
    else:
        print_message('Not a valid option.')
        pause()
        return None, None
            
def list_logs_pair():
    source, replica = pair_selection_option()
    if source:
        logs = get_sync_logs(session, source = source, replica = replica, date = None)
        print_logs(logs)

def list_logs_pair_date():
    source, replica = pair_selection_option()
    if source:
        date = date_selection_option()
        if date:
            logs = get_sync_logs(session, source = source, replica = replica, date = date)
            print_logs(logs)
    
def sync_folders_action_menu():
    source_path = 'Select folder pair...'
    replica_path = 'Select folder pair...' 
    
    while True:
        clean_screen()
        print_message('SYNCHRONAZATION OPTIONS:')
        print()
        print_message(f'Source: {source_path}')
        print_message(f'Replica: {replica_path}')
        print()
        print_message('1 - Select folder pair')
        print_message('2 - Synchronize folders')
        print_message('M - Main Menu')
        print()
        
        selection = entry_message('Option: ').strip().upper()
        match selection:
            case '1':
                source_path, replica_path = pair_selection_option()
                if source_path == None:
                    source_path = 'Select folder pair...'
                    replica_path = 'Select folder pair...'
                    
            case '2':
                sync_folder_option(source_path, replica_path, session)
            case 'M':
                break
            case other:
                print_message(f'{other} is not a valid option.')
                print()
                pause()
      
def export_logs_menu():
    while True:
        clean_screen()
        print_message('EXPORT LOGS MENU:')
        print_message('1 - Export to txt')
        print_message('2 - Export to csv')
        print_message('P - Previous Menu')
        print()

        selection = entry_message('Option: ').strip().upper()
        match selection:
            case '1':
                export_to_txt()
            case '2':
                export_to_csv()
            case 'P':
                break
            case other:
                print_message(f'{other} is not a valid option.')
                print()
                pause()

def set_logs_filename():
    filename = entry_message('Insert a filename for the log file, if not inserted the log file will be named with current date/time: ').strip()
    if filename == '':
        filename = datetime.now().strftime('%d%m%Y_%H%M')
    return filename

def export_to_txt():
    filename = set_logs_filename()
    export_logs_to_txt(filename)
    print_message(f'Created txt log file named {filename}')
    pause()

def export_to_csv():
    filename = set_logs_filename()
    export_logs_to_csv(filename)
    print_message(f'Created csv log file named {filename}')
    pause()
        

def sync_folder_option(source, replica, session):
    if os.path.isdir(source) and os.path.isdir(replica):
        sync_folders(source, replica, session, scheduled = False)
        print_message(f'Synchronized {replica} with {source}')
        print()
        pause()
    else:
        print_message('No folder pair was selected')
        print()
        pause()
        
def schedules_options_menu():
    while True:
        clean_screen()
        print_message('SCHEDULES MENU:')
        print_message('1 - View schedules')
        print_message('2 - Create new schedule')
        print_message('M - Main Menu')
        print()

        selection = entry_message('Option: ').strip().upper()
        match selection:
            case '1':
                show_schedules()
            case '2':
                create_new_schedule_menu()
            case 'M':
                break
            case other:
                print_message(f'{other} is not a valid option.')
                print()
                pause()

def set_schedule_text(type, schedule):
    if type == 'monthly':
        text = f'Monthly every {schedule[0]} day at {schedule[1].strftime('%H:%M')}'
    elif type == 'daily':
        text = f'Daily at {schedule.strftime('%H:%M')}'
    else:
        text = f'Every {schedule.strftime('%H:%M')}'
    return text
              
def show_schedules():
    schedules = get_schedules(session)
    for i in range(len(schedules['source'])):
        text = set_schedule_text(schedules['schedule_type'][i], schedules['schedule'][i])
        print_message(f'Source: {schedules['source'][i]}')
        print_message(f'Replica: {schedules['replica'][i]}')
        print_message(text)
        print()
    pause()
    
def create_new_schedule_menu():
    while True:
        clean_screen()
        print_message('SET NEW SCHEDULE MENU:')
        print_message('1 - Monthly')
        print_message('2 - Daily')
        print_message('3 - Interval')
        print_message('P - Previous Menu')
        print()

        selection = entry_message('Option: ').strip().upper()
        match selection:
            case '1':
                create_monthly_schedule()
            case '2':
                create_daily_schedule()
            case '3':
                create_interval_schedule()
            case 'P':
                break
            case other:
                print_message(f'{other} is not a valid option.')
                print()
                pause()

def create_monthly_schedule():
    source, replica = pair_selection_option()
    if not check_existing_schedule(session, source, replica):
        day_string = entry_message('Insert the schedule day: ')
        if day_string.isdigit():
            day = int(day_string)
            if day > 0 and day <= 31:
                time_string = entry_message('Insert the shedule time (HH:MM): ').strip()
                if validate_time(time_string):
                    time = datetime.strptime(time_string, '%H:%M').time()
                    set_sync_schedule(session, date = day, time = time, interval = None, source = source, replica = replica)
                    print_message(f'Schedule set for every {day} day at {time}')
                    pause()
                else:
                    print_message('Invalid time')
                    pause()
            else:
                print_message('Invalid day')
                pause()
        else:
            print_message('Invalid day')
            pause()
    else:
        print_message('Schedule already exists for the selected folder pair')
        pause()

def create_daily_schedule():
    source, replica = pair_selection_option()
    if not check_existing_schedule(session, source, replica):
        time_string = entry_message('Insert the shedule time (HH:MM): ').strip()
        if validate_time(time_string):
            time = datetime.strptime(time_string, '%H:%M').time()
            set_sync_schedule(session, date = None, time = time, interval = None, source = source, replica = replica)
            print_message(f'Schedule set everyday at {time}')
            pause()
        else:
            print_message('Invalid time')
            pause()
    else:
        print_message('Schedule already exists for the selected folder pair')
        pause()
        
def create_interval_schedule():
    source, replica = pair_selection_option()
    if not check_existing_schedule(session, source, replica):
        time_string = entry_message('Insert the shedule time (HH:MM): ').strip()
        if validate_time(time_string):
            time = datetime.strptime(time_string, '%H:%M').time()
            set_sync_schedule(session, date = None, time = None, interval = time, source = source, replica = replica)
            print_message(f'Schedule for every {time}')
            pause()
        else:
            print_message('Invalid time')
            pause()
    else:
        print_message('Schedule already exists for the selected folder pair')
        pause()
