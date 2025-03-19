from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import create_engine, Column, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List
import uvicorn
import json
import os

# Database connection (PostgreSQL on Neon/Railway)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Message model
class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, index=True)
    group_name = Column(String, index=True)
    email = Column(String, index=True)
    message = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Store message in DB
@app.post("/send_message/")
def send_message(group_name: str, email: str, message: str, db: Session = Depends(get_db)):
    new_message = Message(group_name=group_name, email=email, message=message)
    db.add(new_message)
    db.commit()
    return {"status": "Message sent!"}

# Get messages for a group
@app.get("/messages/{group_name}", response_model=List[str])
def get_messages(group_name: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.group_name == group_name).all()
    return [m.message for m in messages]

# WebSocket for real-time chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{group_name}")
async def websocket_endpoint(websocket: WebSocket, group_name: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{group_name}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Run server locally
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

