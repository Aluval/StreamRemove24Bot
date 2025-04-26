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


    async def save_screenshots_count(self, user_id, screenshots_count):
        await self.users_col.update_one(
            {'id': user_id},
            {'$set': {'settings.screenshots_count': screenshots_count}},
            upsert=True
        )
    
    async def get_screenshots_count(self, user_id):
        user = await self.users_col.find_one({'id': user_id})
        if user:
            return user.get('settings', {}).get('screenshots_count')
        return None
    
    async def get_sample_video_duration(self, user_id):
        user = await self.users_col.find_one({'id': user_id})
        if user:
            return user.get('settings', {}).get('sample_video_duration')
        return None
    
    async def save_thumbnail(self, user_id, file_id):
        await self.files_col.update_one({'id': user_id}, {'$set': {'thumbnail_file_id': file_id}}, upsert=True)
        
    async def get_thumbnail(self, user_id):
        file_data = await self.files_col.find_one({'id': user_id})
        if file_data:
            return file_data.get('thumbnail_file_id')
        return None
    
    async def delete_thumbnail(self, user_id):
        await self.files_col.update_one({'id': user_id}, {'$unset': {'thumbnail_file_id': ""}})

    async def save_screenshot_paths(self, user_id, screenshot_paths):
        result = await self.users_col.update_one(
            {'_id': user_id},
            {'$set': {'screenshot_paths': screenshot_paths}},
            upsert=True
        )
        return result

    async def get_screenshot_paths(self, user_id):
        user = await self.users_col.find_one({'_id': user_id})
        if user:
            return user.get('screenshot_paths', [])
        return []

    async def delete_screenshot_paths(self, user_id):
        result = await self.users_col.update_one(
            {'_id': user_id},
            {'$unset': {'screenshot_paths': ''}}
        )
        return result.modified_count > 0
        
# Initialize the database instance
db = Database(DATABASE_URI, DATABASE_NAME)    
                  
