import requests
import json

class DeepseekLLM:
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        temperature: float = 0.1,
        max_tokens: int = 4096
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.last_prompt = None

    def call(self, instruction: str, context: str = None, **kwargs) -> str:
        """
        调用 Deepseek 模型的 API 以获取响应
        """
        instruction_str = str(instruction)
        self.last_prompt = instruction_str
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": instruction_str}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        response = requests.post(self.base_url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    @property
    def type(self) -> str:
        return "deepseek-chat"


def file_uploader():
    import streamlit as st
    uploaded_file = st.sidebar.file_uploader(
        "上传Excel文件", 
        type=['xlsx', 'xls'],
        help="请上传重庆超充站电量统计表Excel文件"
    )
    if uploaded_file is not None:
        return uploaded_file
    return None


def load_data(uploaded_file):
    import pandas as pd
    if uploaded_file is None:
        return pd.DataFrame()
    
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheets = xls.sheet_names[2:]
    except Exception as e:
        import streamlit as st
        st.error(f"读取Excel文件失败: {str(e)}")
        return pd.DataFrame()
    dfs = []
    for sheet in sheets:
        df = pd.read_excel(xls, sheet_name=sheet)
        df['站点'] = sheet
        dfs.append(df)
    result = pd.concat(dfs, ignore_index=True)
    result['日期'] = pd.to_datetime(result['日期'], unit='D', origin='1899-12-30')
    return result
