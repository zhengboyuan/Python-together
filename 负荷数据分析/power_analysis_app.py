# -*- coding: utf-8 -*-
"""
功率数据分析 Web 应用
基于 Streamlit 的交互式功率数据分析工具

功能：
1. 支持用户直接粘贴CSV格式数据
2. 实时数据预览和验证
3. 24小时功率曲线分析
4. 统计信息展示
5. 错误处理和用户指导

作者: 数据分析助手
创建时间: 2025-06-16
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import io
import platform
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="功率数据分析工具",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 根据操作系统设置中文字体
system = platform.system()
if system == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans GB', 'STHeiti']
elif system == 'Windows':  # Windows
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
else:  # Linux
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Micro Hei']

plt.rcParams['axes.unicode_minus'] = False

def get_sample_data():
    """
    生成示例数据
    """
    sample_data = """时间,时刻,输出功率
01/01/90,00:00:00,0.0
01/01/90,01:00:00,0.0
01/01/90,02:00:00,0.0
01/01/90,03:00:00,0.0
01/01/90,04:00:00,0.0
01/01/90,05:00:00,10.5
01/01/90,06:00:00,320.8
01/01/90,07:00:00,1096.2
01/01/90,08:00:00,2253.1
01/01/90,09:00:00,3368.0
01/01/90,10:00:00,4162.3
01/01/90,11:00:00,4615.8
01/01/90,12:00:00,4692.7
01/01/90,13:00:00,4459.5
01/01/90,14:00:00,3833.9
01/01/90,15:00:00,2836.4
01/01/90,16:00:00,1668.1
01/01/90,17:00:00,631.9
01/01/90,18:00:00,116.2
01/01/90,19:00:00,0.0
01/01/90,20:00:00,0.0
01/01/90,21:00:00,0.0
01/01/90,22:00:00,0.0
01/01/90,23:00:00,0.0"""
    return sample_data

def detect_delimiter(csv_text):
    """
    智能检测CSV数据的分隔符
    """
    # 获取前几行用于分析
    lines = csv_text.strip().split('\n')[:5]  # 使用前5行进行检测
    if not lines:
        return ','

    # 定义候选分隔符及其显示名称
    delimiters = {
        '\t': '制表符(Tab)',
        ',': '逗号',
        ';': '分号',
        '|': '竖线',
        ' ': '空格'
    }

    delimiter_scores = {}

    for delimiter, name in delimiters.items():
        scores = []
        column_counts = []

        for line in lines:
            if line.strip():  # 跳过空行
                parts = line.split(delimiter)
                column_count = len(parts)
                column_counts.append(column_count)

                # 评分标准：
                # 1. 列数一致性（所有行的列数应该相同）
                # 2. 列数合理性（应该大于1）
                # 3. 内容合理性（分割后的内容不应该太长）

                if column_count > 1:
                    scores.append(1)  # 基础分

                    # 检查分割后内容的合理性
                    reasonable_parts = sum(1 for part in parts if len(part.strip()) < 50)
                    if reasonable_parts == column_count:
                        scores.append(1)  # 内容长度合理
                else:
                    scores.append(0)

        if column_counts:
            # 检查列数一致性
            unique_counts = set(column_counts)
            if len(unique_counts) == 1 and list(unique_counts)[0] > 1:
                consistency_score = 2  # 列数完全一致且大于1
            elif len(unique_counts) <= 2:
                consistency_score = 1  # 列数基本一致
            else:
                consistency_score = 0  # 列数不一致

            total_score = sum(scores) + consistency_score
            delimiter_scores[delimiter] = {
                'score': total_score,
                'name': name,
                'columns': max(column_counts) if column_counts else 0
            }

    # 选择得分最高的分隔符
    if delimiter_scores:
        best_delimiter = max(delimiter_scores.keys(),
                           key=lambda x: delimiter_scores[x]['score'])

        # 如果最高分大于0，返回该分隔符
        if delimiter_scores[best_delimiter]['score'] > 0:
            return best_delimiter

    # 如果所有分隔符得分都为0，使用启发式方法
    first_line = lines[0] if lines else ""

    # 按优先级检查
    if '\t' in first_line:
        return '\t'
    elif ',' in first_line:
        return ','
    elif ';' in first_line:
        return ';'
    elif '|' in first_line:
        return '|'
    else:
        return ','  # 默认使用逗号

def parse_csv_data(csv_text):
    """
    解析CSV文本数据，智能识别分隔符
    """
    if not csv_text.strip():
        return None, "输入数据为空"

    # 预处理：移除可能的BOM标记
    csv_text = csv_text.replace('\ufeff', '')

    # 智能检测分隔符
    detected_delimiter = detect_delimiter(csv_text)

    # 分隔符显示名称映射
    delimiter_names = {
        '\t': '制表符(Tab)',
        ',': '逗号',
        ';': '分号',
        '|': '竖线',
        ' ': '空格'
    }

    delimiter_name = delimiter_names.get(detected_delimiter, f"'{detected_delimiter}'")

    # 尝试使用检测到的分隔符解析数据
    try:
        df = pd.read_csv(io.StringIO(csv_text), sep=detected_delimiter)

        # 验证解析结果
        if len(df.columns) < 2:
            raise ValueError("解析后列数少于2列")

        # 检查是否有空列名或重复列名
        if df.columns.duplicated().any():
            raise ValueError("存在重复的列名")

        if any(str(col).strip() == '' for col in df.columns):
            raise ValueError("存在空的列名")

        return df, f"✅ 成功使用 {delimiter_name} 分隔符解析数据"

    except Exception as e:
        # 如果检测的分隔符失败，尝试其他分隔符
        fallback_delimiters = ['\t', ',', ';', '|']

        for delimiter in fallback_delimiters:
            if delimiter == detected_delimiter:
                continue  # 跳过已经尝试过的分隔符

            try:
                df = pd.read_csv(io.StringIO(csv_text), sep=delimiter)

                if len(df.columns) >= 2 and not df.columns.duplicated().any():
                    delimiter_name = delimiter_names.get(delimiter, f"'{delimiter}'")
                    return df, f"⚠️ 使用备用分隔符 {delimiter_name} 解析数据"

            except:
                continue

        # 所有分隔符都失败
        error_msg = f"""
❌ 数据解析失败

**检测到的分隔符**: {delimiter_name}
**错误信息**: {str(e)}

**可能的原因**:
1. 数据格式不规范（列数不一致）
2. 包含特殊字符或编码问题
3. 缺少表头行
4. 分隔符使用不一致

**建议解决方案**:
1. 确保数据包含表头行
2. 检查每行的列数是否一致
3. 确保使用统一的分隔符
4. 尝试使用示例数据格式
"""

        return None, error_msg

def validate_data(df):
    """
    验证数据格式
    """
    errors = []
    warnings = []
    
    # 检查必要的列
    required_columns = ['时刻', '输出功率']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f"缺少必要的列: {missing_columns}")
        errors.append(f"当前列名: {df.columns.tolist()}")
        return errors, warnings
    
    # 检查数据类型
    if df['输出功率'].dtype not in ['int64', 'float64']:
        try:
            df['输出功率'] = pd.to_numeric(df['输出功率'], errors='coerce')
            if df['输出功率'].isna().any():
                warnings.append("部分输出功率数据无法转换为数值，已设为NaN")
        except:
            errors.append("输出功率列包含无法转换为数值的数据")
    
    # 检查时刻格式
    try:
        # 尝试解析时刻数据
        if df['时刻'].dtype == 'object':
            sample_time = str(df['时刻'].iloc[0])
            if ':' not in sample_time:
                errors.append("时刻格式错误，应包含冒号分隔符（如：12:30:00）")
    except:
        errors.append("时刻列数据格式异常")
    
    # 检查数据完整性
    if len(df) < 24:
        warnings.append(f"数据行数较少（{len(df)}行），建议包含24小时完整数据")
    
    return errors, warnings

def extract_hour_data(df):
    """
    从时刻列提取小时数据
    """
    try:
        # 如果时刻列是时间格式，需要先转换为字符串
        if df['时刻'].dtype == 'object':
            # 尝试直接从时间对象提取小时
            try:
                # 如果是时间对象，直接提取小时
                df['小时'] = pd.to_datetime(df['时刻'], format='%H:%M:%S').dt.hour
            except:
                # 如果是字符串格式，按原方法处理
                df['小时'] = df['时刻'].astype(str).str.split(':').str[0].astype(int)
        else:
            # 其他情况转换为字符串后处理
            df['小时'] = df['时刻'].astype(str).str.split(':').str[0].astype(int)
        
        return True, None
        
    except Exception as e:
        # 备用方法：直接从时刻字符串提取小时
        try:
            df['时刻_str'] = df['时刻'].astype(str)
            df['小时'] = df['时刻_str'].str[:2].astype(int)
            return True, "使用备用方法提取小时数据"
        except Exception as e2:
            return False, f"提取小时数据失败: {str(e)} | 备用方法: {str(e2)}"

def calculate_hourly_stats(df):
    """
    计算每小时统计数据
    """
    try:
        # 计算每小时平均功率
        hourly_avg = df.groupby('小时')['输出功率'].mean()
        
        # 计算其他统计信息
        hourly_max = df.groupby('小时')['输出功率'].max()
        hourly_min = df.groupby('小时')['输出功率'].min()
        hourly_std = df.groupby('小时')['输出功率'].std()
        hourly_count = df.groupby('小时')['输出功率'].count()
        
        # 创建统计汇总
        stats_df = pd.DataFrame({
            '小时': hourly_avg.index,
            '平均功率': hourly_avg.values,
            '最大功率': hourly_max.values,
            '最小功率': hourly_min.values,
            '标准差': hourly_std.values,
            '数据点数': hourly_count.values
        })
        
        return hourly_avg, stats_df, None
        
    except Exception as e:
        return None, None, f"计算统计数据时出错: {str(e)}"

def create_plotly_chart(hourly_avg):
    """
    使用Plotly创建交互式图表
    """
    try:
        # 创建主图表
        fig = go.Figure()
        
        # 添加功率曲线
        fig.add_trace(go.Scatter(
            x=hourly_avg.index,
            y=hourly_avg.values,
            mode='lines+markers',
            name='平均功率',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8, color='#A23B72', line=dict(width=2, color='white')),
            hovertemplate='<b>第%{x}小时</b><br>平均功率: %{y:.1f}<extra></extra>'
        ))
        
        # 更新布局
        fig.update_layout(
            title={
                'text': '24小时平均功率曲线',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'family': 'Arial'}
            },
            xaxis_title='小时',
            yaxis_title='平均输出功率',
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1,
                range=[-0.5, 23.5]
            ),
            hovermode='x unified',
            template='plotly_white',
            height=500
        )
        
        return fig, None
        
    except Exception as e:
        return None, f"创建图表时出错: {str(e)}"

def main():
    """
    主应用函数
    """
    # 页面标题
    st.title("⚡ 功率数据分析工具")
    st.markdown("### 基于现有数据处理逻辑的Web版本")
    st.markdown("---")

    # 侧边栏
    with st.sidebar:
        st.header("📋 使用说明")
        st.markdown("""
        ### 数据格式要求：
        - 必须包含 **时刻** 和 **输出功率** 列
        - 时刻格式：HH:MM:SS（如：12:30:00）
        - 输出功率：数值类型
        - 建议包含24小时完整数据

        ### 操作步骤：
        1. 在下方文本框粘贴CSV数据
        2. 点击"分析数据"按钮
        3. 查看分析结果和图表

        ### 数据来源：
        - 支持从Excel复制粘贴
        - 支持CSV格式文本
        - 可使用示例数据测试
        """)

        st.markdown("---")

        # 示例数据按钮
        if st.button("📝 加载示例数据", help="点击加载24小时功率数据示例"):
            st.session_state.sample_loaded = True

        # 清除数据按钮
        if st.button("🗑️ 清除所有数据", help="清除输入数据和分析结果"):
            st.session_state.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 功能特点")
        st.markdown("""
        - ✅ 实时数据验证
        - ✅ 交互式图表
        - ✅ 详细统计分析
        - ✅ 错误处理指导
        - ✅ 数据下载功能
        """)
    
    # 主内容区域
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📊 数据输入")

        # 数据格式提示
        with st.expander("💡 数据格式示例", expanded=False):
            tab1, tab2 = st.tabs(["逗号分隔 (CSV)", "制表符分隔 (Excel复制)"])

            with tab1:
                st.code("""时间,时刻,输出功率
01/01/90,00:00:00,0.0
01/01/90,01:00:00,0.0
01/01/90,02:00:00,0.0
...
01/01/90,12:00:00,4692.7
01/01/90,13:00:00,4459.5
...""", language="csv")

            with tab2:
                st.code("""时间	时刻	输出功率
01/01/90	0:00	0
01/01/90	1:00	0
01/01/90	2:00	0
...
01/01/90	12:00	4692.7
01/01/90	13:00	4459.5
...""", language="text")

            st.caption("💡 提示：支持逗号、制表符、分号等多种分隔符，可以直接从Excel表格复制粘贴数据")

        # 数据输入文本框
        default_data = ""
        if st.session_state.get('sample_loaded', False):
            default_data = get_sample_data()
            st.session_state.sample_loaded = False

        csv_data = st.text_area(
            "请粘贴CSV格式的数据（包含表头）：",
            value=default_data,
            height=300,
            help="支持从Excel复制粘贴表格数据，确保包含'时刻'和'输出功率'列",
            placeholder="时间,时刻,输出功率\n01/01/90,00:00:00,0.0\n01/01/90,01:00:00,0.0\n..."
        )
        
        # 分析按钮
        analyze_col1, analyze_col2 = st.columns([1, 1])

        with analyze_col1:
            if st.button("🔍 分析数据", type="primary", use_container_width=True):
                if csv_data.strip():
                    with st.spinner("正在分析数据..."):
                        # 解析数据
                        df, parse_error = parse_csv_data(csv_data)

                        if df is None:
                            st.error(parse_message)

                            # 提供分隔符检测帮助
                            st.markdown("### 🔍 分隔符检测帮助")

                            # 显示原始数据的前几行用于诊断
                            lines = csv_data.strip().split('\n')[:3]
                            if lines:
                                st.markdown("**您的数据前3行：**")
                                for i, line in enumerate(lines, 1):
                                    st.code(f"第{i}行: {repr(line)}")

                                # 分析可能的分隔符
                                st.markdown("**检测到的可能分隔符：**")
                                delimiters_found = []
                                for delim, name in [('\t', '制表符'), (',', '逗号'), (';', '分号'), ('|', '竖线')]:
                                    if delim in lines[0]:
                                        count = lines[0].count(delim)
                                        delimiters_found.append(f"- {name}: {count}个")

                                if delimiters_found:
                                    for delim_info in delimiters_found:
                                        st.write(delim_info)
                                else:
                                    st.write("- 未检测到常见分隔符")

                            st.markdown("### � 解决建议")
                            st.markdown("""
                            1. **从Excel复制数据时**：直接选中表格区域复制粘贴
                            2. **手动输入时**：确保使用逗号分隔各列
                            3. **检查格式**：确保每行的列数相同
                            4. **测试功能**：可以先使用示例数据测试
                            """)
                        else:
                            # 验证数据
                            errors, warnings = validate_data(df)

                            if errors:
                                st.error("❌ 数据验证失败：")
                                for error in errors:
                                    st.error(f"• {error}")

                                st.markdown("### 🔧 修正建议：")
                                st.markdown("""
                                - 确保包含 **时刻** 和 **输出功率** 列
                                - 时刻格式应为 HH:MM:SS（如：12:30:00）
                                - 输出功率应为数值类型
                                - 检查列名是否正确（区分大小写）
                                """)
                            else:
                                # 显示警告（如果有）
                                if warnings:
                                    for warning in warnings:
                                        st.warning(f"⚠️ {warning}")

                                # 存储数据到session state
                                st.session_state.df = df
                                st.session_state.data_processed = True
                                st.success("✅ 数据分析完成！")
                else:
                    st.warning("⚠️ 请先输入数据")

        with analyze_col2:
            if st.button("🧹 清除输入", use_container_width=True):
                st.session_state.clear()
                st.rerun()
    
    with col2:
        st.header("📈 数据预览")

        if csv_data.strip():
            df, parse_message = parse_csv_data(csv_data)
            if df is not None:
                # 显示解析信息
                if parse_message.startswith("✅"):
                    st.success(parse_message)
                elif parse_message.startswith("⚠️"):
                    st.warning(parse_message)

                # 数据基本信息
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("数据行数", len(df))
                with col_b:
                    st.metric("数据列数", len(df.columns))

                # 列名显示
                st.write("**列名：**")
                cols_display = st.columns(min(len(df.columns), 3))
                for i, col in enumerate(df.columns):
                    with cols_display[i % 3]:
                        st.code(col)

                # 数据预览
                st.dataframe(df.head(10), use_container_width=True)
                st.caption(f"显示前10行，共{len(df)}行数据")

                # 快速统计
                if '输出功率' in df.columns:
                    try:
                        power_col = pd.to_numeric(df['输出功率'], errors='coerce')
                        if not power_col.isna().all():
                            st.write("**功率数据快速统计：**")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("最大值", f"{power_col.max():.1f}")
                                st.metric("平均值", f"{power_col.mean():.1f}")
                            with col_b:
                                st.metric("最小值", f"{power_col.min():.1f}")
                                st.metric("非零值", f"{(power_col > 0).sum()}")
                    except:
                        pass
            else:
                st.error("数据格式错误，无法预览")
                st.markdown("**常见错误：**")
                st.markdown("- 缺少表头行")
                st.markdown("- 列分隔符不是逗号")
                st.markdown("- 包含特殊字符")
        else:
            st.info("输入数据后将显示预览")
            st.markdown("**支持的数据格式：**")
            st.markdown("- CSV格式文本")
            st.markdown("- Excel复制的表格数据")
            st.markdown("- 包含表头的数据")
    
    # 分析结果展示
    if st.session_state.get('data_processed', False) and 'df' in st.session_state:
        st.markdown("---")
        st.header("📊 分析结果")
        
        df = st.session_state.df
        
        # 提取小时数据
        success, message = extract_hour_data(df)
        
        if not success:
            st.error(f"❌ {message}")
        else:
            if message:
                st.info(f"ℹ️ {message}")
            
            # 计算统计数据
            hourly_avg, stats_df, calc_error = calculate_hourly_stats(df)
            
            if calc_error:
                st.error(f"❌ {calc_error}")
            else:
                # 显示图表
                fig, chart_error = create_plotly_chart(hourly_avg)
                
                if chart_error:
                    st.error(f"❌ {chart_error}")
                else:
                    st.plotly_chart(fig, use_container_width=True)
                
                # 显示关键统计信息
                st.subheader("📊 关键指标")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "最大平均功率",
                        f"{hourly_avg.max():.1f}",
                        f"第{hourly_avg.idxmax()}小时"
                    )

                with col2:
                    st.metric(
                        "总平均功率",
                        f"{hourly_avg.mean():.1f}"
                    )

                with col3:
                    st.metric(
                        "功率标准差",
                        f"{hourly_avg.std():.1f}"
                    )

                with col4:
                    # 计算有效发电小时数
                    active_hours = (hourly_avg > 0).sum()
                    st.metric(
                        "有效发电小时",
                        f"{active_hours}小时"
                    )

                # 功率分布分析
                st.subheader("🔍 功率分布分析")

                # 创建功率等级分析
                power_ranges = {
                    "无功率输出 (0)": (hourly_avg == 0).sum(),
                    "低功率 (0-1000)": ((hourly_avg > 0) & (hourly_avg <= 1000)).sum(),
                    "中功率 (1000-3000)": ((hourly_avg > 1000) & (hourly_avg <= 3000)).sum(),
                    "高功率 (>3000)": (hourly_avg > 3000).sum()
                }

                range_col1, range_col2 = st.columns(2)
                with range_col1:
                    for range_name, count in power_ranges.items():
                        st.write(f"**{range_name}**: {count} 小时")

                with range_col2:
                    # 峰值时段分析
                    peak_hours = hourly_avg[hourly_avg > hourly_avg.mean()].index.tolist()
                    if peak_hours:
                        st.write(f"**峰值时段**: {min(peak_hours)}-{max(peak_hours)}小时")
                        st.write(f"**峰值持续**: {len(peak_hours)} 小时")

                    # 发电效率
                    total_possible = 24 * hourly_avg.max()
                    actual_total = hourly_avg.sum()
                    efficiency = (actual_total / total_possible * 100) if total_possible > 0 else 0
                    st.write(f"**发电效率**: {efficiency:.1f}%")
                
                # 详细统计表格
                st.subheader("📋 详细统计数据")
                st.dataframe(stats_df, use_container_width=True)
                
                # 下载按钮
                csv_download = stats_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载统计数据 (CSV)",
                    data=csv_download,
                    file_name=f"功率统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
