from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up the connection URL
username = 'smart'
password = 'smart'
host = 'mysql-db'  # The service name defined in the Docker Compose file
port = '3306'
database_name = 'smartiot'
DATABASE_URI = f'mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}'

# Create the engine and session factory
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

class BaseModel:
    def __init__(self):
        self.session = None

    def connect(self):
        self.session = Session()

    def disconnect(self):
        if self.session is not None:
            self.session.close()
            self.session = None