import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

from deepseek_llm import DeepseekLLM

def calculate_7day_trend(data, metric_name):
    """计算7天指标变化趋势
    
    参数:
        data: 站点数据(DataFrame)
        metric_name: 指标名称(str)
        
    返回:
        百分比变化值(float)
    """
    if len(data) < 14:  # 不足14天数据无法计算
        return 0.0
    
    latest_date = data['日期'].max()
    recent_7days = data[data['日期'] > latest_date - pd.Timedelta(days=7)]
    prev_7days = data[
        (data['日期'] > latest_date - pd.Timedelta(days=14)) & 
        (data['日期'] <= latest_date - pd.Timedelta(days=7))
    ]
    
    if len(recent_7days) == 0 or len(prev_7days) == 0:
        return 0.0
    
    recent_avg = recent_7days[metric_name].mean()
    prev_avg = prev_7days[metric_name].mean()
    
    if prev_avg == 0:  # 避免除以0
        return 0.0
    
    return (recent_avg - prev_avg) / prev_avg * 100

def calculate_30day_trend(data, metric_name):
    """计算30天指标变化趋势
    
    参数:
        data: 站点数据(DataFrame)
        metric_name: 指标名称(str)
        
    返回:
        百分比变化值(float)
    """
    if len(data) < 60:  # 不足60天数据无法计算
        return 0.0
    
    latest_date = data['日期'].max()
    recent_30days = data[data['日期'] > latest_date - pd.Timedelta(days=30)]
    prev_30days = data[
        (data['日期'] > latest_date - pd.Timedelta(days=60)) & 
        (data['日期'] <= latest_date - pd.Timedelta(days=30))
    ]
    
    if len(recent_30days) == 0 or len(prev_30days) == 0:
        return 0.0
    
    recent_avg = recent_30days[metric_name].mean()
    prev_avg = prev_30days[metric_name].mean()
    
    if prev_avg == 0:
        return 0.0
    
    return (recent_avg - prev_avg) / prev_avg * 100

def find_best_month(data, metric_name):
    """查找指标表现最佳的月份
    
    参数:
        data: 站点数据(DataFrame)
        metric_name: 指标名称(str)
        
    返回:
        最佳月份(int)
    """
    monthly_data = data.groupby(data['日期'].dt.month)[metric_name].sum()
    return monthly_data.idxmax()

def create_comparison_chart(data1, data2, metric_name, label1, label2):
    """创建带差异分析的对比柱状图
    
    参数:
        data1: 第一组数据(DataFrame)
        data2: 第二组数据(DataFrame)
        metric_name: 指标名称(str)
        label1: 第一组标签(str)
        label2: 第二组标签(str)
        
    返回:
        Altair图表对象
    """
    # 计算指标值
    val1 = data1[metric_name].mean()
    val2 = data2[metric_name].mean()
    diff = val1 - val2
    pct_diff = (diff / val2 * 100) if val2 != 0 else 0
    
    # 准备对比数据
    df1 = pd.DataFrame({
        'value': [val1],
        'group': [label1]
    })
    df2 = pd.DataFrame({
        'value': [val2], 
        'group': [label2]
    })
    
    df = pd.concat([df1, df2])
    
    # 创建基础柱状图
    bars = alt.Chart(df).mark_bar().encode(
        x=alt.X('group:N', title='对比组', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('value:Q', title=metric_name),
        color=alt.Color('group:N', title='对比组',
                      scale=alt.Scale(range=['#4A90E2', '#FF7F0E'])),
        tooltip=[
            alt.Tooltip('group:N', title='对比组'),
            alt.Tooltip('value:Q', title=metric_name, format='.1f')
        ]
    )
    
    # 添加差异标注
    diff_text = alt.Chart(pd.DataFrame({
        'x': [0.5],
        'y': [max(val1, val2) * 1.05],
        'text': [f"差异: {diff:+.1f} ({pct_diff:+.1f}%)"]
    })).mark_text(
        fontSize=12,
        fontWeight='bold',
        color='#333333'
    ).encode(
        x='x:Q',
        y='y:Q',
        text='text:N'
    )
    
    # 组合图表
    chart = (bars + diff_text).properties(
        width=350,
        height=350,
        title={
            "text": f"{metric_name}对比分析",
            "subtitle": f"{label1} vs {label2}"
        }
    ).configure_axis(
        grid=False
    ).configure_view(
        stroke='transparent'
    )
    
    return chart

def get_max_indicator(df):
    """获取表现最优指标"""
    return df[['充电量', '订单数', '结算收益']].mean().idxmax()

def get_min_indicator(df):
    """获取表现最差指标""" 
    return df[['充电量', '订单数', '结算收益']].mean().idxmin()

def generate_summary_text(data, station=None, deepseek_key=None):
    """生成文字性总结报告
    
    参数:
        data: 充电站数据
        station: 站点名称
        deepseek_key: Deepseek API密钥(可选)
    """
    if station:
        station_data = data[data['站点'] == station]
        total_charge = station_data['充电量'].sum()
        total_orders = station_data['订单数'].sum()
        total_revenue = station_data['结算收益'].sum()
        
        # 计算同比(与上月同期对比)
        current_month = station_data['日期'].max().month
        last_month_data = station_data[station_data['日期'].dt.month == current_month - 1]
        
        if not last_month_data.empty:
            last_month_charge = last_month_data['充电量'].sum()
            charge_yoy = (total_charge - last_month_charge) / last_month_charge * 100
            last_month_orders = last_month_data['订单数'].sum()
            orders_yoy = (total_orders - last_month_orders) / last_month_orders * 100
            last_month_revenue = last_month_data['结算收益'].sum()
            revenue_yoy = (total_revenue - last_month_revenue) / last_month_revenue * 100
            
            yoy_text = f"同比上月: 充电量{charge_yoy:.1f}%, 订单数{orders_yoy:.1f}%, 收益{revenue_yoy:.1f}%"
        else:
            yoy_text = "无上月同期数据"
        
        # 计算与平均值的对比
        avg_charge = data['充电量'].mean()
        charge_vs_avg = (station_data['充电量'].mean() - avg_charge) / avg_charge * 100
        avg_orders = data['订单数'].mean()
        orders_vs_avg = (station_data['订单数'].mean() - avg_orders) / avg_orders * 100
        avg_revenue = data['结算收益'].mean()
        revenue_vs_avg = (station_data['结算收益'].mean() - avg_revenue) / avg_revenue * 100
        
        # 计算运营效率指标
        charge_per_order = total_charge / total_orders if total_orders > 0 else 0
        revenue_per_order = total_revenue / total_orders if total_orders > 0 else 0
        revenue_per_kwh = total_revenue / total_charge if total_charge > 0 else 0
        
        # 获取峰值日数据
        peak_day = station_data.loc[station_data['充电量'].idxmax()]
        avg_day_charge = total_charge / len(station_data['日期'].unique())
        
        summary = f"""
        ## {station}运营分析报告
        
        ### 核心业绩
        - 总充电量: {total_charge:,.0f}kWh (日均 {avg_day_charge:,.0f}kWh)
        - 总订单数: {total_orders:,.0f}单
        - 总收益: {total_revenue:,.0f}元
        - 峰值日: {peak_day['日期'].strftime('%m-%d')} {peak_day['充电量']:,.0f}kWh
        
        ### 运营效率
        - 单订单充电量: {charge_per_order:,.1f}kWh/单
        - 单订单收益: {revenue_per_order:,.1f}元/单 
        - 单位电量收益: {revenue_per_kwh:,.2f}元/kWh
        
        ### 趋势分析
        - {yoy_text}
        - 与全站均值对比:
          充电量{charge_vs_avg:+.1f}% (规模优势显著)
          订单数{orders_vs_avg:+.1f}% (客流量领先)
          收益{revenue_vs_avg:+.1f}% (需关注定价策略)
        
        ### 管理建议
        - 充电量增长强劲，但收益转化率低于均值
        - 建议分析定价策略和成本结构
        - 峰值日表现突出，可总结推广经验
        """
        
        if deepseek_key:
            advice_prompt = f"""
            作为充电站运营专家，请先基于以下数据生成专业分析总结并输出总结报告，严格遵循以下结构:

            ## 1. 执行摘要
            - **核心发现**:
              1. {station}站充电量{total_charge:,.0f}kWh，同比上月{charge_yoy:+.1f}%
              2. 单位电量收益{revenue_per_kwh:.2f}元/kWh，低于全站均值{(revenue_per_kwh - data['结算收益'].sum()/data['充电量'].sum()):+.2f}元
              3. 峰值日{peak_day['日期'].strftime('%m-%d')}充电量{peak_day['充电量']:,.0f}kWh，是均值的{(peak_day['充电量']/avg_day_charge):.1f}倍

            - **关键指标变化**:
              - 充电量: {charge_yoy:+.1f}% (上月)
              - 订单数: {orders_yoy:+.1f}% (上月) 
              - 收益: {revenue_yoy:+.1f}% (上月)

            ## 2. 详细分析
            ### 站点运营对比
            - **排名**: 
              - 充电量排名: {data.groupby('站点')['充电量'].sum().rank(ascending=False)[station]:.0f}/{len(data['站点'].unique())}
              - 收益排名: {data.groupby('站点')['结算收益'].sum().rank(ascending=False)[station]:.0f}/{len(data['站点'].unique())}
            - **效率指标**:
              - 单订单充电量: {charge_per_order:.1f}kWh/单 (全站均值: {data['充电量'].sum()/data['订单数'].sum():.1f})
              - 单位电量收益: {revenue_per_kwh:.2f}元/kWh (全站均值: {data['结算收益'].sum()/data['充电量'].sum():.2f})

            ### 时间趋势
            - 最近7天日均充电量: {station_data[station_data['日期'] > station_data['日期'].max() - pd.Timedelta(days=7)]['充电量'].mean():.0f}kWh
            - 环比增长率: {((station_data[station_data['日期'] > station_data['日期'].max() - pd.Timedelta(days=7)]['充电量'].mean() - station_data[station_data['日期'] > station_data['日期'].max() - pd.Timedelta(days=14)]['充电量'].mean())/station_data[station_data['日期'] > station_data['日期'].max() - pd.Timedelta(days=14)]['充电量'].mean())*100:.1f}%

            ### 异常检测
            - 检测到{len(anomalies)}个异常日，最大偏差: {anomalies['充电量_zscore'].max():.1f}σ

            ## 3. 结论与建议
            要求:
            1. 提供3条可立即实施的改进建议，按优先级排序
            2. 每条建议必须包含:
               - 问题描述(引用上述具体数据)
               - 3个具体可执行措施
               - 预期改善效果(量化指标)
            3. 提供1条长期发展建议
            5. 列出具体风险预警(站点/指标)
            """

            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("管理建议分析", key=f"advice_{station}"):
                    with st.spinner("正在分析..."):
                        try:
                            llm = DeepseekLLM(
                                api_key=deepseek_key,
                                temperature=0.3,
                                max_tokens=1500
                            )
                            ai_advice = llm.call(advice_prompt)
                            advice_text = ai_advice
                        except Exception as e:
                            st.error(f"AI建议生成失败: {str(e)}")
                            advice_text = """
                            - 充电量增长强劲，但收益转化率低于均值
                            - 建议分析定价策略和成本结构
                            - 峰值日表现突出，可总结推广经验
                            """
            
            # 将建议直接显示在总结报告中
            summary += advice_text
        else:
            summary += """
            - 充电量增长强劲，但收益转化率低于均值
            - 建议分析定价策略和成本结构
            - 峰值日表现突出，可总结推广经验
            """
        return summary
    return ""

def hand_analysis(data, deepseek_key=None):
    """专业运营分析仪表板
    
    参数:
        data (DataFrame): 过滤后的充电站数据
        deepseek_key (str): Deepseek API密钥(可选)
    """
    st.header("专业运营分析")
    
    # 检查API密钥
    if not deepseek_key:
        st.warning("请提供Deepseek API密钥以使用AI分析功能")
    
    # 分析模式选择
    analysis_mode = st.radio(
        "选择分析模式",
        ["单站点分析", "多站点对比"],
        horizontal=True
    )
    
    if analysis_mode == "单站点分析":
        single_station_analysis(data, deepseek_key)
    else:
        multi_station_analysis(data)

def single_station_analysis(data, deepseek_key=None):
    """单站点深度分析 - 优化后的业务汇报视角"""
    st.subheader("站点选择")
    station = st.selectbox("选择分析站点", options=data['站点'].unique())
    station_data = data[data['站点'] == station]
    
    if station_data.empty:
        st.warning("该站点无数据")
        return
    
    # ========== 核心KPI展示 ==========
    st.subheader("📊 核心业务指标")
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("总充电量", 
                f"{station_data['充电量'].sum():,.0f}kWh",
                help="历史累计充电总量")
    with kpi2:
        st.metric("总订单数",
                f"{station_data['订单数'].sum():,.0f}单",
                help="历史累计订单总量")
    with kpi3:
        st.metric("总收益",
                f"{station_data['结算收益'].sum():,.0f}元",
                help="历史累计收益总额")
    
    # ========== 趋势分析 ==========
    st.subheader("📈 业务趋势分析")
    
    # 近期趋势卡片
    trend1, trend2, trend3 = st.columns(3)
    with trend1:
        trend_7d = calculate_7day_trend(station_data, '充电量')
        st.metric("7天充电趋势", 
                f"{trend_7d:+.1f}%",
                delta_color="inverse" if trend_7d < 0 else "normal")
    with trend2:
        trend_30d = calculate_30day_trend(station_data, '充电量')
        st.metric("30天充电趋势",
                f"{trend_30d:+.1f}%",
                delta_color="inverse" if trend_30d < 0 else "normal")
    with trend3:
        best_month = find_best_month(station_data, '充电量')
        st.metric("历史最佳月份",
                f"{best_month}月",
                help="充电量最高的历史月份")
    
    # 对比分析选择器
    compare_mode = st.radio(
        "对比分析维度",
        ["与上月对比", "与历史最佳对比"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if compare_mode == "与上月对比":
        # 与上月对比逻辑
        current_month = station_data['日期'].max().month
        current_data = station_data[station_data['日期'].dt.month == current_month]
        last_month_data = station_data[station_data['日期'].dt.month == current_month - 1]
        
        if not last_month_data.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**充电量对比**")
                charge_chart = create_comparison_chart(current_data, last_month_data, "充电量", "本月", "上月")
                st.altair_chart(charge_chart, use_container_width=True)
            
            with col2:
                st.markdown("**订单量对比**")
                order_chart = create_comparison_chart(current_data, last_month_data, "订单数", "本月", "上月")
                st.altair_chart(order_chart, use_container_width=True)
    else:
        # 与历史最佳对比逻辑
        best_month = find_best_month(station_data, '充电量')
        best_data = station_data[station_data['日期'].dt.month == best_month]
        current_data = station_data[station_data['日期'].dt.month == station_data['日期'].max().month]
        
        # 获取全站最佳站点数据
        best_station = data.groupby('站点')['充电量'].sum().idxmax()
        best_station_data = data[data['站点'] == best_station]
        best_station_current = best_station_data[best_station_data['日期'].dt.month == station_data['日期'].max().month]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**充电量对比**")
            # 当前站点与自身历史最佳对比
            charge_chart1 = create_comparison_chart(current_data, best_data, "充电量", "当前月", f"历史最佳({best_month}月)")
            # 当前站点与全站最佳站点对比
            charge_chart2 = create_comparison_chart(current_data, best_station_current, "充电量", "当前站点", f"全站最佳({best_station})")
            st.altair_chart(charge_chart1, use_container_width=True)
            st.altair_chart(charge_chart2, use_container_width=True)
        
        with col2:
            st.markdown("**订单量对比**")
            # 当前站点与自身历史最佳对比
            order_chart1 = create_comparison_chart(current_data, best_data, "订单数", "当前月", f"历史最佳({best_month}月)")
            # 当前站点与全站最佳站点对比
            order_chart2 = create_comparison_chart(current_data, best_station_current, "订单数", "当前站点", f"全站最佳({best_station})")
            st.altair_chart(order_chart1, use_container_width=True)
            st.altair_chart(order_chart2, use_container_width=True)

    # 运营效率分析
    st.subheader("运营效率分析")
    efficiency_metrics = {
        '单订单充电量': lambda d: d['充电量'].sum() / d['订单数'].sum() if d['订单数'].sum() > 0 else 0,
        '单订单收益': lambda d: d['结算收益'].sum() / d['订单数'].sum() if d['订单数'].sum() > 0 else 0,
        '单位电量收益': lambda d: d['结算收益'].sum() / d['充电量'].sum() if d['充电量'].sum() > 0 else 0
    }
    
    eff_cols = st.columns(len(efficiency_metrics))
    for i, (name, func) in enumerate(efficiency_metrics.items()):
        with eff_cols[i]:
            current_value = func(station_data)
            st.metric(
                label=name,
                value=f"{current_value:.2f}",
                delta=f"全站均值: {func(data):.2f}",
                delta_color="inverse" if current_value < func(data) else "normal"
            )

    # 添加管理建议按钮
    if not deepseek_key:
        st.warning("请提供Deepseek API密钥以使用AI分析功能")
    if deepseek_key:
        st.markdown("### 管理建议")
        advice_prompt = f"""
        作为充电站运营专家，请按以下结构输出分析报告：
        
        ### 数据总结（必填）
        用结构化方式概括以下要点：
        1️⃣ 核心指标表现：
        - 日均充电量：{station_data['充电量'].sum()/len(station_data['日期'].unique()):.1f}kWh
        - 订单收益转化率：{(station_data['结算收益'].sum()/station_data['订单数'].sum()):.2f}元/单
        - 设备利用率峰值：{station_data['充电量'].max()/station_data['充电量'].mean():.1%}
        
        2️⃣ 运营特征分析：
        - 优势项：{get_max_indicator(station_data)} 高于均值{(station_data[get_max_indicator(station_data)].mean()/data[get_max_indicator(station_data)].mean()-1):.1%}
        - 短板项：{get_min_indicator(station_data)} 低于均值{(1 - station_data[get_min_indicator(station_data)].mean()/data[get_min_indicator(station_data)].mean()):.1%}
        
        3️⃣ 关键趋势：
        - 最近7天充电量趋势：{calculate_7day_trend(station_data, '充电量'):+.1f}%
        - 最近7天客单价变化：{(station_data['结算收益'].iloc[-7:].mean()/station_data['结算收益'].iloc[:-7].mean()-1):+.1%}
        
        ### 管理建议（必填）
        根据上述总结，按以下模板给出建议：
        
        [优先级] 建议标题
        📌 问题定位：结合[指标A]和[指标B]数据，说明具体问题...
        🔧 落地步骤：
        1. 立即行动（1周内）：具体可操作步骤（如「调整3台快充桩为慢充桩」）
        2. 短期优化（1月内）：需要协调资源的改进（如「上线分时定价系统」）
        3. 长期策略（3月+）：战略级调整（如「与周边商圈签订充电套餐」）
        🎯 效果预测：量化预期（如「预计提升单日收益1500元」）
        
        示例：
        [优先级1] 提升高价值订单占比
        📌 问题定位：结合日均72.3单与32.1kWh/单数据，存在小订单占比过高问题...
        🔧 落地步骤：
        1. 立即行动：设置满30kWh赠洗车券活动（1周上线）
        2. 短期优化：开发大客户专用充电套餐（4周完成）
        3. 长期策略：建设VIP会员专属充电区（Q3落地）
        🎯 效果预测：大订单占比提升至35%（+15%） 
        
        要求：
        1. 必须引用数据总结中的3个及以上指标
        2. 每个建议包含3个时间分阶的落地步骤
        3. 效果预测需关联到具体指标
        """
        
        if st.button("管理建议分析", key=f"advice_{station}"):
            with st.spinner("正在分析..."):
                try:
                    llm = DeepseekLLM(
                        api_key=deepseek_key,
                        temperature=0.3,
                        max_tokens=1500
                    )
                    ai_advice = llm.call(advice_prompt)
                    st.markdown(ai_advice)
                except Exception as e:
                    st.error(f"AI建议生成失败: {str(e)}")
                    st.markdown("""
                    - 充电量增长强劲，但收益转化率低于均值
                    - 建议分析定价策略和成本结构
                    - 峰值日表现突出，可总结推广经验
                    """)
    
    if station_data.empty:
        st.warning("该站点无数据")
        return
    
    # 文字性总结报告
    st.markdown(generate_summary_text(data, station))
    
    # 详细指标
    st.subheader(f"{station} - 详细指标")
    
    # 当月数据
    current_month = station_data['日期'].max().month
    month_data = station_data[station_data['日期'].dt.month == current_month]
    prev_month_data = station_data[station_data['日期'].dt.month == current_month - 1]
    
    # 当日数据
    latest_date = station_data['日期'].max()
    day_data = station_data[station_data['日期'] == latest_date]
    prev_day_data = station_data[station_data['日期'] == latest_date - pd.Timedelta(days=1)]
    
    # 计算全站当月均值
    all_stations_month_data = data[data['日期'].dt.month == current_month]
    avg_month_charge = all_stations_month_data.groupby('站点')['充电量'].sum().mean()
    avg_month_orders = all_stations_month_data.groupby('站点')['订单数'].sum().mean()
    avg_month_revenue = all_stations_month_data.groupby('站点')['结算收益'].sum().mean()
    
    # 计算变化量
    month_charge_change = month_data['充电量'].sum() - prev_month_data['充电量'].sum() if not prev_month_data.empty else 0
    month_orders_change = month_data['订单数'].sum() - prev_month_data['订单数'].sum() if not prev_month_data.empty else 0
    month_revenue_change = month_data['结算收益'].sum() - prev_month_data['结算收益'].sum() if not prev_month_data.empty else 0
    
    # 计算与全站均值的差异
    month_charge_vs_avg = month_data['充电量'].sum() - avg_month_charge
    month_orders_vs_avg = month_data['订单数'].sum() - avg_month_orders
    month_revenue_vs_avg = month_data['结算收益'].sum() - avg_month_revenue
    
    day_charge_change = day_data['充电量'].sum() - prev_day_data['充电量'].sum() if not prev_day_data.empty else 0
    day_orders_change = day_data['订单数'].sum() - prev_day_data['订单数'].sum() if not prev_day_data.empty else 0
    day_revenue_change = day_data['结算收益'].sum() - prev_day_data['结算收益'].sum() if not prev_day_data.empty else 0
    
    # 指标展示 - 合并当月数据和均值对比
    st.markdown("**当月数据 (含全站均值对比)**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("充电量(kWh)", 
                f"{month_data['充电量'].sum():,.0f}", 
                f"{month_charge_vs_avg:+,.0f} vs 均值",
                delta_color="normal",
                help=f"上月变化: {month_charge_change:+,.0f}")
    with col2:
        st.metric("订单数", 
                f"{month_data['订单数'].sum():,.0f}", 
                f"{month_orders_vs_avg:+,.0f} vs 均值",
                delta_color="normal",
                help=f"上月变化: {month_orders_change:+,.0f}")
    with col3:
        st.metric("收益(元)", 
                f"{month_data['结算收益'].sum():,.0f}", 
                f"{month_revenue_vs_avg:+,.0f} vs 均值",
                delta_color="normal",
                help=f"上月变化: {month_revenue_change:+,.0f}")
    
    st.markdown("**当日数据**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"{latest_date.strftime('%m-%d')}充电量(kWh)", 
                f"{day_data['充电量'].sum():,.0f}", 
                f"{day_charge_change:+,.0f}")
    with col2:
        st.metric(f"{latest_date.strftime('%m-%d')}订单数", 
                f"{day_data['订单数'].sum():,.0f}", 
                f"{day_orders_change:+,.0f}")
    with col3:
        st.metric(f"{latest_date.strftime('%m-%d')}收益(元)", 
                f"{day_data['结算收益'].sum():,.0f}", 
                f"{day_revenue_change:+,.0f}")
    
    # 异常检测
    st.subheader(f"{station} - 异常检测")
    daily_data = station_data.groupby('日期').agg({
        '充电量': 'sum',
        '订单数': 'sum',
        '结算收益': 'sum'
    }).reset_index()
    daily_data['充电量_zscore'] = (daily_data['充电量'] - daily_data['充电量'].mean()) / daily_data['充电量'].std()
    anomalies = daily_data[np.abs(daily_data['充电量_zscore']) > 2]
    
    tab1, tab2, tab3 = st.tabs(["充电量", "订单数", "收益"])
    with tab1:
        st.altair_chart(alt.Chart(daily_data).mark_line().encode(
            x='日期:T',
            y='充电量:Q',
            tooltip=['日期', '充电量']
        ).properties(height=300), use_container_width=True)
    with tab2:
        st.altair_chart(alt.Chart(daily_data).mark_line().encode(
            x='日期:T',
            y='订单数:Q',
            tooltip=['日期', '订单数']
        ).properties(height=300), use_container_width=True)
    with tab3:
        st.altair_chart(alt.Chart(daily_data).mark_line().encode(
            x='日期:T',
            y='结算收益:Q',
            tooltip=['日期', '结算收益']
        ).properties(height=300), use_container_width=True)
    
    # 时间趋势分析
    st.subheader(f"{station} - 时间趋势")
    
    if not anomalies.empty:
        # 异常统计卡片
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("异常天数", f"{len(anomalies)}天", help="偏离均值2个标准差以上的天数")
        with col2:
            max_dev = anomalies['充电量_zscore'].abs().max()
            st.metric("最大偏差", f"{max_dev:.1f}σ", delta_color="off")
        with col3:
            avg_charge = daily_data['充电量'].mean()
            st.metric("异常日平均充电量", 
                     f"{anomalies['充电量'].mean():,.0f}kWh", 
                     f"均值: {avg_charge:,.0f}kWh")

        # 增强型异常分析图表
        st.subheader("异常检测分析")
        
        # 计算参考数据
        mean_charge = daily_data['充电量'].mean()
        std_charge = daily_data['充电量'].std()
        
        # 创建基础图表
        base = alt.Chart(daily_data).encode(
            x=alt.X('日期:T', 
                   title='日期',
                   axis=alt.Axis(format='%m-%d', labelAngle=-45,
                                labelFlush=False, labelPadding=5)),
            y=alt.Y('充电量:Q', title='充电量 (kWh)',
                   scale=alt.Scale(zero=False))
        )
        
        # 置信区间背景
        confidence_band = base.mark_area(opacity=0.2, color='#FFD700').encode(
            y=alt.Y('datum.mean_charge + 2*datum.stdev_charge:Q', title=''),
            y2=alt.Y2('datum.mean_charge - 2*datum.stdev_charge:Q')
        ).transform_calculate(
            mean_charge=str(mean_charge),
            stdev_charge=str(std_charge)
        )
        
        # 原始数据趋势线
        trend_line = base.mark_line(
            color='#4A90E2',
            size=2,
            opacity=0.8
        ).encode(
            tooltip=[
                alt.Tooltip('日期:T', format='%Y-%m-%d', title='日期'),
                alt.Tooltip('充电量:Q', format=',.0f', title='实际值'),
                alt.Tooltip('充电量_zscore:Q', format='.1f', title='标准差')
            ]
        )
        
        # 异常点标记
        anomaly_points = alt.Chart(anomalies).mark_point(
            shape='triangle-up',
            size=120,
            color='red',
            filled=True,
            opacity=0.9
        ).encode(
            x='日期:T',
            y='充电量:Q',
            tooltip=[
                alt.Tooltip('日期:T', format='%Y-%m-%d', title='异常日期'),
                alt.Tooltip('充电量:Q', format=',.0f', title='异常值'),
                alt.Tooltip('充电量_zscore:Q', format='.1f', title='偏离标准差'),
                alt.Tooltip('订单数:Q', format=',.0f', title='当日订单'),
                alt.Tooltip('结算收益:Q', format=',.0f', title='当日收益')
            ]
        )
        
        # 组合图表
        chart = alt.layer(
            confidence_band,
            trend_line,
            anomaly_points
        ).properties(
            height=500,
            width=800
        ).configure_axis(
            gridColor='#f0f0f0',
            labelFontSize=12,
            titleFontSize=14
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)

        # 异常日详细数据
        with st.expander("查看异常日详细数据"):
            # 格式化数据框
            df_display = anomalies[['日期', '充电量', '充电量_zscore']].copy()
            df_display['日期'] = df_display['日期'].dt.strftime('%Y-%m-%d')
            df_display['充电量'] = df_display['充电量'].apply(lambda x: f"{x:,.0f}kWh")
            df_display['充电量_zscore'] = df_display['充电量_zscore'].apply(lambda x: f"{x:.1f}σ")
            df_display.columns = ['异常日期', '充电量', '偏离程度']
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "异常日期": st.column_config.DatetimeColumn(
                        "日期",
                        format="YYYY-MM-DD"
                    )
                }
            )
        
        # 分析说明
        st.markdown("""
        <div style="background-color:#F8F9FA;padding:15px;border-radius:8px">
            <h4>📊 分析说明</h4>
            <ul>
                <li>异常检测标准：充电量偏离历史均值2个标准差(σ)以上</li>
                <li>红色标记表示异常日期，建议重点关注这些日期的运营情况</li>
                <li>点击图表中的异常点可查看详细数据</li>
                <li>展开下方面板可查看完整异常日列表</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.success("✅ 运营数据正常，未检测到显著异常")

def multi_station_analysis(data):
    """多站点对比分析"""
    selected_stations = st.multiselect(
        "选择对比站点(至少2个)", 
        options=data['站点'].unique(),
        default=data['站点'].unique()[:2]
    )
    
    if len(selected_stations) < 2:
        st.warning("请选择至少2个站点进行对比")
        return
    
    filtered_data = data[data['站点'].isin(selected_stations)]
    
    # 站点对比指标
    st.subheader("站点核心指标对比")
    summary = filtered_data.groupby('站点').agg({
        '充电量': ['sum', 'mean'],
        '订单数': ['sum', 'mean'],
        '结算收益': ['sum', 'mean']
    }).reset_index()
    
    # 扁平化多级列名
    summary.columns = ['站点', '总充电量', '平均充电量', '总订单数', '平均订单数', '总收益', '平均收益']
    st.dataframe(summary.style.format({
        '总充电量': '{:,.0f}',
        '平均充电量': '{:,.1f}',
        '总订单数': '{:,.0f}',
        '平均订单数': '{:,.1f}',
        '总收益': '{:,.0f}',
        '平均收益': '{:,.1f}'
    }))
    
    # 对比图表
    st.subheader("对比可视化")
    metric = st.selectbox("选择对比指标", ['总充电量', '总订单数', '总收益'])
    
    bar_chart = alt.Chart(summary).mark_bar().encode(
        x='站点:N',
        y=f'{metric}:Q',
        color='站点:N',
        tooltip=['站点', metric]
    ).properties(height=400)
    st.altair_chart(bar_chart, use_container_width=True)
    
    # 时间趋势对比
    st.subheader("时间趋势对比")
    daily_comparison = filtered_data.groupby(['日期', '站点']).agg({
        '充电量': 'sum',
        '订单数': 'sum',
        '结算收益': 'sum'
    }).reset_index()
    
    trend_metric = st.selectbox("选择趋势指标", ['充电量', '订单数', '结算收益'])
    trend_chart = alt.Chart(daily_comparison).mark_line().encode(
        x='日期:T',
        y=f'{trend_metric}:Q',
        color='站点:N',
        tooltip=['日期', '站点', trend_metric]
    ).properties(height=400)
    st.altair_chart(trend_chart, use_container_width=True)
