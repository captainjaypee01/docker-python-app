from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from database import BaseModel

Base = declarative_base()

class Node(Base, BaseModel):
    __tablename__ = 'node_details'

    id = Column(Integer, primary_key=True)
    network_id = Column(String(10))
    node_id = Column(String(10))
    area_id = Column(String(10))
    config = Column(String(10))
    node_type = Column(String(100))
    status = Column(String(50))
    node_name = Column(String(255))
    postal_code = Column(String(255))
    building_name = Column(String(255))
    building_level = Column(String(255))
    sector_name = Column(String(255))
    application_code = Column(String(255))
    application_type = Column(String(255))

    def __init__(self) -> None:
        Base.__init__(self)
        BaseModel.__init__(self)
        
        pass

    def save(self):
        pass

    @staticmethod
    def get_node_by_nodeid(session, node_id):
        # Add the necessary logic to retrieve the user by email
        # This is just a placeholder implementation
        node = session.query(Node).filter_by(node_id=node_id).first()
        return node