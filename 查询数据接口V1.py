#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 11:04:24 2024

@author: zhengboyuan
"""

import http.client
import hashlib
import hmac
import time
from urllib.parse import urlencode, urlunparse, urlparse, parse_qs, quote
import pandas as pd
import json
import datetime
import streamlit as st
import seaborn as sns  # 可选，用于更好的默认样式
import traceback
from datetime import date
def generate_token(access_key, access_secret, http_method, url):
    # Get current millisecond timestamp
    access_timestamp_ms = int(time.time() * 1000)
    # access_timestamp_ms = 1721013637624
    # Construct the sign key with sorted dictionary and millisecond timestamp
    params = {
        "accessKey": access_key,
        "accessTs": access_timestamp_ms,
        "httpMethod": http_method,
        "url": escape_url_params(url)
    }
    sign_key = kv_tokenize(params)
    # print('sign_key:', sign_key)
    # Generate HMAC
    hmac_sha256 = hmac.new(sign_key.encode(), access_secret.encode(), hashlib.sha256)
    # print('hmac_sha256:', hmac_sha256)
    hmac_digest = hmac_sha256.hexdigest()
    # print('hmac_digest:', hmac_digest)
    # Results
    token = hmac_digest
    ts_ms = access_timestamp_ms
    return token, ts_ms

# 转换时间戳为标准时间格式
def timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp / 1000)
def kv_tokenize(dict):
    res = ""
    for key, value in sorted(dict.items()):
        if isinstance(value, list):
            for v in value:
                res += key + "=" + str(v) + "&"
        else:
            res += key + "=" + str(value) + "&"
    return res[:-1]
def escape_url_params(url):
    # 解析URL
    parsed_url = urlparse(url)
    # 重新组合URL
    new_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        escape_qs(parsed_url),
        parsed_url.fragment
    ))
    return new_url
def escape_qs(parsed_url):
    # 获取查询参数
    params = parse_qs(parsed_url.query)
    # 转义每个参数的值
    escaped_params = {
        key: [urlencode({key: value})[len(key) + 1:] for value in values]
        for key, values in params.items()
    }
    return kv_tokenize(escaped_params)

def st_sidebar():
    LOGO_URL_LARGE = 'https://pic.imgdb.cn/item/667f9aa9d9c307b7e90ae152.jpg'
    st.sidebar.markdown(
        f"""
        <style>
        .custom-logo {{
            width: 100px;  /* 您希望的大小 */
            height: 80;
        }}
        </style>
        <img src="{LOGO_URL_LARGE}" class="custom-logo">
        """,
        unsafe_allow_html=True
    )

    ## 侧边栏函数，返回option,select_date,start_time,end_time,select_start_time,select_end_time
    option = st.sidebar.selectbox("选择表计", 
                                  ("黄冈产业园增量配电网测量数据", "保碧储能站测量数据"),
                                  index=1,
                                  key='selectbox_option')

    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    day_before_yesterday = yesterday - datetime.timedelta(days=1)
    next_year = today.year
    jan_1 = datetime.date(next_year, 1, 1)
    dec_31 = datetime.date(next_year+2, 12, 31)
    # 创建一个包含开始日期和结束日期的元组
    # default_date = (day_before_yesterday, yesterday)
    # 默认昨天时间数据
    default_date = (yesterday, yesterday)
    select_date = st.sidebar.date_input(
        "开始日期-结束日期",
        default_date,
        jan_1,
        dec_31,
        format="MM.DD.YYYY",
        key='date_input'
    )

    # 确保日期被完整选择
    if len(select_date) == 2 and select_date[1] <= today.date():
        # 时间选择输入
        t1 = st.sidebar.time_input("开始时间", value=datetime.time(12, 00), key='time_input_start')
        t2 = st.sidebar.time_input("结束时间", value=datetime.time(23, 45), key='time_input_end')

        # 构造时间字符串
        select_start_time = f"{select_date[0]} {t1}"
        select_end_time = f"{select_date[1]} {t2}"
    else:
        # 如果日期未完整选择，显示警告并使用默认处理
        st.warning("请选择完整或正确的日期范围（开始日期和结束日期）。")
        select_start_time = ""
        select_end_time = ""
        t1 = st.sidebar.time_input("开始时间", value=datetime.time(12, 00), key='time_input_start_default')
        t2 = st.sidebar.time_input("结束时间", value=datetime.time(23, 45), key='time_input_end_default')

    if len(select_date) > 1:
        try:
            select_end_time = str(select_date[1]) + ' ' + str(t2)
        except Exception as e:
            st.error(f"发生未知错误：{e}", icon="🚨")
    else:
        st.warning("选择的日期不完整，无法获取结束时间。")

    try:
        start_time = select_start_time
        end_time = select_end_time
    except:
        st.warning("选择的日期未满足要求请重新选择。")

    time_interva_option = st.sidebar.selectbox("选择时间间隔（分钟）",
                                               ("1", "15", "30", "60"),
                                               index=2,
                                               key='selectbox_time_interval')

    pv_price = st.sidebar.slider("光伏上网电价", 0.00, 1.00, 0.01, key='slider_pv_price')
    tip_electricity_price = st.sidebar.slider("尖电价", 0.00, 1.00, 0.7, step=0.01, key='slider_tip_electricity_price')
    peak_electricity_price = st.sidebar.slider("峰电价", 0.00, 1.00, 0.6, step=0.01, key='slider_peak_electricity_price')
    valley_electricity_price = st.sidebar.slider("谷电价", 0.00, 1.00, 0.51, step=0.01, key='slider_valley_electricity_price')
    average_electricity_price = st.sidebar.slider("平电价", 0.00, 1.00, 0.5, step=0.01, key='slider_average_electricity_price')

    query_button_clicked = st.sidebar.button("查询", key='button_query'
                                             # ,on_click= main()
                                             )

    length = len(select_date)
    return (option, select_date, start_time, end_time, select_start_time,
            select_end_time, time_interva_option,
            tip_electricity_price, peak_electricity_price, valley_electricity_price, average_electricity_price
            ,query_button_clicked
            , length)

def interface_read_data(option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price,length):
    access_key = "chint-hubei"
    access_secret = "UIJLL(q0BZq0y5tKq"
    http_method = "GET"
    host = "api.eiot6.com"
    # option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price,query_button_clicked,length =st_sidebar()
    if length<2:
        st.warning("开始时间和结束时间未完整选择，无法发起接口请求。")
        return None  # 或者根据需要返回其他提示信息或数据
    if option== '黄冈产业园增量配电网测量数据':
        uri_template  = "/vpp-aggr/open-api/v1/control_unit/measurements/history?aggregatorNo=91421100MA49DL1B77&edgeId=nation_hubei_grid&gridAcct=4206916039019&startDate={start_time}&endDate={end_time}&interval={time_interva_option}"
    else:
        uri_template  = "/vpp-aggr/open-api/v1/control_unit/measurements/history?aggregatorNo=pN6MWCf5bnKsBNQU&edgeId=nation_hubei_grid&gridAcct=10112101970&startDate={start_time}&endDate={end_time}&interval={time_interva_option}"
    uri_with_time = uri_template.format(start_time=start_time, end_time=end_time,time_interva_option=time_interva_option)
    url = f'https://{host}{uri_with_time}'
    # Generate token and timestamp
    token, ts = generate_token(access_key, access_secret, http_method, url)
    conn = http.client.HTTPSConnection(host)
    payload = ''
    headers = {
        'X-ACCESS-KEY': access_key,
        'X-ACCESS-TOKEN': token,
        'X-ACCESS-TS': ts
    }
    p = urlparse(url)
    qs = escape_qs(p)
    conn.request(http_method, f'{p.path}?{qs}', payload, headers)
    res = conn.getresponse()
    data = res.read()
    return data,option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price

def data_process(data,k):
    ## data dataframe；k 列名
    # 提取 'P' 值和 'ts' 值
    p_values = [item['data'][k] for item in data['data']]
    ts_values = [item['ts'] for item in data['data']]
    # 转换提取的 ts 值
    ts_datetime_values = [timestamp_to_datetime(ts) for ts in ts_values]
    # 将 'P' 值和 'ts' 值转换为 DataFrame
    df_p = pd.DataFrame({ 'ts': ts_datetime_values
                         ,k: p_values})
    
    df_p['day'] = df_p['ts'].dt.day
    df_p['time'] = df_p['ts'].dt.time
    # 确保时间列是正确的日期时间格式
    df_p['ts'] = pd.to_datetime(df_p['ts'])
    #将time列设置为索引
    df_p.set_index('time',inplace = True)
    
    return df_p

def datafram_group(df_p,name,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price):
    df_p['period'] = df_p['ts'].apply(lambda x: classify_energy_period(x, x.hour, x.month))
    # 按日期和时段类型分组，计算每组的最大值和最小值
    grouped = df_p.groupby(['period',])[name].agg(['min', 'max'])
    df_p['price'] = df_p['period'].apply(
                                        lambda period: apply_price_rule(
                                            period=period,
                                            tip_electricity_price=tip_electricity_price,
                                            peak_electricity_price=peak_electricity_price,
                                            valley_electricity_price=valley_electricity_price,
                                            average_electricity_price=average_electricity_price
                                        )
                                    )
    grouped_with_price = df_p.groupby(['period', 'price']).agg(
        {name: ['min', 'max'],  # 假定name是你关心进行min和max计算的列名
          'price': ['first']}  # 显式指定price列，并使用first保持原值
    )
    
    # 重置列名以去除外层多层索引结构
    grouped_with_price.columns = grouped_with_price.columns.get_level_values(1)
    grouped_diff = grouped_with_price['max'] - grouped_with_price['min']
    grouped_result = grouped_diff * grouped_with_price['first']
    sum_1 = round(grouped_result.sum(),3)
    return sum_1
def plot_data(df_p,select_start_time,select_end_time,parameters
              ,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price
              ,re_TotalChargeEnergy,re_TotalDischargeEnergy):
    """
    根据给定的dataframe 开始时间、结束时间、表计参数绘制折线图。
    
    :param df_p: 输入的dataframe。
    :param select_start_time: 选择的开始时间。
    :param select_end_time: 选择的结束时间。
    :param parameters: 选择的表计参数。
    :return: df_pivot dataframe。
    """
    df_pivot = df_p.pivot(columns = 'day',values = parameters)
    df_pivot = df_pivot.dropna(how='any')
    st.subheader(f'{select_start_time}-{select_end_time} {parameters}参数分析')
    col1, col2= st.columns(2)
    col1.metric(f"{parameters}最大值", df_pivot.max().max())
    col2.metric(f"{parameters}最小值", df_pivot.min().min())
    if parameters == 'TotalChargeEnergy':
        col3, col4= st.columns(2)
        charging_electricity_amount= df_pivot.max().max()-df_pivot.min().min()
        charging_cost = round(charging_electricity_amount*valley_electricity_price,0)
        col3.metric(f"充电电量（kWh）", charging_electricity_amount)
        col4.metric(f"充电成本（元）",re_TotalChargeEnergy )
    elif parameters == 'TotalDischargeEnergy':
        col3, col4= st.columns(2)
        Discharging_electricity_amount= df_pivot.max().max()-df_pivot.min().min()
        Discharging_cost = round(Discharging_electricity_amount*tip_electricity_price,0)
        col3.metric(f"放电电量（kWh）", Discharging_electricity_amount)
        col4.metric(f"放电收益（元）",re_TotalDischargeEnergy )
    # 绘制折线图
    df_pivot.index = df_pivot.index.astype(str)
    st.line_chart(data=df_pivot
                  ,x_label= '时间'
                  ,y_label = parameters
                  )
    #df_pivot.T
    df_pivot = df_pivot.apply(lambda x: round(x, 2) if x.dtype == 'float64' else x)
    df_pivot = df_pivot.T
    st.dataframe(df_pivot.style.highlight_max(axis=0))
    return df_pivot
def classify_energy_period(date_time, hour, month):
    """
    根据给定的日期和时间，将其分类为高峰、非高峰或低谷时段。
    
    :param date_time: 代表特定日期和时间的datetime对象。
    :param hour: 表示一天中的小时数（0-23）的整数。
    :param month: 表示一年中月份（1-12）的整数。
    :return: 表示时段类型的字符串（"高峰"、"非高峰"或"低谷"）。
    """
    if 0 <= hour < 6 or 12 <= hour < 14:
        return "低谷时段"
    elif 6 <= hour < 12 or 14 <= hour < 16:
        return "平时段"
    
    # Special conditions for July and August
    if month in [7, 8]:
        if 16 <= hour < 20 or 22 <= hour <= 23:
            return "高峰时段"
        elif 20 <= hour < 22:
            return "尖峰时段"
    else:  # For other months
        if 16 <= hour < 18 or 20 <= hour <= 23:
            return "高峰时段"
        elif 18 <= hour < 20:
            return "尖峰时段"
    
    # In case an unexpected hour is provided, default to a period (this line should理论上不会执行如果输入有效)
    return "未知时段"
def apply_price_rule(period,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price):
    price_rules = {"低谷时段": valley_electricity_price
                   ,"平时段": average_electricity_price
                   , "高峰时段": peak_electricity_price
                   , "尖峰时段": tip_electricity_price}
    return price_rules.get(period, None)

def main(option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option
         ,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price
         ,query_button_clicked,length):
    print("*******开始!*********")
    start = time.time()
    standard_time = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')
    print('查询时间：',standard_time)
    # option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price,query_button_clicked,length= st_sidebar() 
    # 如选择两个时间段执行；
    if length>1:
        # data,option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price =interface_read_data(option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price,length)
        data =interface_read_data(option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price,length)[0]
        data = json.loads(data.decode("utf-8"))
        #判断数据请求是否成功
        if data['success']:
            # st.info('数据接口请求成功!')
            st.toast('数据接口请求成功!', icon='🎉')
            parameter_names = list(data['data'][-1]['data'].keys())
            # 创建多选菜单
            multiselect = st.multiselect( "选择参数", parameter_names)
            # 如果用户做出了选择
            if multiselect  :
                for name in multiselect:
                    df_p = data_process(data, name)
                    df_p['period'] = df_p['ts'].apply(lambda x: classify_energy_period(x, x.hour, x.month))
                    # 按日期和时段类型分组，计算每组的最大值和最小值
                    grouped = df_p.groupby(['day', 'period',])[name].agg(['min', 'max'])
                    df_p['price'] = df_p['period'].apply(
                                                        lambda period: apply_price_rule(
                                                            period=period,
                                                            tip_electricity_price=tip_electricity_price,
                                                            peak_electricity_price=peak_electricity_price,
                                                            valley_electricity_price=valley_electricity_price,
                                                            average_electricity_price=average_electricity_price
                                                        )
                                                    )
                    # df_p
                    grouped = df_p.groupby(['day', 'period','price'])[name].agg(['min', 'max'])
                    # df_p, grouped= datafram_group(df_p,name,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price)
                    try:
                        # 定义起始日期
                        start_date_to_check = date(2024, 7, 17)
                        # 检查起始日期是否在7月14日之后
                        is_after_july_17 = select_date[1] <= start_date_to_check
                        # 输出结果
                        if is_after_july_17:
                            st.info("选择的数据包含7月17日之前的日期，接口数据不完整。")
                        else:
                            if option =='保碧储能站测量数据':
                                df_TotalChargeEnergy = data_process(data, 'TotalChargeEnergy')
                                re_TotalChargeEnergy =datafram_group(df_TotalChargeEnergy,'TotalChargeEnergy',tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price)
                                df_TotalDischargeEnergy = data_process(data, 'TotalDischargeEnergy')
                                re_TotalDischargeEnergy =datafram_group(df_TotalDischargeEnergy,'TotalDischargeEnergy',tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price)
                                plot_data(df_p, select_start_time, select_end_time, name
                                          ,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price
                                          ,re_TotalChargeEnergy,re_TotalDischargeEnergy)
                            else:
                                plot_data(df_p, select_start_time, select_end_time, name
                                          ,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price
                                          ,re_TotalChargeEnergy=None,re_TotalDischargeEnergy=None)
                    except:
                        st.error("数据绘图展示失败，7月14日前参数有缺失可以选择之后的数据。", icon="🚨")
            if not multiselect:
                st.info("请选择参数分析！")
        else:
            st.warning('数据接口请求失败!!!')
        end = time.time() 
        elapsed = round(end - start,2)
        print(f"Elapsed Time: {elapsed} seconds")
        print("******* 结束！*********")
if __name__ == '__main__':
    # 设置页面配置
    st.set_page_config(page_title="虚拟电厂数据查询", page_icon="🏠")
    option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price,query_button_clicked,length = st_sidebar()
    print("query_button_clicked:",query_button_clicked)
    main(option,select_date,start_time,end_time,select_start_time,select_end_time,time_interva_option,tip_electricity_price,peak_electricity_price,valley_electricity_price,average_electricity_price,query_button_clicked,length)