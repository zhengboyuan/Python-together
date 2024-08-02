import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta,time
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
    CT = st.sidebar.number_input("CT", value=100, step=100)
    PT = st.sidebar.number_input("PT", value=100, step=100)
    selectbox = st.sidebar.selectbox('选择分析的户号:', unique_users, 0)
    min_date = df.index.min().date() if df is not None else None
    max_date = df.index.max().date() if df is not None else None
    selected_date = st.sidebar.date_input("选择日期：", value=min_date, min_value=min_date, max_value=max_date)
    main_capacity = st.sidebar.number_input("主变容量（kVA）", value=2000,step=100)
    ues_per = st.sidebar.number_input("主变容量利用率（%）", value=85, step=5)
    select_power_start = st.sidebar.number_input("选定瞬时功率开始值（kW）", value=1000, step=50)
    select_power_step = st.sidebar.number_input("选定瞬时功率间隔值（kW）", value=10,help='选定瞬时功率间隔值，默认10,进行递增')
    low_start_time = st.sidebar.time_input("设置谷时段开始时间",step=3600,value=time(11, 0),help='默认11点开始')
    low_end_time = st.sidebar.time_input("设置谷时段结束时间",step=3600,value=time(14, 0))
    up_start_time = st.sidebar.time_input("设置尖时段开始时间",step=3600,value=time(18, 0),help='默认18点开始')
    up_end_time = st.sidebar.time_input("设置尖时段结束时间",step=3600,value=time(20, 0))
        # 检查时间设置是否正确
    if low_start_time.hour == up_start_time.hour or low_end_time.hour == up_end_time.hour:
        st.sidebar.warning(":red[***谷时段与尖时段的开始、结束时间一致，请检查！***]")
    elif low_start_time.hour < low_end_time.hour and up_start_time.hour < up_end_time.hour:
        st.sidebar.write('**时间设置条件：**', 
                          '谷时段开始时间:', low_start_time.strftime('%H点'), 
                          '； 谷时段结束时间:', low_end_time.strftime('%H点'), 
                          '； 尖时段开始时间:', up_start_time.strftime('%H点'), 
                          '； 尖时段结束时间:', up_end_time.strftime('%H点'))
    else:
        st.sidebar.warning(":red[***存在开始时间大于结束时间的情况，请检查！***]")

    return selectbox, selected_date,main_capacity,ues_per,CT,PT,select_power_start,select_power_step

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
        st.metric(label="日平均负荷（kW）", value=f"{value_on_per1:.2f} ", delta=f"{value_on_per1_1:.2f}",help='计算展示日平均符合及与前一日差值')
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
def power_lower(df, selectbox, selected_date,main_capacity,ues_per,CT,PT,select_power_start,select_power_step):
    """
    中午谷电时间段数据判断装机量分析函数
    输入：
    1、df 输出整体datafrmae, 
    2、selectbox 选择的分析户号,
    3、selected_date 选择的日期,
    4、main_capacity 主变容量,
    5、ues_per 主变容量利用率,
    6、CT,
    7、PT,
    8、select_power_start 选定瞬时功率开始值,
    9、select_power_step 选定瞬时功率间隔值
    输出：中午谷电时间段数据判断装机量部分相关参数输出
    """
    filtered_df =df[
        (
        (((df.index.hour == 11) & (df.index.minute >= 10)))|
        (((df.index.hour == 12) & (df.index.minute >= 0)))|
        (((df.index.hour == 13) & (df.index.minute >= 0)))|
        (((df.index.hour == 14) & (df.index.minute == 0)))
        )
        ]
    # st.dataframe(filtered_df.sort_index(ascending=True))
    rate =[]
    power = []
    for i in range(select_power_start,select_power_start+select_power_step*50,select_power_step):
        re= filtered_df[filtered_df['瞬时有功']<i].shape[0]/filtered_df.shape[0]
        re = round(re,4)
        power.append(i)
        rate.append(re)
    rate_df = pd.DataFrame({'power':power,'rate':rate})
    rate_df['365_rate']= round(rate_df['rate']*365,2)
    st.write('______________________________________')
    st.subheader('中午谷电时间段数据判断装机量')
    st.write('**筛选条件的参数如下：**')
    st.write('户号：', selectbox,'|', '主变容量：', main_capacity, '|',"主变利用率：", f"{ues_per} %")
    st.write("CT:", CT, '|'," PT:", PT,'|', ' 选定瞬时功率开始值:', select_power_start,'|', ' 选定瞬时功率间隔值:', select_power_step)
    col5, col6,col7 = st.columns(3)
    with col5:
        st.subheader("折算成365天对应的天数")
        display_rate_df = rate_df
        display_rate_df = display_rate_df.reset_index().iloc[:,1:4]
        display_rate_df.columns=['选定的瞬时功率','占比','折算成365天对应的天数']
        print(display_rate_df.columns)
        st.dataframe(display_rate_df, hide_index=True)
    with col6:
        day = []
        result =[]
        for j in range(300,321,1):
            closest_value = rate_df['365_rate'].iloc[(rate_df['365_rate'] - j).abs().idxmin()]
            power =  rate_df[rate_df['365_rate']==closest_value]['power'].min()
            poweer_result = j,main_capacity*ues_per-power
            day.append(j)
            result.append(poweer_result)
            #print(result)
        result = pd.DataFrame(result)  
        result.index=result[0]
        st.subheader("中午谷电时间段数据判断装机量")
        # 创建一个条形图
        fig, ax = plt.subplots()
        result[1].plot(kind='bar', ax=ax)
        # 设置x轴标题
        ax.set_xlabel('365天对应的天数')
        ax.set_ylabel('装机规模')
        # 添加y轴数据值
        for i, value in enumerate(result[1].values):
            ax.text(i, value + 0.05, f'{value:.2f}', ha='center')
        # 显示图表
        st.pyplot(fig)
        result = result[(result[0]==300)|(result[0]==319)|(result[0]==320)]
        result.columns=['年利用天数','储能推荐装机规模']
    with col7:
        st.subheader("折算成365天对应的天数")
        st.dataframe(result, hide_index=True)

def power_up(df, selectbox, selected_date,main_capacity,ues_per,CT,PT,select_power_start,select_power_step):
    """
    尖峰时间段数据判断装机量分析函数
    输入：
    1、df 输出整体datafrmae, 
    2、selectbox 选择的分析户号,
    3、selected_date 选择的日期,
    4、main_capacity 主变容量,
    5、ues_per 主变容量利用率,
    6、CT,
    7、PT,
    8、select_power_start 选定瞬时功率开始值,
    9、select_power_step 选定瞬时功率间隔值
    输出：中午谷电时间段数据判断装机量部分相关参数输出
    """
    filtered_df =df[
        (
        (((df.index.hour == 11) & (df.index.minute >= 10)))|
        (((df.index.hour == 12) & (df.index.minute >= 0)))|
        (((df.index.hour == 13) & (df.index.minute >= 0)))|
        (((df.index.hour == 14) & (df.index.minute == 0)))
        )
        ]
    # st.dataframe(filtered_df.sort_index(ascending=True))
    rate =[]
    power = []
    for i in range(select_power_start,select_power_start+select_power_step*50,select_power_step):
        re= filtered_df[filtered_df['瞬时有功']<i].shape[0]/filtered_df.shape[0]
        re = round(re,4)
        power.append(i)
        rate.append(re)
    rate_df = pd.DataFrame({'power':power,'rate':rate})
    rate_df['365_rate']= round(rate_df['rate']*365,2)
    st.write('______________________________________')
    st.subheader('尖峰时间段数据判断装机量')
    st.write('**筛选条件的参数如下：**')
    st.write('户号：', selectbox,'|', '主变容量：', main_capacity, '|',"主变利用率：", f"{ues_per} %")
    st.write("CT:", CT, '|'," PT:", PT,'|', ' 选定瞬时功率开始值:', select_power_start,'|', ' 选定瞬时功率间隔值:', select_power_step)
    col5, col6,col7 = st.columns(3)
    with col5:
        st.subheader("折算成365天对应的天数")
        display_rate_df = rate_df
        display_rate_df = display_rate_df.reset_index().iloc[:,1:4]
        display_rate_df.columns=['选定的瞬时功率','占比','折算成365天对应的天数']
        print(display_rate_df.columns)
        st.dataframe(display_rate_df, hide_index=True)
    with col6:
        day = []
        result =[]
        for j in range(300,321,1):
            closest_value = rate_df['365_rate'].iloc[(rate_df['365_rate'] - j).abs().idxmin()]
            power =  rate_df[rate_df['365_rate']==closest_value]['power'].min()
            poweer_result = j,main_capacity*ues_per-power
            day.append(j)
            result.append(poweer_result)
            #print(result)
        result = pd.DataFrame(result)  
        result.index=result[0]
        st.subheader("尖峰时间段数据判断装机量")
        # 创建一个条形图
        fig, ax = plt.subplots()
        result[1].plot(kind='bar', ax=ax)
        # 设置x轴标题
        ax.set_xlabel('365天对应的天数')
        ax.set_ylabel('装机规模')
        # 添加y轴数据值
        for i, value in enumerate(result[1].values):
            ax.text(i, value + 0.05, f'{value:.2f}', ha='center')
        # 显示图表
        st.pyplot(fig)
        result = result[(result[0]==300)|(result[0]==319)|(result[0]==320)]
        result.columns=['年利用天数','储能推荐装机规模']
    with col7:
        st.subheader("折算成365天对应的天数")
        st.dataframe(result, hide_index=True)
    
def main():
    print('****************************')
    print('开始执行：')
    print('****************************')
    data_file = st.sidebar.file_uploader('读取CSV文件',help='支持csv文件上传', type=['csv'])
    df = load_and_process_data(data_file)
    
    if df is not None:
        st.sidebar.write("<p style='color:green; font-weight:bold;'>文件上传成功。</p>", unsafe_allow_html=True)
        st.subheader("数据预览")
        options = st.multiselect('选择列:'
                                  , list(df.columns)
                                  # , default=list(df.columns)
                                  ,help='可以选择多列进行数据筛选显示')
        # 根据用户的选择显示DataFrame
        if options:
            st.dataframe(df[options].head())
        else:
            st.warning(':red[**请至少选择一列**]')
        # st.dataframe(df.head())
        
        selectbox, selected_date,main_capacity,ues_per,CT,PT,select_power_start,select_power_step = display_sidebar(df)
        if selectbox and selected_date:
            df_filtered = df[df['用户编号'] == selectbox]
            p_day_av, r_day, _, P_day_std, Sd, df_month = calculate_metrics(df_filtered)
            plot_results(df_filtered,selected_date, p_day_av, r_day, P_day_std, Sd, df_month)
        #中午谷电时间段数据判断装机量分析函数
        power_lower(df, selectbox, selected_date,main_capacity,ues_per,CT,PT,select_power_start,select_power_step)
        #尖峰时间段数据判断装机量分析函数
        power_up(df, selectbox, selected_date,main_capacity,ues_per,CT,PT,select_power_start,select_power_step)
    else:
        st.sidebar.write("<p style='color:red; font-weight:bold;'>请上传CSV文件。</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
