# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 09:29:07 2024

@author: boyuan.zheng
"""
import pandas as pd
import math
import matplotlib.pyplot as plt
from datetime import timedelta,time
import streamlit as st

# 设置matplotlib字体支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def investment(first_year,second_year,up_ratio):
    """
    软件、硬件、运营投资部分处理函数
    输入：首年投入、次年投入、年度增长率
    输出：10年投资数据 dataframe
    """
    data = [first_year]
    for i in range (1,11):
        if i ==0:
            investment = first_year
        else:
            investment = second_year*(1+up_ratio)
        investment = round(investment,3) 
        data.append(investment)
    data = pd.DataFrame(data)
    data = data.iloc[:-1,:]
    return data
# hardware_investment = investment(0,20,0)
# software_investment = investment(0,3,0)
# operating_cost = investment(40,40,0)

# total_investment_cost =pd.concat([hardware_investment, software_investment, operating_cost], axis=1)


# print(total_investment_cost)
# print(total_investment_cost.sum(1))
def power_up(power,up_ratio,response_ratio
                        ,peak_shaving_moring_price,peak_shaving_count
                        ,valley_filling_afternoon_price,valley_filling_count
                        ,valley_filling_morning_price,valley__morning_count
                        ,day_ahead_response_price,day_ahead_response_count
                        ,intra_day_response_price,intra_day_response_count
                        ,intra_day_near_real_time_price,intra_day_near_real_time_count
                        ,split_ratio
             ):
    data = [power]
    for i in range (1,11):
        power = power*(1+up_ratio)
        power = round(power,3) 
        data.append(power)
    data = pd.DataFrame(data)
    data = data.iloc[:-1,:]
    energy_response = data*response_ratio
    #辅助服务收益部分计算
    peak_shaving_moring = energy_response*peak_shaving_moring_price*split_ratio*peak_shaving_count/10000
    valley_filling_afternoon = energy_response*valley_filling_afternoon_price*split_ratio*valley_filling_count/10000
    valley_filling_morning = energy_response*valley_filling_morning_price*split_ratio*valley__morning_count/10000
    #需求响应部分收益计算
    day_ahead_response = energy_response*day_ahead_response_price*day_ahead_response_count*(split_ratio+0.4)/10 #日前响应（万元/年）
    intra_day_response = energy_response*intra_day_response_price*intra_day_response_count*(split_ratio+0.4)/10 #日内响应（万元/年）
    intra_day_near_real_time = energy_response*intra_day_near_real_time_price*intra_day_near_real_time_count*(split_ratio+0.4)/10 #日内响应（万元/年）
    # 使用 concat 函数纵向合并 DataFrame
    combined_df_1 = pd.concat([peak_shaving_moring, valley_filling_afternoon, valley_filling_morning], axis=1)
    combined_df_1.columns= ['削峰（上午平峰）净收益（万元/年）','削峰（夜晚尖峰）净收益（万元/年）','填谷（凌晨低谷）净收益（万元/年）']
    combined_df_1 = pd.DataFrame(combined_df_1.sum(1))
    # 使用 concat 函数纵向合并 DataFrame
    combined_df_2 = pd.concat([day_ahead_response, intra_day_response, intra_day_near_real_time], axis=1)
    combined_df_2.columns= ['削峰（上午平峰）净收益（万元/年）','削峰（夜晚尖峰）净收益（万元/年）','填谷（凌晨低谷）净收益（万元/年）']
    combined_df_2 = pd.DataFrame(combined_df_2.sum(1))
    combined_df = combined_df_1+combined_df_2
    combined_df = combined_df_1+combined_df_2
    # 绘制柱状图
    # plot_bar(combined_df,'可调、可控负荷参与辅助服务+需求响应（万元/年）')
    return combined_df,combined_df_1,combined_df_2



def wind_solar_revenue(power,up_ratio,response_ratio
                        ,peak_shaving_moring_price,peak_shaving_count
                        ,valley_filling_afternoon_price,valley_filling_count
                        ,valley_filling_morning_price,valley__morning_count
                        ,day_ahead_response_price,day_ahead_response_count
                        ,intra_day_response_price,intra_day_response_count
                        ,intra_day_near_real_time_price,intra_day_near_real_time_count
                        ,split_ratio
                        ,hour
                        ,valley_filling_response_ratio
                        ,valley_filling_response_count
                        ,flat_period_electricity_price,subsidy_unit_price,purchase_grid_unit_price
             ):
    data = [power]
    for i in range (1,11):
        power = power*(1+up_ratio)
        power = round(power,3) 
        data.append(power)
    data = pd.DataFrame(data)
    data = data.iloc[:-1,:]
    adjustable_controllable_load_capacity = data
    print(adjustable_controllable_load_capacity)
    energy_response = data*response_ratio*hour
    peak_shaving_moring = energy_response*peak_shaving_moring_price*peak_shaving_count/10000 #削峰（万元/年
    abandonment_cost = energy_response*0.53*5/10*(-1) #弃光成本（万元/年）
    # 辅助服务合计收益（万元/年）= 削峰（万元/年）+弃光成本（万元/年）
    total_auxiliary_service_revenue = peak_shaving_moring+abandonment_cost
    #园区内填谷响应部分
    effective_response_capacity = adjustable_controllable_load_capacity*hour*valley_filling_response_ratio*0.1
    park_effective_response_capacity = effective_response_capacity*valley_filling_response_count
    electricity_price = flat_period_electricity_price-subsidy_unit_price-purchase_grid_unit_price
    total_demand_response_revenue = electricity_price*park_effective_response_capacity/10
    
    total_revenue = total_auxiliary_service_revenue+total_demand_response_revenue
    return total_revenue



def Battery_Degradation(energy_storage,energy_storage_deep,Battery_Degradation_year_1
                        ,Battery_Degradation_firstyear,Battery_Degradation_lateryear
                        ,Charging_Efficiency,Discharging_Efficiency):
    # energy_storage = 35 # 储能规模（MWh）
    # energy_storage_deep = 0.8 #储能放电深度
    # Battery_Degradation_year_1 = 0.10 
    # Battery_Degradation_firstyear = 0.05 #电池年衰减率-首年
    # Battery_Degradation_lateryear = 0.0225 # 电池年衰减率-以后年度
    #充电效率 (Charging Efficiency)\放电效率 (Discharging Efficiency)\系统效率 (System Efficiency)
    energy_storage_power = [energy_storage]
    System_Efficiency = math.sqrt(Charging_Efficiency*Discharging_Efficiency)
    year = 1
    for i in range(1, 11):
        if i == 1:
            energy_storage = energy_storage *energy_storage_deep* (1 - Battery_Degradation_firstyear)*System_Efficiency
        else:
            energy_storage = energy_storage*(1-Battery_Degradation_lateryear)
        energy_storage = round(energy_storage,4)
        energy_storage_power.append(energy_storage)
        year += 1
    energy_storage =  pd.DataFrame(energy_storage_power)
    print(energy_storage.iloc[1:,:].T)
    return energy_storage.iloc[1:,:]
# energy_storage = Battery_Degradation(35,0.9,0.10,0.05,0.0225,0.897,0.965)
def plot_bar(df,set_ylabel):
# 创建一个条形图函数，输入dataframe
    fig, ax = plt.subplots()
    df.plot(kind='bar', ax=ax)
    # 设置x轴标题
    ax.set_xlabel('年份')
    ax.set_ylabel(set_ylabel)
    ax.set_title(set_ylabel)
    # 添加y轴数据值，并确保文本位于柱状图上方
    for i, value in enumerate(df[0].values):
        ax.text(i, value + 1, f'{value:.2f}', ha='center', va='top')
    # # 调整y轴范围，以便文本不会被柱状图顶端所遮挡
    # ax.set_ylim(0, max(energy_storage.values) + 0.1)
# plot_bar(energy_storage)   
def energy_storage_vpp(energy_storage,energy_storage_deep,Battery_Degradation_year_1
                        ,Battery_Degradation_firstyear,Battery_Degradation_lateryear
                        ,Charging_Efficiency,Discharging_Efficiency,Response_Ratio
                        ,peak_shaving_moring_price,peak_shaving_count
                        ,valley_filling_afternoon_price,valley_filling_count
                        ,valley_filling_morning_price,valley__morning_count
                        ,day_ahead_response_price,day_ahead_response_count
                        ,intra_day_response_price,intra_day_response_count
                        ,intra_day_near_real_time_price,intra_day_near_real_time_count
                        ,split_ratio
                        ):
    energy_storage =Battery_Degradation(energy_storage,energy_storage_deep,Battery_Degradation_year_1
                            ,Battery_Degradation_firstyear,Battery_Degradation_lateryear
                            ,Charging_Efficiency,Discharging_Efficiency
                            
                            )
    energy_response = energy_storage*Response_Ratio
    # plot_bar(energy_storage,'储能实际容量（MWh）')
    # plot_bar(energy_response,'储能有效响应容量（MWh）')
    #辅助服务收益部分计算
    peak_shaving_moring = energy_response*peak_shaving_moring_price*split_ratio*peak_shaving_count/10000
    valley_filling_afternoon = energy_response*valley_filling_afternoon_price*split_ratio*valley_filling_count/10000
    valley_filling_morning = energy_response*valley_filling_morning_price*split_ratio*valley__morning_count/10000
    #需求响应部分收益计算
    day_ahead_response = energy_response*day_ahead_response_price*day_ahead_response_count*split_ratio/10 #日前响应（万元/年）
    intra_day_response = energy_response*intra_day_response_price*intra_day_response_count*split_ratio/10 #日内响应（万元/年）
    intra_day_near_real_time = energy_response*intra_day_near_real_time_price*intra_day_near_real_time_count*split_ratio/10 #日内响应（万元/年）
    # 使用 concat 函数纵向合并 DataFrame
    combined_df_1 = pd.concat([peak_shaving_moring, valley_filling_afternoon, valley_filling_morning], axis=1)
    combined_df_1.columns= ['削峰（上午平峰）净收益（万元/年）','削峰（夜晚尖峰）净收益（万元/年）','填谷（凌晨低谷）净收益（万元/年）']
    combined_df_1 = pd.DataFrame(combined_df_1.sum(1))
    # plot_bar(combined_df_1,'辅助服务合计收益（万元/年）')
    
    # 使用 concat 函数纵向合并 DataFrame
    combined_df_2 = pd.concat([day_ahead_response, intra_day_response, intra_day_near_real_time], axis=1)
    combined_df_2.columns= ['削峰（上午平峰）净收益（万元/年）','削峰（夜晚尖峰）净收益（万元/年）','填谷（凌晨低谷）净收益（万元/年）']
    combined_df_2 = pd.DataFrame(combined_df_2.sum(1))
    # plot_bar(combined_df_2,'储能需求响应（万元/年）')
    combined_df = combined_df_1+combined_df_2
    # plot_bar(combined_df,'储能参与辅助服务+需求响应（万元/年）')
    combined_df = combined_df.reset_index(drop=True)
    return combined_df,combined_df_1,combined_df_2
# energy_storage_revenue = energy_storage_vpp(35,0.9,0,0.05,0.0225,0.897,0.965,0.8,1000,20,1000,20,400,24,1,6,1.2,2,4,2,0.5)
# controllable_load_revenue = power_up(38,0.05,0.13,1000,10,1000,5,400,5,1,3,1.2,1,4,1,0.5)
# wind_solar_revenue = wind_solar_revenue(50,0.03,0.3,1000,4,1000,5,400,5,1,3,1.2,1,4,1,0.5,2,0.8,80,0.67,0.2,0.4)
# total_revenue_sum = energy_storage_revenue+controllable_load_revenue+wind_solar_revenue # 收益总和
# hardware_investment = investment(0,20,0)
# software_investment = investment(0,3,0)
# operating_cost = investment(40,40,0)
# investment_sum = hardware_investment+software_investment +operating_cost
# software_vendor_revenue = total_revenue_sum*0.1
# revenue = total_revenue_sum- software_vendor_revenue
# print(revenue)
# print(investment_sum)


def display_sidebar():
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
    ## 6月29日 优化number_input 最大值、最小值 加入logo展示
    st.sidebar.title('泰能电力虚拟电厂用户收益测算')
    
    ## 储能部分
    st.sidebar.subheader('储能输入参数')
    energy_storage_option = st.sidebar.selectbox("是否进行储能数据修改", ("是", "否"),index=1)
    if energy_storage_option == "是":
       #a = st.sidebar.select_slider('选择一个值', options=range(0, 101), value=0)
       energy_storage = st.sidebar.number_input("储能额定容量（MWh）", min_value=0,value=35, step=1)
       energy_storage_deep = st.sidebar.select_slider("放电深度（%）",options=range(0, 101), value=90)/100
       Battery_Degradation_firstyear = st.sidebar.number_input("电池年衰减率-首年（%）",min_value=0,max_value=100,value=5, step=1)/100
       Battery_Degradation_lateryear = st.sidebar.number_input("电池年衰减率-以后年度-首年（%）",min_value=0.00,max_value=100.00, value=2.25, step=0.01)/100
       Charging_Efficiency = st.sidebar.number_input("储能充电效率（%）", value=89.7,min_value=0.00,max_value=100.00, step=0.01)/100
       Discharging_Efficiency = st.sidebar.number_input("储能放电效率（%）",min_value=0.00,max_value=100.00, value=96.5, step=0.01)/100
       Response_Ratio = st.sidebar.select_slider("储能响应比例（%）", options=range(0, 101),value=80)/100
       peak_shaving_moring_price =  st.sidebar.number_input("削峰（上午平峰）响应单价（元/MWh）", min_value=0,max_value=10000,value=1000, step=1)
       peak_shaving_count =  st.sidebar.number_input("削峰（上午平峰）次数/年", value=20, min_value=0,max_value=1000,step=1)
       valley_filling_afternoon_price =  st.sidebar.number_input("削峰（夜晚尖峰）响应单价（元/MWh）", min_value=0,max_value=10000,value=1000, step=1)
       valley_filling_count =  st.sidebar.number_input("削峰（夜晚尖峰）次数/年", value=20, min_value=0,max_value=1000,step=1)
       valley_filling_morning_price =  st.sidebar.number_input("填谷（凌晨低谷）响应单价（元/MWh）", value=400, step=1, min_value=0,max_value=10000)
       valley__morning_count =  st.sidebar.number_input("填谷（凌晨低谷）次数/年", value=24, step=1,min_value=0,max_value=1000)
       day_ahead_response_price =  st.sidebar.number_input("日前响应响应单价（元/KWh）", value=1.0, step=0.1,min_value=0.00,max_value=100.00)
       day_ahead_response_count =  st.sidebar.number_input("日前响应次数/年", value=6, step=1,min_value=0,max_value=1000)
       intra_day_response_price =  st.sidebar.number_input("日内响应响应单价（元/KWh）", value=1.2, step=0.1,min_value=0.00,max_value=100.00)
       intra_day_response_count =  st.sidebar.number_input("日内响应次数/年", value=2, step=1,min_value=0,max_value=1000)
       intra_day_near_real_time_price =  st.sidebar.number_input("日内准实时响应单价（元/KWh）", value=4.0, step=0.1,min_value=0.00,max_value=100.00)
       intra_day_near_real_time_count =  st.sidebar.number_input("日内准实时次数/年", value=2, step=1,min_value=0,max_value=1000)
       split_ratio = st.sidebar.select_slider("与用户分享比例（%）", value=50,options=range(0, 101,5) )/100
       
       total,auxiliary_service_revenue,demand_response_revenue = energy_storage_vpp(energy_storage,energy_storage_deep,0
                               ,Battery_Degradation_firstyear,Battery_Degradation_lateryear
                               ,Charging_Efficiency,Discharging_Efficiency,Response_Ratio
                               ,peak_shaving_moring_price,peak_shaving_count
                               ,valley_filling_afternoon_price,valley_filling_count
                               ,valley_filling_morning_price,valley__morning_count
                               ,day_ahead_response_price,day_ahead_response_count
                               ,intra_day_response_price,intra_day_response_count
                               ,intra_day_near_real_time_price,intra_day_near_real_time_count
                               ,split_ratio
                               )
    else:
       total,auxiliary_service_revenue,demand_response_revenue = energy_storage_vpp(35,0.9,0,0.05,0.0225,0.897,0.965,0.8,1000,20,1000,20,400,24,1,6,1.2,2,4,2,0.5)
    ## 可调可控负荷部分 power_up(38,0.05,0.13,1000,10,1000,5,400,5,1,3,1.2,1,4,1,0.5)
    
    st.sidebar.subheader('可调可控负荷输入参数')
    controllable_load_energy_storage_option = st.sidebar.selectbox("是否进行可调可控负荷数据修改", ("是", "否"),index=1)
    if controllable_load_energy_storage_option == "是":
        controllable_load_power = st.sidebar.number_input("接入总负荷（MWh）", value=38, step=1,min_value=0,max_value=10000)
        controllable_load_up_ratio = st.sidebar.select_slider("负荷增长率（%）", value=5, options=range(0, 101))/100
        controllable_load_response_ratio= st.sidebar.select_slider("负荷响应比例（%）", value=13, options=range(0, 101))/100
        controllable_load_peak_shaving_moring_price  =  st.sidebar.number_input("可调可控负荷削峰（上午平峰）响应单价（元/MWh）", value=1000, step=1,min_value=0,max_value=10000)
        controllable_load_peak_shaving_count =  st.sidebar.number_input("可调可控负荷削峰（上午平峰）次数/年", value=10, step=1,min_value=0,max_value=1000)
        
        controllable_load_valley_filling_afternoon_price =  st.sidebar.number_input("可调可控负荷削峰（夜晚尖峰）响应单价（元/MWh）", value=1000, step=1,min_value=0,max_value=10000)
        controllable_load_valley_filling_count=  st.sidebar.number_input("可调可控负荷削峰（夜晚尖峰）次数/年", value=5, step=1,min_value=0,max_value=1000)
        controllable_load_valley_filling_morning_price =  st.sidebar.number_input("可调可控负荷填谷（凌晨低谷）响应单价（元/MWh））", value=400, step=1,min_value=0,max_value=10000)
        controllable_load_valley__morning_count =  st.sidebar.number_input("可调可控负荷填谷（凌晨低谷）次数/年", value=5, step=1,min_value=0,max_value=1000)
        #需求响应部分
        controllable_load_day_ahead_response_price=  st.sidebar.number_input("可调可控负荷日前响应单价（元/KWh）", value=1.0, step=0.1,min_value=0.00,max_value=10.00)
        controllable_load_day_ahead_response_count=  st.sidebar.number_input("可调可控负荷日前响应次数/年", value=3, step=1,min_value=0,max_value=1000)
        controllable_load_intra_day_response_price=  st.sidebar.number_input("可调可控负荷日内响应单价（元/KWh）", value=1.2, step=0.1,min_value=0.00,max_value=10.00)
        controllable_load_intra_day_response_count=  st.sidebar.number_input("可调可控负荷日内响应次数/年", value=1, step=1,min_value=0,max_value=1000)
        controllable_load_intra_day_near_real_time_price=  st.sidebar.number_input("可调可控负荷日内准实时响应单价（元/KWh）", value=4.0, step=0.1,min_value=0.00,max_value=10.00)
        controllable_load_intra_day_near_real_time_count=  st.sidebar.number_input("可调可控负荷日内准实时次数/年", value=1, step=1,min_value=0,max_value=1000)
        controllable_load_split_ratio = st.sidebar.select_slider("可调可控负荷与用户分享比例（%）", value=50, options=range(0, 101,5))/100
        controllable_load_total,controllable_load_auxiliary_service_revenue,controllable_load_demand_response_revenue= power_up(controllable_load_power,controllable_load_up_ratio,
                  controllable_load_response_ratio,controllable_load_peak_shaving_moring_price,controllable_load_peak_shaving_count,
                  controllable_load_valley_filling_afternoon_price,controllable_load_valley_filling_count,
                  controllable_load_valley_filling_morning_price,controllable_load_valley__morning_count,
                  controllable_load_day_ahead_response_price,controllable_load_day_ahead_response_count,
                  controllable_load_intra_day_response_price,controllable_load_intra_day_response_count,
                  controllable_load_intra_day_near_real_time_price,controllable_load_intra_day_near_real_time_count,
                  controllable_load_split_ratio
                  )
    else:
        controllable_load_total,controllable_load_auxiliary_service_revenue,controllable_load_demand_response_revenue= power_up(38,0.05,0.13,1000,10,1000,5,400,5,1,3,1.2,1,4,1,0.5)
    return total,auxiliary_service_revenue,demand_response_revenue,controllable_load_total,controllable_load_auxiliary_service_revenue,controllable_load_demand_response_revenue
def main():
    total,auxiliary_service_revenue,demand_response_revenue,controllable_load_total,controllable_load_auxiliary_service_revenue,controllable_load_demand_response_revenue = display_sidebar()
    ##储能参与辅助服务+需求响应
    with st.expander("虚拟电厂介绍 点击展开详情"):
        st.markdown('''
            ### 一、虚拟电厂是什么？————聚合资源、取长补短、量变到质变
        ''')
        st.markdown('''
- :red[***虚拟电厂是一种基于先进的信息通信技术和智能电网技术的新型电力系统管理解决方案。它通过将分散的、异构的分布式能源资源（如太阳能、风能、储能设备、可调负荷等）进行聚合和优化调度，形成一个虚拟的、可统一管理和调度的电力系统参与主体。***]
虚拟电厂不仅能够提高分布式能源的利用效率，增强电网的灵活性和可靠性，还能为电力市场提供更多的参与主体，促进市场竞争和创新发展。
- 风电、光伏等可再生能源，缺乏足够的可控制性，尽管发电边际成本低，但单独参与电能量市场，尤其是合约市场，存在一定的难度。  
- 储能、分布式燃机、生物质等同步发电机输出形式的发电资源具有友好、灵活、可调的优势，但边际成本偏高，在电力市场中“先天不足”。  
- :red[***虚拟电厂可以实现这些资源整合，扬长避短，获取最大收益。虚拟电厂通过聚合资源，量变上升为质变，以聚合后资源参与电能益市场和调节产品服务市场，提高议价能力。***]''')

        st.markdown('''### 二、虚拟电厂主要盈利模式''')
        st.markdown('''#### 1、基于电力市场波动实现低用高售''')
        st.markdown('''利用电力市场价格波动，虚拟电厂通过储能与光伏等资源的配合，实现低谷用电、高峰售电，获取最大的经济利润。''')
        st.markdown('''#### 2、利用快速调节能力赚取辅助服务''')
        st.markdown('''利用储能、微燃机等启动速度快、出力灵活的特点，参与电网的辅助服务，获取额外收益。''')
        st.markdown('''#### 3、参与现货市场参与高价品种竞争''')
        st.markdown(''':red[***《电力现货市场基本规则（试行）》经营主体扩大到虚拟电厂、独立储能等新型主体，在规则下可以参与备类高价交易品种市场竞争。***]''')
        VIDEO_URL = """<iframe src="//player.bilibili.com/player.html?isOutside=true&aid=492374152&bvid=BV1TN411x7Fa&cid=1303415771&p=1"width="100%" height="360" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>"""
        st.components.v1.html(VIDEO_URL,height=380)
    st.subheader('储能参与辅助服务+需求响应')
    #with st.expander("储能参与辅助服务+需求响应计算逻辑"):
            #st.markdown('分别计算储能参与辅助服务与需求的收益。')
            #st.selectbox("数据修改", ("是", "否"),index=1)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="合计收益（万元/年）",value= round(total.sum()))
    col2.metric(label="辅助服务收益（万元/年）",value= round(auxiliary_service_revenue.sum()))
    col3.metric(label="需求响应收益（万元/年）",value= round(demand_response_revenue.sum()))
    total = pd.DataFrame(total, columns=[0])
    total.index = total.index + 1
    total.columns=['储能收益']
    total= total.round(2)
    st.markdown('**储能参与虚拟电厂10年收益分布（万元/年）**')
    st.dataframe(total.T)
    st.bar_chart(total)
    st.markdown("----")
    ##可调、可控负荷参与辅助服务+需求响应
    st.subheader('可调、可控负荷参与辅助服务+需求响应')
    col4, col5, col6 = st.columns(3)
    col4.metric(label="合计收益（万元/年）",value= round(controllable_load_total.sum()))
    col5.metric(label="辅助服务收益（万元/年）",value= round(controllable_load_auxiliary_service_revenue.sum()))
    col6.metric(label="需求响应收益（万元/年）",value= round(controllable_load_demand_response_revenue.sum()))
    controllable_load_total = pd.DataFrame(controllable_load_total, columns=[0])
    controllable_load_total.index = controllable_load_total.index + 1
    controllable_load_total.columns=['可调、可控负荷收益']
    st.markdown('**可调、可控负荷参与虚拟电厂10年收益分布（万元/年）**')
    controllable_load_total= controllable_load_total.round(2)
    st.dataframe(controllable_load_total.T)
    st.bar_chart(controllable_load_total)
    
    st.subheader('储能+可调、可控负荷总收益情况')
    col7, col8, col9 = st.columns(3)
    # data1 = controllable_load_auxiliary_service_revenue
    # st.dataframe(data1)
    col7.metric(label="合计收益（万元/年）",value= round((total['储能收益']+controllable_load_total['可调、可控负荷收益']).sum()))
    col8.metric(label="辅助服务收益（万元/年）",value= round((controllable_load_auxiliary_service_revenue[0]+auxiliary_service_revenue[0]).sum()))
    col9.metric(label="需求响应收益（万元/年）",value= round((controllable_load_demand_response_revenue[0]+demand_response_revenue[0]).sum()))
    csv = total['储能收益']+controllable_load_total['可调、可控负荷收益']
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode("utf-8")
    csv = convert_df(csv)
    st.download_button(label="下载导出总收益CSV文件",data=csv,file_name="large_df.csv")
    st.bar_chart(total['储能收益']+controllable_load_total['可调、可控负荷收益'])
    
if __name__ == "__main__":
    main()
