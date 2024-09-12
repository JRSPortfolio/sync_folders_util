import os
import sys
import subprocess
import shutil
import csv
from apscheduler.schedulers.background import BackgroundScheduler
import functools
from datetime import datetime
from database.sf_crud import register_synchronization, get_schedules, get_sync_logs
from database.db_url_session import session

def print_message(*args, indentation = 5):
    print(' ' * indentation, *args)
        
def entry_message(msg: str, indentation = 5):
    return input(f'{" " * indentation}{msg}')
    
def clean_screen():
    if sys.platform == 'win32':
        subprocess.run(['cls'], shell = True, check = True)
    elif sys.platform in ('darwin', 'linux', 'bsd', 'unix'):
        subprocess.run(['clear'], check = True)

def pause():
    input('Press Enter to continue...')

def sync_folders(source: str, replica: str, session, scheduled: bool):
    source_content = os.listdir(source)
    replica_content = os.listdir(replica)
    file_actions = {}
    
    print()
    for content in source_content:
        if content not in replica_content:
            content_path = os.path.join(source, content)
            if os.path.isdir(content_path):
                shutil.copytree(content_path, os.path.join(replica, content))
            else:
                shutil.copy(content_path, replica)
            file_actions[content_path] = 'Copy'
            print_operation_to_CP(content_path, operation = 'Copied')
            
    for content in replica_content:
        if content not in source_content:
            content_path = os.path.join(replica, content)
            if os.path.isdir(content_path):
                shutil.rmtree(content_path, os.path.join(replica, content))
            else:
                os.remove(content_path)
            file_actions[content_path] = 'Delete'
            print_operation_to_CP(content_path, operation = 'Deleted')
    
    register_synchronization(session, source, replica, scheduled, file_actions)
    
def print_operation_to_CP(path, operation):
    print_message(f'{operation} {path}')
                
def validate_folder_path(path: str):
    if os.path.isdir(path):
        return True
    else:
        return False

def validate_date(date: str):
    try:
        datetime.strptime(date, '%d/%m/%Y')
        return True
    except:
        return False
    
def validate_time(time: str):
    try:
        datetime.strptime(time, '%H:%M')
        return True
    except:
        return False
 
def export_logs_to_txt(filename: str):
    logs = get_sync_logs(session, source = None, replica = None, date = None)
    with open(f'logs/{filename}.txt', 'w') as logfile:
        for i in range(len(logs['source'])):
            if logs['scheduled'][i]:
                scheduled = 'Scheduled'
            else:
                scheduled = 'Not Scheduled'
            logfile.write(f'Source: {logs['source'][i]}  ---  Replica: {logs['replica'][i]}\n')
            logfile.write(f'Object: {logs['file'][i]}  --- {logs['operation'][i]}\n')
            logfile.write(f'{scheduled} --- Previous Synchronization: {logs['interval'][i]}\n')
            logfile.write('\n')

def export_logs_to_csv(filename: str):
    logs = get_sync_logs(session, source = None, replica = None, date = None)
    with open(f'logs/{filename}.csv', 'w', newline = '') as logfile:
        csv_writer = csv.writer(logfile)
        csv_writer.writerow(['Source', 'Replica', 'Object', 'Operation', 'Scheduled', 'Previous Synchronization'])
        for i in range(len(logs['source'])):
            csv_writer.writerow([logs['source'][i], logs['replica'][i], logs['file'][i], logs['operation'][i], logs['scheduled'][i], logs['interval'][i]])
    
def start_sync_schedules():
    schedules = get_schedules(session)
    scheduler = BackgroundScheduler()
    
    for i in range(len(schedules['source'])):
        job = functools.partial(sync_folders, schedules['source'][i], schedules['replica'][i], session, scheduled = True)
        schedule_type = schedules['schedule_type'][i]
        if schedule_type == 'monthly':
            scheduler.add_job(job, 'cron', day = schedules['schedule'][i][0], hour = schedules['schedule'][i][1].hour, minute = schedules['schedule'][i][1].minute)
        elif schedule_type == 'daily':
            scheduler.add_job(job, 'cron', hour = schedules['schedule'][i].hour, minute = schedules['schedule'][i].minute)
        else:
            minutes = (schedules['schedule'][i].hour * 60) + schedules['schedule'][i].minute
            
            scheduler.add_job(job, 'interval', minutes = minutes)

    scheduler.start()
    return scheduler