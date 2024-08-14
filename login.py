import streamlit as st

# 定义实际凭据
actual_email = "zcdl"
actual_password = "zcdl"

# 初始化会话状态变量
if 'oklogin' not in st.session_state:
    st.session_state.oklogin = False
def login_cb(form_email, form_password):
    """表单提交时更新登录状态"""
    # 比较输入的凭据与实际凭据是否匹配
    if form_email == actual_email and form_password == actual_password:
        st.session_state.oklogin = True  # 更新登录状态为True
        st.session_state.username = form_email  # 保存用户名
        placeholder.empty()  # 清空表单容器
        st.session_state.sync()  # 同步session状态
    else:
        st.error("无效的用户名或密码。请重试。")  # 显示错误消息
# 检查用户是否已经登录
if not st.session_state.oklogin:
    # 显示登录页面
    st.header('泰能虚拟电厂测算登录页')

    # 创建一个空的容器用于存放表单
    placeholder = st.empty()

    

    # 在容器中插入表单
    with placeholder.form("泰能虚拟电厂测算登录页"):
        email = st.text_input("账号")  # 输入账号
        password = st.text_input("密码", type="password")  # 输入密码
        st.markdown("有问题请联系管理员")  # 显示联系管理员的信息
        submit = st.form_submit_button("登录", on_click=login_cb, args=(email, password))  # 提交按钮

# 如果用户已经登录
elif st.session_state.oklogin:
    # 显示成功消息和链接
    st.success("登录成功！")
    st.write(f"欢迎, {st.session_state.username}!")
    st.page_link("https://vppinvestmentv2.streamlit.app/", label="虚拟电厂投资测算", icon="🏠")
    st.page_link("https://vppinvestmentv2.streamlit.app/%E5%82%A8%E8%83%BD%E8%A7%84%E6%A8%A1%E6%B5%8B%E7%AE%97V1", label="储能规模测算", icon="🏠")
    st.page_link("https://vppinvestmentv2.streamlit.app/%E6%9F%A5%E8%AF%A2%E6%95%B0%E6%8D%AE%E6%8E%A5%E5%8F%A3V1", label="查询数据接口V1", icon="🏠")
