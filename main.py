# run_all_scrapers.py
import asyncio
import os
# Import the main functions from each scraper script
from Amazon_disque_dur import main as main_category1
from Amazon_ordinateurs import main as main_category2
from Amazone_moniteurs import main as main_category3
from Amazone_smartphone import main as main_category4

try:
    MY_SECRET_TOKEN = os.environ["MY_SECRET_TOKEN"]
except KeyError:
    MY_SECRET_TOKEN = "Token not available!"

async def run_all_scrapers():
    # Run all the scrapers one by one
    print("Starting all scrapers...")
    await main_category1()
    await main_category2()
    await main_category3()
    await main_category4()


if __name__ == "__main__":
    asyncio.run(run_all_scrapers())
