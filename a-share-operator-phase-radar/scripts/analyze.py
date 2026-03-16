#!/usr/bin/env python3
"""
A股庄家阶段分析工具
用法: python analyze.py 洛阳钼业
     python analyze.py 603993
"""

import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import os

# 清除代理环境变量，让所有 HTTP 请求直连（必须在 requests/akshare import 之前执行）
for _k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
           "all_proxy", "ALL_PROXY"):
    os.environ.pop(_k, None)
os.environ["no_proxy"] = "*"
os.environ["NO_PROXY"] = "*"

import pandas as pd
import numpy as np
import akshare as ak

STOCK_LIST_PATH = Path(__file__).parent.parent / "stockList.json"


# ============================================================
#  股票名称 → 代码 模糊搜索
# ============================================================

def find_stock_code(query: str) -> tuple[str, str]:
    """
    通过名称、拼音缩写或代码查找股票，返回 (code, name)

    优先级：精确代码 > 精确名称 > 名称包含 > 拼音缩写
    示例：query="洛阳钼业" → ("603993", "洛阳钼业")
    """
    with open(STOCK_LIST_PATH, encoding="utf-8") as f:
        data = json.load(f)

    stocks = data["stockList"]
    query = query.strip()

    # 1. 精确代码匹配
    for s in stocks:
        if s["code"] == query:
            return s["code"], s["zwjc"]

    # 2. 精确名称匹配
    for s in stocks:
        if s["zwjc"] == query:
            return s["code"], s["zwjc"]

    # 3. 名称包含匹配
    matches = [s for s in stocks if query in s["zwjc"]]
    if len(matches) == 1:
        return matches[0]["code"], matches[0]["zwjc"]
    if len(matches) > 1:
        # 优先返回最短名称（最精确）
        matches.sort(key=lambda s: len(s["zwjc"]))
        return matches[0]["code"], matches[0]["zwjc"]

    # 4. 拼音缩写匹配（不区分大小写）
    query_lower = query.lower()
    for s in stocks:
        if s.get("pinyin", "").lower() == query_lower:
            return s["code"], s["zwjc"]

    raise ValueError(f"未找到股票：{query!r}，请检查名称或代码")


# ============================================================
#  带重试的 AKShare API 调用
# ============================================================

def fetch_with_retry(func, *args, max_retries=3, delay=2, **kwargs):
    """带指数退避重试的 AKShare API 调用包装器"""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                wait = delay * (attempt + 1)
                print(f"  ⚠️ 第{attempt + 1}次请求失败，{wait}秒后重试: {e}")
                time.sleep(wait)
    raise last_exc


# ============================================================
#  衍生指标计算
# ============================================================

def calculate_indicators(df_daily):
    """
    输入: stock_zh_a_hist 返回的日K线 DataFrame
    输出: (enriched_df, summary_dict)
    """
    df = df_daily.copy()
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)

    # 均线系统
    for period in [5, 20, 60, 120, 250]:
        df[f"MA{period}"] = df["收盘"].rolling(window=period).mean()

    # 成交量均线
    df["VOL_MA5"]  = df["成交量"].rolling(window=5).mean()
    df["VOL_MA20"] = df["成交量"].rolling(window=20).mean()
    df["VOL_MA60"] = df["成交量"].rolling(window=60).mean()

    # 量比（当日成交量 / 近5日均量）
    df["量比"] = df["成交量"] / df["VOL_MA5"]

    latest   = df.iloc[-1]
    last_5   = df.tail(5)
    last_20  = df.tail(20)
    last_60  = df.tail(60)
    last_120 = df.tail(120)
    last_250 = df.tail(250)

    current_price = latest["收盘"]

    # 近1年最高/最低价
    year_high = last_250["最高"].max() if len(last_250) >= 60 else df["最高"].max()
    year_low  = last_250["最低"].min() if len(last_250) >= 60 else df["最低"].min()

    # 当前价在1年区间的百分位
    price_percentile = (
        (current_price - year_low) / (year_high - year_low) * 100
        if year_high != year_low else 50
    )

    def calc_change(n_days):
        if len(df) >= n_days:
            old_price = df.iloc[-n_days]["收盘"]
            return (current_price - old_price) / old_price * 100
        return None

    change_3m = calc_change(60)
    change_6m = calc_change(120)
    change_1y = calc_change(250)

    turnover_5  = last_5["换手率"].mean()
    turnover_20 = last_20["换手率"].mean()

    vol_ma20 = last_20["成交量"].mean()
    vol_ma60 = last_60["成交量"].mean() if len(last_60) >= 60 else vol_ma20

    amplitude_20 = last_20["振幅"].mean()

    if len(last_60) >= 20:
        range_60_high  = last_60["最高"].max()
        range_60_low   = last_60["最低"].min()
        oscillation_60 = (range_60_high / range_60_low - 1) * 100
    else:
        oscillation_60 = 0

    ma5   = latest.get("MA5", None)
    ma20  = latest.get("MA20", None)
    ma60  = latest.get("MA60", None)
    ma120 = latest.get("MA120", None)

    if all(v is not None and not np.isnan(v) for v in [ma5, ma20, ma60, ma120]):
        if ma5 > ma20 > ma60 > ma120:
            ma_arrangement = "多头排列"
        elif ma5 < ma20 < ma60 < ma120:
            ma_arrangement = "空头排列"
        else:
            ma_arrangement = "缠绕/过渡"
    else:
        ma_arrangement = "数据不足"

    ma250 = latest.get("MA250", None)
    above_ma250 = (
        current_price > ma250
        if ma250 is not None and not np.isnan(ma250)
        else None
    )

    low_20       = last_20["最低"].min()
    low_not_new  = low_20 > year_low

    if len(last_60) >= 20:
        ma5_s  = last_60["MA5"].dropna()
        ma20_s = last_60["MA20"].dropna()
        if len(ma5_s) > 1 and len(ma20_s) > 1:
            aligned   = pd.DataFrame({"ma5": ma5_s, "ma20": ma20_s}).dropna()
            crosses   = ((aligned["ma5"] > aligned["ma20"]).astype(int).diff().abs().sum()) / 2
            ma_cross_count = int(crosses)
        else:
            ma_cross_count = 0
    else:
        ma_cross_count = 0

    bullish_5 = (last_5["收盘"] > last_5["开盘"]).sum()

    if len(last_20) >= 5:
        rolling_max = last_20["最高"].expanding().max()
        new_highs   = (last_20["最高"] == rolling_max).sum()
    else:
        new_highs = 0

    def has_long_upper_shadow(row):
        body  = abs(row["收盘"] - row["开盘"])
        upper = row["最高"] - max(row["收盘"], row["开盘"])
        return upper > body * 2 if body > 0 else False

    long_upper_count = last_20.apply(has_long_upper_shadow, axis=1).sum()

    if len(last_250) >= 60:
        max_vol_1y    = last_250["成交量"].max()
        has_sky_volume = last_5["成交量"].max() >= max_vol_1y * 0.9
    else:
        has_sky_volume = False

    summary = {
        "当前股价":             current_price,
        "近1年最高":            year_high,
        "近1年最低":            year_low,
        "价格百分位":           round(price_percentile, 1),
        "近3月涨跌幅":          round(change_3m, 2) if change_3m is not None else None,
        "近6月涨跌幅":          round(change_6m, 2) if change_6m is not None else None,
        "近1年涨跌幅":          round(change_1y, 2) if change_1y is not None else None,
        "近5日平均换手率":      round(turnover_5, 2),
        "近20日平均换手率":     round(turnover_20, 2),
        "近20日均量":           round(vol_ma20),
        "近60日均量":           round(vol_ma60),
        "量比_20vs60":          round(vol_ma20 / vol_ma60, 2) if vol_ma60 > 0 else None,
        "近20日平均振幅":       round(amplitude_20, 2),
        "近60日最大振幅区间":   round(oscillation_60, 1),
        "均线排列":             ma_arrangement,
        "股价在年线之上":       above_ma250,
        "近20日低点高于年低点": low_not_new,
        "近60日MA5/MA20交叉次数": ma_cross_count,
        "近5日阳线数":          int(bullish_5),
        "近20日创新高次数":     int(new_highs),
        "近20日长上影线次数":   int(long_upper_count),
        "近5日出现天量":        has_sky_volume,
    }

    return df, summary


# ============================================================
#  筹码分布本地计算（东方财富三角分布衰减算法，无需外部API）
# ============================================================

def _compute_cyq_metrics(chips: np.ndarray, min_price: float, accuracy: float,
                         factor: int, current_price: float) -> dict:
    """从筹码数组计算各项指标（内部辅助函数）"""
    total = chips.sum()
    if total == 0:
        return None

    price_levels = min_price + accuracy * np.arange(factor)

    # 获利比例：当前价及以下的筹码占比
    profit_ratio = chips[price_levels <= current_price].sum() / total

    # 平均成本（加权均价）
    avg_cost = float((price_levels * chips).sum() / total)

    # 按累积比例查找价格（getCostByChip）
    def cost_at_pct(pct: float) -> float:
        target = total * pct
        cumsum = 0.0
        for i in range(factor):
            cumsum += chips[i]
            if cumsum > target:
                return float(min_price + i * accuracy)
        return float(min_price + (factor - 1) * accuracy)

    low_90  = cost_at_pct(0.05)
    high_90 = cost_at_pct(0.95)
    low_70  = cost_at_pct(0.15)
    high_70 = cost_at_pct(0.85)

    def concentration(lo: float, hi: float) -> float:
        return (hi - lo) / (hi + lo) if (hi + lo) > 0 else 0.0

    con_90 = concentration(low_90, high_90)
    con_70 = concentration(low_70, high_70)

    cost_premium = (current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0.0
    price_in_range_90 = (
        (current_price - low_90) / (high_90 - low_90) * 100
        if high_90 > low_90 else 50.0
    )

    return {
        "获利比例":           round(profit_ratio * 100, 1),
        "平均成本":           round(avg_cost, 2),
        "成本溢价率":         round(cost_premium, 1),
        "90集中度":           round(con_90, 4),
        "70集中度":           round(con_70, 4),
        "90成本区间":         f"{low_90:.2f} ~ {high_90:.2f}",
        "70成本区间":         f"{low_70:.2f} ~ {high_70:.2f}",
        "当前价在90区间位置": round(min(max(price_in_range_90, 0.0), 100.0), 1),
    }


def calculate_cyq_from_kline(df_daily) -> dict | None:
    """
    从日K线数据本地计算筹码分布，无需任何网络请求。

    算法：东方财富三角分布衰减法（与 stock_cyq_em 使用的 JS 算法等价）
      - 每个交易日，旧筹码按换手率衰减：chips *= (1 - 换手率)
      - 当日新增筹码按 (低价→均价→高价) 三角形分布叠加
      - 最终筹码数组即为当前持仓分布快照

    输入: stock_zh_a_hist 返回的日K线 DataFrame（需含 开盘/收盘/最高/最低/换手率）
    输出: 筹码指标摘要字典，或 None（数据不足时）
    """
    FACTOR  = 150   # 价格档位数（与东方财富一致）
    LOOKBACK = 210  # 参与计算的交易日数

    df = df_daily.tail(LOOKBACK).reset_index(drop=True)
    n  = len(df)
    if n < 20:
        return None

    max_price = float(df["最高"].max())
    min_price = float(df["最低"].min())
    if max_price == min_price:
        return None

    # 精度不小于 0.01（与 JS 一致）
    accuracy = max(0.01, (max_price - min_price) / (FACTOR - 1))

    chips      = np.zeros(FACTOR)
    snap_10ago = None   # 10日前快照，用于计算趋势

    for idx in range(n):
        row     = df.iloc[idx]
        open_p  = float(row["开盘"])
        close_p = float(row["收盘"])
        high_p  = float(row["最高"])
        low_p   = float(row["最低"])
        hsl     = min(1.0, float(row["换手率"] or 0) / 100)

        avg = (open_p + close_p + high_p + low_p) / 4

        H = min(int((high_p - min_price) / accuracy), FACTOR - 1)
        L = max(int(np.ceil((low_p  - min_price) / accuracy)), 0)

        # 旧筹码衰减
        chips *= (1 - hsl)

        # 叠加新筹码（三角分布）
        if high_p == low_p:
            # 一字板：等效矩形，面积为三角的 2 倍
            g_y = min(int((avg - min_price) / accuracy), FACTOR - 1)
            chips[g_y] += (FACTOR - 1) * hsl / 2
        else:
            g_x = 2.0 / (high_p - low_p)
            for j in range(L, H + 1):
                cur = min_price + accuracy * j
                if cur <= avg:
                    denom = avg - low_p
                    chips[j] += (g_x * hsl if abs(denom) < 1e-8
                                 else (cur - low_p) / denom * g_x * hsl)
                else:
                    denom = high_p - avg
                    chips[j] += (g_x * hsl if abs(denom) < 1e-8
                                 else (high_p - cur) / denom * g_x * hsl)

        # 保存 10 日前快照
        if idx == n - 11:
            snap_10ago = (_compute_cyq_metrics(chips.copy(), min_price, accuracy,
                                               FACTOR, close_p))

    current_price = float(df.iloc[-1]["收盘"])
    result = _compute_cyq_metrics(chips, min_price, accuracy, FACTOR, current_price)
    if result is None:
        return None

    # 趋势：与 10 日前对比
    if snap_10ago:
        result["获利比例趋势"] = round(result["获利比例"] - snap_10ago["获利比例"], 2)
        result["集中度趋势"]   = round(result["90集中度"]  - snap_10ago["90集中度"],  4)
    else:
        result["获利比例趋势"] = None
        result["集中度趋势"]   = None

    return result


# ============================================================
#  四阶段判断逻辑（含资金流向 + 龙虎榜 + 筹码分布加分）
# ============================================================

def judge_stage(summary, df_fund=None, df_lhb=None, cyq_summary=None):
    """
    输入: summary 字典 + 可选资金流向 DataFrame + 可选龙虎榜 DataFrame
    输出: { "stage", "confidence", "scores", "details", "transition" }
    """
    scores  = {"建仓": 0, "洗盘": 0, "拉升": 0, "出货": 0}
    details = {"建仓": [], "洗盘": [], "拉升": [], "出货": []}
    s = summary

    # =============================================
    #  阶段一：建仓
    # =============================================

    if s["近1年涨跌幅"] is not None and s["近1年涨跌幅"] < -15:
        scores["建仓"] += 1
        details["建仓"].append(f"✅ 近1年涨跌幅 {s['近1年涨跌幅']}% < -15%")
    else:
        details["建仓"].append(f"❌ 近1年涨跌幅 {s.get('近1年涨跌幅', 'N/A')}%")

    if s["量比_20vs60"] is not None and s["量比_20vs60"] < 0.7:
        scores["建仓"] += 1
        details["建仓"].append(f"✅ 20/60日均量比 {s['量比_20vs60']}，持续缩量")
    else:
        details["建仓"].append(f"❌ 20/60日均量比 {s.get('量比_20vs60', 'N/A')}")

    if s["近20日平均换手率"] < 2:
        scores["建仓"] += 1
        details["建仓"].append(f"✅ 近20日平均换手率 {s['近20日平均换手率']}% < 2%")
    else:
        details["建仓"].append(f"❌ 近20日平均换手率 {s['近20日平均换手率']}%")

    if s["近20日平均振幅"] < 3:
        scores["建仓"] += 1
        details["建仓"].append(f"✅ 近20日平均振幅 {s['近20日平均振幅']}% < 3%")
    else:
        details["建仓"].append(f"❌ 近20日平均振幅 {s['近20日平均振幅']}%")

    if s["价格百分位"] < 25:
        scores["建仓"] += 1
        details["建仓"].append(f"✅ 价格百分位 {s['价格百分位']}%（低位区间）")
    else:
        details["建仓"].append(f"❌ 价格百分位 {s['价格百分位']}%")

    if s["股价在年线之上"] is False:
        scores["建仓"] += 1
        details["建仓"].append("✅ 股价在MA250年线之下")
    else:
        details["建仓"].append("❌ 股价在MA250年线之上或数据不足")

    # =============================================
    #  阶段二：洗盘
    # =============================================

    if 20 <= s["近60日最大振幅区间"] <= 40:
        scores["洗盘"] += 1
        details["洗盘"].append(f"✅ 近60日振幅区间 {s['近60日最大振幅区间']}%（20%-40%）")
    else:
        details["洗盘"].append(f"❌ 近60日振幅区间 {s['近60日最大振幅区间']}%")

    if s["量比_20vs60"] is not None and s["量比_20vs60"] > 1.2:
        scores["洗盘"] += 1
        details["洗盘"].append(f"✅ 20/60日均量比 {s['量比_20vs60']}，温和放量")
    else:
        details["洗盘"].append(f"❌ 20/60日均量比 {s.get('量比_20vs60', 'N/A')}")

    if 2 <= s["近20日平均换手率"] <= 6:
        scores["洗盘"] += 1
        details["洗盘"].append(f"✅ 近20日平均换手率 {s['近20日平均换手率']}%（2%-6%）")
    else:
        details["洗盘"].append(f"❌ 近20日平均换手率 {s['近20日平均换手率']}%")

    if s["近20日低点高于年低点"]:
        scores["洗盘"] += 1
        details["洗盘"].append("✅ 近20日低点高于1年最低点（未创新低）")
    else:
        details["洗盘"].append("❌ 近期创新低")

    if s["近60日MA5/MA20交叉次数"] >= 3:
        scores["洗盘"] += 1
        details["洗盘"].append(f"✅ 近60日均线交叉 {s['近60日MA5/MA20交叉次数']} 次（缠绕）")
    else:
        details["洗盘"].append(f"❌ 近60日均线交叉 {s['近60日MA5/MA20交叉次数']} 次")

    if s["均线排列"] == "缠绕/过渡":
        scores["洗盘"] += 1
        details["洗盘"].append("✅ 均线处于缠绕/过渡状态")
    else:
        details["洗盘"].append(f"❌ 均线排列：{s['均线排列']}")

    # =============================================
    #  阶段三：拉升
    # =============================================

    if s["近3月涨跌幅"] is not None and s["近3月涨跌幅"] > 30:
        scores["拉升"] += 1
        details["拉升"].append(f"✅ 近3月涨跌幅 {s['近3月涨跌幅']}% > 30%")
    else:
        details["拉升"].append(f"❌ 近3月涨跌幅 {s.get('近3月涨跌幅', 'N/A')}%")

    if s["均线排列"] == "多头排列":
        scores["拉升"] += 1
        details["拉升"].append("✅ 均线多头排列 (MA5>MA20>MA60>MA120)")
    else:
        details["拉升"].append(f"❌ 均线排列：{s['均线排列']}")

    if s["量比_20vs60"] is not None and s["量比_20vs60"] > 1.5:
        scores["拉升"] += 1
        details["拉升"].append(f"✅ 20/60日均量比 {s['量比_20vs60']}，明显放量")
    else:
        details["拉升"].append(f"❌ 20/60日均量比 {s.get('量比_20vs60', 'N/A')}")

    if 3 <= s["近20日平均换手率"] <= 8:
        scores["拉升"] += 1
        details["拉升"].append(f"✅ 近20日平均换手率 {s['近20日平均换手率']}%（3%-8%）")
    else:
        details["拉升"].append(f"❌ 近20日平均换手率 {s['近20日平均换手率']}%")

    if s["价格百分位"] > 70:
        scores["拉升"] += 1
        details["拉升"].append(f"✅ 价格百分位 {s['价格百分位']}%（高位区间）")
    else:
        details["拉升"].append(f"❌ 价格百分位 {s['价格百分位']}%")

    if s["近20日创新高次数"] >= 5:
        scores["拉升"] += 1
        details["拉升"].append(f"✅ 近20日创新高 {s['近20日创新高次数']} 次")
    else:
        details["拉升"].append(f"❌ 近20日创新高 {s['近20日创新高次数']} 次")

    if s["近5日阳线数"] >= 4:
        scores["拉升"] += 1
        details["拉升"].append(f"✅ 近5日阳线 {s['近5日阳线数']} 根（连续上涨）")
    else:
        details["拉升"].append(f"❌ 近5日阳线 {s['近5日阳线数']} 根")

    # =============================================
    #  阶段四：出货
    # =============================================

    if s["价格百分位"] > 80:
        scores["出货"] += 1
        details["出货"].append(f"✅ 价格百分位 {s['价格百分位']}%（高位区间）")
    else:
        details["出货"].append(f"❌ 价格百分位 {s['价格百分位']}%")

    if s["近5日平均换手率"] > 10:
        scores["出货"] += 2  # 危险信号，权重加倍
        details["出货"].append(f"⚠️ 近5日平均换手率 {s['近5日平均换手率']}% > 10%（危险！）")
    elif s["近5日平均换手率"] > 8:
        scores["出货"] += 1
        details["出货"].append(f"✅ 近5日平均换手率 {s['近5日平均换手率']}% > 8%（偏高）")
    else:
        details["出货"].append(f"❌ 近5日平均换手率 {s['近5日平均换手率']}%")

    if s["量比_20vs60"] is not None and s["量比_20vs60"] > 2.0:
        scores["出货"] += 1
        details["出货"].append(f"✅ 20/60日均量比 {s['量比_20vs60']}，巨量放大")
    else:
        details["出货"].append(f"❌ 20/60日均量比 {s.get('量比_20vs60', 'N/A')}")

    if s["近20日平均振幅"] > 5:
        scores["出货"] += 1
        details["出货"].append(f"✅ 近20日平均振幅 {s['近20日平均振幅']}%（波动剧烈）")
    else:
        details["出货"].append(f"❌ 近20日平均振幅 {s['近20日平均振幅']}%")

    if s["近20日长上影线次数"] >= 3:
        scores["出货"] += 1
        details["出货"].append(f"✅ 近20日长上影线 {s['近20日长上影线次数']} 次（卖压重）")
    else:
        details["出货"].append(f"❌ 近20日长上影线 {s['近20日长上影线次数']} 次")

    if s["近6月涨跌幅"] is not None and s["近6月涨跌幅"] > 50:
        scores["出货"] += 1
        details["出货"].append(f"✅ 近6月涨跌幅 {s['近6月涨跌幅']}%（前期拉升明显）")
    else:
        details["出货"].append(f"❌ 近6月涨跌幅 {s.get('近6月涨跌幅', 'N/A')}%")

    if s["近5日出现天量"]:
        scores["出货"] += 1
        details["出货"].append("⚠️ 近5日出现天量（近1年最大成交量）")
    else:
        details["出货"].append("❌ 未出现天量")

    # =============================================
    #  资金流向加分（可选）
    # =============================================

    if df_fund is not None and len(df_fund) > 0:
        recent_fund   = df_fund.tail(20)
        col           = "主力净流入-净额"
        if col in recent_fund.columns:
            net_sum    = recent_fund[col].sum()
            avg_abs    = recent_fund[col].abs().mean()

            if net_sum > 0 and abs(net_sum) < avg_abs * 10:
                scores["建仓"] += 1
                details["建仓"].append("✅ 主力资金小幅净流入（暗中吸筹）")

            if net_sum > avg_abs * 10:
                scores["拉升"] += 1
                details["拉升"].append("✅ 主力资金持续大幅净流入（拉升信号）")

            if net_sum < -avg_abs * 10:
                scores["出货"] += 1
                details["出货"].append("⚠️ 主力资金大幅净流出（出货信号）")

    # =============================================
    #  龙虎榜席位加分（可选）
    # =============================================

    if df_lhb is not None and len(df_lhb) > 0:
        # 尝试识别机构席位
        inst_col = None
        for col_name in df_lhb.columns:
            if "机构" in str(col_name) or "买入额" in str(col_name):
                inst_col = col_name
                break

        # 基于买入/卖出净额判断
        buy_col  = next((c for c in df_lhb.columns if "买入" in str(c) and "净" not in str(c)), None)
        sell_col = next((c for c in df_lhb.columns if "卖出" in str(c) and "净" not in str(c)), None)

        if buy_col and sell_col:
            total_buy  = pd.to_numeric(df_lhb[buy_col], errors="coerce").sum()
            total_sell = pd.to_numeric(df_lhb[sell_col], errors="coerce").sum()
            net        = total_buy - total_sell

            if net > 0:
                scores["建仓"] += 1
                scores["拉升"] += 1
                details["建仓"].append(f"✅ 龙虎榜席位净买入 {net/1e8:.2f}亿（建仓/拉升信号）")
                details["拉升"].append(f"✅ 龙虎榜席位净买入 {net/1e8:.2f}亿")
            elif net < 0:
                scores["出货"] += 1
                details["出货"].append(f"⚠️ 龙虎榜席位净卖出 {abs(net)/1e8:.2f}亿（出货信号）")

    # =============================================
    #  筹码分布加分（可选）
    # =============================================

    if cyq_summary is not None:
        cyq = cyq_summary

        # --- 获利比例 ---
        profit = cyq["获利比例"]
        if profit < 20:
            scores["建仓"] += 1
            details["建仓"].append(f"✅ 获利比例 {profit}%（大量套牢，吸筹特征）")
        elif profit > 80:
            scores["出货"] += 1
            details["出货"].append(f"⚠️ 获利比例 {profit}%（高度获利，出货风险高）")
        elif 20 <= profit <= 50:
            scores["洗盘"] += 1
            details["洗盘"].append(f"✅ 获利比例 {profit}%（洗盘区间，多空分歧）")

        # --- 筹码集中度（90%） ---
        con = cyq["90集中度"]
        if con < 0.1:
            scores["建仓"] += 1
            scores["洗盘"] += 1
            details["建仓"].append(f"✅ 90%筹码集中度 {con}（高度集中，庄家控盘）")
            details["洗盘"].append(f"✅ 90%筹码集中度 {con}（高度集中）")
        elif con > 0.3:
            scores["出货"] += 1
            details["出货"].append(f"⚠️ 90%筹码集中度 {con}（筹码分散，派发特征）")

        # --- 成本溢价率 ---
        premium = cyq["成本溢价率"]
        if premium > 50:
            scores["出货"] += 1
            details["出货"].append(f"⚠️ 当前价高于平均成本 {premium}%（高溢价，出货风险）")
        elif -10 <= premium <= 15:
            scores["洗盘"] += 1
            details["洗盘"].append(f"✅ 当前价接近平均成本（溢价 {premium}%，洗盘区间）")
        elif premium < -10:
            scores["建仓"] += 1
            details["建仓"].append(f"✅ 当前价低于平均成本 {abs(premium):.1f}%（破成本价，底部特征）")

        # --- 获利比例趋势（快速上升=拉升信号）---
        p_trend = cyq["获利比例趋势"]
        if p_trend is not None and p_trend > 5:
            scores["拉升"] += 1
            details["拉升"].append(f"✅ 近10日获利比例上升 +{p_trend}%（拉升信号）")
        elif p_trend is not None and p_trend < -5:
            scores["建仓"] += 1
            details["建仓"].append(f"✅ 近10日获利比例下降 {p_trend}%（套牢盘增加，吸筹机会）")

        # --- 集中度趋势（持续收窄=吸筹中，快速发散=派发）---
        c_trend = cyq["集中度趋势"]
        if c_trend is not None and c_trend < -0.02:
            scores["建仓"] += 1
            details["建仓"].append(f"✅ 筹码集中度持续收窄（庄家持续吸筹）")
        elif c_trend is not None and c_trend > 0.02:
            scores["出货"] += 1
            details["出货"].append(f"⚠️ 筹码集中度快速发散（派发迹象）")

    # =============================================
    #  综合判断
    # =============================================

    max_score = max(scores.values())
    stage     = max(scores, key=scores.get)

    total_conditions = {"建仓": 6, "洗盘": 6, "拉升": 7, "出货": 7}
    match_rate = max_score / total_conditions.get(stage, 6)

    if match_rate >= 0.7:
        confidence = "高"
    elif match_rate >= 0.5:
        confidence = "中"
    else:
        confidence = "低"

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    transition    = None
    if len(sorted_scores) >= 2 and sorted_scores[0][1] - sorted_scores[1][1] <= 1:
        transition = f"{sorted_scores[0][0]} → {sorted_scores[1][0]}"

    return {
        "stage":      stage,
        "confidence": confidence,
        "scores":     scores,
        "details":    details,
        "transition": transition,
    }


# ============================================================
#  完整分析流程
# ============================================================

def analyze_stock(query: str):
    """
    完整分析流程
    query: 股票代码或名称，如 "603993" 或 "洛阳钼业"
    """

    # Step 1: 解析股票代码
    print(f"\n正在查找股票：{query} ...")
    try:
        code, name = find_stock_code(query)
        print(f"  找到：{name}（{code}）")
    except ValueError as e:
        print(f"  ❌ {e}")
        return None

    # Step 2: 获取基本信息
    try:
        df_info    = fetch_with_retry(ak.stock_individual_info_em, symbol=code)
        stock_name = df_info[df_info["item"] == "股票简称"]["value"].values[0]
    except Exception as e:
        stock_name = name
        print(f"  ⚠️ 获取基本信息失败（使用默认名称）: {e}")

    # Step 3: 获取日K线数据（近3年）
    today      = datetime.today()
    start_date = (today - timedelta(days=365 * 3)).strftime("%Y%m%d")
    end_date   = today.strftime("%Y%m%d")

    print(f"\n正在获取 {stock_name} K线数据（{start_date} ~ {end_date}）...")
    try:
        df_daily = fetch_with_retry(
            ak.stock_zh_a_hist,
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        if df_daily is None or len(df_daily) == 0:
            print("  ❌ 未获取到K线数据，请检查股票代码")
            return None
        print(f"  获取成功，共 {len(df_daily)} 条记录")
    except Exception as e:
        print(f"  ❌ K线数据获取失败: {e}")
        return None

    # Step 4: 计算衍生指标
    print("\n正在计算衍生指标...")
    df_enriched, summary = calculate_indicators(df_daily)
    print("  计算完成")

    # Step 5: 获取资金流向（可选）
    df_fund = None
    print("\n正在获取资金流向数据（可选）...")
    try:
        if code.startswith("6"):
            market = "sh"
        elif code.startswith(("8", "9")):
            market = "bj"
        else:
            market = "sz"
        df_fund = fetch_with_retry(
            ak.stock_individual_fund_flow,
            stock=code,
            market=market,
        )
        print(f"  获取成功，共 {len(df_fund)} 条记录")
    except Exception as e:
        print(f"  ⚠️ 资金流向获取失败（不影响核心判断）: {e}")

    # Step 6: 获取龙虎榜数据（可选）
    df_lhb = None
    print("\n正在获取龙虎榜数据（可选）...")
    try:
        df_lhb = fetch_with_retry(ak.stock_lhb_stock_detail_em, symbol=code)
        if df_lhb is not None and len(df_lhb) > 0:
            print(f"  获取成功，共 {len(df_lhb)} 条记录")
        else:
            print("  近期无龙虎榜记录")
            df_lhb = None
    except Exception as e:
        print(f"  ⚠️ 龙虎榜数据获取失败（不影响核心判断）: {e}")

    # Step 7: 本地计算筹码分布（基于已有K线数据，无需网络）
    print("\n正在计算筹码分布（本地算法）...")
    try:
        cyq_summary = calculate_cyq_from_kline(df_daily)
        if cyq_summary:
            print(f"  计算完成（基于近 {min(210, len(df_daily))} 个交易日）")
        else:
            print("  ⚠️ 数据不足，跳过筹码分布")
    except Exception as e:
        cyq_summary = None
        print(f"  ⚠️ 筹码分布计算失败: {e}")

    # Step 8: 判断阶段
    print("\n正在分析庄家阶段...")
    result = judge_stage(summary, df_fund, df_lhb, cyq_summary)

    # Step 8: 输出结果
    vol_ratio    = summary.get("量比_20vs60")
    vol_label    = (
        "放量" if vol_ratio and vol_ratio > 1.2
        else "缩量" if vol_ratio and vol_ratio < 0.8
        else "平稳"
    )
    price_label  = (
        "低位" if summary["价格百分位"] < 30
        else "中位" if summary["价格百分位"] < 70
        else "高位"
    )
    danger_label = " ⚠️ 危险!" if summary["近5日平均换手率"] > 10 else ""

    print(f"""
═══════════════════════════════════════════════════
  {stock_name}（{code}）庄家阶段分析
═══════════════════════════════════════════════════

  当前判断：【{result['stage']}阶段】
  置信度：{result['confidence']}
  各阶段得分：建仓={result['scores']['建仓']} | 洗盘={result['scores']['洗盘']} | 拉升={result['scores']['拉升']} | 出货={result['scores']['出货']}""")

    if result["transition"]:
        print(f"  可能处于过渡期：{result['transition']}")

    # 筹码分布文字
    if cyq_summary:
        profit = cyq_summary["获利比例"]
        profit_label = "大量套牢" if profit < 30 else "多空分歧" if profit < 60 else "高度获利"
        con_90 = cyq_summary["90集中度"]
        con_label = "高度集中" if con_90 < 0.1 else "较为集中" if con_90 < 0.2 else "中等分散" if con_90 < 0.3 else "高度分散"
        cyq_block = f"""
── 筹码分布 ────────────────────────────────────────
  获利比例：{profit}%（{profit_label}）
  平均成本：{cyq_summary['平均成本']} 元（溢价 {cyq_summary['成本溢价率']}%）
  90%筹码区间：{cyq_summary['90成本区间']} 元
  70%筹码区间：{cyq_summary['70成本区间']} 元
  筹码集中度（90%）：{con_90}（{con_label}）
  当前价在90%区间位置：{cyq_summary['当前价在90区间位置']}%"""
    else:
        cyq_block = "\n── 筹码分布 ────────────────────────────────────────\n  ⚠️ 数据获取失败"

    print(f"""
── 关键数据 ────────────────────────────────────────
  当前股价：{summary['当前股价']} 元
  近1年涨跌幅：{summary.get('近1年涨跌幅', 'N/A')}%
  价格百分位：{summary['价格百分位']}%（{price_label}）
  近5日平均换手率：{summary['近5日平均换手率']}%{danger_label}
  近20日平均换手率：{summary['近20日平均换手率']}%
  20/60日均量比：{vol_ratio}（{vol_label}）
  近60日最大振幅区间：{summary['近60日最大振幅区间']}%
  均线排列：{summary['均线排列']}
{cyq_block}
""")

    stage_order = ["建仓", "洗盘", "拉升", "出货"]
    for stage_name in stage_order:
        marker = "👉 " if stage_name == result["stage"] else "   "
        print(f"{marker}── {stage_name}阶段（得分: {result['scores'][stage_name]}）──")
        for d in result["details"][stage_name]:
            print(f"     {d}")
        print()

    print("""── 风险提示 ────────────────────────────────────────
  ⚠️ 本分析仅供参考，不构成投资建议
  ⚠️ 庄家判断存在主观性，市场有风险
  ⚠️ 换手率 > 10% 时需高度警惕
═══════════════════════════════════════════════════
""")

    return result


# ============================================================
#  CLI 入口
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze.py <股票代码或名称>")
        print("示例: python analyze.py 洛阳钼业")
        print("      python analyze.py 603993")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    analyze_stock(query)
