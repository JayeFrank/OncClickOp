# backend/app/main.py - Version 0.2
"""
Desktop App Framework Backend - Version 0.2
Multi-platform publishing system with Edge WebDriver
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import subprocess
import platform
import os
import json
import asyncio
from datetime import datetime
import threading
import time
import shutil
from pathlib import Path

# Selenium imports - using Edge WebDriver
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Desktop App Framework API - V0.2",
    description="Multi-platform publishing system",
    version="0.2.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Configuration =====
# IMPORTANT: Update these paths to match your system
EDGE_DRIVER_PATH = r"D:\wDriver\msedgedriver.exe"
COOKIE_FILE = r"D:\myCook.txt"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount uploads directory to serve files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    special_handler: Optional[str] = None
    publishable: bool = False  # New field to indicate if app supports publishing

class OpenAppRequest(BaseModel):
    app_name: str

class OpenAppResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime
    action: Optional[str] = None

class PublishRequest(BaseModel):
    """Model for publishing request"""
    video_path: str
    title: str
    description: Optional[str] = ""
    platforms: List[str]  # List of platform IDs to publish to

class PublishStatus(BaseModel):
    """Model for tracking publish status"""
    platform: str
    status: str  # 'pending', 'uploading', 'success', 'failed'
    message: Optional[str] = None
    timestamp: datetime

class UserProfile(BaseModel):
    """User profile information"""
    username: str
    display_name: str
    avatar: Optional[str] = None
    email: Optional[str] = None

# ===== Data =====
apps_database = {
    "小红书": AppInfo(
        id="xiaohongshu",
        name="Xiaohongshu",
        display_name="小红书",
        icon="🔥",
        background="linear-gradient(45deg, #ff1744, #ff6b6b)",
        category="social",
        url="https://creator.xiaohongshu.com/login",
        special_handler="xiaohongshu_login",
        publishable=True
    ),
    "哔哩哔哩": AppInfo(
        id="bilibili",
        name="Bilibili",
        display_name="哔哩哔哩",
        icon="📺",
        background="linear-gradient(45deg, #ff69b4, #ff1493)",
        category="entertainment",
        url="https://www.bilibili.com",
        publishable=True
    ),
    "微博": AppInfo(
        id="weibo",
        name="Weibo",
        display_name="微博",
        icon="👁️",
        background="linear-gradient(45deg, #ff8c00, #ffd700)",
        category="social",
        url="https://weibo.com",
        publishable=True
    ),
    "TikTok": AppInfo(
        id="tiktok",
        name="TikTok",
        display_name="TikTok",
        icon="🎵",
        background="linear-gradient(45deg, #000, #333)",
        category="social",
        url="https://www.tiktok.com",
        publishable=True
    ),
    "知乎": AppInfo(
        id="zhihu",
        name="Zhihu",
        display_name="知乎",
        icon="💡",
        background="linear-gradient(45deg, #4169e1, #87cefa)",
        category="knowledge",
        url="https://www.zhihu.com",
        publishable=False  # Not supported for publishing yet
    ),
    "头条": AppInfo(
        id="toutiao",
        name="Toutiao",
        display_name="头条",
        icon="📰",
        background="linear-gradient(45deg, #dc143c, #ff6347)",
        category="news",
        url="https://www.toutiao.com",
        publishable=True
    )
}

# Global variables
selenium_monitor_active = False
publish_status = {}  # Track publishing status for each platform

# ===== Edge WebDriver Helper Functions =====
def get_edge_driver():
    """Create and return Edge WebDriver instance"""
    logger.info("🔧 Creating Edge WebDriver instance")
    
    try:
        # Check if driver file exists
        if not os.path.exists(EDGE_DRIVER_PATH):
            logger.error(f"❌ Edge driver not found at: {EDGE_DRIVER_PATH}")
            raise FileNotFoundError(f"msedgedriver.exe not found at {EDGE_DRIVER_PATH}")
        
        logger.info(f"✅ Edge driver found at: {EDGE_DRIVER_PATH}")
        
        service = Service(EDGE_DRIVER_PATH)
        options = Options()
        
        # Add options to make automation less detectable
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        logger.info("📋 Edge options configured")
        
        driver = webdriver.Edge(service=service, options=options)
        driver.set_window_size(1400, 900)
        
        logger.info("✅ Edge WebDriver created successfully")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Failed to create Edge driver: {type(e).__name__}: {str(e)}")
        raise

# ===== Login Functions =====
def monitor_xiaohongshu_login():
    """
    Monitor Xiaohongshu login using Edge WebDriver
    Based on user's script.py
    """
    global selenium_monitor_active
    logger.info("🚀 Starting Xiaohongshu login monitor function")
    
    try:
        logger.info(f"📂 Edge driver path: {EDGE_DRIVER_PATH}")
        logger.info(f"📝 Cookie file will be saved to: {COOKIE_FILE}")
        
        driver = get_edge_driver()
        logger.info("✅ Edge WebDriver created successfully")
        
        driver.get('https://creator.xiaohongshu.com/login')
        logger.info("🌐 Navigated to Xiaohongshu login page")
        logger.info(f"📄 Page title: {driver.title}")
        
        wait_flag = True
        wait_count = 0
        
        while wait_flag:
            try:
                logger.info(f"⏳ Waiting for login... (attempt {wait_count + 1})")
                
                # Wait for login success indicator
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='personal']"))
                )
                
                logger.info("🎉 Login success detected! Found personal div element")
                
                # Save cookies to file
                cookies = driver.get_cookies()
                logger.info(f"🍪 Retrieved {len(cookies)} cookies from browser")
                
                with open(COOKIE_FILE, "w", encoding="utf8") as f:
                    f.write(json.dumps(cookies, indent=4, ensure_ascii=False))
                
                logger.info(f"💾 Cookies saved to {COOKIE_FILE}")
                
                # Also save user info for our system
                user_info = {
                    "login_time": datetime.now().isoformat(),
                    "cookies": cookies,
                    "platform": "xiaohongshu",
                    "status": "logged_in"
                }
                save_user_data(user_info)
                logger.info("✅ User data saved to our system")
                
                wait_flag = False
                time.sleep(2)
                driver.quit()
                logger.info("🏁 Browser closed, login process complete")
                
            except TimeoutException:
                wait_count += 1
                if wait_count >= 30:  # 5 minutes total (30 * 10 seconds)
                    logger.error("❌ Login timeout - user didn't login within 5 minutes")
                    driver.quit()
                    break
                # Continue waiting
                
    except FileNotFoundError as e:
        logger.error(f"❌ Edge driver not found at {EDGE_DRIVER_PATH}")
        logger.error(f"❌ Error details: {str(e)}")
        logger.error("💡 Please check that msedgedriver.exe exists at the specified path")
    except Exception as e:
        logger.error(f"❌ Login monitor error: {type(e).__name__}: {str(e)}")
        logger.error(f"📍 Full error details: {e}")
    finally:
        selenium_monitor_active = False
        logger.info("🔚 Login monitor finished")

# ===== Publishing Functions =====
def publish_to_xiaohongshu(video_path: str, title: str, description: str = ""):
    """
    Publish video to Xiaohongshu using saved cookies
    Based on user's rBook.py
    """
    try:
        # Check if cookies exist
        if not os.path.exists(COOKIE_FILE):
            return PublishStatus(
                platform="xiaohongshu",
                status="failed",
                message="请先登录小红书",
                timestamp=datetime.now()
            )
        
        driver = get_edge_driver()
        
        # Load main page first
        driver.get("https://creator.xiaohongshu.com")
        
        # Load cookies
        with open(COOKIE_FILE, encoding="utf8") as f:
            cookies = json.loads(f.read())
            for cookie in cookies:
                driver.add_cookie(cookie)
            logger.info(f"Loaded {len(cookies)} cookies")
        
        # Navigate to publish page
        driver.get("https://creator.xiaohongshu.com/publish/publish")
        
        wait = WebDriverWait(driver, 12)
        
        # Upload video
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        file_input.send_keys(str(video_path))
        logger.info("Video selected for upload")
        
        # Wait for upload success
        wait.until(EC.text_to_be_present_in_element(
            (By.XPATH, '//*[contains(text(),"上传成功")]'), "上传成功"
        ))
        logger.info("✅ Video uploaded successfully")
        
        # Input title
        title_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[contains(@class,"d-text")]')))
        title_input.clear()
        title_input.send_keys(title)
        logger.info("Title entered")
        
        # Add description if provided
        if description:
            # You'll need to find the correct selector for description field
            try:
                desc_input = driver.find_element(By.XPATH, '//textarea[contains(@class,"description")]')
                desc_input.send_keys(description)
            except NoSuchElementException:
                logger.warning("Could not find description field")
        
        time.sleep(2)
        
        # Click publish button
        publish_btn = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "button.publishBtn"
        )))
        wait.until(lambda drv: publish_btn.is_enabled())
        publish_btn.click()
        logger.info("Clicked publish button")
        
        # Wait for success page
        wait.until(EC.url_contains("/publish/success"))
        success_url = driver.current_url
        logger.info(f"✅ Published successfully: {success_url}")
        
        time.sleep(3)
        driver.quit()
        
        return PublishStatus(
            platform="xiaohongshu",
            status="success",
            message="发布成功",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ Xiaohongshu publish error: {str(e)}")
        try:
            driver.quit()
        except:
            pass
        return PublishStatus(
            platform="xiaohongshu",
            status="failed",
            message=f"发布失败: {str(e)}",
            timestamp=datetime.now()
        )

def publish_to_bilibili(video_path: str, title: str, description: str = ""):
    """Publish to Bilibili - Implementation needed"""
    # This is a placeholder - you'll need to implement Bilibili publishing
    return PublishStatus(
        platform="bilibili",
        status="pending",
        message="Bilibili发布功能开发中",
        timestamp=datetime.now()
    )

def publish_to_weibo(video_path: str, title: str, description: str = ""):
    """Publish to Weibo - Implementation needed"""
    return PublishStatus(
        platform="weibo",
        status="pending",
        message="微博发布功能开发中",
        timestamp=datetime.now()
    )

# Publishing dispatcher
PLATFORM_PUBLISHERS = {
    "xiaohongshu": publish_to_xiaohongshu,
    "bilibili": publish_to_bilibili,
    "weibo": publish_to_weibo,
    # Add more platforms here
}

def save_user_data(user_info: Dict[str, Any]):
    """Save user data to file"""
    try:
        os.makedirs("data", exist_ok=True)
        
        filename = f"data/user_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)
        
        with open("data/latest_login.json", 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"Error saving user data: {str(e)}")

# ===== API Endpoints =====
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Desktop App Framework Backend Starting...")
    logger.info(f"📍 Edge driver path: {EDGE_DRIVER_PATH}")
    logger.info(f"📍 Cookie file path: {COOKIE_FILE}")
    logger.info(f"📍 Upload directory: {UPLOAD_DIR}")
    logger.info(f"📱 Total apps loaded: {len(apps_database)}")
    logger.info("✅ Backend startup complete")

@app.get("/")
async def root():
    return {
        "message": "Desktop App Framework API V0.2",
        "version": "0.2.0",
        "status": "healthy",
        "features": ["app-launcher", "multi-platform-publishing"]
    }

@app.get("/api/apps", response_model=List[AppInfo])
async def get_apps():
    return list(apps_database.values())

@app.get("/api/publishable-apps", response_model=List[AppInfo])
async def get_publishable_apps():
    """Get only apps that support publishing"""
    return [app for app in apps_database.values() if app.publishable]

@app.post("/api/open-app", response_model=OpenAppResponse)
async def open_app(request: OpenAppRequest, background_tasks: BackgroundTasks):
    """Open app with special handling for platform logins"""
    global selenium_monitor_active
    
    app_name = request.app_name
    logger.info(f"🔍 Received request to open app: '{app_name}'")
    logger.info(f"📋 Available apps in database: {list(apps_database.keys())}")
    
    # Try to find app by display_name if direct lookup fails
    app = apps_database.get(app_name)
    if not app:
        # Search by display_name
        for key, app_info in apps_database.items():
            if app_info.display_name == app_name or app_info.name == app_name:
                app = app_info
                logger.info(f"✅ Found app by display_name: {app_info.display_name}")
                break
    
    if not app:
        logger.error(f"❌ App '{app_name}' not found in database")
        logger.error(f"Available apps: {[app.display_name for app in apps_database.values()]}")
        raise HTTPException(status_code=404, detail=f"Application '{app_name}' not found")
    
    # Special handler for Xiaohongshu login
    if app.special_handler == "xiaohongshu_login":
        logger.info("🎯 Special handler detected: xiaohongshu_login")
        
        if not selenium_monitor_active:
            selenium_monitor_active = True
            logger.info("🔄 Starting Selenium monitor thread")
            
            monitor_thread = threading.Thread(target=monitor_xiaohongshu_login)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            logger.info("✅ Monitor thread started successfully")
            
            return OpenAppResponse(
                success=True,
                message="请在弹出的窗口中登录小红书创作者中心",
                timestamp=datetime.now(),
                action="selenium_login"
            )
        else:
            logger.warning("⚠️ Selenium monitor already running")
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

@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file for publishing"""
    try:
        # Validate file type
        allowed_types = ['.mp4', '.mov', '.avi', '.mkv']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
        
        # Save file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "filename": filename,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "message": "视频上传成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/api/publish")
async def publish_video(request: PublishRequest, background_tasks: BackgroundTasks):
    """Publish video to multiple platforms"""
    global publish_status
    
    # Validate video file exists
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # Initialize status for each platform
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    publish_status[job_id] = {}
    
    for platform_id in request.platforms:
        publish_status[job_id][platform_id] = PublishStatus(
            platform=platform_id,
            status="pending",
            message="等待发布",
            timestamp=datetime.now()
        )
    
    # Start publishing in background
    background_tasks.add_task(
        publish_to_platforms,
        job_id,
        request.video_path,
        request.title,
        request.description,
        request.platforms
    )
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"开始发布到 {len(request.platforms)} 个平台",
        "platforms": request.platforms
    }

async def publish_to_platforms(job_id: str, video_path: str, title: str, description: str, platforms: List[str]):
    """Background task to publish to multiple platforms"""
    global publish_status
    
    for platform_id in platforms:
        # Update status to uploading
        publish_status[job_id][platform_id] = PublishStatus(
            platform=platform_id,
            status="uploading",
            message="正在发布...",
            timestamp=datetime.now()
        )
        
        # Get publisher function
        publisher = PLATFORM_PUBLISHERS.get(platform_id)
        
        if publisher:
            # Execute publish
            result = publisher(video_path, title, description)
            publish_status[job_id][platform_id] = result
        else:
            publish_status[job_id][platform_id] = PublishStatus(
                platform=platform_id,
                status="failed",
                message="不支持的平台",
                timestamp=datetime.now()
            )
        
        # Add delay between platforms to avoid rate limiting
        await asyncio.sleep(5)

@app.get("/api/publish-status/{job_id}")
async def get_publish_status(job_id: str):
    """Get publishing status for a job"""
    if job_id not in publish_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": publish_status[job_id]
    }

@app.get("/api/user/profile", response_model=UserProfile)
async def get_user_profile():
    """Get current user profile information"""
    logger.info("📱 User profile requested")
    # Return a default profile for now
    return UserProfile(
        username="user",
        display_name="用户",
        avatar="U",
        email="user@example.com"
    )
    """Check if user is logged in to platforms"""
    login_status = {}
    
    # Check Xiaohongshu
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                login_status["xiaohongshu"] = {
                    "logged_in": True,
                    "cookie_count": len(cookies)
                }
        except:
            login_status["xiaohongshu"] = {"logged_in": False}
    else:
        login_status["xiaohongshu"] = {"logged_in": False}
    
    # Add other platforms here
    login_status["bilibili"] = {"logged_in": False}
    login_status["weibo"] = {"logged_in": False}
    
    return login_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)