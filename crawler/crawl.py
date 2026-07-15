import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import TASKS, BASE_DOWNLOAD_DIR, HEADERS

# ==========================================
# PDF LINK EXTRACTION & CLEANING
# ==========================================

def extract_clean_title(link_tag, default_href):
    """Extract title from link tag, clean junk words, and sanitize for file system."""
    raw_title = link_tag.get_text(separator=" ", strip=True)
    if not raw_title:
        raw_title = default_href.split('/')[-1]
    
    junk_words = ["Xem", "Tải về", "Download", "PDF", "Đã soát xét", "kiểm toán"]
    
    for word in junk_words:
        if raw_title.lower().endswith(word.lower()):
            raw_title = raw_title[:-len(word)].strip()
            
    clean_name = re.sub(r'[\\/*?:"<>|]', "", raw_title)
    
    clean_name = " ".join(clean_name.split())
    
    if not clean_name.lower().endswith(".pdf"):
        clean_name += ".pdf"
        
    return clean_name

# ==========================================
# SCAN FILES
# ==========================================

def scan_files(tasks):
    print("\n" + "="*50 + "\n STARTED SCANNING (SELENIUM)\n" + "="*50)
    total_files_found = 0

    chrome_options = Options()
    #chrome_options.add_argument("--headless") 
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        for task in tasks:
            print(f"\n[*] Scanning company: {task['company']}")
            for url in task["urls"]:
                print(f"    -> Accessing: {url}")
                driver.get(url)
                time.sleep(4)

                if task["click_years"]:
                    for year in task["click_years"]:
                        print(f"       + Scanning year: {year}")
                        try:
                            xpath = f"//*[text()='{year}' or contains(text(), ' {year}')]"
                            btn = driver.find_element(By.XPATH, xpath)
                            driver.execute_script("arguments[0].click();", btn)
                            
                            time.sleep(3)
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            
                            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
                            
                            for link in pdf_links:
                                href = link.get('href')
                                full_url = urljoin(url, href)
                                file_name = extract_clean_title(link, href)

                                if not any(f['url'] == full_url for f in task["files_to_download"]):
                                    task["files_to_download"].append({"title": file_name, "url": full_url})
                                    total_files_found += 1
                                    
                        except Exception as e:
                            print(f"       [!] Error occurred while scanning year {year}: {e}")

                else:
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
                    
                    for link in pdf_links:
                        href = link.get('href')
                        full_url = urljoin(url, href)
                        file_name = extract_clean_title(link, href)
                        
                        if not any(f['url'] == full_url for f in task["files_to_download"]):
                            task["files_to_download"].append({"title": file_name, "url": full_url})
                            total_files_found += 1
                            
    finally:
        driver.quit()
        
    return tasks, total_files_found

# ==========================================
# DISPLAY AND CONFIRMATION
# ==========================================

def display_and_confirm(tasks, total_files):
    if total_files == 0:
        print("\n[!] No PDF files found. Please check the website structure.")
        return False
        
    print(f"\n LIST OF FILES READY TO DOWNLOAD (Total: {total_files} files)")
    for task in tasks:
        if task["files_to_download"]:
            print(f"\n+ Company: {task['company']} ({len(task['files_to_download'])} files)")
            for idx, f in enumerate(task["files_to_download"], 1):
                print(f"  {idx}. {f['title']}")
                
    confirm = input(f"\nDo you want to download these {total_files} files? (y/n): ").strip().lower()
    return confirm == 'y'

# ==========================================
# DOWNLOAD FILES
# ==========================================

def download_files(tasks):
    print("\n" + "="*50 + "\n STARTING FILE DOWNLOAD\n" + "="*50)
    os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)
        
    for task in tasks:
        if not task["files_to_download"]: 
            continue
            
        company_dir = os.path.join(BASE_DOWNLOAD_DIR, task["company"])
        os.makedirs(company_dir, exist_ok=True)
        print(f"\n[*] Scanning company: {task['company']}")
        
        for file_info in task["files_to_download"]:
            file_path = os.path.join(company_dir, file_info["title"])
            
            if os.path.exists(file_path):
                print(f"    [Skip] File already exists: {file_info['title']}")
                continue
                
            print(f"    -> Downloading: {file_info['title']}")
            try:
                res = requests.get(file_info["url"], headers=HEADERS, timeout=15)
                if res.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(res.content)
                else:
                    print(f"    [!] Error HTTP {res.status_code} when downloading.")
                
                time.sleep(0.5)
            except Exception as e:
                print(f"    [!] Connection error: {e}")
                
    print("\nCOMPLETE ALL DOWNLOAD PROCESSES!")

# # ==========================================
# EXECUTION
# # ==========================================

if __name__ == "__main__":
    tasks_updated, total_files = scan_files(TASKS)
    if display_and_confirm(tasks_updated, total_files):
        download_files(tasks_updated)
    else:
        print("\nDownload canceled. See you again!")