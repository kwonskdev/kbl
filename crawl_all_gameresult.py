import time as sleep

import gspread
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

SEASON_KEY = "S43G01N"

key_list = [f"{SEASON_KEY}{i}" for i in range(1, 271)]
results = pd.DataFrame()

for key in key_list:
    url = f"https://www.kbl.or.kr/game/record/{key}"
    driver.get(url)
    sleep.sleep(0.2)

    date = driver.find_elements(By.XPATH, '//*[@id="container"]/div/ul[1]/li[2]/ul/li[2]/span')[0].text
    date = date[:10]  # 2024.03.28 (목)

    player_detail_record = driver.find_elements(By.XPATH, '//*[@id="container"]/div/ul[2]/li[2]')[0]
    player_detail_record.click()
    sleep.sleep(0.2)

    home_team_xpath = '//*[@id="container"]/div/div[3]/div/div[2]/div[1]/div[1]/div/h6'
    home_team = driver.find_elements(By.XPATH, home_team_xpath)[0].text
    home_players = driver.find_elements(By.XPATH, '//*[@id="container"]/div/div[5]/div[2]/div[1]')[0]
    home_players = pd.read_html(home_players.get_attribute("innerHTML"))[0]

    home_records = driver.find_elements(By.XPATH, '//*[@id="container"]/div/div[5]/div[2]/div[2]')[0]
    home_records = pd.read_html(home_records.get_attribute("innerHTML"))[0]

    home_records = pd.concat([home_players, home_records], axis=1)
    home_records["Team"] = home_team
    home_records["Date"] = date

    away_team_xpath = '//*[@id="container"]/div/div[3]/div/div[2]/div[1]/div[3]/div/h6'
    away_team = driver.find_elements(By.XPATH, away_team_xpath)[0].text
    away_players = driver.find_elements(By.XPATH, '//*[@id="container"]/div/div[6]/div[2]/div[1]')[0]
    away_players = pd.read_html(away_players.get_attribute("innerHTML"))[0]

    away_records = driver.find_elements(By.XPATH, '//*[@id="container"]/div/div[6]/div[2]/div[2]')[0]
    away_records = pd.read_html(away_records.get_attribute("innerHTML"))[0]

    away_records = pd.concat([away_players, away_records], axis=1)
    away_records["Team"] = away_team
    away_records["Date"] = date

    result = pd.concat([home_records, away_records])
    results = pd.concat([results, result])

results.columns = [col[0] if col[0] == col[1] else f"{col[0]} {col[1]}" for col in results.columns]
results.columns = [col.strip() for col in results.columns]
results = results.rename(columns={"No": "Starting", "No No.1": "No"})
results = results.query("Starting!='합계'").copy()

season = results["Date"].str[:4].min() + "-" + results["Date"].str[:4].max()
results["SEASON"] = season
results = results.fillna("-")

if results.shape[1] == 12 * 2 * 270:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    json_file_name = "ys-futsal-c94bf5ee6f76.json"
    gc = gspread.service_account(filename=json_file_name, scopes=scope)
    sh = gc.open("시즌별 전구단 기록")
    worksheets = [worksheet.title for worksheet in sh.worksheets()]
    if season not in worksheets:
        sh.add_worksheet(title=season, rows=results.shape[0] + 1, cols=results.shape[1] + 1)
    worksheet = sh.worksheet(season)
    worksheet.update([results.columns.values.tolist()] + results.values.tolist())
