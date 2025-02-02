import httpx
import csv
import traceback
import asyncio
import os
from lxml import html
from datetime import datetime
from RotateUserAgent import RotateUserAgent  

TARGET_HREFS = 100
# Ensure the DATA folder exists
os.makedirs("DATA", exist_ok=True)

headers = {
    "user-agent": "Mozilla/5.0 (Linux; Android 9; AFTWMST22 Build/PS7233; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/88.0.4324.152 Mobile Safari/537.36",
    "accept-language": "en-GB,en;q=0.7",
    "origin": "https://www.amazon.com",
    "referer": "https://www.amazon.com/",
}

# Ensure the user agents are loaded
RotateUserAgent.load_user_agents()

# Initialize the headers with a dynamic user-agent
def get_dynamic_headers():
    user_agent = RotateUserAgent.get_random()  # Get a random user agent
    return {
        "user-agent": user_agent,
        "accept-language": "en-GB,en;q=0.7",
    }

class Product:
    product_id = 1
    def __init__(self, website, category, asin, title, price, brand, model_name, hard_drive, memory_ram,screen_resolution, color, link):
        self.id = Product.product_id
        self.website = website
        self.category = category
        self.asin = asin
        self.title = title
        self.price = price
        self.brand = brand
        self.model_name = model_name
        self.hard_drive = hard_drive
        self.ram = memory_ram
        self.screen_resolution = screen_resolution
        self.color = color
        self.link = link
        
        Product.product_id += 1

    def to_dict(self):
        return vars(self)

async def save_product_to_csv(product_dict, filename):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=product_dict.keys())
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(product_dict)

async def send_request(url: str, session: httpx.AsyncClient):
    #headers = get_dynamic_headers()
    try:
        response = await session.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def check_val(element):
    return element[0].strip() if element else None

def price_to_float(price_element):
    try:
        price_str = check_val(price_element)
        return float(price_str.replace("$", "").replace(",", "")) if price_str else None
    except:
        return None

async def get_products_links(session: httpx.AsyncClient, product_name: str):
    base_url = "https://www.amazon.com/s?k="
    links = []
    
    for page in range(TARGET_HREFS) :
        url = f"{base_url}{product_name}&page={page+1}"
        response = await send_request(url, session)
        if not response:
            continue
            
        root = html.fromstring(response.text)
        products = root.xpath("//div[contains(@class, 's-result-item')]")
        
        for product in products:
            link = product.xpath(".//a[@class='a-link-normal s-no-outline']/@href")
            if link:
                links.append(f"https://www.amazon.com{link[0]}")
        
    return links

async def get_product_details(session: httpx.AsyncClient, link: str, sem: asyncio.Semaphore):
    async with sem:  # Contrôle de concurrence
        response = await send_request(link, session)
        if not response:
            return None

        try:
            page = html.fromstring(response.text)
            
            # Extraction des données avec gestion d'erreurs
            title = check_val(page.xpath("//span[@id='productTitle']/text()"))
            asin = check_val(page.xpath("//th[contains(text(),'ASIN')]/following-sibling::td/text()"))
            price = page.xpath("//span[@class='a-offscreen']/text()")
            price = price_to_float(price)
            product = Product(
                website="Amazon",
                category="laptop",
                asin=asin,
                title=title,
                price=price,
                brand=check_val(page.xpath("//table/tr[@class='a-spacing-small po-brand']/td[2]/span[@class='a-size-base po-break-word']/text()")),
                model_name=check_val(page.xpath("//table/tr[@class='a-spacing-small po-model_name']/td[2]/span[1]/text()")),
                hard_drive=check_val(page.xpath("//th[contains(text(),'Hard Drive')]/following-sibling::td/text()")),
                memory_ram=check_val(page.xpath("//th[contains(text(),'RAM')]/following-sibling::td/text()")),
                screen_resolution = check_val(page.xpath("//th[contains(text(),'Screen Resolution')]/following-sibling::td/text()")),
                color=check_val(page.xpath("//th[contains(text(),'Color')]/following-sibling::td/text()")),
                link=link
            )
            current_date = datetime.now().strftime("%Y-%m-%d")
            filename = os.path.join("DATA", f'Laptop_Data_Amazon_{current_date}.csv')  # Save to 'DATA' folder
            
            await save_product_to_csv(product.to_dict(), filename)
            return product
            
        except Exception as e:
            print(f"Error parsing {link}: {str(e)}")
            return None

async def main():
    sem = asyncio.Semaphore(2)  # 5 requêtes simultanées max
    
    async with httpx.AsyncClient() as session:
        try:
            links = await get_products_links(session, "laptop")
            print(f"Found {len(links)} products")
            
            tasks = [get_product_details(session, link, sem) for link in links]
            results = await asyncio.gather(*tasks)
            
            valid_results = [r for r in results if r]
            print(f"Successfully scraped {len(valid_results)} products")
            
        except Exception as e:
            print(f"Main error: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())