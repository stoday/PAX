from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("math")

@mcp.tool()
def txai_budget(distance, city):
    """
    city: 縣市名稱 (string)，用於決定計價規則
    distance: 距離 (float)，單位為公里
    根據距離與縣市估算計程車費用，公式: 起跳價 + 續程費用 + 20% 彈性金額
    計算方式:
    1) 依縣市取得「起跳價」與「起程距離」 與 「續程單位距離」
    2) 若實際距離超過起程距離，續程距離 = (距離 - 起程距離)
    3) 小計 = 起跳價 + ceil(續程距離 / 每5元續程距離) * 5
    4) 總價 = 小計 * 1.2
    回傳格式: int 整數
    """
    # if distance is None or distance < 0:
    #     raise ValueError("distance 必須為非負數")

    # if not city:
    #     raise ValueError("city 不可為空")

    # 列出所有縣市與其對應的參數
    # 每縣市: start_fare(起跳價), start_distance(起程距離), unit_distance_per_5(每5元的續程距離)
    CITY_PRICING = {
        # 示例：起跳 85；起程 1.5km；每 0.25km 加 5 元
        "臺北市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "新北市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "基隆市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},

        # 示例：起跳 90；起程 2.0km；每 0.30km 加 5 元
        "桃園市":   {"start_fare": 90, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "新竹市":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "新竹縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "苗栗縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.2},

        "臺中市":   {"start_fare": 85, "start_distance": 1.5, "unit_distance_per_5": 0.2},
        "彰化縣":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "南投縣":   {"start_fare": 100, "start_distance": 1.5, "unit_distance_per_5": 0.25},

        "雲林縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.22},
        "嘉義市":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.22},
        "嘉義縣":   {"start_fare": 100, "start_distance": 1.25, "unit_distance_per_5": 0.22},
        "臺南市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},

        "高雄市":   {"start_fare": 85, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "屏東縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.2},

        "宜蘭縣":   {"start_fare": 120, "start_distance": 1.5, "unit_distance_per_5": 0.25},
        "花蓮縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.23},
        "臺東縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.23},
        "連江縣":   {"start_fare": 120, "start_distance": 1.25, "unit_distance_per_5": 0.2},
        "金門縣":   {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.2},
        "澎湖縣":   {"start_fare": 120, "start_distance": 1.0, "unit_distance_per_5": 0.2},
    }

    # 查找前將 '台' 正規化為 '臺'，避免不同寫法導致查找失敗
    city_key = str(city).strip().replace("台", "臺")
    print(city_key)
    # 預設值：若找不到對應縣市，使用這組參數
    DEFAULT_PRICING = {"start_fare": 100, "start_distance": 1.0, "unit_distance_per_5": 0.25}
    cfg = CITY_PRICING.get(city_key, DEFAULT_PRICING)

    start_fare = cfg["start_fare"]
    start_distance = cfg["start_distance"]
    unit_distance = cfg["unit_distance_per_5"]

    # 計算續程距離
    import math
    extra_distance = max(0.0, float(distance) - float(start_distance))
    blocks = math.ceil(extra_distance / float(unit_distance)) if extra_distance > 0 else 0
    continuation_price = blocks * 5
    subtotal = float(start_fare) + continuation_price
    total = int(round(subtotal * 1.2))

    # 回傳整數（四捨五入）
    return total

if __name__ == "__main__":
    # # 測試範例
    # test_cases = [
    #     (5.0, "臺北市"),
    #     (10.0, "高雄市"),
    #     (3.5, "花蓮縣"),
    #     (8.2, "未知市"),  # 使用預設計價
    # ]
    # for distance, city in test_cases:
    #     fare = txai_budget(distance, city)
    #     print(f"距離: {distance} km, 縣市: {city} => 計程車費用: {fare} 元")

    mcp.run(transport="stdio")
