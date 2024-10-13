import PyPDF2
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTImage
import re  # 导入正则表达式库
import jieba
import transapi

def text_extraction(element):
    """提取文本并返回文本及其字体信息"""
    line_text = element.get_text()
    line_formats = []
    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            for character in text_line:
                if isinstance(character, LTChar):
                    line_formats.append(character.fontname)
                    line_formats.append(character.size)
    format_per_line = list(set(line_formats))
    return (line_text, format_per_line)

def process_two_column_pdf(pdf_path):
    """处理带有两栏文本的 PDF"""
    pdfFileObj = open(pdf_path, 'rb')
    pdfReaded = PyPDF2.PdfReader(pdfFileObj)
    paragraphs = []
    for pagenum, page in enumerate(extract_pages(pdf_path)):
        pageObj = pdfReaded.pages[pagenum]
        column_text = []
        
        page_height = pageObj.mediabox.upper_right[1]
        header_footer_height = 50  
        for element in page:
            if isinstance(element, LTTextContainer):
                line_text, x0, x1 = element.get_text(), element.x0, element.x1
                
                if element.y0 > (page_height - header_footer_height) or element.y1 < header_footer_height:
                    continue  
                processed_text = process_text(line_text)

                column_width = pageObj.mediabox.upper_right[0] / 2
                if (x0 < column_width + 50) and (x1 > column_width - 50): 
                    column_text.append(processed_text.strip())
                else:
                    column_text.append(processed_text.strip())

            elif isinstance(element, LTImage):  
                image_filename = crop_image(element, pageObj) 
                column_text.append(f"[Image: {image_filename}]")  

        page_text = '\n'.join(column_text)
        paragraphs.append((pagenum + 1, page_text.split('\n\n')))  # 记录页码和对应的文本

    pdfFileObj.close()
    return paragraphs 

def process_text(line_text):
    """处理文本，去除段落内的换行符"""
    lines = line_text.split("\n")
    processed_text = " ".join(line.strip() for line in lines if line.strip())  # 使用空格连接有效行
    return processed_text

def remove_unwanted_characters(text):
    """删除乱码、特殊符号和无意义的内容"""
    # 匹配并删除所有非中文、数字、字母和常用标点符号的字符
    cleaned_text = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9，。！？；：（）【】《》“”‘’—……、,.!?;:()\[\]<>\"\'—…\n\t]', '', text)
    
    # 删除多余的空白和换行
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 将多个空白合并为一个空格
    cleaned_text = cleaned_text.strip()  # 去掉首尾空白

    return cleaned_text


def remove_consecutive_repeats(text):
    """使用jieba分词并去掉连续重复的词"""
    # 使用jieba进行分词
    words = list(jieba.cut(text))
    
    # 去除连续重复的词
    filtered_words = []
    for word in words:
        # 只保留不重复的词
        if not filtered_words or filtered_words[-1] != word:
            filtered_words.append(word)
    
    return ''.join(filtered_words)

def extract_and_translate_pdf(pdf_path):
    """提取 PDF 文本并进行翻译，返回中英文对应及其页码"""
    extracted_paragraphs = process_two_column_pdf(pdf_path)
    return extracted_paragraphs


