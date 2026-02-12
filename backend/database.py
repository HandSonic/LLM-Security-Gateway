from sqlmodel import SQLModel, create_engine
from sqlmodel.pool import StaticPool

sqlite_file_name = "gateway.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
