import streamlit as st
import pandas as pd
import os
import json
from openai import OpenAI
from collections import defaultdict
import logging # Import logging for better error tracking

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenRouter API配置
# It's best practice to use Streamlit secrets for API keys, especially in deployment.
# st.secrets['openrouter_key'] will fetch the key from .streamlit/secrets.toml
# For local testing, you can keep the direct assignment or use an environment variable.
openrouter_key = os.getenv("OPENROUTER_API_KEY", "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") # Fallback for local testing
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_key
)

def test_openrouter_connection():
    """测试OpenRouter API连接"""
    try:
        test_prompt = "请回复'API连接正常'"
        response = client.chat.completions.create(
            model="qwen/qwen3-235b-a22b",
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=10,
            extra_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "工作总结分析系统"
            }
        )
        # Ensure the response content is handled as UTF-8
        response_content = response.choices[0].message.content
        if response_content and response_content.strip() == "API连接正常":
            st.success("✅ OpenRouter API连接正常")
        else:
            st.warning(f"⚠️ API返回异常或内容不匹配: {response_content}")
            logging.warning(f"API connection test returned: {response_content}")
    except Exception as e:
        st.error(f"❌ OpenRouter API连接失败: {str(e)}")
        logging.error(f"OpenRouter API connection failed: {e}", exc_info=True)

# Streamlit界面配置（只执行一次）
st.set_page_config(page_title="工作总结分析系统", layout="wide")
st.title("📊 工作日报总结分析")

# 初始化session_state
if 'report_df' not in st.session_state:
    st.session_state.report_df = None
if 'last_uploaded' not in st.session_state:
    st.session_state.last_uploaded = None

# Test API connection first
test_openrouter_connection()

@st.cache_data(show_spinner=False) # Cache the function result to avoid re-running unnecessarily
def extract_keywords_for_person(person_name: str, summaries: list) -> list:
    """使用OpenRouter LLM分析一个人的所有工作总结"""
    try:
        # Ensure all summaries are strings and handle potential NaNs if they sneak in
        cleaned_summaries = [str(s) for s in summaries if pd.notna(s)]
        if not cleaned_summaries:
            logging.info(f"No valid summaries found for {person_name}.")
            return []

        combined_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(cleaned_summaries)])

        # Ensure the system prompt is clear about JSON format
        system_prompt = """你是一个工作分析助手，请分析一个人一段时间的工作总结。
1. 提取主要工作任务，每个任务用3-5个字的短语描述。
2. 相似任务应进行合并（如'处理噪声'、'噪声投诉处理'、'噪音测试'统一归为'噪声处理'）。
3. 合并规则：相同领域的工作使用最简短的标准化表述。
4. 必须返回纯JSON格式，示例：{'tasks': ['任务1','任务2']}。请确保JSON是完全合法的，没有多余的字符或格式错误。"""

        # Using a more robust model for extraction if available and cost-effective.
        # Deepseek-coder-v2-instruct might be good for structured output, but qwen/qwen3-30b-a3b:free is what you used.
        # It's crucial that the model supports 'json_object' response format reliably.
        response = client.chat.completions.create(
            model="qwen/qwen3-30b-a3b:free", # Stick to your chosen model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析{person_name}的工作总结，提取标准化的工作任务:\n{combined_text}"}
            ],
            temperature=0.2,
            max_tokens=1000,
            response_format={"type": "json_object"}, # This is key for structured output
            extra_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "工作总结分析系统"
            }
        )
        result_content = response.choices[0].message.content
        logging.info(f"Raw LLM response for {person_name}: {result_content}")

        try:
            data = json.loads(result_content)
            if isinstance(data, dict) and 'tasks' in data and isinstance(data['tasks'], list):
                # Ensure tasks are strings and clean up whitespace
                return [task.strip() for task in data['tasks'] if isinstance(task, str)]
            logging.warning(f"LLM returned invalid structure for {person_name}: {data}")
            return []
        except json.JSONDecodeError as jde:
            st.error(f"解析{person_name}的工作分析结果失败，LLM返回内容不是有效JSON: {result_content}. 错误: {jde}")
            logging.error(f"JSON Decode Error for {person_name}: {result_content}", exc_info=True)
            return []
    except Exception as e:
        st.error(f"分析{person_name}工作出错: {e}")
        logging.error(f"Error analyzing {person_name}'s work: {e}", exc_info=True)
        return []

@st.cache_data(show_spinner=False) # Cache the function result
def analyze_work_history(df: pd.DataFrame) -> pd.DataFrame:
    """分析工作历史，记录每项工作的首次和最后一次出现"""
    # Ensure '提交时间' is datetime for proper sorting
    df['提交时间'] = pd.to_datetime(df['提交时间'], errors='coerce')
    df.dropna(subset=['姓名', '提交时间', '今日总结'], inplace=True) # Drop rows with missing crucial data

    work_records = []
    
    # Group by person and sort by time
    grouped = df.groupby('姓名')
    
    # Use st.progress for better UX during analysis
    progress_bar = st.progress(0)
    total_persons = len(grouped)
    
    for i, (name, group) in enumerate(grouped):
        group = group.sort_values('提交时间').reset_index(drop=True) # Reset index after sorting for .iloc safety
        valid_summaries = [s for s in group['今日总结'].tolist() if pd.notna(s) and s.strip() != '']
        
        if not valid_summaries:
            logging.info(f"Skipping {name}: No valid summaries after filtering.")
            progress_bar.progress((i + 1) / total_persons)
            continue
            
        st.info(f"正在分析: {name} 的工作总结 ({len(valid_summaries)} 条)")
        keywords = extract_keywords_for_person(name, valid_summaries)
        
        if not keywords:
            st.warning(f"⚠️ 未能为 {name} 提取到有效关键词。")
            logging.warning(f"No keywords extracted for {name}.")
            progress_bar.progress((i + 1) / total_persons)
            continue

        st.write(f"提取到关键词: {', '.join(keywords)}") # Display keywords for user feedback
        
        # Associate extracted keywords with their original dates from the group
        # This part needs careful alignment. If LLM extracts fewer keywords than summaries,
        # or if it summarizes across multiple days, the simple modulo approach might not be accurate.
        # A more robust approach might be to try and map keywords back to specific summaries/dates.
        # For now, let's keep the modulo but add a check to prevent IndexError.
        for work in keywords:
            # Try to find a date that's closest or representative.
            # A simple approach: find the first summary that might contain the work, then use its date.
            # This is heuristic and might not be perfect.
            associated_date = None
            for original_summary, submit_time in zip(group['今日总结'], group['提交时间']):
                if work in str(original_summary): # Check if the keyword is in the original summary
                    associated_date = submit_time
                    break
            
            if associated_date is None: # If not directly found, fallback to the group's earliest/latest date
                associated_date = group['提交时间'].min() # Or group['提交时间'].max()

            work_records.append({
                'work': work,
                'person': name,
                'date': associated_date # Use the derived date
            })
        
        progress_bar.progress((i + 1) / total_persons)
    
    progress_bar.empty() # Clear the progress bar after completion
    
    # Group by work content and count occurrences for each person
    work_stats_detailed = defaultdict(lambda: defaultdict(list))
    for record in work_records:
        work_stats_detailed[record['work']][record['person']].append(record['date'])
    
    # Generate summary report
    report = []
    for work, persons_data in work_stats_detailed.items():
        all_dates_for_work = []
        all_persons_involved = []
        person_occurrence_counts = defaultdict(int)

        for person, dates in persons_data.items():
            all_dates_for_work.extend(dates)
            all_persons_involved.append(person)
            person_occurrence_counts[person] += len(dates) # Count how many times this person did this work

        if not all_dates_for_work:
            continue

        # Determine the main person based on the most occurrences for this specific work
        main_person = max(person_occurrence_counts.items(), key=lambda item: item[1])[0]

        report.append({
            '工作内容': work,
            '负责人': main_person,
            '开始时间': min(all_dates_for_work).strftime('%Y-%m-%d') if pd.notna(min(all_dates_for_work)) else 'N/A',
            '结束时间': max(all_dates_for_work).strftime('%Y-%m-%d') if pd.notna(max(all_dates_for_work)) else 'N/A',
            '出现次数': len(all_dates_for_work),
            '涉及人员': ', '.join(sorted(set(all_persons_involved))) # Ensure unique and sorted persons
        })
    
    # Sort the final report by '开始时间' for better readability
    final_report_df = pd.DataFrame(report)
    if not final_report_df.empty:
        final_report_df['开始时间_sort'] = pd.to_datetime(final_report_df['开始时间'], errors='coerce')
        final_report_df = final_report_df.sort_values(by='开始时间_sort').drop(columns=['开始时间_sort'])
    
    return final_report_df

# --- Main UI logic ---

st.sidebar.header("文件上传")
uploaded_file = st.sidebar.file_uploader("上传工作总结CSV文件", type=["csv"])

if uploaded_file:
    # Check if a new file is uploaded or if the content has changed (simple filename check)
    if uploaded_file.name != st.session_state.last_uploaded:
        st.session_state.report_df = None  # Clear previous analysis results
        st.session_state.last_uploaded = uploaded_file.name
        st.session_state.file_processed = False # Flag to indicate new file, not yet processed

    try:
        # Explicitly specify encoding for reading CSV, common for Chinese characters
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        # Check if essential columns exist
        required_columns = ['姓名', '提交时间', '今日总结']
        if not all(col in df.columns for col in required_columns):
            st.error(f"CSV文件缺少必要的列。请确保包含 '{', '.join(required_columns)}'。")
            st.session_state.report_df = None
            st.session_state.file_processed = False
        else:
            st.session_state.raw_df = df # Store raw dataframe for analysis
            st.session_state.file_processed = True
            with st.expander("原始数据预览"):
                st.dataframe(df.head())
    except UnicodeDecodeError:
        st.error("无法解码CSV文件。请尝试使用UTF-8编码的文件。")
        st.session_state.report_df = None
        st.session_state.file_processed = False
    except Exception as e:
        st.error(f"读取CSV文件时发生错误: {e}")
        st.session_state.report_df = None
        st.session_state.file_processed = False

    if st.session_state.file_processed:
        if st.button("开始分析", key="analyze_button"):
            with st.spinner("正在分析中，请稍候..."):
                # Use the raw_df from session state
                st.session_state.report_df = analyze_work_history(st.session_state.raw_df.copy()) # Pass a copy to avoid modifying original df in cache
            st.success("分析完成！")

# If analysis results are available, display the report and filtering controls
if st.session_state.report_df is not None and not st.session_state.report_df.empty:
    report_df = st.session_state.report_df
    
    st.markdown("---")
    st.subheader("分析结果")
    st.dataframe(report_df, use_container_width=True) # Use container_width for better display

    st.markdown("---")
    st.subheader("数据筛选")
    col1, col2 = st.columns(2)
    
    with col1:
        # Get unique values for dropdowns, ensure they are string types
        unique_persons = [str(p) for p in report_df['负责人'].unique()]
        selected_person = st.multiselect(
            "按负责人筛选",
            options=unique_persons,
            default=unique_persons # Default to all selected
        )
        
    with col2:
        unique_works = [str(w) for w in report_df['工作内容'].unique()]
        selected_work = st.multiselect(
            "按工作内容筛选", 
            options=unique_works,
            default=unique_works # Default to all selected
        )
    
    # Apply filtering conditions
    # Check if selected_person or selected_work are empty lists (if nothing is selected)
    person_filter = report_df['负责人'].isin(selected_person) if selected_person else pd.Series([True] * len(report_df))
    work_filter = report_df['工作内容'].isin(selected_work) if selected_work else pd.Series([True] * len(report_df))
    
    filtered_df = report_df[person_filter & work_filter]
    
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("没有找到匹配的数据，请调整筛选条件")
        
    st.download_button(
        label="下载分析结果 (CSV)",
        data=filtered_df.to_csv(index=False, encoding='utf-8-sig'), # 'utf-8-sig' for BOM, better for Excel
        file_name="工作历史分析报告.csv",
        mime="text/csv"
    )
    st.download_button(
        label="下载分析结果 (JSON)",
        data=filtered_df.to_json(orient='records', force_ascii=False, indent=4).encode('utf-8'),
        file_name="工作历史分析报告.json",
        mime="application/json"
    )

st.markdown("---")
with st.expander("使用说明", expanded=True):
    st.markdown("""
    1.  **上传CSV文件**: 请上传包含工作总结的CSV文件。文件必须包含以下三列：
        * `姓名` (员工姓名)
        * `提交时间` (日报提交日期/时间)
        * `今日总结` (具体的工作总结内容)
        确保CSV文件采用**UTF-8编码**，特别是包含中文内容时。
    2.  **开始分析**: 上传文件后，点击"**开始分析**"按钮，系统将利用AI模型提取和标准化每位员工的工作任务。这个过程可能需要一些时间，请耐心等待。
    3.  **查看和筛选结果**: 分析完成后，您可以看到一个汇总报告。您可以使用下方的筛选器根据"**负责人**"或"**工作内容**"来精细查看数据。
    4.  **下载报告**: 您可以将筛选后的分析结果下载为CSV或JSON格式。
    """)
    st.info("💡 **提示**: 首次运行时，或上传新文件后，分析过程可能较长。后续如果文件内容不变，系统会使用缓存加速。")
