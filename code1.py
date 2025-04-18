import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
import streamlit as st

# 设置matplotlib字体支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 页面配置
st.set_page_config(page_title="负荷分析应用", layout="wide")

def load_and_process_data(file_uploader):
    """加载并预处理数据"""
    if file_uploader is not None:
        try:
            df = pd.read_csv(file_uploader, encoding="gbk", low_memory=False)
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            return df
        except Exception as e:
            st.sidebar.error(f"读取或处理文件时出错: {e}")
    return None

def display_sidebar(df):
    """侧边栏内容：选择户号和日期"""
    unique_users = df['用户编号'].unique() if df is not None else []
    selectbox = st.sidebar.selectbox('选择分析的户号:', unique_users, 0)
    min_date = df.index.min().date() if df is not None else None
    max_date = df.index.max().date() if df is not None else None
    selected_date = st.sidebar.date_input("选择日期：", value=min_date, min_value=min_date, max_value=max_date)
    return selectbox, selected_date

def calculate_metrics(df):
    """计算负荷特性指标"""
    # 计算日平均负荷等指标
    df.loc[df.index, 'daily_average_load'] = df['瞬时有功'].resample('D').mean()
    
    p_day_av = df['daily_average_load']
    #r_day = p_day_av / df['瞬时有功'].resample('D').max()
    r_day = df['瞬时有功'].resample('D').mean() / df['瞬时有功'].resample('D').max()
    P_day_div = df['瞬时有功'].resample('D').max() - df['瞬时有功'].resample('D').min()
    P_day_std = df['瞬时有功'].resample('D').std()
    Sd = P_day_std / p_day_av
    df_month = p_day_av.resample('M').mean()
    return p_day_av, r_day, P_day_div, P_day_std, Sd, df_month

def plot_results(df_filtered,selected_date, p_day_av, r_day, P_day_std, Sd, df_month):
    # 确保日负荷数据包含所有非缺失的 '瞬时有功' 数据
    df_filtered =df_filtered['瞬时有功']
    #df_filtered = df_filtered.dropna(subset=['瞬时有功'])
    
    # 计算日平均负荷
    # print('df_filtered:',df_filtered.index)
    p_day_av = df_filtered.resample('D').mean()
    selected_datetime = pd.to_datetime(selected_date)
    # 检查selected_datetime的类型和值
    # print('selected_datetime转换后',selected_datetime)
    str_date = str(selected_datetime)[:10]
    str_month = str(selected_datetime)[:7]
    # 选择日期输入当日负荷曲线
    st.subheader(f"选择日期：{str_date} 负荷")
    #print('日负荷：',df1[df1.index==selected_datetime].columns)
    #print(df1['time'].iloc[0])
    
    year_mon =str(selected_datetime.year)+str(selected_datetime.month).zfill(2)
    year = selected_datetime.year
    month = selected_datetime.month
    # print('power_day处理前:',df_filtered)
    # print('******************************')
    # print('date:',selected_datetime.date())
    power_day = df_filtered[df_filtered.index.date==selected_datetime.date()]
    #print('power_day:',power_day)
    #power_day.set_index('time', inplace=True)
    st.line_chart(power_day)
    
    ## 选择日期输入当月负荷柱状图
    #print('输出月份：',month)
    power_month = p_day_av[(p_day_av.index.month == month)&(p_day_av.index.year == year)]
    st.subheader(f"选择月份：{str_month} 负荷" )
    st.bar_chart(power_month)
    
    # print('p_day_av:',p_day_av)
    # print('r_day:',r_day)
    st.subheader('关键指标展示')
    per_1, per_2,per_3, per_4 = st.columns(4)
    per_5, per_6 = st.columns(2)
    if selected_datetime in p_day_av.index:
        value_on_per1 = p_day_av.loc[selected_datetime]
        #print(p_day_av[p_day_av.index.month== month])
        #print(p_day_av[p_day_av.index.month== year])
        #year_month_p_day_av = p_day_av[(p_day_av.index.year == year) & (p_day_av.index.month == month)]
        year_month_p_day_av = df_filtered[(df_filtered.index.year == year)&(df_filtered.index.month == month)]
        #print('结果：', year_month_p_day_av)
        
        value_on_per1_1 = value_on_per1- p_day_av.shift(1).loc[selected_datetime]
        value_on_per2 = r_day.loc[selected_datetime]
        value_on_per2_1 = value_on_per2- r_day.shift(1).loc[selected_datetime]
        value_on_per3 = P_day_std.loc[selected_datetime]
        value_on_per3_1 = value_on_per3- P_day_std.shift(1).loc[selected_datetime]
        value_on_per4 = Sd.loc[selected_datetime]
        value_on_per4_1 = value_on_per4- Sd.shift(1).loc[selected_datetime]
    else:
        value_on_per1 = value_on_per2 = value_on_per3 = value_on_per4 = None
    with per_1:
        st.metric(label="日平均负荷（kW）", value=f"{value_on_per1:.2f} ", delta=f"{value_on_per1_1:.2f}")
        st.caption("日瞬时有功的平均值")
    with per_2:
        st.metric(label="日负荷率（%）", value=f"{round(value_on_per2, 2)}", delta=f"{value_on_per2_1:.2f}")
        st.caption("日平均负荷/日最大负荷")
    with per_3:
        st.metric(label="日负荷标准差", value=f"{int(value_on_per3)} KWh", delta=f"{value_on_per3_1:.2f}")
        st.caption("日负荷标准差")
    with per_4:
        st.metric(label="日负荷波动率（%）", value=f"{round(value_on_per4, 2)}", delta=f"{value_on_per4_1:.2f}")
        st.caption("日负荷标准差/日平均负荷（kW）")
    with per_5:
        st.metric(label="选择当月最大负荷（kW）", value=f"{year_month_p_day_av.max():.2f} ")
        st.caption("选择当月日瞬时有功的最大值")
    with per_6:
        st.metric(label="选择当月最小负荷（kW）", value=f"{year_month_p_day_av.min():.2f} ")
        st.caption("选择当月日瞬时有功的最小值")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("日平均负荷")
        st.line_chart(p_day_av)
    with col2:
        st.subheader("月平均负荷")
        st.bar_chart(df_month)
    st.markdown("--------------")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("日负荷率")
        st.line_chart(r_day)
    with col4:
        st.subheader("日负荷波动率")
        st.bar_chart(Sd)
    
    
def main():
    print('****************************')
    print('开始执行：')
    print('****************************')
    data_file = st.sidebar.file_uploader('读取CSV文件', type=['csv'])
    df = load_and_process_data(data_file)
    
    if df is not None:
        st.sidebar.write("<p style='color:green; font-weight:bold;'>文件上传成功。</p>", unsafe_allow_html=True)
        st.subheader("数据预览")
        st.dataframe(df.head())
        
        selectbox, selected_date = display_sidebar(df)
        
        if selectbox and selected_date:
            df_filtered = df[df['用户编号'] == selectbox]
            p_day_av, r_day, _, P_day_std, Sd, df_month = calculate_metrics(df_filtered)
            plot_results(df_filtered,selected_date, p_day_av, r_day, P_day_std, Sd, df_month)
    else:
        st.sidebar.write("<p style='color:red; font-weight:bold;'>请上传CSV文件。</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
