from database.db_url_session import Base
from sqlalchemy import (Column, Integer, String, Numeric, ForeignKey, Date, Time, Boolean, UniqueConstraint,
                        func, DateTime, Enum)
from sqlalchemy.orm import relationship

class Schedule(Base):
    __tablename__ = 'schedule'
    
    schedule_id = Column(Integer, primary_key = True, autoincrement = True, nullable = False)
    sync_date = Column(Integer, nullable = True)
    sync_time = Column(Time, nullable = True)
    sync_interval = Column(Time, nullable = True)
    pair_id = Column(Integer, ForeignKey("folder_pair.pair_id"), nullable = False, unique = True)
    
    pairs = relationship('Folder_Pair', back_populates = 'schedule')
    
class Folder_Pair(Base):
    __tablename__ = 'folder_pair'
    
    pair_id = Column(Integer, primary_key = True, autoincrement = True, nullable = False)
    source_folder = Column(String(255), nullable = False)
    replica_folder = Column(String(255), nullable = False)

    sync = relationship('Synchronization', back_populates = 'pairs')
    schedule = relationship('Schedule', back_populates = 'pairs')
    
class Synchronization(Base):
    __tablename__ = 'synchronization'
    
    sync_id = Column(Integer, primary_key = True, autoincrement = True, nullable = False)
    sync_interval = Column(Numeric, nullable = False)
    pair_id = Column(Integer, ForeignKey("folder_pair.pair_id"), nullable = False)
    operation_datetime = Column(DateTime, nullable = False)
    scheduled = Column(Boolean, nullable = False)

    operation = relationship('Operations', back_populates = 'sync')
    pairs = relationship('Folder_Pair', back_populates = 'sync')
    
class Operations (Base):
    __tablename__ = 'operations'
    
    op_id = Column(Integer, primary_key = True, autoincrement = True, nullable = False)
    sync_id = Column(Integer, ForeignKey("synchronization.sync_id"), nullable = False)
    filename = Column(String(255), nullable = False)
    operation_type = Column(Enum('Copy', 'Delete', name = 'type_enum'), nullable = False)

    sync = relationship('Synchronization', back_populates = 'operation')