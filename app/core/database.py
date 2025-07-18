from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.user import User
from app.models.stock import Stock, StockPrice
from app.models.chat import ChatHistory

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database() -> AsyncIOMotorClient:
    return db.client

async def init_database():
    try:
        # Create Motor client
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
        )
        
        # Test the connection
        await db.client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        db.database = db.client[settings.DATABASE_NAME]
        
        # Initialize Beanie with all document models
        await init_beanie(
            database=db.database,
            document_models=[User, Stock, StockPrice, ChatHistory]
        )
        
        print(f"✅ Connected to MongoDB database: {settings.DATABASE_NAME}")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise

async def close_database():
    if db.client:
        db.client.close()
        print("MongoDB connection closed")