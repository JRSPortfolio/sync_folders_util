from sqlalchemy.orm import Session
from database.sf_db_models import Schedule, Operations, Folder_Pair, Synchronization
from database.db_url_session import check_metadata
from datetime import datetime, timedelta

def register_folder_pair(db_session: Session, source: str, replica: str):
    check_metadata('folder_pair')
    folder_pair = Folder_Pair(source_folder = source, replica_folder = replica)
    db_session.add(folder_pair)
    db_session.commit()
    db_session.refresh(folder_pair)
    db_session.close()
    
def check_duplicated_folder_pairs(db_session: Session, source: str, replica: str):
    check_metadata('folder_pair')
    existing_pair = db_session.query(Folder_Pair).filter_by(source_folder = source, replica_folder = replica).value(Folder_Pair.pair_id)
    if existing_pair:
        db_session.close()
        return True
    else:
        db_session.close()
        return False
        
def get_existing_folder_pairs(db_session: Session):
    check_metadata('folder_pair')
    pairs_list = []
    pairs = db_session.query(Folder_Pair.pair_id).all()
    pair_ids = [pair[0] for pair in pairs]
    for pair_id in pair_ids:
        source = db_session.query(Folder_Pair.source_folder).filter_by(pair_id = pair_id).scalar()
        replica = db_session.query(Folder_Pair.replica_folder).filter_by(pair_id = pair_id).scalar()
        pairs_list.append([source, replica])
    db_session.close()
    return pairs_list
    
def set_sync_schedule(db_session: Session, date, time, interval, source: str, replica: str):
    check_metadata('schedule')
    check_metadata('folder_pair')
    
    pair_id = db_session.query(Folder_Pair).filter_by(source_folder = source, replica_folder = replica).value(Folder_Pair.pair_id)
        
    if date is not None and time is not None:
        schedule = Schedule(sync_date = date, sync_time = time, pair_id = pair_id)
    elif date is None and time is not None:
        schedule = Schedule(sync_time = time, pair_id = pair_id)
    elif interval is not None:
        schedule = Schedule(sync_interval = interval, pair_id = pair_id)
    
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    db_session.close()
    
def check_existing_schedule(db_session: Session, source: str, replica: str):
    check_metadata('schedule')
    check_metadata('folder_pair')
    pair_id = db_session.query(Folder_Pair).filter_by(source_folder = source, replica_folder = replica).value(Folder_Pair.pair_id)
    schedule = db_session.query(Schedule).filter_by(pair_id = pair_id).scalar()
    db_session.close()
    if schedule:
        return True
    else:
        return False

def register_operations(db_session: Session, files: dict, sync_id: int):
    check_metadata('operations')
    
    for item in files:
        operation = Operations(sync_id = sync_id, filename = item, operation_type = files[item])
        db_session.add(operation)
        db_session.commit()
        db_session.refresh(operation)
        db_session.close()

def register_synchronization(db_session: Session, source: str, replica: str, scheduled: bool, files: dict):
    check_metadata('folder_pair')
    check_metadata('synchronization')
    
    pair_id = db_session.query(Folder_Pair).filter_by(source_folder = source, replica_folder = replica).value(Folder_Pair.pair_id)
    previous_datetime = db_session.query(Synchronization.operation_datetime).filter_by(pair_id = pair_id).order_by(Synchronization.operation_datetime.desc()).first()
    op_datetime = datetime.now()
    if previous_datetime:
        previous_datetime = previous_datetime[0]
        interval = (op_datetime - previous_datetime).total_seconds()
    else:
        interval = 0
        
    sync = Synchronization(sync_interval = interval, pair_id = pair_id, operation_datetime = op_datetime, scheduled = scheduled)
    db_session.add(sync)
    db_session.commit()
    db_session.refresh(sync)
    
    register_operations(db_session, files, sync.sync_id)
    
    db_session.close()
    
def get_sync_logs(db_session: Session, source: str, replica: str, date: datetime):
    check_metadata('synchronization')
    check_metadata('operations')
    check_metadata('folder_pair')
    
    logs_dict = {'source' : [], 'replica': [], 'file': [], 'operation' : [], 'scheduled' : [], 'interval': []}
    sync_ids = get_sync_ids_from_pair(db_session, source, replica, date)
    
    for sync_id in sync_ids:
        pair_id = db_session.query(Synchronization.pair_id).filter_by(sync_id = sync_id).scalar()
        source_folder = db_session.query(Folder_Pair.source_folder).filter_by(pair_id = pair_id).scalar()
        replica_folder = db_session.query(Folder_Pair.replica_folder).filter_by(pair_id = pair_id).scalar()
        scheduled = db_session.query(Synchronization.scheduled).filter_by(sync_id = sync_id).scalar()
        interval = unpack_interval_time(db_session, sync_id)
        files_and_ops = get_filenames_and_operations_from_sync_id(db_session, sync_id)
        for items in files_and_ops:
            logs_dict['source'].append(source_folder)
            logs_dict['replica'].append(replica_folder)
            logs_dict['file'].append(items[0])
            logs_dict['operation'].append(items[1])
            logs_dict['scheduled'].append(scheduled)
            logs_dict['interval'].append(interval)
    
    db_session.close()
    return logs_dict

def unpack_interval_time(db_session: Session, sync_id):
    check_metadata('synchronization')
    
    interval = float(db_session.query(Synchronization.sync_interval).filter_by(sync_id = sync_id).scalar())
    total_seconds = timedelta(seconds = interval)
    days = total_seconds.days
    hours, remainder = divmod(total_seconds.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f'Days: {days} - Hours: {hours} - Minutes: {minutes} - Seconds: {seconds}'
      
def get_sync_ids_from_pair(db_session: Session, source, replica, date):
    check_metadata('folder_pair')
    check_metadata('synchronization')
    
    if source is None and date is None:
        sync_ids = db_session.query(Synchronization.sync_id).order_by(Synchronization.pair_id.asc(), Synchronization.operation_datetime.asc()).all()
    elif date and source is None:
        sync_ids = db_session.query(Synchronization.sync_id).filter(Synchronization.operation_datetime >= date).order_by(Synchronization.pair_id.asc(), Synchronization.operation_datetime.asc()).all()
    else:
        pair_id = db_session.query(Folder_Pair.pair_id).filter_by(source_folder = source, replica_folder = replica).scalar()
        sync_ids = db_session.query(Synchronization.sync_id).filter_by(pair_id = pair_id).order_by(Synchronization.operation_datetime.asc()).all()
        
    return [sync_id for (sync_id,) in sync_ids]

def get_filenames_and_operations_from_sync_id(db_session: Session, sync_id: int):
    check_metadata('operations')
    check_metadata('synchronization')
    
    results = db_session.query(Operations.filename, Operations.operation_type).filter_by(sync_id = sync_id).all()
    return results

def get_schedules(db_session: Session):
    check_metadata('schedule')
    check_metadata('folder_pair')
    
    schedules_dict = {'source': [], 'replica' : [], 'schedule_type' : [], 'schedule': []}
    
    schedule_ids_query = db_session.query(Schedule.schedule_id).all()
    schedule_ids = [schedule for (schedule,) in schedule_ids_query]
    
    for schedule_id in schedule_ids:
        pair_id = db_session.query(Schedule.pair_id).filter_by(schedule_id = schedule_id).scalar()
        source = db_session.query(Folder_Pair.source_folder).filter_by(pair_id = pair_id).scalar()
        replica = db_session.query(Folder_Pair.replica_folder).filter_by(pair_id = pair_id).scalar()
        
        date = db_session.query(Schedule.sync_date).filter_by(schedule_id = schedule_id).scalar()

        if date:
            time = db_session.query(Schedule.sync_time).filter_by(schedule_id = schedule_id).scalar()
            schedule_type = 'monthly'
            schedule = [date, time]
        else:
            time = db_session.query(Schedule.sync_time).filter_by(schedule_id = schedule_id).scalar()
            if time:
                schedule_type = 'daily'
                schedule = time
            else:
                interval = db_session.query(Schedule.sync_interval).filter_by(schedule_id = schedule_id).scalar()
                schedule_type = 'interval'
                schedule = interval
                
        schedules_dict['source'].append(source)
        schedules_dict['replica'].append(replica)
        schedules_dict['schedule_type'].append(schedule_type)
        schedules_dict['schedule'].append(schedule)
        
    db_session.close()
    return schedules_dict
        
        
    