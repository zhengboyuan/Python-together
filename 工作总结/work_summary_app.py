import streamlit as st
import pandas as pd
import os
import json
from openai import OpenAI
from collections import defaultdict

# Deepseek API配置
deepseek_key = "sk-5e2d18a842094fdead32a0a2b259439f"
client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")

def test_deepseek_connection():
    """测试Deepseek API连接"""
    try:
        test_prompt = "请回复'API连接正常'"
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=10
        )
        if response.choices[0].message.content == "API连接正常":
            st.success("✅ Deepseek API连接正常")
        else:
            st.warning(f"⚠️ API返回异常: {response.choices[0].message.content}")
    except Exception as e:
        st.error(f"❌ Deepseek API连接失败: {str(e)}")

# Streamlit界面配置（只执行一次）
st.set_page_config(page_title="工作总结分析系统", layout="wide")
st.title("📊 工作日报总结分析")

# 初始化session_state
if 'report_df' not in st.session_state:
    st.session_state.report_df = None
if 'last_uploaded' not in st.session_state:
    st.session_state.last_uploaded = None

# 测试API连接
test_deepseek_connection()

def extract_keywords_for_person(person_name, summaries):
    """使用Deepseek分析一个人的所有工作总结"""
    try:
        combined_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(summaries)])
        system_prompt = """你是一个工作分析助手，请分析一个人一段时间的工作总结。
1. 提取主要工作任务，每个任务用3-5个字的短语描述
2. 相似任务应进行合并（如'处理噪声'、'噪声投诉处理'、'噪音测试'统一归为'噪声处理'）
3. 合并规则：相同领域的工作使用最简短的标准化表述
4. 必须返回纯JSON格式，示例：{'tasks': ['任务1','任务2']}"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析{person_name}的工作总结，提取标准化的工作任务:\n{combined_text}"}
            ],
            temperature=0.2,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        result = response.choices[0].message.content
        try:
            data = json.loads(result)
            if isinstance(data, dict) and 'tasks' in data:
                return data['tasks']
            return []
        except json.JSONDecodeError:
            st.error(f"解析{person_name}的工作分析结果失败，返回内容: {result}")
            return []
    except Exception as e:
        st.error(f"分析{person_name}工作出错: {e}")
        return []

def analyze_work_history(df):
    """分析工作历史，记录每项工作的首次和最后一次出现"""
    work_records = []
    
    # 按人员分组并按时间排序
    grouped = df.groupby('姓名')
    
    for name, group in grouped:
        group = group.sort_values('提交时间')
        valid_summaries = [s for s in group['今日总结'] if pd.notna(s)]
        
        if not valid_summaries:
            continue
            
        st.write(f"正在分析: {name} 的工作总结")
        keywords = extract_keywords_for_person(name, valid_summaries)
        st.write(f"提取到关键词: {keywords}")
        
        # 记录每项工作的实际日期
        for idx, work in enumerate(keywords):
            record_idx = idx % len(group)  # 使用循环索引避免越界
            work_records.append({
                'work': work,
                'person': name,
                'date': group.iloc[record_idx]['提交时间']
            })
    
    # 按工作内容分组统计
    work_stats = defaultdict(list)
    for record in work_records:
        work_stats[record['work']].append(record)
    
    # 生成汇总报告
    report = []
    for work, records in work_stats.items():
        dates = [r['date'] for r in records]
        persons = list(set([r['person'] for r in records]))
        
        person_counts = defaultdict(int)
        for r in records:
            person_counts[r['person']] += 1
        main_person = max(person_counts.items(), key=lambda x: x[1])[0]
        
        report.append({
            '工作内容': work,
            '负责人': main_person,
            '开始时间': min(dates),
            '结束时间': max(dates),
            '出现次数': len(dates),
            '涉及人员': ','.join(persons)
        })
    
    return pd.DataFrame(report)

# 主界面功能

uploaded_file = st.file_uploader("上传工作总结CSV文件", type=["csv"])

if uploaded_file:
    # 检查是否上传了新文件
    if uploaded_file.name != st.session_state.last_uploaded:
        st.session_state.report_df = None  # 清除之前的分析结果
        st.session_state.last_uploaded = uploaded_file.name
    
    df = pd.read_csv(uploaded_file)
    with st.expander("原始数据预览"):
        st.dataframe(df.head())
    
    if st.button("开始分析"):
        with st.spinner("正在分析中，请稍候..."):
            # 保存分析结果到session_state
            st.session_state.report_df = analyze_work_history(df)
    
    # 如果已有分析结果，显示分析报告和筛选控件
    if st.session_state.report_df is not None:
        report_df = st.session_state.report_df
        st.subheader("分析结果")
        st.dataframe(report_df)
        
        st.subheader("数据筛选")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_person = st.multiselect(
                "按负责人筛选",
                options=report_df['负责人'].unique(),
                default=report_df['负责人'].unique()
            )
        
        with col2:
            selected_work = st.multiselect(
                "按工作内容筛选", 
                options=report_df['工作内容'].unique(),
                default=report_df['工作内容'].unique()
            )
        
        # 应用筛选条件（简化逻辑）
        person_filter = report_df['负责人'].isin(selected_person) if selected_person else True
        work_filter = report_df['工作内容'].isin(selected_work) if selected_work else True
        
        # 应用筛选条件
        filtered_df = report_df[person_filter & work_filter]
        
        if not filtered_df.empty:
            st.dataframe(filtered_df)
        else:
            st.warning("没有找到匹配的数据，请调整筛选条件")
        
        st.download_button(
            label="下载分析结果",
            data=filtered_df.to_csv(index=False, encoding='utf-8-sig'),
            file_name="工作历史分析报告.csv",
            mime="text/csv"
        )


with st.expander("使用说明"):
    st.markdown("""
    1. 上传包含工作总结的CSV文件（需包含'姓名'、'提交时间'和'今日总结'列）
    2. 点击"开始分析"按钮
    3. 使用筛选功能查看特定人员或工作内容
    4. 点击"下载分析结果"保存报告
    """)
