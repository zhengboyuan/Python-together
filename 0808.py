# -*- coding: utf-8 -*-
"""
Spyder 编辑器

这是一个临时脚本文件。
"""

import streamlit as st
import pandas as pd
import numpy as np
def layout():
    """"
    布局函数
    """
    with st.form("my_form"):
        st.write("查询条件")
        # 使用st.select_slider创建滑动选择器
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        # 在第一列放置滑动选择器
        with col1:
            x = st.number_input(
                "输入x值",  # 数字输入框的标签
                min_value=1,     # 最小值
                max_value=10,    # 最大值
                value=5          # 默认值
            )
        
        # 在第二列放置数字输入框
        with col2:
            y = st.number_input(
                "输入y值",  # 数字输入框的标签
                min_value=1,     # 最小值
                max_value=10,    # 最大值
                value=5          # 默认值
            )
        
    # Every form must have a submit button.
        submitted = st.form_submit_button("查询")
    col3, col4 = st.columns(2)
    with col3:
        agree1 = st.checkbox("是否配有储能")
        if agree1:
            st.checkbox("z")
    with col4:
        agree2 = st.selectbox('是否有光伏',['是','否'],index = 1)
        if agree2:
            st.write("Great!y")
    return x,y
def data_plot(x,y):
    chart_data = pd.DataFrame(
    {
        "x": np.random.randint(0, 101, x),
        "y": np.random.randint(0, 101, y),
    }
)
    st.dataframe(chart_data.T)
    st.line_chart(chart_data, x="x", y="y")
def main():
    x,y = layout()
    data_plot(x,y)
if __name__ == "__main__":
    main()
