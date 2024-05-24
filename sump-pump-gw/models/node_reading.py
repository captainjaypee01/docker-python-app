from sqlalchemy import Column, Integer, String, TIMESTAMP
from models.database import Base

class NodeReading(Base):
    __tablename__ = 'node_readings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    NodeID = Column(String(12), nullable=False)
    payload = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default='CURRENT_TIMESTAMP')