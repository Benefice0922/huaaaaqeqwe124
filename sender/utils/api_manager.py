import aiohttp
import json
from typing import Optional, Dict, Any
import asyncio

class APIManager:
    def __init__(self):
        # Bastard API настройки
        self.bastart_project_token = "4d101c3e-ee78-4712-bb60-f6cf5d6776c5"
        self.bastart_worker_token = "a9dba46e-e9bb-44a4-a7d8-d633234bbf65"
        self.bastart_api_url = "https://web-api.bdev.su/"
        
        # Сокращатель URL настройки
        self.shortener_api_url = "http://193.233.112.8/api/shorten"
        
        # Настройки площадки по умолчанию
        self.default_platform_id = 902  # Для Krisha.kz
        self.default_profile_id = 384912
        self.default_price = 0.11
        
        self.enabled = False
        

        
    def set_enabled(self, enabled: bool):
        """Включить/выключить API"""
        self.enabled = enabled
        
    def set_platform(self, platform_name: str):
        """Установить platform_id по имени площадки"""
        platform_name = platform_name.lower()
        if platform_name in self.platform_mapping:
            self.default_platform_id = self.platform_mapping[platform_name]
            print(f"[API Manager] Platform set to {platform_name} (id: {self.default_platform_id})")
        
    def load_settings(self, settings: Dict[str, Any]):
        """Загрузка настроек из конфига"""
        api_settings = settings.get("api_settings", {})
        self.bastart_project_token = api_settings.get("bastart_project_token", self.bastart_project_token)
        self.bastart_worker_token = api_settings.get("bastart_worker_token", self.bastart_worker_token)
        self.bastart_api_url = api_settings.get("bastart_api_url", self.bastart_api_url)
        self.shortener_api_url = api_settings.get("shortener_api_url", self.shortener_api_url)
        
        # Конвертируем в правильные типы
        try:
            self.default_platform_id = int(api_settings.get("default_platform_id", self.default_platform_id))
            self.default_profile_id = int(api_settings.get("default_profile_id", self.default_profile_id))
            self.default_price = float(api_settings.get("default_price", self.default_price))
        except (ValueError, TypeError):
            pass
        
    def save_settings(self):
        """Получить настройки для сохранения"""
        return {
            "bastart_project_token": self.bastart_project_token,
            "bastart_worker_token": self.bastart_worker_token,
            "bastart_api_url": self.bastart_api_url,
            "shortener_api_url": self.shortener_api_url,
            "default_platform_id": self.default_platform_id,
            "default_profile_id": self.default_profile_id,
            "default_price": self.default_price
        }
    
    async def get_catalog(self):
        """Получить каталог площадок (GET запрос)"""
        headers = {
            "X-Team-Token": self.bastart_project_token,
            "X-User-Token": self.bastart_worker_token,
            "Accept": "application/json"
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)  # 5 секунд для GET
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.bastart_api_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data
                    else:
                        text = await resp.text()
                        print(f"[Catalog] Error {resp.status}: {text[:200]}")
                        return None
        except Exception as e:
            print(f"[Catalog] Exception: {e}")
            return None
    
    async def create_bastart_link(self, phone: str, title: str = None) -> Optional[Dict]:
        """Создание ссылки через Bastart API (POST запрос)"""
        if not self.enabled:
            return None
            
        # Заголовки обязательные
        headers = {
            "X-Team-Token": self.bastart_project_token,
            "X-User-Token": self.bastart_worker_token,
            "Content-Type": "application/json"
        }
        
        # Формируем title
        if not title:
            # Простой title с номером
            title = phone.replace("+", "")
        
        # Тело запроса в точном формате из документации
        data = {
            "platform_id": self.default_platform_id,  # int
            "profile_id": self.default_profile_id,    # int
            "title": title,                            # string
            "price": self.default_price               # float
        }
        
        print(f"[Bastart API] POST {self.bastart_api_url}")
        print(f"[Bastart API] Headers: {headers}")
        print(f"[Bastart API] Body: {json.dumps(data)}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)  # 10 секунд для POST
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.bastart_api_url,
                    headers=headers,
                    json=data
                ) as resp:
                    response_text = await resp.text()
                    print(f"[Bastart API] Response {resp.status}: {response_text}")
                    
                    if resp.status == 201:
                        # Успешное создание ссылки
                        try:
                            result = json.loads(response_text)
                            if not result.get("error", True):
                                return {
                                    "link": result.get("link"),
                                    "error": False
                                }
                            else:
                                print(f"[Bastart API] API returned error: {result}")
                                return None
                        except json.JSONDecodeError as e:
                            print(f"[Bastart API] JSON decode error: {e}")
                            return None
                    else:
                        # Ошибка
                        print(f"[Bastart API] HTTP {resp.status} error")
                        return None
                        
        except asyncio.TimeoutError:
            print(f"[Bastart API] Request timeout (10s)")
            return None
        except aiohttp.ClientError as e:
            print(f"[Bastart API] Client error: {e}")
            return None
        except Exception as e:
            print(f"[Bastart API] Unexpected error: {type(e).__name__}: {e}")
            return None
    
    async def shorten_url(self, url: str) -> Optional[str]:
        """Сокращение ссылки через API сокращателя"""
        if not url:
            return None
            
        print(f"[Shortener] Shortening URL: {url[:50]}...")
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.shortener_api_url, 
                    json={"url": url}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        short_url = data.get("short_url")
                        print(f"[Shortener] Success: {short_url}")
                        return short_url
                    else:
                        text = await resp.text()
                        print(f"[Shortener] Error {resp.status}: {text[:100]}")
                        return url  # Возвращаем оригинальную
        except Exception as e:
            print(f"[Shortener] Exception: {e}")
            return url  # Возвращаем оригинальную при ошибке
    
    async def get_link(self, phone: str, platform: str = None) -> Optional[str]:
        """Получить ссылку: Bastart -> Сокращатель -> результат"""
        if not self.enabled:
            print(f"[API Manager] API is disabled")
            return None
        
        # НЕ переопределяем platform_id - используем загруженный из settings.json (902)
        print(f"[API Manager] Getting link for {phone[:30]}... (platform_id: {self.default_platform_id})")
        
        # Установка платформы если указана
        if platform:
            self.set_platform(platform)
        
        print(f"[API Manager] Getting link for {phone} (platform_id: {self.default_platform_id})")
        
        # 1. Получаем ссылку от Bastart
        result = await self.create_bastart_link(phone)
        
        if not result or result.get("error"):
            print(f"[API Manager] Failed to get link from Bastart")
            return None
        
        original_link = result.get("link")
        if not original_link:
            print(f"[API Manager] No link in Bastart response")
            return None
            
        print(f"[API Manager] Got Bastart link: {original_link}")
        
        # 2. Сокращаем ссылку
        short_link = await self.shorten_url(original_link)
        
        if short_link and short_link != original_link:
            print(f"[API Manager] Final shortened link: {short_link}")
            return short_link
        else:
            print(f"[API Manager] Using original link (shortener failed)")
            return original_link

    async def test_api(self):
        """Тестирование API с диагностикой"""
        print("\n" + "="*50)
        print("BASTART API DIAGNOSTIC TEST")
        print("="*50)
        
        # 1. Проверяем каталог
        print("\n1. Testing GET (catalog)...")
        catalog = await self.get_catalog()
        
        if catalog:
            print("✅ Catalog received successfully!")
            
            # Анализируем структуру
            if isinstance(catalog, dict):
                print("\nCatalog structure:")
                for key in catalog.keys():
                    if isinstance(catalog[key], list):
                        print(f"  - {key}: {len(catalog[key])} items")
                    elif isinstance(catalog[key], dict):
                        print(f"  - {key}: {len(catalog[key])} keys")
                    else:
                        print(f"  - {key}: {type(catalog[key])}")
                
                # Сохраняем для анализа
                with open("catalog_structure.json", "w", encoding="utf-8") as f:
                    json.dump(catalog, f, ensure_ascii=False, indent=2)
                print("\nFull catalog saved to catalog_structure.json")
        else:
            print("❌ Failed to get catalog")
            print("Check your tokens:")
            print(f"  Project Token: {self.bastart_project_token[:20]}...")
            print(f"  Worker Token: {self.bastart_worker_token[:20]}...")
        
        # 2. Тестируем создание ссылки
        print("\n2. Testing POST (create link)...")
        self.enabled = True
        
        test_phone = "+77011234567"
        result = await self.create_bastart_link(test_phone, f"Test {test_phone}")
        
        if result and not result.get("error"):
            print(f"✅ Link created successfully!")
            print(f"   Link: {result.get('link')}")
            
            # 3. Тестируем сокращатель
            print("\n3. Testing URL shortener...")
            short = await self.shorten_url(result.get("link"))
            if short:
                print(f"✅ Shortened: {short}")
            else:
                print("❌ Shortener failed")
        else:
            print("❌ Failed to create link")
            print("Possible issues:")
            print("  - Invalid platform_id or profile_id")
            print("  - Invalid tokens")
            print("  - API server issues")
        
        print("\n" + "="*50)
        print("TEST COMPLETED")
        print("="*50)
        
        return catalog