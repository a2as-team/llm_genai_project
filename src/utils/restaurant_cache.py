"""
Restaurant cache singleton for storing restaurant configuration.

Loads restaurant hours and capacity once at startup to avoid
repeated database queries when generating the system prompt.
"""

class RestaurantCache:
    """
    Singleton cache for restaurant configuration.
    
    Stores:
    - Opening hours (lunch/dinner)
    - Maximum capacity (sum of all table capacities)
    
    Must be initialized once at app startup via `await RestaurantCache.initialize()`.
    """
    
    _initialized: bool = False
    _hours: dict = {
                "lunch_open": "11h30",
                "lunch_close": "14h30", 
                "dinner_open": "18h30",
                "dinner_close": "23h00"
            }
    _max_capacity: int = 0
    
    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize the cache by loading data from database.
        
        Should be called once at application startup.
        """
        if cls._initialized:
            return
        
        from src.bdd.dbmanager import DBManager
        
        db = DBManager()
        cls._hours = await db.get_restaurant_hours()
        cls._max_capacity = await db.get_max_capacity()
        cls._initialized = True
        
        print(f"🏪 RestaurantCache initialized:")
        print(f"   - Hours: {cls._hours}")
        print(f"   - Max capacity: {cls._max_capacity} personnes")
    
    @classmethod
    def get_hours(cls) -> dict :
        """
        Get restaurant opening hours.
        
        Returns:
            dict with keys: lunch_open, lunch_close, dinner_open, dinner_close
        """
        if not cls._initialized:
            # Fallback values if not initialized
            return cls._hours
        return cls._hours
    
    @classmethod
    def get_max_capacity(cls) -> int:
        """
        Get maximum restaurant capacity (sum of all tables).
        
        Returns:
            int: Maximum number of guests
        """
        if not cls._initialized:
            return 10  # Fallback
        return cls._max_capacity
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if cache has been initialized."""
        return cls._initialized
    
    @classmethod
    def reset(cls) -> None:
        """Reset cache (useful for testing)."""
        cls._initialized = False
        cls._hours = {
            "lunch_open": "11h30",
            "lunch_close": "14h30", 
            "dinner_open": "18h30",
            "dinner_close": "23h00"
        }
        cls._max_capacity = 0
