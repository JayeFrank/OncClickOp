# backend/app/main.py - Version 0.1
"""
Desktop App Framework Backend - Version 0.1
Special handling for Bilibili → Xiaohongshu Creator login with Selenium monitoring
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import subprocess
import platform
import os
import json
import asyncio
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import threading
import time

# Initialize FastAPI app
app = FastAPI(
    title="Desktop App Framework API - V0.1",
    description="MVP with Xiaohongshu login monitoring",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Models =====
class AppInfo(BaseModel):
    id: str
    name: str
    display_name: str
    icon: str
    background: str
    category: str
    executable_path: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    special_handler: Optional[str] = None  # New field for special handling

class OpenAppRequest(BaseModel):
    app_name: str

class OpenAppResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime
    action: Optional[str] = None  # To tell frontend what action was taken

# ===== Data =====
apps_database = {
    "TikTok": AppInfo(
        id="tiktok",
        name="TikTok",
        display_name="TikTok",
        icon="🎵",
        background="linear-gradient(45deg, #000, #333)",
        category="social",
        url="https://www.tiktok.com"
    ),
    "链接": AppInfo(
        id="links",
        name="Links",
        display_name="链接",
        icon="🔗",
        background="linear-gradient(45deg, #ff4500, #ff8c00)",
        category="utility"
    ),
    "记事": AppInfo(
        id="notes",
        name="Notes",
        display_name="记事",
        icon="📝",
        background="linear-gradient(45deg, #ffa500, #ffb347)",
        category="productivity"
    ),
    "小红书": AppInfo(
        id="xiaohongshu",
        name="Xiaohongshu",
        display_name="小红书",
        icon="🔥",
        background="linear-gradient(45deg, #ff1744, #ff6b6b)",
        category="social",
        url="https://creator.xiaohongshu.com/login",
        special_handler="xiaohongshu_login"  # Special handler for V0.1
    ),
    "哔哩哔哩": AppInfo(
        id="bilibili",
        name="Bilibili",
        display_name="哔哩哔哩",
        icon="📺",
        background="linear-gradient(45deg, #ff69b4, #ff1493)",
        category="entertainment",
        url="https://bilibili.com"
    ),
    "同步": AppInfo(
        id="sync",
        name="Sync",
        display_name="同步",
        icon="🔄",
        background="linear-gradient(45deg, #1e90ff, #87ceeb)",
        category="utility"
    ),
    "头条": AppInfo(
        id="toutiao",
        name="Toutiao",
        display_name="头条",
        icon="📰",
        background="linear-gradient(45deg, #dc143c, #ff6347)",
        category="news",
        url="https://www.toutiao.com"
    ),
    "微博": AppInfo(
        id="weibo",
        name="Weibo",
        display_name="微博",
        icon="👁️",
        background="linear-gradient(45deg, #ff8c00, #ffd700)",
        category="social",
        url="https://passport.weibo.com"
    ),
    "知乎": AppInfo(
        id="zhihu",
        name="Zhihu",
        display_name="知乎",
        icon="💡",
        background="linear-gradient(45deg, #4169e1, #87cefa)",
        category="knowledge",
        url="https://www.zhihu.com"
    ),
    "Snapchat": AppInfo(
        id="snapchat",
        name="Snapchat",
        display_name="Snapchat",
        icon="👻",
        background="linear-gradient(45deg, #333, #666)",
        category="social",
        url="https://www.snapchat.com"
    )
}

# Global variable to track Selenium monitoring
selenium_monitor_active = False

# ===== Selenium Functions =====
def monitor_xiaohongshu_login():
    """
    Monitor Xiaohongshu login using Selenium
    This runs in a separate thread
    """
    global selenium_monitor_active
    
    try:
        # Configure Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        driver = webdriver.Chrome(options=options)
        driver.get("https://creator.xiaohongshu.com/login")
        
        print("🔍 Selenium monitor started, waiting for login...")
        
        # Wait for successful login (you'll need to adjust these selectors based on actual page)
        wait = WebDriverWait(driver, 300)  # Wait up to 5 minutes
        
        # Wait for an element that appears after login
        # You'll need to inspect the page to find the right selector
        try:
            # Example: wait for user avatar or dashboard element
            # Adjust this selector based on what appears after login
            logged_in_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "user-avatar"))  # Adjust selector
            )
            
            print("✅ Login detected!")
            
            # Get cookies
            cookies = driver.get_cookies()
            
            # Get any user info from the page (adjust selectors as needed)
            user_info = {
                "login_time": datetime.now().isoformat(),
                "cookies": cookies,
                "url": driver.current_url,
                "platform": "xiaohongshu"
            }
            
            # Try to get username if visible
            try:
                username_element = driver.find_element(By.CLASS_NAME, "username")  # Adjust selector
                user_info["username"] = username_element.text
            except:
                user_info["username"] = "Unknown"
            
            # Save user info to file
            save_user_data(user_info)
            
            # Close driver after successful save
            time.sleep(2)  # Give user time to see success
            driver.quit()
            
        except TimeoutException:
            print("❌ Login timeout - user didn't login within 5 minutes")
            driver.quit()
            
    except Exception as e:
        print(f"❌ Selenium error: {str(e)}")
    finally:
        selenium_monitor_active = False

def save_user_data(user_info: Dict[str, Any]):
    """Save user data to a JSON file"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("../data", exist_ok=True)
        
        # Save to file with timestamp
        filename = f"data/user_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ User data saved to {filename}")
        
        # Also save as latest.json for easy access
        with open("data/latest_login.json", 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"❌ Error saving user data: {str(e)}")

# ===== API Endpoints =====
@app.get("/")
async def root():
    return {
        "message": "Desktop App Framework API V0.1",
        "version": "0.1.0",
        "status": "healthy"
    }

@app.get("/api/apps", response_model=List[AppInfo])
async def get_apps():
    return list(apps_database.values())

@app.post("/api/open-app", response_model=OpenAppResponse)
async def open_app(request: OpenAppRequest, background_tasks: BackgroundTasks):
    """Open app with special handling for Bilibili → Xiaohongshu login"""
    global selenium_monitor_active
    
    app_name = request.app_name
    app = apps_database.get(app_name)
    
    if not app:
        raise HTTPException(status_code=404, detail=f"Application '{app_name}' not found")
    
    # Special handler for Bilibili → Xiaohongshu login
    if app.special_handler == "xiaohongshu_login":
        # Start Selenium monitor in background if not already running
        if not selenium_monitor_active:
            selenium_monitor_active = True
            monitor_thread = threading.Thread(target=monitor_xiaohongshu_login)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return OpenAppResponse(
                success=True,
                message="请在弹出的窗口中登录小红书创作者中心",
                timestamp=datetime.now(),
                action="open_popup"
            )
        else:
            return OpenAppResponse(
                success=False,
                message="登录监控已在运行中，请完成当前登录",
                timestamp=datetime.now()
            )
    
    # Normal app handling
    try:
        if app.url:
            if platform.system() == "Windows":
                os.startfile(app.url)
            elif platform.system() == "Darwin":
                subprocess.run(["open", app.url])
            else:
                subprocess.run(["xdg-open", app.url])
            
            message = f"Successfully opened {app.display_name}"
        else:
            message = f"{app.display_name} has no launch method"
            
        return OpenAppResponse(
            success=True,
            message=message,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        return OpenAppResponse(
            success=False,
            message=f"Failed to open {app.display_name}: {str(e)}",
            timestamp=datetime.now()
        )

@app.get("/api/login-status")
async def check_login_status():
    """Check if we have saved login data"""
    try:
        if os.path.exists("data/latest_login.json"):
            with open("data/latest_login.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    "logged_in": True,
                    "username": data.get("username", "Unknown"),
                    "login_time": data.get("login_time", "Unknown")
                }
    except:
        pass
    
    return {"logged_in": False}

@app.get("/api/selenium-status")
async def get_selenium_status():
    """Check if Selenium monitor is running"""
    return {"monitoring": selenium_monitor_active}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)