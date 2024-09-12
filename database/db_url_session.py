from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def set_url():
    url = "sqlite:///./SF_DB/sf_db.db"
    engine = create_engine(url)
    Session = sessionmaker(bind = engine)
    session = Session()
    return session, engine

Base = declarative_base()
session, engine = set_url()

def table_check(engine = engine):
    check = inspect(engine)
    return check

def check_metadata(table: 'str', Base = Base):
    check = table_check()
    if check.has_table(table):
        pass
    else:
        Base.metadata.create_all(engine)
