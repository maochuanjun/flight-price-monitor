import json
import os
import time
import logging
from typing import Dict
import sys
import smtplib
from email.mime.text import MIMEText
from email.header import Header

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# 常量定义
BASE_URL = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice?"
RETRY_DELAY = 30  # 重试等待时间（秒）
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）
HISTORY_FILE = "price_history.json"

# 请求头，模拟浏览器以避免被拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://flights.ctrip.com/online/list/oneway",
    "Accept": "application/json, text/plain, */*",
}

# 机场代码到城市名称的映射
AIRPORT_CITY_MAP = {
    "BJS": "北京",
    "SHA": "上海(虹桥国际机场)",
    "PVG": "上海(浦东国际机场)",
    "CAN": "广州",
    "SZX": "深圳",
    "CTU": "成都",
    "HGH": "杭州",
    "WUH": "武汉",
    "SIA": "西安",
    "CKG": "重庆",
    "TAO": "青岛",
    "CSX": "长沙",
    "NKG": "南京",
    "XMN": "厦门",
    "KMG": "昆明",
    "DLC": "大连",
    "TSN": "天津",
    "CGO": "郑州",
    "SYX": "三亚",
    "TNA": "济南",
    "FOC": "福州",
    "AAT": "阿勒泰",
    "AKU": "阿克苏",
    "AOG": "鞍山",
    "AQG": "安庆",
    "AVA": "安顺",
    "AXF": "阿拉善左旗",
    "MFM": "中国澳门",
    "NGQ": "阿里",
    "RHT": "阿拉善右旗",
    "YIE": "阿尔山",
    "BZX": "巴中",
    "AEB": "百色",
    "BAV": "包头",
    "BFJ": "毕节",
    "BHY": "北海",
    "PKX": "北京(大兴国际机场)",
    "PEK": "北京(首都国际机场)",
    "BPL": "博乐",
    "BSD": "保山",
    "DBC": "白城",
    "KJI": "布尔津",
    "NBS": "白山",
    "RLK": "巴彦淖尔",
    "BPX": "昌都",
    "CDE": "承德",
    "CGD": "常德",
    "CGQ": "长春",
    "CHG": "朝阳",
    "CIF": "赤峰",
    "CIH": "长治",
    "CWJ": "沧源",
    "CZX": "常州",
    "JUH": "池州",
    "DAT": "大同",
    "DAX": "达州",
    "DCY": "稻城",
    "DDG": "丹东",
    "DIG": "迪庆",
    "DLU": "大理",
    "DNH": "敦煌",
    "DOY": "东营",
    "DQA": "大庆",
    "HXD": "德令哈",
    "DSN": "鄂尔多斯",
    "EJN": "额济纳旗",
    "ENH": "恩施",
    "ERL": "二连浩特",
    "FUG": "阜阳",
    "FYJ": "抚远",
    "FYN": "富蕴",
    "GMQ": "果洛",
    "GOQ": "格尔木",
    "GYS": "广元",
    "GYU": "固原",
    "KHH": "中国高雄",
    "KOW": "赣州",
    "KWE": "贵阳",
    "KWL": "桂林",
    "AHJ": "红原",
    "HAK": "海口",
    "HCJ": "河池",
    "HDG": "邯郸",
    "HEK": "黑河",
    "HET": "呼和浩特",
    "HFE": "合肥",
    "HIA": "淮安",
    "HJJ": "怀化",
    "HLD": "海拉尔",
    "HMI": "哈密",
    "HNY": "衡阳",
    "HRB": "哈尔滨",
    "HTN": "和田",
    "HTT": "花土沟",
    "HUN": "中国花莲",
    "HUO": "霍林郭勒",
    "HUZ": "惠州",
    "HZG": "汉中",
    "TXN": "黄山",
    "XRQ": "呼伦贝尔",
    "CYI": "中国嘉义",
    "JDZ": "景德镇",
    "JGD": "加格达奇",
    "JGN": "嘉峪关",
    "JGS": "井冈山",
    "JIC": "金昌",
    "JIU": "九江",
    "JM1": "荆门",
    "JMU": "佳木斯",
    "JNG": "济宁",
    "JNZ": "锦州",
    "JSJ": "建三江",
    "JXA": "鸡西",
    "JZH": "九寨沟",
    "KNH": "中国金门",
    "SWA": "揭阳",
    "KCA": "库车",
    "KGT": "康定",
    "KHG": "喀什",
    "KJH": "凯里",
    "KRL": "库尔勒",
    "KRY": "克拉玛依",
    "HZH": "黎平",
    "JMJ": "澜沧",
    "LCX": "龙岩",
    "LFQ": "临汾",
    "LHW": "兰州",
    "LJG": "丽江",
    "LLB": "荔波",
    "LLV": "吕梁",
    "LNJ": "临沧",
    "LNL": "陇南",
    "LPF": "六盘水",
    "LXA": "拉萨",
    "LYA": "洛阳",
    "LYG": "连云港",
    "LYI": "临沂",
    "LZH": "柳州",
    "LZO": "泸州",
    "LZY": "林芝",
    "LUM": "芒市",
    "MDG": "牡丹江",
    "MFK": "中国马祖",
    "MIG": "绵阳",
    "MXZ": "梅州",
    "MZG": "中国马公",
    "NZH": "满洲里",
    "OHE": "漠河",
    "KHN": "南昌",
    "LZN": "中国南竿",
    "NAO": "南充",
    "NGB": "宁波",
    "NLH": "宁蒗",
    "NNG": "南宁",
    "NNY": "南阳",
    "NTG": "南通",
    "PZI": "攀枝花",
    "SYM": "普洱",
    "BAR": "琼海",
    "BPE": "秦皇岛",
    "HBQ": "祁连",
    "IQM": "且末",
    "IQN": "庆阳",
    "JIQ": "黔江",
    "JJN": "泉州",
    "JUZ": "衢州",
    "NDG": "齐齐哈尔",
    "RIZ": "日照",
    "RKZ": "日喀则",
    "RQA": "若羌",
    "HPG": "神农架",
    "QSZ": "莎车",
    "SHE": "沈阳",
    "SHF": "石河子",
    "SJW": "石家庄",
    "SQD": "上饶",
    "SQJ": "三明",
    "WDS": "十堰",
    "WGN": "邵阳",
    "YSQ": "松原",
    "HYN": "台州",
    "RMQ": "中国台中",
    "TCG": "塔城",
    "TCZ": "腾冲",
    "TEN": "铜仁",
    "TGO": "通辽",
    "THQ": "天水",
    "TLQ": "吐鲁番",
    "TNH": "通化",
    "TNN": "中国台南",
    "TPE": "中国台北",
    "TTT": "中国台东",
    "TVS": "唐山",
    "TYN": "太原",
    "DTU": "五大连池",
    "HLH": "乌兰浩特",
    "UCB": "乌兰察布",
    "URC": "乌鲁木齐",
    "WEF": "潍坊",
    "WEH": "威海",
    "WNH": "文山",
    "WNZ": "温州",
    "WUA": "乌海",
    "WUS": "武夷山",
    "WUX": "无锡",
    "WUZ": "梧州",
    "WXN": "万州",
    "WZQ": "乌拉特中旗",
    "WSK": "巫山",
    "ACX": "兴义",
    "GXH": "夏河",
    "HKG": "中国香港",
    "JHG": "西双版纳",
    "NLT": "新源",
    "WUT": "忻州",
    "XAI": "信阳",
    "XFN": "襄阳",
    "XIC": "西昌",
    "XIL": "锡林浩特",
    "XNN": "西宁",
    "XUZ": "徐州",
    "ENY": "延安",
    "INC": "银川",
    "LDS": "伊春",
    "LLF": "永州",
    "UYN": "榆林",
    "YBP": "宜宾",
    "YCU": "运城",
    "YIC": "宜春",
    "YIH": "宜昌",
    "YIN": "伊宁",
    "YIW": "义乌",
    "YKH": "营口",
    "YNJ": "延吉",
    "YNT": "烟台",
    "YNZ": "盐城",
    "YTY": "扬州",
    "YUS": "玉树",
    "YYA": "岳阳",
    "DYG": "张家界",
    "HSN": "舟山",
    "NZL": "扎兰屯",
    "YZY": "张掖",
    "ZAT": "昭通",
    "ZHA": "湛江",
    "ZHY": "中卫",
    "ZQZ": "张家口",
    "ZUH": "珠海",
    "ZYI": "遵义",
}


def get_readable_location(airport_code: str) -> str:
    return AIRPORT_CITY_MAP.get(airport_code, airport_code)


def send_email(message: str, config: dict) -> bool:
    sender = config.get("email_sender")
    password = config.get("email_password")
    receiver = config.get("email_receiver")
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port", 465)

    if not all([sender, password, receiver, smtp_server]):
        logger.warning("邮件配置不完整，跳过发送")
        return False

    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = Header("航班价格提醒", "utf-8")

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()

        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        logger.info(f"邮件发送成功: {message}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def load_config_from_env() -> dict:
    """从环境变量加载配置"""
    try:
        # 必需的环境变量
        dates_str = os.environ.get("DATE_TO_GO")
        if not dates_str:
            raise ValueError("环境变量 DATE_TO_GO 未设置")

        dates = [d.strip() for d in dates_str.split(",") if d.strip()]

        config = {
            "dateToGo": dates,
            "placeFrom": os.environ.get("PLACE_FROM", "SHA"),
            "placeTo": os.environ.get("PLACE_TO", "JIQ"),
            "flightWay": os.environ.get("FLIGHT_WAY", "OneWay"),
            "priceStep": int(os.environ.get("PRICE_STEP", "50")),
            "email_sender": os.environ.get("EMAIL_SENDER"),
            "email_password": os.environ.get("EMAIL_PASSWORD"),
            "email_receiver": os.environ.get("EMAIL_RECEIVER"),
            "smtp_server": os.environ.get("SMTP_SERVER", "smtp.qq.com"),
            "smtp_port": int(os.environ.get("SMTP_PORT", "465")),
        }

        logger.info("从环境变量加载配置成功")
        return config
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        raise


def load_history() -> Dict[str, Dict[str, int]]:
    """加载历史价格数据"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
    return {"target_prices": {}, "no_target_prices": {}}


def save_history(history: Dict[str, Dict[str, int]]):
    """保存历史价格数据"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"保存历史数据失败: {e}")


def fetch_flight_prices(config: dict, direct: bool = True) -> dict:
    flight_way = config["flightWay"]
    if flight_way.lower() == "oneway":
        flight_way = "Oneway"
    elif flight_way.lower() == "roundtrip":
        flight_way = "Roundtrip"

    params = {
        "flightWay": flight_way,
        "dcity": config["placeFrom"].upper(),
        "acity": config["placeTo"].upper(),
        "army": "false",
        "classType": "ALL",
        "quantity": "1",
    }

    if direct:
        params["direct"] = "true"

    try:
        response = requests.get(
            BASE_URL, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == 2:
            raise ValueError(f"API返回错误状态: {data.get('msg', '未知错误')}")

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"获取{'直飞' if direct else '非直飞'}航班价格失败: {e}")
        raise


def main():
    try:
        config = load_config_from_env()
        history = load_history()

        # 确保历史数据中有当前日期的键
        target_prices = history.get("target_prices", {})
        no_target_prices = history.get("no_target_prices", {})

        # 初始化新日期的价格记录
        for date in config["dateToGo"]:
            if date not in target_prices:
                target_prices[date] = 0
            if date not in no_target_prices:
                no_target_prices[date] = 0

        logger.info("开始检查航班价格...")

        # 获取直飞和非直飞的机票信息
        direct_data = fetch_flight_prices(config, direct=True)
        non_direct_data = fetch_flight_prices(config, direct=False)

        if not direct_data.get("data") and not non_direct_data.get("data"):
            logger.warning("API返回数据为空")
            return

        direct_results_list = direct_data.get("data", {}).get("oneWayPrice", [])
        non_direct_results_list = non_direct_data.get("data", {}).get("oneWayPrice", [])

        direct_results = (
            direct_results_list[0]
            if (isinstance(direct_results_list, list) and direct_results_list)
            else {}
        )
        non_direct_results = (
            non_direct_results_list[0]
            if (isinstance(non_direct_results_list, list) and non_direct_results_list)
            else {}
        )

        notification_messages = []

        for date in config["dateToGo"]:
            direct_price = direct_results.get(date)
            non_direct_price = non_direct_results.get(date)

            if direct_price is None and non_direct_price is None:
                continue

            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"

            # 检查直飞价格
            if direct_price:
                last_price = target_prices.get(date, 0)
                if last_price == 0:
                    logger.info(f"首次记录 {formatted_date} 直飞价格: ¥{direct_price}")
                    notification_messages.append(
                        f"首次记录: {formatted_date} 直飞价格 ¥{direct_price}"
                    )
                    target_prices[date] = direct_price
                elif abs(direct_price - last_price) >= config["priceStep"]:
                    change_text = "上涨" if direct_price > last_price else "下降"
                    diff = abs(direct_price - last_price)
                    msg = f"{formatted_date} 直飞价格{change_text} ¥{diff} (¥{last_price} → ¥{direct_price})"
                    logger.info(msg)
                    notification_messages.append(msg)
                    target_prices[date] = direct_price

            # 检查非直飞价格
            if non_direct_price:
                last_price = no_target_prices.get(date, 0)
                if last_price == 0:
                    logger.info(
                        f"首次记录 {formatted_date} 非直飞价格: ¥{non_direct_price}"
                    )
                    notification_messages.append(
                        f"首次记录: {formatted_date} 非直飞价格 ¥{non_direct_price}"
                    )
                    no_target_prices[date] = non_direct_price
                elif abs(non_direct_price - last_price) >= config["priceStep"]:
                    change_text = "上涨" if non_direct_price > last_price else "下降"
                    diff = abs(non_direct_price - last_price)
                    msg = f"{formatted_date} 非直飞价格{change_text} ¥{diff} (¥{last_price} → ¥{non_direct_price})"
                    logger.info(msg)
                    notification_messages.append(msg)
                    no_target_prices[date] = non_direct_price

        # 发送通知
        if notification_messages:
            full_message = "\n".join(notification_messages)
            send_email(full_message, config)
        else:
            logger.info("价格无显著变化，不发送通知")

        # 保存历史数据
        history["target_prices"] = target_prices
        history["no_target_prices"] = no_target_prices
        save_history(history)

    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
