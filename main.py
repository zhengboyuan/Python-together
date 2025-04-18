import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
import streamlit as st
import time
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
            with st.spinner('数据处理中...'):    
                time.sleep(2)
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            return df
        except Exception as e:
            st.sidebar.error(f"读取或处理文件时出错: {e}")
    return None
def display_sidebar(df):
    """侧边栏内容：选择户号和日期
    输入参数：df load_and_process_data 上传的csv文件读取结果。
    输出参数：
    selectbox 下拉列表选择的户号
    selected_date 选择时间数据
    selected_column 选择的分析列
    """
    unique_users = df['用户编号'].unique() if df is not None else []
    selectbox = st.sidebar.selectbox('选择分析的户号:', unique_users,help='选择数据文件中的户号进行分析')
    min_date = df.index.min().date() if df is not None else None
    max_date = df.index.max().date() if df is not None else None
    selected_date = st.sidebar.date_input("选择日期：", value=min_date, min_value=min_date, max_value=max_date)
    columns = df.columns
    selected_column = st.sidebar.selectbox('选择一列数据进行分析', columns ,help = "只有数据类型的列可进行选择分析")
    return selectbox, selected_date,selected_column

def plot_fuc(df,selected_column,selected_date):
    """    
    主页面展示内容
    1、绘制当日数据曲线
    2、绘制选择当月数据柱状图
    3、绘制选择当年数据柱状图
    4、tab展示部分数据
    如出现问题，则输出：择列数据无法分析
    输入参数：
    df
    selected_date 选择时间数据
    selected_column 选择的分析列
    输出参数：None
    """
    try:
        df_filtered_date = df[df.index.date == selected_date]
        df_plot = df_filtered_date[selected_column]
        # 当日数据曲线
        st.subheader(f"{selected_date}当日{selected_column} 数据曲线")
        #f"**负荷最大值:** {data['负荷'].max()}
        st.line_chart(data = df_plot)
        # 选择当月数据柱状图
        df_filtered_month = df[(df.index.year == selected_date.year)&((df.index.month == selected_date.month))][selected_column]
        df_filtered_month = df_filtered_month.resample('D').mean()
        st.subheader(f"{selected_date.year}年{selected_date.month}月{selected_column} 柱状图")
        st.bar_chart(data = df_filtered_month)
        # 选择当年数据柱状图
        st.subheader(f"{selected_date.year}年 {selected_column} （平均）柱状图")
        df_filtered_year_data = df[(df.index.year == selected_date.year)][selected_column]
        df_filtered_year = df_filtered_year_data.resample('M').mean()
        st.bar_chart(data = df_filtered_year)
        # tab部分
        st.subheader('选择数据详情')
        tab1, tab2, tab3 = st.tabs(["当日数据", "选择当月数据", "选择当年数据"])
        with tab1:
           #st.header("当日数据")
           st.dataframe(df_plot)
        
        with tab2:
           #st.header("选择当月数据")
           st.dataframe(df_filtered_month)
        
        with tab3:
           #st.header("选择当年数据")
           st.dataframe(df_filtered_year)
        
    except:
        st.write("<p style='color:red; font-weight:bold;'>选择列数据无法分析。</p>", unsafe_allow_html=True)
    return None    
def main():
    print('****************************')
    print('开始执行：')
    print('****************************')
    data_file = st.sidebar.file_uploader('读取CSV文件', type=['csv'],help='支持CSV文件，进行负荷文档数据分析')
    df = load_and_process_data(data_file)
    
    if df is not None:
        st.sidebar.write("<p style='color:green; font-weight:bold;'>文件上传成功。</p>", unsafe_allow_html=True)
        st.subheader("数据预览")
        st.dataframe(df.head())
        selectbox, selected_date,selected_column = display_sidebar(df)
        if selectbox and selected_date:
            df_filtered = df[df['用户编号'] == selectbox]
            plot_fuc(df_filtered,selected_column,selected_date)
    
    else:
        st.sidebar.write("<p style='color:red; font-weight:bold;'>请上传CSV文件。</p>", unsafe_allow_html=True)
    print('执行完毕：')
if __name__ == "__main__":
    main()
