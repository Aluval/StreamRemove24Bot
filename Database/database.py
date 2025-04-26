import motor.motor_asyncio
from config import DATABASE_NAME, DATABASE_URI


class Database:
    def __init__(self, uri, database_name):        
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users_col = self.db["users"]    
    
    
    async def update_user_settings(self, user_id, settings):
        await self.users_col.update_one({'id': user_id}, {'$set': {'settings': settings}}, upsert=True)
        
    async def get_user_settings(self, user_id):
        default_settings = {            
            'gdrive_folder_id': None,                              
        }
        user = await self.users_col.find_one({'id': user_id})
        if user:
            return user.get('settings', default_settings)
        return default_settings
          
                
    async def save_gdrive_folder_id(self, user_id, folder_id):
        await self.users_col.update_one({'id': user_id}, {'$set': {'settings.gdrive_folder_id': folder_id}}, upsert=True)
    
    async def get_gdrive_folder_id(self, user_id):
        user = await self.users_col.find_one({'id': user_id})
        if user:
            return user.get('settings', {}).get('gdrive_folder_id')
        return None
     
    async def clear_database(self):
        # Drop all collections
        await self.users_col.drop()
                    
# Initialize the database instance
db = Database(DATABASE_URI, DATABASE_NAME)    
                  
