import sys
from pathlib import Path

# Ajouter le parent au path pour importer src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bdd.dbmanager import DBManager

if __name__ == "__main__":
    import asyncio

    async def main():
        db_manager = DBManager()
        
        await db_manager.test_db()
    asyncio.run(main())