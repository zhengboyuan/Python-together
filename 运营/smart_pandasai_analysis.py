import os
import pandas as pd
import streamlit as st
from pandasai import Agent, SmartDataframe
from deepseek_llm import DeepseekLLM
from dotenv import load_dotenv
from pdf_utils import generate_pdf_report
# 加载环境变量
load_dotenv()

def smart_pandasai_analysis(filtered_data, deepseek_key):
    """智能PandasAI分析功能"""
    filtered_data = SmartDataframe(filtered_data)
    st.header("智能PandasAI分析")
    llm = DeepseekLLM(
            api_key=deepseek_key,
            temperature=0.3,
            max_tokens=1500
        )
    question = st.text_input(
        "输入您想分析的问题", 
        help="建议包含具体指标如充电量、订单数等，明确分析要求"
    )
    # 在question输入后添加提示增强
    enhanced_question = f"""
            请基于充电场站数据回答以下问题:
            {question}

            要求:
            1. 使用中文回答
            2. 结果必须包含以下结构化内容:
                - 1. 结论: 简明扼要的核心发现
                - 2. 数据支持: 
                    * 环比变化分析(与上月/上周期比较，如有) 
                    * 与其他场站的横向对比
                    * 关键指标数值(明确标注高于/低于基准值多少)
                    * 可视化数据摘要(如表格、关键统计量)
                - 3. 建议: 
                    * 基于数据分析的可行性建议
                    * 潜在改进方向
                    * 风险预警(如适用)可以指出具体是哪些场站需要注意。
            """
    if st.button("执行PandasAI分析"):
        with st.spinner("正在分析..."):
            try:
                #加入预处理功能
                #preprocessed_data = filtered_data.copy()
                #转换日期列为字符串格式(如果存在)
                #date_cols = preprocessed_data.select_dtypes(include=['datetime']).columns
                #preprocessed_data[date_cols] = preprocessed_data[date_cols].astype(str)
                agent = Agent(filtered_data
                              , config = {
                                "llm": llm,                     # 指定语言模型
                                "enable_cache": True,           # 启用缓存
                                "max_retries": 3,               # 最大重试次数
                                "conversational": False,        # 非对话模式更快
                                "api_key": os.getenv("PANDASAI_API_KEY")
                            }
                              ,description="智能充电场站运营数据分析助手，支持充电量、订单数、利用率等核心指标分析"
                              ,memory_size=20  # 扩大记忆容量
                              )
                response = agent.chat(enhanced_question)
                st.success("分析完成")
                st.write(response)
                
                # 生成PDF下载按钮
                if isinstance(response, str):
                    generate_pdf_report(response)
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                st.info("请检查: 1. API密钥是否有效 2. 网络连接 3. 服务可用性")
