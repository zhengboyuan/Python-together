import os
import pandas as pd
import streamlit as st
from pandasai import Agent, SmartDataframe
from deepseek_llm import DeepseekLLM
from dotenv import load_dotenv
from pdf_utils import generate_pdf_report
# 加载环境变量
load_dotenv()

def smart_report(filtered_data, deepseek_key):
    """智能PandasAI分析功能"""
    filtered_data = SmartDataframe(filtered_data)
    print('SmartDataframe的数据：',filtered_data)
    llm = DeepseekLLM(
            api_key=deepseek_key,
            temperature=0.3,
            max_tokens=1500
        )
    
    # 在question输入后添加提示增强
    enhanced_question = prompt = f"""
                    请基于充电场站数据生成专业分析报告
                    
                    报告结构要求:
                    ======================
                    1. 执行摘要
                        - 核心发现(不超过3点，必须包含具体站点名称和数值)
                        - 关键指标变化概览
                    
                    2. 详细分析
                        - 站点运营对比:
                            * 按总充电量/订单数/收益的排名
                            * 表现最佳和最差站点(附具体数据)
                            * 站点间差异分析
                        - 时间趋势分析:
                            * 日/周/月趋势图表描述
                            * 环比增长率(与上月比较)
                            * 关键转折点标注
                        - 异常检测:
                            * 异常站点/时段识别
                            * 可能原因分析
                            * 数据质量检查
                    
                    3. 结论与建议
                        - 可立即实施的3条改进建议
                        - 长期发展建议(1-2条)
                        - 风险预警(具体站点/指标)
                    
                    技术要求:
                    - 使用中文，专业术语但表述清晰
                    - 每个结论必须附带数据支持(如: "A站充电量环比下降15%")
                    - 使用Markdown格式，包含二级标题和列表
                    - 关键数据用**加粗**突出显示
                    严格要求:
                    - 所有比较必须包含完整站点名称和具体数值
                    - 禁止使用模糊表述如"某些站点"、"部分站点"
                    - 关键数据用**加粗**突出显示
                    """
    if st.button("执行Deepseck分析"):
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
                print('分析报告：',response)
                # 删除前8个字符
                if isinstance(response, str):
                    processed_response = response[12:]
                    st.write(processed_response)
                    
                    # 生成Markdown下载按钮
                    st.download_button(
                        label="下载Markdown报告",
                        data=processed_response,
                        file_name="智能分析报告.md",
                        mime="text/markdown"
                    )
                    
                    # 生成PDF下载按钮
                    generate_pdf_report(processed_response)
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                st.info("请检查: 1. API密钥是否有效 2. 网络连接 3. 服务可用性")
