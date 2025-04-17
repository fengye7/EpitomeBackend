import json
import os
import time
import requests
from openai import OpenAI

def create_client():
    """Create and return an OpenAI client."""
    api_key = "4263a967-94a2-48ef-b324-baf8787d5de0"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    return OpenAI(api_key=api_key, base_url=base_url)

def load_teaching_scripts(json_path):
    """Load teaching scripts from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def parse_teaching_script(script_json_str):
    """Parse the teaching script JSON string into a list of sentences."""
    try:
        # Handle case where script_json_str is a list
        if isinstance(script_json_str, list):
            # Join all elements if there are multiple JSON strings
            script_json_str = script_json_str[0] if len(script_json_str) > 0 else ""
        
        # Remove ```json and ``` if present
        clean_json = script_json_str.strip()
        if clean_json.startswith('```json'):
            clean_json = clean_json[7:]
        if clean_json.endswith('```'):
            clean_json = clean_json[:-3]
        
        script_dict = json.loads(clean_json)
        # Extract all teaching script lines in order
        scripts = []
        i = 1
        while f"teaching_script_{i}" in script_dict:
            scripts.append(script_dict[f"teaching_script_{i}"])
            i += 1
        return scripts
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []
    except AttributeError as e:
        print(f"Error processing teaching script: {e}")
        return []

def get_ai_response(client, context, user_input, is_continuation_check=False, interaction_count=1):
    """Get AI response based on the context and user input."""
    if is_continuation_check:
        # 直接返回"下一话题"，不管回答是否正确
        return "下一话题"
    else:
        # 使用Dify API而不是OpenAI
        url = 'https://api.dify.ai/v1/chat-messages'
        headers = {
            'Authorization': 'Bearer app-vozmPVajHi4CGqH6YNjvroxb',
            'Content-Type': 'application/json',
        }
        
        # 构建提示信息
        prompt = f"""你是一个专业的教师，正在给学生上课。
请根据学生的回答进行点评。

当前讲课内容：{context}

学生回答：{user_input}

如果学生回答正确：
1. 给予肯定和表扬
2. 进入下一个话题


如果学生回答错误：
1. 以鼓励的语气指出错误
2. 进入下一个话题

回答要简洁。"""
        
        data = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",  # 使用blocking模式获取完整回复
            "user": f"student-{interaction_count}"
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()
        
        # 从响应中提取回复内容
        if 'answer' in response_data:
            return response_data['answer']
        else:
            return "对不起，我现在无法评价你的回答。让我们继续下一个话题。"

def is_question(text, client=None):
    """判断文本是否是需要学生回答的问句
    
    仅根据是否包含问号和排除规则来判断，不再调用LLM
    
    Args:
        text: 要判断的文本
        client: OpenAI client实例，此参数已不再使用，保留是为了兼容性
    
    Returns:
        bool: True表示需要学生回答，False表示不需要回答
    """
    # 检查句子中是否包含问号
    has_question_mark = '？' in text or '?' in text
    
    # 如果没有问号，直接返回False
    if not has_question_mark:
        return False
    
    # # 定义明确不需要回答的关键词
    # non_interactive_keywords = [
    #     '有没有听说过', '大家知道', '相信大家都', 
    #     '我们都知道', '想必大家', '不是吗',
    #     '对不对', '是不是', '难道不'
    # ]
    
    # # 如果包含明确不需要回答的关键词，返回False
    # if any(keyword in text for keyword in non_interactive_keywords):
    #     return False
        
    return True

def interactive_teaching():
    """Main function for interactive teaching."""
    # Initialize OpenAI client
    client = create_client()
    
    # Load teaching scripts
    json_path = "/home/ubuntu/project/AutomaticTeach/output/诊断部分_test/all_slides.json"
    slides_data = load_teaching_scripts(json_path)
    
    print("欢迎来到交互式课堂！")
    print("遇到老师提问时需要回答，其他时候系统会自动继续。")
    print("输入 'q' 退出，输入 'n' 进入下一页。")
    print("系统会根据你的回答情况，自然地引导讨论进程。")
    print("\n" + "="*50 + "\n")
    
    current_context = ""
    
    for slide in slides_data:
        print(f"\n第 {slide['slide_number']} 页PPT")
        print(f"内容：{slide['content']}\n")
        
        # Parse teaching scripts for this slide
        teaching_scripts = parse_teaching_script(slide['teaching_script'])
        
        i = 0
        while i < len(teaching_scripts):
            script = teaching_scripts[i]
            current_context = script
            print("\n老师：" + script)
            
            # 如果是问句，等待用户输入
            if is_question(script, client):
                user_input = input("\n请输入你的回答（或按q退出，n下一页）: ").strip()
                
                if not user_input or user_input.lower() == '':
                    pass  # 如果没有输入，直接继续
                elif user_input.lower() == 'q':
                    print("\n课程结束！感谢参与！")
                    return
                elif user_input.lower() == 'n':
                    continue  # 跳到下一个循环
                else:
                    # 获取AI对学生回答的评价
                    response = get_ai_response(client, current_context, user_input, False)
                    print("\n老师：" + response)
                    
                    # 不再询问是否继续讨论，简短暂停后继续
                    time.sleep(1)
                
                if user_input.lower() == 'n':
                    break
            else:
                # 如果不是问句，暂停一下让用户阅读，然后自动继续
                time.sleep(2)
            
            i += 1
            
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    interactive_teaching()