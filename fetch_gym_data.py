"""
抓取台北市運動中心即時人數資料（內湖運動中心）
資料來源：台北市運動中心預約系統 API
執行後會把資料以 append 的方式寫入 gym_data.csv
"""

import requests
import csv
import os
from datetime import datetime, timezone, timedelta

API_URL = "https://booking-tpsc.sporetrofit.com/Home/loadLocationPeopleNum"
TARGET_LID = "NHSC"  # 內湖運動中心代碼
CSV_PATH = "gym_data.csv"

# 台北時區 (UTC+8)，因為 GitHub Actions 伺服器預設是 UTC 時間
TAIPEI_TZ = timezone(timedelta(hours=8))


def fetch_data():
    """呼叫 API，回傳所有運動中心的 JSON 資料"""
    response = requests.post(API_URL, timeout=15)
    response.raise_for_status()  # 如果請求失敗會直接噴錯，方便在 Actions log 中發現問題
    return response.json()


def extract_location_list(data):
    """
    API 回傳的最外層格式不一定是陣列，也可能是物件包著陣列，例如：
    {"data": [...]} 或 {"result": [...]} 等。
    這裡自動判斷並找出真正裝著各運動中心資料的那個陣列。
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value
        raise ValueError(
            f"回傳的物件裡找不到任何陣列欄位，實際格式為: {data}"
        )

    raise ValueError(f"未預期的回傳格式: {type(data)} -> {data}")


def extract_target_location(data, lid):
    """從全部運動中心資料中，找出指定的那一間"""
    locations = extract_location_list(data)
    for location in locations:
        if location.get("LID") == lid:
            return location
    raise ValueError(f"找不到 LID={lid} 的運動中心資料，回傳資料可能改格式了")


def append_to_csv(record):
    """把一筆資料寫進 CSV，如果檔案不存在就先寫入標題列"""
    file_exists = os.path.isfile(CSV_PATH)

    with open(CSV_PATH, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


def main():
    now = datetime.now(TAIPEI_TZ)
    data = fetch_data()

    try:
        location = extract_target_location(data, TARGET_LID)
    except ValueError:
        print("解析失敗，印出原始回傳資料方便排查：")
        print(data)
        raise

    record = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "weekday": now.strftime("%A"),  # Monday, Tuesday...
        "gym_people_num": location.get("gymPeopleNum"),
        "gym_max_people_num": location.get("gymMaxPeopleNum"),
        "sw_people_num": location.get("swPeopleNum"),
        "sw_max_people_num": location.get("swMaxPeopleNum"),
    }

    append_to_csv(record)
    print(f"寫入成功: {record}")


if __name__ == "__main__":
    main()
