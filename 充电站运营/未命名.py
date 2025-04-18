# usage_example.py
import pandas as pd
from pandasai import SmartDataframe # 或者 SmartDatalake, 或旧版本的 PandasAI
from deepseek_llm import DeepseekLLM # 从你创建的文件中导入
from dotenv import load_dotenv
import os

load_dotenv()

# --- 1. 准备你的数据 ---
# data = {
#     'Country': ['USA', 'Canada', 'Mexico', 'USA', 'Canada'],
#     'Sales': [1500, 1200, 800, 1600, 1300],
#     'Date': pd.to_datetime(['2023-01-15', '2023-01-15', '2023-01-16', '2023-01-17', '2023-01-18'])
# }
df= pd.read_csv("data.csv")
df = pd.DataFrame(df)

# --- 2. 初始化自定义的 Deepseek LLM ---
# 从环境变量获取API密钥
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("请在.env文件中设置DEEPSEEK_API_KEY环境变量")

deepseek_llm_instance = DeepseekLLM(
    api_key=api_key,  # 从环境变量获取
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=500
)

# --- 3. 初始化 PandasAI (或 SmartDataframe/SmartDatalake) ---
# 将自定义的 LLM 实例传递给 PandasAI
# 注意：根据你的 PandasAI 版本，可能是 PandasAI(), SmartDataframe(), 或 SmartDatalake()
# 对于较新版本 (>=2.0)，推荐使用 SmartDataframe 或 SmartDatalake
sdf = SmartDataframe(df, config={
    "llm": deepseek_llm_instance,
    "enable_cache": False,
    "plot_config": {
        "use_restricted_matplotlib": False,
        "use_plotly": False,
        "use_text_based_visualizations": True
    }
})

# --- 4. 与你的数据进行交互 ---
print("数据问答系统已启动，输入您的问题或输入'退出'结束")
while True:
    try:
        question = input("\n请输入您的问题: ")
        if question.lower() in ['退出', 'exit']:
            print("感谢使用，再见！")
            break
            
        response = sdf.chat(question)
        print(f"\n问题：{question}")
        print(f"回答：{response}")
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        print("最后发送的 Prompt:", deepseek_llm_instance.last_prompt) # 调试用
        continue
