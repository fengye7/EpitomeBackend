# from pptx import Presentation
import os
import json
from typing import List, Dict
import subprocess
import shutil
import base64
from openai import OpenAI
import traceback

# 设置环境变量
# os.environ.setdefault("DASHSCOPE_API_KEY", "sk-ba6a5c10094b440e91aa5d3bd412888e")  # 请替换为您的API Key

def create_client():
    """Create and return an OpenAI client."""
    # api_key = "4263a967-94a2-48ef-b324-baf8787d5de0"  # 请替换为您的API Key
    # base_url = "https://ark.cn-beijing.volces.com/api/v3"
    # return OpenAI(api_key=api_key, base_url=base_url)
    
    api_key = "sk-EvVIm6CzSFCbM4OxX961OoXjssK0riwfAiODVPJxSVr19cxf"  # 请替换为您的API Key
    base_url = "https://api.pandalla.ai/v1"
    return OpenAI(api_key=api_key, base_url=base_url)
    
def save_slide_as_image(presentation_path: str, output_dir: str) -> Dict[int, str]:
    """Save each slide as an image and return a dictionary mapping slide numbers to image paths."""
    # 创建images子目录
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # 复制PPT文件到输出目录
    temp_pptx = os.path.join(images_dir, "temp_presentation.pptx")
    shutil.copy2(presentation_path, temp_pptx)
    
    print(f"\n开始转换PPT到图片...")
    print(f"输出目录: {output_dir}")
    print(f"图片目录: {images_dir}")
    
    # 使用soffice (LibreOffice)将PPT转换为PDF
    try:
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', images_dir, temp_pptx], 
                      check=True, capture_output=True)
        print("PPT成功转换为PDF")
    except subprocess.CalledProcessError as e:
        print(f"转换PPT到PDF时出错: {e}")
        return {}
    
    pdf_path = os.path.join(images_dir, "temp_presentation.pdf")
    
    # 使用pdftoppm将PDF转换为图片，修改输出格式
    try:
        subprocess.run(['pdftoppm', '-png', pdf_path, os.path.join(images_dir, 'slide')], 
                      check=True, capture_output=True)
        print("PDF成功转换为图片")
    except subprocess.CalledProcessError as e:
        print(f"转换PDF到图片时出错: {e}")
        return {}
    
    # 清理临时文件
    os.remove(temp_pptx)
    os.remove(pdf_path)
    
    # 获取所有生成的图片文件并重命名
    slide_image_paths = {}
    prs = Presentation(presentation_path)
    total_slides = len(prs.slides)
    
    # 获取output目录的基础名称（用于构建相对路径）
    base_output_dir = os.path.basename(output_dir)
    
    for idx in range(1, total_slides + 1):
        # pdftoppm生成的文件格式为slide-000001.png, slide-000002.png等
        old_image_name = f"slide-{idx:06d}.png"
        new_image_name = f"slide-{idx}.png"
        old_image_path = os.path.join(images_dir, old_image_name)
        new_image_path = os.path.join(images_dir, new_image_name)
        
        # 重命名文件
        if os.path.exists(old_image_path):
            os.rename(old_image_path, new_image_path)
            # 构建相对路径
            relative_path = os.path.join(base_output_dir, "images", new_image_name)
            slide_image_paths[idx] = relative_path
            print(f"已保存第 {idx} 页幻灯片的图片: {relative_path}")
        else:
            print(f"警告：未找到第 {idx} 页的图片文件: {old_image_path}")
    
    return slide_image_paths

def extract_text_from_shape(shape):
    """Extract text from a shape in the slide."""
    if hasattr(shape, "text"):
        return shape.text.strip()
    return ""

def extract_slide_content(slide):
    """Extract all text content from a slide."""
    text_content = []
    
    # Extract text from shapes
    for shape in slide.shapes:
        text = extract_text_from_shape(shape)
        if text:
            text_content.append(text)
    
    return "\n".join(text_content)

def encode_image_to_base64(image_path: str) -> str:
    """Convert image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

import json
import re

def generate_teaching_script(
    client: OpenAI,
    current_slide: Dict,
    previous_scripts: List[str]
) -> Dict:
    """Generate teaching script for a slide."""
    slide_number = current_slide["slide_number"]
    slide_content = current_slide["content"]
    
    prompt = f"""你是一位省立医院的院长，正在准备一堂医疗培训课的讲稿。
请根据幻灯片内容，生成简短的讲稿。讲稿应该包含以下内容：
1. 对幻灯片内容的简单讲解。
2. 不要生成任何问题，以及问号结尾的内容。
3. 讲稿应该口语化。

幻灯片内容：
{slide_content}

请生成教学讲稿，每条讲稿应该是一个完整的段落或教学点。
将讲稿格式化为以下JSON格式：
{{
  "teaching_scripts": [
    "第一条讲稿内容",
    "第二条讲稿内容",
    "第三条讲稿内容",
    ...
  ]
}}

请确保讲稿内容连贯、专业，并能够有效地传达幻灯片的核心内容。
"""

    if previous_scripts:
        prompt += f"\n\n前一页的讲稿内容：\n{previous_scripts[-1]}\n\n请确保新的讲稿与前一页的内容保持连贯性。"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位省立医院的院长，擅长编写医疗培训课的讲稿。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )

        teaching_script_str = response.choices[0].message.content.strip()

        # 移除 Markdown 代码块包裹
        teaching_script_str = re.sub(r'^```(?:json)?\n?', '', teaching_script_str)
        teaching_script_str = re.sub(r'\n?```$', '', teaching_script_str)

        # 转换成 Python 字典
        teaching_script_json = json.loads(teaching_script_str)
        return teaching_script_json

    except Exception as e:
        print(f"生成讲稿时出错: {e}")
        return {}


def extract_ppt_content(ppt_path, output_dir, client: OpenAI):
    """Extract content from a PowerPoint presentation."""
    try:
        # Load the presentation
        prs = Presentation(ppt_path)
        
        # Get the base name of the PPT file without extension
        ppt_name = os.path.splitext(os.path.basename(ppt_path))[0]
        
        # Create output directory
        ppt_output_dir = os.path.join(output_dir, ppt_name)
        os.makedirs(ppt_output_dir, exist_ok=True)
        
        # Save slides as images
        slide_image_paths = save_slide_as_image(ppt_path, ppt_output_dir)
        
        # Extract content from each slide
        slides_content = []
        previous_scripts = []
        
        for i, slide in enumerate(prs.slides, 1):
            print(f"\n处理第 {i} 页幻灯片...")
            
            # Extract text content
            content = extract_slide_content(slide)
            
            # Create slide data structure
            slide_data = {
                "slide_number": i,
                "content": content,
                "image_path": slide_image_paths.get(i, "")
            }
            
            # Generate teaching script
            teaching_script = generate_teaching_script(client, slide_data, previous_scripts, ppt_output_dir)
            
            # Update slide data with teaching script
            slide_data["teaching_script"] = teaching_script
            
            # Add to slides content
            slides_content.append(slide_data)
            
            # Update previous scripts for context
            if teaching_script:
                previous_scripts.append(teaching_script[0])
        
        # Save all slides content
        output_dir = save_slides_content(slides_content, ppt_name)
        
        return output_dir
    
    except Exception as e:
        print(f"处理PPT时出错: {e}")
        traceback.print_exc()
        return None

def save_slides_content(slides_content, ppt_name):
    """Save each slide's content to a separate file."""
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", ppt_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create content directory for text files
    content_dir = os.path.join(output_dir, "content")
    os.makedirs(content_dir, exist_ok=True)
    
    # Prepare the final JSON structure
    final_slides_content = []
    
    # First pass: Save content and teaching scripts
    for slide in slides_content:
        slide_number = slide["slide_number"]
        content = slide["content"]
        teaching_script = slide.get("teaching_script", [])
        
        # Create initial slide data structure
        slide_data = {
            "slide_number": slide_number,
            "content": content,
            "teaching_script": teaching_script,
            "image_path": ""
        }
        
        final_slides_content.append(slide_data)
        
        # Save as text file in content directory
        text_file_path = os.path.join(content_dir, f"slide_{slide_number}.txt")
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(f"原始内容：\n{content}\n\n")
            f.write(f"讲稿：\n{json.dumps(teaching_script, ensure_ascii=False, indent=2)}\n")
    
    # Second pass: Update image paths by checking all possible image formats
    images_dir = os.path.join(output_dir, "images")
    if os.path.exists(images_dir):
        print("\n开始查找并添加图片路径...")
        
        # 获取images目录下的所有文件
        image_files = os.listdir(images_dir)
        
        # 遍历所有幻灯片数据
        for slide_data in final_slides_content:
            slide_num = slide_data["slide_number"]
            
            # 尝试多种可能的文件名格式
            possible_filenames = [
                f"slide-{slide_num}.png",           # 新格式: slide-1.png
                f"slide-{slide_num:06d}.png",       # 旧格式: slide-000001.png
                f"slide{slide_num}.png",            # 可能的格式: slide1.png
                f"slide_{slide_num}.png",           # 可能的格式: slide_1.png
                f"{slide_num}.png"                  # 可能的格式: 1.png
            ]
            
            # 检查每种可能的文件名
            found_image = False
            for filename in possible_filenames:
                if filename in image_files:
                    # 使用绝对路径
                    absolute_path = os.path.join("/home/ubuntu/project/AutomaticTeach/output", ppt_name, "images", filename)
                    slide_data["image_path"] = absolute_path
                    print(f"找到第 {slide_num} 页的图片: {absolute_path}")
                    found_image = True
                    break
            
            if not found_image:
                print(f"警告：未找到第 {slide_num} 页的图片文件")
    
    # Save final JSON with updated image paths
    json_file_path = os.path.join(output_dir, "all_slides.json")
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(final_slides_content, f, ensure_ascii=False, indent=4)
    
    print(f"\n保存完成！")
    print(f"JSON文件路径: {json_file_path}")
    print("\n图片路径示例:")
    for slide in final_slides_content:
        if slide.get("image_path"):
            print(f"第 {slide['slide_number']} 页: {slide['image_path']}")
    
    return output_dir

def main():
    ppt_path = "/home/ubuntu/project/AutomaticTeach/data/ppt/全国幽门螺杆菌感染处理共识报告非根除治疗部分（一）.pptx"
    
    try:
        # 初始化OpenAI客户端
        client = create_client()
        
        # 创建输出目录
        ppt_name = os.path.splitext(os.path.basename(ppt_path))[0]
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        
        # 提取PPT内容并生成讲稿
        print("\n开始提取PPT内容和生成讲稿...")
        result_dir = extract_ppt_content(ppt_path, output_dir, client)
        
        if result_dir:
            print(f"\n处理完成！内容已保存到: {result_dir}")
            
            # 读取生成的JSON文件来获取幻灯片数量
            json_file_path = os.path.join(result_dir, "all_slides.json")
            if os.path.exists(json_file_path):
                with open(json_file_path, "r", encoding="utf-8") as f:
                    slides_data = json.load(f)
                    slide_count = len(slides_data)
                    
                    print(f"总共处理页数: {slide_count}")
                    print("\n创建的文件:")
                    print(f"- JSON文件: {json_file_path}")
                    print(f"- 各页面文本文件: content/slide_1.txt 到 content/slide_{slide_count}.txt")
                    print(f"- 幻灯片图片: images/slide-1.png 到 images/slide-{slide_count}.png")
        else:
            print("\n处理失败！请检查错误信息。")
            
    except Exception as e:
        print(f"主程序执行出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
