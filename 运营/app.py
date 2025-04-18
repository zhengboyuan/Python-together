import streamlit as st
import pandas as pd
import altair as alt
from utils import DeepseekLLM, file_uploader, load_data
from .pandasai_analysis import pandasai_analysis
from smart_pandasai_analysis import smart_pandasai_analysis
from Deepseek_report import smart_report
from pandasai import Agent, SmartDataframe
from hand_analysis import hand_analysis
# 设置页面布局和中文字体
st.set_page_config(layout="wide")
st.markdown("""
<style>
@font-face {
    font-family: 'SimHei';
    src: local('SimHei');
}
html, body, [class*="css"]  {
    font-family: 'SimHei';
}
</style>
""", unsafe_allow_html=True)
st.title("重庆超充站电量数据分析")

# 获取上传的文件
uploaded_file = file_uploader()
data = load_data(uploaded_file)

if data.empty:
    st.warning("请上传Excel数据文件或检查文件格式是否正确")
    st.stop()

# 侧边栏 - 筛选条件
st.sidebar.header("数据筛选")
date_range = st.sidebar.date_input(
    "日期范围",
    value=[data['日期'].min(), data['日期'].max()],
    min_value=data['日期'].min(),
    max_value=data['日期'].max()
)

selected_stations = st.sidebar.multiselect(
    "选择站点",
    options=data['站点'].unique(),
    default=data['站点'].unique()
)

# 应用筛选条件
filtered_data = data[
    (data['日期'] >= pd.to_datetime(date_range[0])) & 
    (data['日期'] <= pd.to_datetime(date_range[1])) &
    (data['站点'].isin(selected_stations))
]

# 主界面
tab1, tab2, tab3, tab4, tab5, tab6,tab7 = st.tabs(["核心指标", "站点对比", "趋势分析", "Deepseek报告分析", "PandasAI分析", "智能问答分析",'手动分析'])

# 侧边栏 - Deepseek API设置
st.sidebar.header("AI分析设置")
deepseek_key = st.sidebar.text_input("Deepseek API密钥", type="password")

with tab1:
    st.header("核心指标概览")
    
    # 计算每日核心指标
    daily_summary = filtered_data.groupby('日期').agg(
        总充电量=('充电量', 'sum'),
        总订单数=('订单数', 'sum'),
        总结算收益=('结算收益', 'sum'),
        总服务费收入=('服务费收入', 'sum'),
        总停车费收入=('停车费收入', 'sum')
    ).reset_index()
    
    # 指标卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("总充电量(kWh)", f"{daily_summary['总充电量'].sum():,.0f}")
    with col2:
        st.metric("总订单数", f"{daily_summary['总订单数'].sum():,.0f}")
    with col3:
        st.metric("总结算收益(元)", f"{daily_summary['总结算收益'].sum():,.0f}")
    with col4:
        st.metric("服务费收入(元)", f"{daily_summary['总服务费收入'].sum():,.0f}")
    with col5:
        st.metric("停车费收入(元)", f"{daily_summary['总停车费收入'].sum():,.0f}")
    
    # 当日数据快照
    st.subheader("当日数据快照")
    latest_day = daily_summary.iloc[-1]
    prev_day = daily_summary.iloc[-2] if len(daily_summary) > 1 else latest_day
    
    col1, col2, col3 = st.columns(3)
    with col1:
        delta = latest_day['总充电量'] - prev_day['总充电量']
        st.metric("总充电量(kWh)", 
                 f"{latest_day['总充电量']:,.0f}", 
                 f"{delta:+.0f} (环比{delta/prev_day['总充电量']*100:.1f}%)")
    with col2:
        delta = latest_day['总订单数'] - prev_day['总订单数']
        st.metric("总订单数", 
                 f"{latest_day['总订单数']:,.0f}", 
                 f"{delta:+.0f} (环比{delta/prev_day['总订单数']*100:.1f}%)")
    with col3:
        delta = latest_day['总结算收益'] - prev_day['总结算收益']
        st.metric("总结算收益(元)", 
                 f"{latest_day['总结算收益']:,.0f}", 
                 f"{delta:+.0f} (环比{delta/prev_day['总结算收益']*100:.1f}%)")

    # 分指标趋势图
    st.subheader("分指标趋势分析")
    
    inner_tab1, inner_tab2, inner_tab3 = st.tabs(["充电量趋势", "订单数趋势", "收益趋势"])
    
    with inner_tab1:
        st.altair_chart(alt.Chart(daily_summary).mark_line(color='#1f77b4').encode(
            x='日期:T',
            y=alt.Y('总充电量:Q', title='充电量(kWh)'),
            tooltip=['日期', '总充电量']
        ).properties(height=300), use_container_width=True)
        
    with inner_tab2:
        st.altair_chart(alt.Chart(daily_summary).mark_line(color='#ff7f0e').encode(
            x='日期:T',
            y=alt.Y('总订单数:Q', title='订单数'),
            tooltip=['日期', '总订单数']
        ).properties(height=300), use_container_width=True)
        
    with inner_tab3:
        st.altair_chart(alt.Chart(daily_summary).mark_line(color='#2ca02c').encode(
            x='日期:T',
            y=alt.Y('总结算收益:Q', title='结算收益(元)'),
            tooltip=['日期', '总结算收益']
        ).properties(height=300), use_container_width=True)
    
    # 月度统计
    st.subheader("月度核心指标")
    monthly_summary = filtered_data.groupby(filtered_data['日期'].dt.to_period('M')).agg(
        总充电量=('充电量', 'sum'),
        总订单数=('订单数', 'sum'),
        总结算收益=('结算收益', 'sum')
    ).reset_index()
    monthly_summary['日期'] = monthly_summary['日期'].astype(str)
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(monthly_summary)
    with col2:
        bar_chart = alt.Chart(monthly_summary).mark_bar().encode(
            x='日期:N',
            y='总充电量:Q',
            tooltip=['日期', '总充电量']
        ).properties(width=400, height=300)
        st.altair_chart(bar_chart)

with tab2:
    st.header("各站点对比分析")
    
    if filtered_data.empty:
        st.warning("没有可用的站点数据，请检查筛选条件")
    else:
        # 站点汇总数据
        station_summary = filtered_data.groupby('站点').agg(
            总充电量=('充电量', 'sum'),
            总订单数=('订单数', 'sum'),
            平均每单充电量=('充电量', 'mean'),
            平均每单收益=('结算收益', 'mean')
        ).reset_index()
        
        # 站点排名 - 展示前三名和最后三名
        st.subheader("站点核心指标排名")
        metrics = ['总充电量', '总订单数', '平均每单充电量', '平均每单收益']
        
        for metric in metrics:
            sorted_data = station_summary.sort_values(metric, ascending=False)
            top3 = sorted_data.head(3)
            bottom3 = sorted_data.tail(3)
            
            st.markdown(f"**{metric}排名**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**前三名**")
                st.dataframe(top3[['站点', metric]].reset_index(drop=True))
            
            with col2:
                st.markdown("**后三名**")
                st.dataframe(bottom3[['站点', metric]].reset_index(drop=True))
        
        # 交互式对比分析
        st.subheader("交互式对比分析")
        compare_cols = st.columns(2)
        
        with compare_cols[0]:
            # 散点图展示充电量与订单数关系
            scatter = alt.Chart(station_summary).mark_circle(size=60).encode(
                x='总订单数:Q',
                y='总充电量:Q',
                color=alt.Color('站点:N', legend=None),
                tooltip=['站点', '总订单数', '总充电量']
            ).interactive()
            st.altair_chart(scatter, use_container_width=True)
            
        with compare_cols[1]:
            # 雷达图展示多维度对比
            selected = st.multiselect(
                "选择对比站点",
                options=station_summary['站点'].tolist(),
                default=station_summary['站点'].head(2).tolist()
            )
            if selected:
                radar_data = station_summary[station_summary['站点'].isin(selected)]
                radar_data = radar_data.melt(id_vars='站点', 
                                          value_vars=['总充电量', '总订单数', '平均每单充电量', '平均每单收益'],
                                          var_name='指标', value_name='值')
                
                # 标准化数据
                radar_data = radar_data.reset_index(drop=True)
                radar_data['标准化值'] = radar_data.groupby('指标')['值'].transform(
                    lambda x: (x - x.min()) / (x.max() - x.min()))
                
                radar_chart = alt.Chart(radar_data).mark_line().encode(
                    x='指标:N',
                    y='标准化值:Q',
                    color='站点:N',
                    tooltip=['站点', '指标', '值']
                ).properties(width=400, height=300)
                st.altair_chart(radar_chart)
        
        # 性能对比热力图
        st.subheader("站点性能热力图")
        heat_data = station_summary.set_index('站点')[['总充电量', '总订单数', '平均每单充电量', '平均每单收益']]
        # 标准化数据
        heat_data = (heat_data - heat_data.min()) / (heat_data.max() - heat_data.min())
        
        heatmap = alt.Chart(heat_data.reset_index().melt(id_vars='站点')).mark_rect().encode(
            x='variable:N',
            y='站点:N',
            color=alt.Color('value:Q', legend=alt.Legend(title="标准化值")),
            tooltip=['站点', 'variable', alt.Tooltip('value:Q', format='.2f')]
        ).properties(width=600, height=400)
        st.altair_chart(heatmap, use_container_width=True)

with tab3:
    st.header("趋势与环比分析")
    
    if filtered_data.empty:
        st.warning("没有可用的数据，请检查筛选条件")
    else:
        # 月度环比增长率
        monthly_summary = filtered_data.groupby(filtered_data['日期'].dt.to_period('M')).agg(
            总充电量=('充电量', 'sum'),
            总订单数=('订单数', 'sum'),
            总结算收益=('结算收益', 'sum')
        ).reset_index()
        monthly_summary['日期'] = monthly_summary['日期'].astype(str)
        
        # 计算环比增长率
        monthly_summary['充电量环比'] = monthly_summary['总充电量'].pct_change() * 100
        monthly_summary['订单数环比'] = monthly_summary['总订单数'].pct_change() * 100
        monthly_summary['收益环比'] = monthly_summary['总结算收益'].pct_change() * 100
        
        # 环比趋势图
        st.subheader("月度环比增长率")
        chart_data = monthly_summary.melt(id_vars='日期', 
                                        value_vars=['充电量环比', '订单数环比', '收益环比'],
                                        var_name='指标', value_name='增长率(%)')
        
        line_chart = alt.Chart(chart_data).mark_line().encode(
            x='日期:N',
            y='增长率(%):Q',
            color='指标:N',
            tooltip=['日期', '指标', '增长率(%)']
        ).properties(width=800, height=400)
        st.altair_chart(line_chart, use_container_width=True)
        
        # 站点月度趋势
        st.subheader("各站点月度趋势")
        station_monthly = filtered_data.groupby([filtered_data['日期'].dt.to_period('M'), '站点'])['充电量'].sum().reset_index()
        station_monthly['日期'] = station_monthly['日期'].astype(str)
        
        heatmap = alt.Chart(station_monthly).mark_rect().encode(
            x='日期:N',
            y='站点:N',
            color='充电量:Q',
            tooltip=['日期', '站点', '充电量']
        ).properties(width=800, height=400)
        st.altair_chart(heatmap, use_container_width=True)

with tab4:
    st.header("智能分析报告")
    smart_report(filtered_data, deepseek_key)

with tab5:
    pandasai_analysis(filtered_data, deepseek_key)

with tab6:
    smart_pandasai_analysis(filtered_data, deepseek_key)

with tab7:
    hand_analysis(filtered_data, deepseek_key)
# 数据下载
st.sidebar.header("数据导出")
if st.sidebar.button("导出筛选数据"):
    csv = filtered_data.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="下载CSV",
        data=csv,
        file_name='charging_data.csv',
        mime='text/csv'
    )
