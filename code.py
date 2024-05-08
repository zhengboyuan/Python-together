import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
pd.options.mode.chained_assignment = None
# 设置 matplotlib 的默认字体为支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
# 设置页面配置
st.set_page_config(page_title="负荷分析应用", layout="wide")
# 创建一个空的DataFrame
df = pd.DataFrame()
selected_date = None
# 创建一个侧边栏
st.sidebar.title('数据上传')
data_file = st.sidebar.file_uploader('读取CSV文件', type=['csv'])
if data_file is not None:
    df = pd.read_csv(data_file, encoding="gbk")
    st.sidebar.write("<p style='color:green; font-weight:bold;'>文件上传成功。</p>", unsafe_allow_html=True)
    st.subheader("数据预览")
    st.dataframe(df.head())
    st.subheader("筛选时间预览")
    # 选择分析的户号
    unique_users = df['用户编号'].unique()
    selectbox = st.sidebar.selectbox('选择分析的户号:', unique_users, 0)
else:
    st.sidebar.write("<p style='color:red; font-weight:bold;'>请上传CSV文件。</p>", unsafe_allow_html=True)



def data_fuc(selected_date):
    if data_file is not None:
        
        if 'df1' in locals() or 'df1' in globals():
            # 将日期字段转换为datetime类型
            df1['day'] = pd.to_datetime(df1['day'])
            
            # 确保日期列是索引
            df1.set_index('day', inplace=True)
            #print('df1:',df1)
            # 计算负荷特性指标
            df1.loc[:, 'daily_average_load'] = df1['瞬时有功'].resample('D').mean()
            ## p_day_av 日平均负荷
            p_day_av = df1['瞬时有功'].resample('D').mean()
            print('********************')
            #print('p_day_av索引为:',p_day_av.index)
            #print('p_day_av为:',p_day_av)
            ## 日负荷率
            r_day = df1['瞬时有功'].resample('D').mean() / df1['瞬时有功'].resample('D').max()
            ## 日峰谷差
            P_day_div = df1['瞬时有功'].resample('D').max() - df1['瞬时有功'].resample('D').min()
            ## 日负荷标准差
            P_day_std = df1['瞬时有功'].resample('D').std()
            ## 日负荷波动率
            Sd = P_day_std / p_day_av
            
            df_month = df1['daily_average_load'].resample('M').mean()
            st.subheader("关键指标")
            per_1, per_2,per_3, per_4 = st.columns(4)
            per_5, per_6 = st.columns(2)
            print('********************')
            print('selected_date:',selected_date)
            selected_datetime = pd.to_datetime(selected_date)
            # 检查selected_datetime的类型和值
            print('selected_datetime转换后',selected_datetime)
            print('********************')
            year_mon =str(selected_datetime.year)+str(selected_datetime.month).zfill(2)
            year = selected_datetime.year
            month = selected_datetime.month
            print('年月：',year_mon)
            str_date = str(selected_datetime)[:10]
            str_month = str(selected_datetime)[:7]
            # 选择日期输入当日负荷曲线
            st.subheader(f"选择日期：{str_date} 负荷")
            #print('日负荷：',df1[df1.index==selected_datetime].columns)
            #print(df1['time'].iloc[0])
            power_day = df1[df1.index==selected_datetime]
            #print('power_day:',power_day)
            power_day.set_index('time', inplace=True)
            power_day = power_day['瞬时有功']
            st.line_chart(power_day)
            
            ## 选择日期输入当月负荷柱状图
            #print('输出月份：',month)
            power_month = df1[(df1.index.month == month)&(df1.index.year == year)]['瞬时有功']
            #print('power_month:',power_month)
            st.subheader(f"选择月份：{str_month} 负荷" )
            st.bar_chart(power_month)
            #print('当月负荷数据：',power_month)
            if selected_datetime in p_day_av.index:
                value_on_per1 = p_day_av.loc[selected_datetime]
                #print('index:',p_day_av.index)
                print('month:',month)
                #print(p_day_av[p_day_av.index.month== month])
                #print(p_day_av[p_day_av.index.month== year])
                #year_month_p_day_av = p_day_av[(p_day_av.index.year == year) & (p_day_av.index.month == month)]
                year_month_p_day_av = df1[(df1.index.year == year)&(df1.index.month == month)]
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
                st.metric(label="选择当月最大负荷（kW）", value=f"{year_month_p_day_av['瞬时有功'].max():.2f} ")
                st.caption("选择当月日瞬时有功的最大值")
            with per_6:
                st.metric(label="选择当月最小负荷（kW）", value=f"{year_month_p_day_av['瞬时有功'].min():.2f} ")
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
            


# 过滤数据并显示
try:
    if selectbox:
        df1 = df[df['用户编号'] == selectbox]
        #print('df_filtered:',df1)
        # 将日期字段转换为datetime类型
        df1.loc[:, '日期'] = pd.to_datetime(df1['日期'])  
        # 确保日期列是索引
        df1.set_index('日期', inplace=True)
        df1['day'] = df1.index
        df1['day'] = df1['day'].dt.date
        df1['time'] =df1['day'].index
        min_date = df1['day'].min()
        max_date = df1['day'].max()
        selected_date = st.sidebar.date_input("选择日期：", value=min_date, min_value=min_date, max_value=max_date)
        filtered_data = df1.loc[df1['day'] == selected_date, :].copy()
        st.sidebar.write("选择的日期：", selected_date)
        df_data = df1[df1['day'] == selected_date].copy()
        st.dataframe(df_data.iloc[:, -10:])
        data_fuc(selected_date)
except Exception as e:
    st.write("<p style='color:red; font-weight:bold;'>注意：文件未上传或发生其他错误。</p>", unsafe_allow_html=True)
    print("异常信息：", e)
