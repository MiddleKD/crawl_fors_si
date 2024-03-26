import re
import time

import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def open_query_file(file_path):
    with open(file_path, "r") as f:
        query_list = [cur.replace("\n", "") for cur in f.readlines()]
    return query_list

def list_to_excel(data_list, output_fn):
    # 데이터프레임 생성
    df = pd.DataFrame([d for d in data_list if d is not None])

    # 엑셀 파일로 저장
    df.to_excel(output_fn, index=False)

class CrawlManager:
    def __init__(self):
        pass
    
    def call_driver(self, invisible=True):
        driver_path = ChromeDriverManager().install()
        
        options = Options()
        if invisible==True:
            options.add_argument("--headless")
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=options)

    def extract_user_id(self, text):

        pattern = r"https://in.naver.com/(\w+)/contents"
        match = re.search(pattern, text)

        if match:
            return match.group(1)
        else:
            None

    def crawl_user_ids(self, url, user_ele_selector, max_retry_num=30):
        self.driver.get(url)

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            bf_li_ct = len(self.driver.find_elements(By.TAG_NAME, "li"))
            for _ in range(max_retry_num):
                time.sleep(0.05)
                af_li_ct = len(self.driver.find_elements(By.TAG_NAME, "li"))
                if bf_li_ct != af_li_ct:
                    break

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height

        user_eles = self.driver.find_elements(By.CSS_SELECTOR, user_ele_selector)
        user_ids = [self.extract_user_id(cur.get_property("href")) for cur in user_eles]

        return user_ids

    def kill_driver(self):
        self.driver.quit()


import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import threading

if __name__ == "__main__":
    user_ele_selector = "div.detail_box > div.title_area > a"
    url_prefix = f"https://search.naver.com/search.naver?ssc=tab.influencer.chl&where=influencer&sm=tab_jum&query="

    def log_tk(text):
        log_text.insert(tk.END, f"{text}\n")
        log_text.update_idletasks()

    def crawl_data(file_path, user_ele_selector, url_prefix):
        try:
            max_retry_num = 30

            log_tk("Make brower driver...")
            crawler = CrawlManager()
            crawler.call_driver(invisible=True)
            log_tk("Done")

            log_tk("Open query file...")
            log_tk(f"You selected {file_path} for query list")
            query_list = open_query_file(file_path)
            log_tk("Done")

            log_tk("\nStart crawling...\n")
            for query in query_list:
                log_tk(f"Query: {query}...")
                user_ids = crawler.crawl_user_ids(url=url_prefix+query,
                                                user_ele_selector=user_ele_selector,
                                                max_retry_num=max_retry_num)
                log_tk(f"It has {len(user_ids)} datas.")

                log_tk(f"Saving {query+'_inf_list.xlsx'}")
                list_to_excel(user_ids, query+"_inf_list.xlsx")
                log_tk(f"{query} Done\n")

            log_tk("Finish crawling\n")
            
            crawler.kill_driver()
            del crawler
        
            crawl_button.config(state=tk.NORMAL)
        except Exception as e:
            log_tk(e)

    def clear_log():
        log_text.delete(1.0, tk.END)

    def browse_file():
        file_path = filedialog.askopenfilename()
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)

    def crawl_thread():
        crawl_button.config(state=tk.DISABLED)
        threading.Thread(target=lambda: crawl_data(file_entry.get(), user_ele_selector_entry.get(), url_prefix_entry.get())).start()

    # GUI 생성
    root = tk.Tk()
    root.title("Naver influencer crawler")

    # 파일 경로 입력 위젯
    file_frame = tk.Frame(root)
    file_frame.pack(pady=5)
    file_label = tk.Label(file_frame, text="TXT path:")
    file_label.pack(side=tk.LEFT)
    file_entry = tk.Entry(file_frame, width=50)
    file_entry.pack(side=tk.LEFT, padx=5)
    browse_button = tk.Button(file_frame, text="browse", command=browse_file)
    browse_button.pack(side=tk.LEFT)

    # 사용자 요소 선택자 입력 위젯
    user_ele_selector_frame = tk.Frame(root)
    user_ele_selector_frame.pack(pady=5)
    user_ele_selector_label = tk.Label(user_ele_selector_frame, text="CSS selector:")
    user_ele_selector_label.pack(side=tk.LEFT)
    user_ele_selector_entry = tk.Entry(user_ele_selector_frame, width=50)
    user_ele_selector_entry.insert(0, user_ele_selector)
    user_ele_selector_entry.pack(side=tk.LEFT, padx=5)

    # URL 접두사 입력 위젯
    url_prefix_frame = tk.Frame(root)
    url_prefix_frame.pack(pady=5)
    url_prefix_label = tk.Label(url_prefix_frame, text="URL prefix:")
    url_prefix_label.pack(side=tk.LEFT)
    url_prefix_entry = tk.Entry(url_prefix_frame, width=50)
    url_prefix_entry.insert(0, url_prefix)
    url_prefix_entry.pack(side=tk.LEFT, padx=5)

    # 로그 표시 위젯
    log_label = tk.Label(root, text="Log:")
    log_label.pack(pady=5)
    log_text = ScrolledText(root, width=60, height=15)
    log_text.pack()

    # 크롤링 실행 및 로그 지우기 버튼
    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)
    crawl_button = tk.Button(button_frame, text="Run", command=crawl_thread)
    crawl_button.pack(side=tk.LEFT)
    clear_button = tk.Button(button_frame, text="Clear log", command=clear_log)
    clear_button.pack(side=tk.LEFT, padx=10)

    root.mainloop()
