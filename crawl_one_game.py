import time as sleep

import gspread
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

GAME_KEY = "S43G01N239"
OT = False  # 연장전 여부

url = f"https://www.kbl.or.kr/game/record/{GAME_KEY}"
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

driver.get(url)
sleep.sleep(1)
hometeam = driver.find_elements(
    By.XPATH,
    '//*[@id="container"]/div/div[3]/div/div[2]/div[1]/div[1]/div/h6',
)[0].text
awayteam = driver.find_elements(
    By.XPATH,
    '//*[@id="container"]/div/div[3]/div/div[2]/div[1]/div[3]/div/h6',
)[0].text
text_broadcast = driver.find_elements(
    By.XPATH,
    '//*[@id="container"]/div/ul[2]/li[4]',
)[0]
text_broadcast.click()
sleep.sleep(1)
date = driver.find_elements(
    By.XPATH,
    '//*[@id="container"]/div/ul[1]/li[2]/ul/li[2]/span',
)[
    0
].text[:10]
sleep.sleep(1)

quarters = {
    "1Q": 2,
    "2Q": 3,
    "3Q": 4,
    "4Q": 5,
}
if OT:
    quarters.update({"OT": 6})
quarters = dict(
    sorted(
        quarters.items(),
        key=lambda k: k[1],
        reverse=True,
    )
)

columns = [
    "쿼터",
    "팀",
    "시간",
    "선수",
    "2점슛시도",
    "2점슛성공",
    "3점슛시도",
    "3점슛성공",
    "자유투시도",
    "자유투성공",
    "공격리바운드",
    "수비리바운드",
    "어시스트",
    "스틸",
    "블록",
    "덩크슛성공",
    "턴오버",
    "굿디펜스",
    "파울",
    "기타파울",
    "교체",
    "기타",
]
records = pd.DataFrame(columns=columns)

for q, idx in quarters.items():
    tab = driver.find_elements(
        By.XPATH,
        f'//*[@id="container"]/div/div[4]/div[2]/div/table/thead/tr/th[{idx}]/a',
    )[0]
    record_table = driver.find_elements(
        By.XPATH,
        '//*[@id="container"]/div/div[4]/div[2]/div/table/tbody',
    )[0]
    tab.click()
    sleep.sleep(1)
    record_table = BeautifulSoup(
        record_table.get_attribute("innerHTML"),
        "html.parser",
    )

    for record in record_table.find_all("td"):
        record_ = pd.DataFrame(columns=columns)
        home, time, away = record.find_all("li")

        # 홈
        if home.text != "":
            record_["쿼터"] = [q]
            record_["팀"] = [hometeam]
            record_["시간"] = [time.text]
            home_text = home.text.replace("5반칙", "").strip().split(" ")

            if len(home_text) != 1:
                if len(home_text) == 2:
                    player = home_text[0]
                    metric = home_text[-1]
                else:
                    player = " ".join(home_text[:-1])
                    metric = home_text[-1]

                if metric == "파울자유투":
                    metric = "파울"
                    value = 1
                elif "교체" in metric:
                    (
                        metric,
                        value,
                    ) = metric.split("(")
                    value = value[:-1]
                else:
                    value = 1

                record_["선수"] = [player]
                record_[metric] = [value]
            else:
                record_["기타"] = home.text.strip()
        # 어웨이
        elif away.text != "":
            record_["쿼터"] = [q]
            record_["팀"] = [awayteam]
            record_["시간"] = [time.text]
            away_text = away.text.replace("5반칙", "").strip().split(" ")

            if len(away_text) != 1:
                if len(away_text) == 2:
                    player = away_text[0]
                    metric = away_text[-1]
                else:
                    player = " ".join(away_text[:-1])
                    metric = away_text[-1]

                if metric == "파울자유투":
                    metric = "파울"
                    value = 1
                elif "교체" in metric:
                    (
                        metric,
                        value,
                    ) = metric.split("(")
                    value = value[:-1]
                else:
                    value = 1

                record_["선수"] = [player]
                record_[metric] = [value]
            else:
                record_["기타"] = away.text.strip()
        records = pd.concat(
            [
                record_,
                records,
            ]
        )
records = records.fillna("-")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
json_file_name = "ys-futsal-c94bf5ee6f76.json"
gc = gspread.service_account(filename=json_file_name, scopes=scope)
sh = gc.open("농구 기록")
worksheets = [worksheet.title for worksheet in sh.worksheets()]
if date not in worksheets:
    sh.add_worksheet(title=date, rows=records.shape[0] + 1, cols=records.shape[1] + 1)
worksheet = sh.worksheet(date)
worksheet.update([records.columns.values.tolist()] + records.values.tolist())
