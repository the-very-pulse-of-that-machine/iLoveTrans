import requests

def translate_text(query,port, source_lang='en', target_lang='zh'):
    try:
        # 调用本地 API 进行翻译
        response = requests.post("http://127.0.0.1:"+str(port)+"/translate", 
                                 json={"q": query, "source": source_lang, "target": target_lang})
        result = response.json()

        # 检查是否有翻译结果
        if 'translatedText' in result:
            return result['translatedText']
        elif 'error' in result:
            print(f"Translation error: {result['error']}")
            return None
        else:
            print(f"Unexpected response structure: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def translate_extracted_text(extracted_text, port, source_lang='en', target_lang='zh'):
    extracted_text = extracted_text.replace("- ", "")
    sentences = extracted_text.split('.')
    
    # 存储翻译结果与原文对应
    translations = {}
    current_translation = []
    current_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:  # 确保句子不为空
            if current_length + len(sentence) + 1 <= 1000:
                current_translation.append(sentence)
                current_length += len(sentence) + 1
            else:
                # 翻译已收集的句子
                translated_sentence = translate_text(' '.join(current_translation).strip(),port, source_lang, target_lang)
                translations[' '.join(current_translation).strip()] = translated_sentence

                # 重置当前翻译
                current_translation = [sentence]
                current_length = len(sentence) + 1

    # 处理最后一段句子
    if current_translation:
        translated_sentence = translate_text(' '.join(current_translation).strip(),port, source_lang, target_lang)
        translations[' '.join(current_translation).strip()] = translated_sentence

    return translations
