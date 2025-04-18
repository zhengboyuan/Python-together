import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st

def generate_pdf_report(text_content: str, filename: str = "智能分析报告.pdf"):
    """
    生成PDF报告并提供下载按钮
    
    参数:
        text_content: 要转换为PDF的文本内容
        filename: 下载的文件名(默认为"智能分析报告.pdf")
        
    返回:
        Streamlit下载按钮组件
    """
    try:
        # 注册中文字体
        try:
            pdfmetrics.registerFont(TTFont('SimHei', '/System/Library/Fonts/STHeiti Medium.ttc'))
            styles = getSampleStyleSheet()
            styles["Normal"].fontName = "SimHei"
        except:
            styles = getSampleStyleSheet()
        
        # 创建PDF缓冲区
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        
        # 将文本内容转换为PDF段落
        story = []
        for line in text_content.split('\n'):
            if line.strip():
                p = Paragraph(line, styles["Normal"])
                story.append(p)
        
        # 构建PDF文档
        doc.build(story)
        pdf_buffer.seek(0)
        
        # 返回下载按钮
        return st.download_button(
            label="下载PDF报告",
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf"
        )
        
    except ImportError:
        st.error("生成PDF需要安装reportlab库，请运行: pip install reportlab")
        return None
    except Exception as e:
        st.error(f"生成PDF报告失败: {str(e)}")
        return None
