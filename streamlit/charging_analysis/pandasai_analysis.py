import pandas as pd
from pandasai import SmartDataframe
from deepseek_llm import DeepseekLLM
import streamlit as st
import time
import logging
import io
import os
from dotenv import load_dotenv
from pandasai.agent.base_judge import BaseJudge
# 加载环境变量
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHART_DIR = "exports/charts"

def get_df_info(df: pd.DataFrame) -> str:
    """Captures DataFrame.info() output as a string."""
    buffer = io.StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()

def analyze_with_pandasai(data: pd.DataFrame, question: str, api_key: str) -> dict:
    """使用PandasAI分析数据并返回结构化结果"""
    try:
        if data.empty:
            return {"type": "error", "message": "输入数据为空"}
        if not api_key:
            return {"type": "error", "message": "缺少Deepseek API密钥"}

        llm = DeepseekLLM(
            api_key=api_key,
            temperature=0.3,
            max_tokens=1500
        )
        
        # 准备数据信息
        df_info = get_df_info(data)
        df_head = data.head().to_markdown(index=False)
        
        enhanced_question = f"""
        请基于以下数据进行分析:
        数据结构信息:
        {df_info}
        
        前5行数据:
        {df_head}
        
        问题: {question}
        
        要求:
        1. 用中文回答，结构清晰
        2. 包含具体数据支持
        3. 返回文本分析结果
        """
        
        df = SmartDataframe(
            data,
            config={
                "llm": llm,
                "enable_cache": True,
                "verbose": True,
                "max_retries": 3,
                "conversational": False,
                "save_charts": False,
                "api_key": os.getenv("PANDASAI_API_KEY")
            }
        )
        
        logging.info(f"正在分析问题: {question}")
        result = df.chat(enhanced_question)
        generated_code = df.last_code_generated
        
        # 处理不同类型的结果
        if isinstance(result, pd.DataFrame):
            return {
                "type": "dataframe",
                "value": result.to_markdown(index=False),
                "code": generated_code
            }
        elif isinstance(result, str):
            return {
                "type": "text", 
                "value": result,
                "code": generated_code
            }
        else:
            return {
                "type": "other",
                "value": str(result),
                "code": generated_code
            }
            
    except Exception as e:
        logging.error(f"分析失败: {str(e)}")
        return {
            "type": "error",
            "message": f"分析失败: {str(e)}",
            "code": getattr(df, 'last_code_generated', None) if 'df' in locals() else None
        }

def pandasai_analysis(filtered_data, deepseek_key):
    """执行PandasAI智能分析"""
    if not deepseek_key:
        st.warning("请输入Deepseek API密钥以使用智能分析功能")
        return
    if filtered_data.empty:
        st.warning("没有可用的数据，请检查筛选条件")
        return

    st.header("PandasAI智能分析")
    
    # 问题模板选择
    question_type = st.selectbox(
        "选择问题类型",
        ["站点比较", "时间趋势", "异常检测", "统计分析", "自定义问题"],
        index=0
    )
    
    # 根据问题类型提供模板
    templates = {
        "站点比较": "比较不同站点在[指标]方面的表现，列出前3名和后3名",
        "时间趋势": "分析[指标]随时间的变化趋势，指出关键变化点", 
        "异常检测": "近一周，检测各个站点充电量中的异常值，分析可能原因",
        "统计分析": "计算[指标]的基本统计量（均值/中位数/标准差等）",
        "自定义问题": ""
    }
    
    default_question = templates[question_type]
    if question_type == "自定义问题":
        default_question = "哪些站点表现最好？"
    
    question = st.text_input(
        "输入您想分析的问题", 
        default_question,
        help="建议包含具体指标如充电量、订单数等，明确分析要求"
    )
    
    if st.button("执行智能分析"):
        with st.spinner("正在分析..."):
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    # 使用封装好的分析函数
                    analysis_result = analyze_with_pandasai(
                        data=filtered_data,
                        question=question,
                        api_key=deepseek_key
                    )
                    
                    if analysis_result["type"] == "error":
                        st.error(analysis_result["message"])
                        if analysis_result.get("code"):
                            with st.expander("查看生成代码(调试)"):
                                st.code(analysis_result["code"], language="python")
                    elif analysis_result["type"] == "dataframe":
                        st.success("分析结果(表格)")
                        st.markdown(analysis_result["value"])
                        if analysis_result.get("code"):
                            with st.expander("查看生成代码(调试)"):
                                st.code(analysis_result["code"], language="python")
                    else:  # text or other
                        st.success("分析结果")
                        st.markdown(analysis_result["value"])
                        if analysis_result.get("code"):
                            with st.expander("查看生成代码(调试)"):
                                st.code(analysis_result["code"], language="python")
                    break
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        st.error(f"分析失败: {str(e)}")
                    else:
                        st.warning(f"尝试 {attempt + 1} 失败，正在重试...")
                        time.sleep(retry_delay)
