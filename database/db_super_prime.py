import motor.motor_asyncio
from config import DB_URI, DB_NAME
from pytz import timezone
from datetime import datetime, timedelta
import logging

# Create an async client with Motor
dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
super_prime_collection = database['super-prime-users']

# Configure logging for super prime operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if the user is a super prime user
async def is_super_prime_user(user_id):
    user = await super_prime_collection.find_one({"user_id": user_id})
    return user is not None

# Add super prime user
async def add_super_prime(user_id, duration_days):
    try:
        # Define IST timezone
        ist = timezone("Asia/Kolkata")
        
        # Calculate expiration time
        current_time = datetime.now(ist)
        expiration_time = current_time + timedelta(days=duration_days)
        
        # Create user document
        user_doc = {
            "user_id": user_id,
            "granted_timestamp": current_time.isoformat(),
            "expiration_timestamp": expiration_time.isoformat(),
            "duration_days": duration_days
        }
        
        # Check if user already exists
        existing = await super_prime_collection.find_one({"user_id": user_id})
        if existing:
            # Update existing user
            await super_prime_collection.update_one(
                {"user_id": user_id}, 
                {"$set": user_doc}
            )
            logger.info(f"Updated super prime for user: {user_id} for {duration_days} days")
        else:
            # Insert new user
            await super_prime_collection.insert_one(user_doc)
            logger.info(f"Added super prime for user: {user_id} for {duration_days} days")
        
        return True
    except Exception as e:
        logger.error(f"Error adding super prime user {user_id}: {e}")
        return False

# Remove super prime user
async def remove_super_prime(user_id):
    result = await super_prime_collection.delete_one({"user_id": user_id})
    if result.deleted_count > 0:
        logger.info(f"Super prime removed for user: {user_id}")
    return result.deleted_count > 0

# Remove expired super prime users
async def remove_expired_super_prime_users():
    try:
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        removed_count = 0

        async for user in super_prime_collection.find({}):
            user_id = user.get("user_id")
            expiration = user.get("expiration_timestamp")
            
            if not expiration or not user_id:
                await super_prime_collection.delete_one({"user_id": user_id})
                logger.warning(f"Removed invalid super prime entry for user: {user_id}")
                removed_count += 1
                continue

            try:
                expiration_time = datetime.fromisoformat(expiration).astimezone(ist)
                if expiration_time <= current_time:
                    await super_prime_collection.delete_one({"user_id": user_id})
                    logger.info(f"Auto-removed expired super prime user: {user_id}")
                    removed_count += 1
            except Exception as e:
                logger.error(f"Error processing super prime user {user_id}: {e}")
                await super_prime_collection.delete_one({"user_id": user_id})
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Super prime cleanup completed: {removed_count} expired users removed")
        
        return removed_count
    except Exception as e:
        logger.error(f"Error in remove_expired_super_prime_users: {e}")
        return 0

# List all super prime users
async def list_super_prime_users():
    try:
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        super_prime_users = super_prime_collection.find({})
        super_prime_user_list = []

        async for user in super_prime_users:
            user_id = user.get("user_id")
            granted_time = user.get("granted_timestamp")
            expiration_time = user.get("expiration_timestamp")
            duration_days = user.get("duration_days", 0)
            
            if expiration_time and user_id:
                try:
                    exp_time = datetime.fromisoformat(expiration_time).astimezone(ist)
                    granted_time_dt = datetime.fromisoformat(granted_time).astimezone(ist) if granted_time else None
                    
                    time_left = exp_time - current_time
                    days_left = max(0, time_left.days)
                    
                    super_prime_user_list.append({
                        'user_id': user_id,
                        'granted_time': granted_time_dt,
                        'expiration_time': exp_time,
                        'duration_days': duration_days,
                        'days_left': days_left,
                        'is_active': exp_time > current_time
                    })
                except Exception as e:
                    logger.error(f"Error processing super prime user {user_id}: {e}")
        
        return super_prime_user_list
    except Exception as e:
        logger.error(f"Error listing super prime users: {e}")
        return []

# Get super prime user details
async def get_super_prime_details(user_id):
    try:
        user = await super_prime_collection.find_one({"user_id": user_id})
        if not user:
            return None
        
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
        granted_time = datetime.fromisoformat(user["granted_timestamp"]).astimezone(ist)
        
        time_left = expiration_time - current_time
        days_left = max(0, time_left.days)
        
        return {
            'user_id': user_id,
            'granted_time': granted_time,
            'expiration_time': expiration_time,
            'duration_days': user.get("duration_days", 0),
            'days_left': days_left,
            'is_active': expiration_time > current_time
        }
    except Exception as e:
        logger.error(f"Error getting super prime details for {user_id}: {e}")
        return None
