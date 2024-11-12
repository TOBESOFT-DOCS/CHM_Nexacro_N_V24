import requests
import json
import random
import time
import os
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

start_time = time.time()

# URL에서 HTML 가져오기
url_github = 'https://raw.githubusercontent.com/TOBESOFT-DOCS/CHM_Nexacro_N_V24/refs/heads/main/images/'
file_path = r'D:\chm\24.0.0.400\KOR'

# keyword 가져오기
url_keyword = "https://raw.githubusercontent.com/TOBESOFT-DOCS/sample_Nexacro_N_V24/master/FileSample/file_sample_list.xml"


commcon_path = None
bFile = True

if bFile:
    commcon_path = file_path
else:
    commcon_path = url_github

# XML 데이터 가져오기
def fetch_xml_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to fetch data from {url}, status code: {response.status_code}")

xml_keyword = fetch_xml_data(url_keyword)

# XML 데이터에서 지정된 키워드 가져오기
def find_matching_rows(xml_data, object_name, item_name):
    ns = {'ns': 'http://www.nexacroplatform.com/platform/dataset'}

    root = ET.fromstring(xml_data)
    rows = root.findall(".//ns:Row", namespaces=ns)

    result_lines = []

    target_keywords = [
        f"{object_name}.{item_name}",
        f"Component.{item_name}"
    ]

    for row in rows:
        keyword = row.find(".//ns:Col[@id='keyword']", namespaces=ns)
        subject = row.find(".//ns:Col[@id='subject']", namespaces=ns)
        id_sample = row.find(".//ns:Col[@id='id_sample']", namespaces=ns)

        if subject is not None and id_sample is not None:
            subject_value = subject.text
            id_sample_value = id_sample.text

            if keyword is None or keyword.text is None:
                continue

            keyword_values = [kw.strip() for kw in keyword.text.split(',')]

            if any(target_keyword in keyword_values for target_keyword in target_keywords):
                result_lines.append(f"* <a class='link' href='/developer_guide_nexacro_n_v24_ko/{id_sample_value}'>{subject_value}</a>")
    
    return "\n".join(result_lines)

# (공통 함수) SOUP 처리하기
def get_soup(module_name, module_cagegory, item_type=None, item_name=None):
    if item_type:
        target_object = os.path.join(commcon_path, f"{module_cagegory}{module_name}_{item_type}_{item_name}.html")
    else:
        target_object = os.path.join(commcon_path, f"{module_cagegory}{module_name}.html")

    if not os.path.exists(target_object):
        return None

    if bFile:
        with open(target_object, 'r', encoding='utf-8') as file:
            return_soup = BeautifulSoup(file, 'html.parser')
            return return_soup
    else:
        response = requests.get(target_object)
        html = response.text
        return_soup = BeautifulSoup(html, 'html.parser')
        return return_soup
    

# (공통 함수) 설명 텍스트 가져오기 
# Object > Description
# Object > Remark
def get_desc_text(soup, title, item=None, remark=None):
    desc_title_td = soup.find('td', class_='sub_title', string=title)
    if not desc_title_td:
        print(f"{title}을 포함한 요소를 찾을 수 없습니다. 참고 {item}")
        raise ValueError(f"{title}을 포함한 요소를 찾을 수 없습니다. 참고 {item}")
    
    table_tag = None  
    desc_content_td = desc_title_td.find_next('td', class_='list')
    if desc_content_td and desc_content_td.pre:
        table_tag = desc_content_td.find('table')
        if table_tag:
            table_tag.extract()
        desc_text = desc_content_td.pre.get_text().strip()
        desc_text = get_html_text(desc_text)
    else:
        print(f"{title} 본문 텍스트를 포함한 요소를 찾을 수 없습니다. 참고 {item}")
    
    if remark:
        return desc_text, table_tag
    else:
        return desc_text

# (공통 함수) 제목, 표 형식 가져오기 
# Object > Contents Sizing
# Object > Basic Key Action
# Object > Accessibility Key Action
# Object > Constructor
# Property > Setting Syntax
# Method > Parameters
# Method > Return
def get_table_content(soup, title, layout, bTitle=None, item=None, constructor_except=None, bEvent=None):
    content_title_td = soup.find('td', class_='sub_title', string=title)
    if not content_title_td:
        print(f"{title}을 포함한 요소를 찾을 수 없습니다. 참고 {item}")
        raise ValueError(f"{title}을 포함한 요소를 찾을 수 없습니다. 참고 {item}")

    if title=="Constructor":
        content_tds = content_title_td.find_next('td', class_='list').find_all_next('td', class_='list')
    else:
        content_tds = content_title_td.find_all_next('td', class_='list')

    for index, content_td in enumerate(content_tds):
        if (content_td.find_previous('td', class_='sub_title').get_text() != title):
            break
        
        # {title} 설명 텍스트만 있는 경우
        if content_td and content_td.find_next().name=='pre':
            if title=="Constructor":
                content_type = "command"
            else:
                content_type = "pre"
            add_element("u_09_"+str(random.random()), content_type, content_td.pre.get_text().strip())
        # {title} 샘플만 있는 경우
        # 속성 Parameters 항목 중 bringToFront() 처럼 값이 없지만 샘플 설명이 있는 경우
        elif content_td and content_td.find_next().name == 'br':
            add_element("u_09_"+str(random.random()), "command", content_td.find_next().find_next().get_text().strip())
        # {title} 관련 표가 있는 경우 
        elif content_td and content_td.find_next().name=='table':
            
            # 속성 제거
            for tag in content_td.find_all():
                attrs_to_remove = [attr for attr in tag.attrs if attr != 'colspan']
                for attr in attrs_to_remove:
                    del tag[attr]

            table_tag = content_td.find('table')  

            # colgroup 태그 삭제
            for colgroup in table_tag.find_all('colgroup'):
                colgroup.decompose()

            # a 태그 삭제(a 태그 내 텍스트는 유지)
            for td_tag in content_td.find_all('td'):
                a_tag = td_tag.find('a')
                if a_tag:
                    a_text = a_tag.get_text()
                    td_tag.string = a_text

            bTitleSkip = True

            if bTitle:
                if not (title == 'Constructor' and constructor_except):
                    thead_tag = soup.new_tag('thead')
                    first_tr_tag = table_tag.find('tr')
                    first_tr_tag.wrap(thead_tag)

                    for td_tag in first_tr_tag.find_all('td'):
                        th_tag = soup.new_tag('th')
                        th_tag.string = td_tag.string
                        if td_tag.get('colspan'):
                            th_tag['colspan'] = td_tag.get('colspan')
                        td_tag.replace_with(th_tag)
                    bTitleSkip = None
                bTitle = None                    

            tbody_tag = soup.new_tag('tbody')
            caption_tag = soup.new_tag('caption')

            for tr_tag in table_tag.find_all('tr'):
                if(bTitleSkip):
                    tr_tag.wrap(tbody_tag)
                else:
                    bTitleSkip = True

            table_tag.insert(0, caption_tag)

            # 태그 사이의 공백과 줄바꿈 제거
            for pre_tag in table_tag.find_all('pre'):
                pre_tag.string = pre_tag.text.strip()

            for pre_tag in table_tag.find_all('pre'):
                div_tag = soup.new_tag('div')
                div_tag.string = pre_tag.string
                pre_tag.replace_with(div_tag)

            # Constructor 예외 - 특정 문자열 삭제, class 속성 추가
            target_string = "Sample Call:<br/>"
            if title == "Constructor" or title == "Parameters":
                for td_tag in table_tag.find_all('td'):
                    if target_string in ''.join(map(str, td_tag.contents)):
                        td_tag.contents[0].replace_with("")
                        td_tag.contents[1].replace_with("")
                        td_tag['class'] = "code_cell"

                if index == 2 or (title == 'Constructor' and constructor_except and index == 1):
                    table_tag.find('td')['class'] = "code_cell"
                    layout = "100%"
            
            # Setting Syntax 예외 - colspan=3이 있으면 code_cell, 없으면 th
            if title == "Setting Syntax":
                for td_tag in table_tag.find_all('td'):
                    if 'colspan' in td_tag.attrs and td_tag.attrs['colspan'] == '3':
                        td_tag['class'] = 'code_cell'
                    elif 'colspan' not in td_tag.attrs:
                        th_tag = soup.new_tag('th')
                        th_tag.string = td_tag.string
                        td_tag.replace_with(th_tag)         

            # Event Parameter - EventInfo 처리
            if  title == "Parameters" and bEvent:
                for td_tag in table_tag.find_all('td'):
                    if 'EventInfo' in td_tag.get_text():
                        td_tag.string.replace_with(
                            soup.new_tag('a', href='#' + td_tag.get_text(), **{'class': 'reference'}, string=td_tag.get_text())
                        )

            # div 태그를 제외한 나머지 결과물에서 줄바꿈(\n) 삭제
            for element in table_tag.find_all(string=True):
                if element.parent.name != "div":
                    element.replace_with(element.replace("\n", ""))

            add_element("u_10_"+str(random.random()), "table", str(table_tag), get_table_option(layout))            
        else:
            print(f"{title} 본문 텍스트, 표를 포함한 요소를 찾을 수 없습니다. 참고 {item}")

# Remark 등에 테이블이 있는 경우 처리
# (soup, title, layout, bTitle=None, item=None, constructor_except=None):
def get_simple_table_content(soup, table_tag, item=None):
    bTitle = True

    if table_tag:
        
        # 속성 제거
        table_tag.attrs.clear()
        for tag in table_tag.find_all():
            attrs_to_remove = [attr for attr in tag.attrs if attr not in ('colspan', 'rowspan')]
            for attr in attrs_to_remove:
                del tag[attr]

        # colgroup 태그 삭제
        for colgroup in table_tag.find_all('colgroup'):
            colgroup.decompose()

        # a 태그 삭제(a 태그 내 텍스트는 유지)
        for td_tag in table_tag.find_all('td'):
            a_tag = td_tag.find('a')
            if a_tag:
                a_text = a_tag.get_text()
                td_tag.string = a_text

        bTitleSkip = True

        if bTitle:
            thead_tag = soup.new_tag('thead')
            first_tr_tag = table_tag.find('tr')
            first_tr_tag.wrap(thead_tag)

            for td_tag in first_tr_tag.find_all('td'):
                th_tag = soup.new_tag('th')
                th_tag.string = td_tag.string
                if td_tag.get('colspan'):
                    th_tag['colspan'] = td_tag.get('colspan')
                td_tag.replace_with(th_tag)
            bTitleSkip = None
            bTitle = None                    

        tbody_tag = soup.new_tag('tbody')
        caption_tag = soup.new_tag('caption')

        for tr_tag in table_tag.find_all('tr'):
            if(bTitleSkip):
                tr_tag.wrap(tbody_tag)
            else:
                bTitleSkip = True

        table_tag.insert(0, caption_tag)

        # 태그 사이의 공백과 줄바꿈 제거
        for pre_tag in table_tag.find_all('pre'):
            pre_tag.string = pre_tag.text.strip()

        for pre_tag in table_tag.find_all('pre'):
            div_tag = soup.new_tag('div')
            div_tag.string = pre_tag.string
            pre_tag.replace_with(div_tag)

        # div 태그를 제외한 나머지 결과물에서 줄바꿈(\n) 삭제
        for element in table_tag.find_all(string=True):
            if element.parent.name != "div":
                element.replace_with(element.replace("\n", ""))

        add_element("u_10_"+str(random.random()), "table", str(table_tag), get_table_option(None, "auto"))            
    else:
        print(f"{title} Remark 표를 포함한 요소를 찾을 수 없습니다. 참고 {item}")

# 속성, 메서드, 이벤트 목록 처리
def set_item_list(soup, module_name, module_category, title="Property"):
    content_title_td = soup.find('td', class_='sub_title', string=title)
    if not content_title_td:
        print(f"{title}을 포함한 요소를 찾을 수 없습니다.")
        raise ValueError(f"{title}을 포함한 요소를 찾을 수 없습니다.")
    
    table_tag = content_title_td.find_next('table')
    item_list = [a_tag.string for a_tag in table_tag.find_all('a')]
    for item in item_list:
        if title=="Property":
            set_property_data(module_name, module_category, item)
        elif title=="Method":
            set_method_data(module_name, module_category, item)
        elif title=="Event":
            set_event_data(module_name, module_category, item)

# 속성 데이터 처리
def set_property_data(module_name, module_category, property):
    property_soup = get_soup(module_name, module_category, "Property", property)
    if property_soup is None:
        return

    add_element(f"p_01_{property}", "heading2", property, get_alias_option(module_name, property))
    add_element(f"p_02_{property}", "pre", get_desc_text(property_soup, "Description"))
    add_element(f"p_03_{property}", "headline", "지원 환경")
    add_element(f"p_04_{property}", "table", get_support_table(property_soup), get_table_option())
    add_element(f"p_05_{property}", "headline", "속성 타입")
    add_element(f"p_06_{property}", "table", get_property_type_table(property_soup), get_table_option('80,70,90,90,110,80,110,140'))

    if property_soup.find('td', class_='sub_title', string="Syntax"):
        add_element(f"p_07_{property}", "headline", "문법")
        add_element(f"p_08_{property}", "command", get_desc_text(property_soup, "Syntax", property))

    if property_soup.find('td', class_='sub_title', string="Setting Syntax"):
        add_element(f"p_09_{property}", "headline", "문법 설정")
        get_table_content(property_soup, "Setting Syntax", "180,120,?", None, property)  

    if property_soup.find('td', class_='sub_title', string="Remark"):
        add_element(f"p_11_{property}", "headline", "참고")
        remark_desc, remark_table = get_desc_text(property_soup, "Remark", property, True)
        add_element(f"p_12_{property}", "pre", remark_desc)
        if remark_table:
            get_simple_table_content(property_soup, remark_table, property)  

    result_text = find_matching_rows(xml_keyword, module_name, property)
    if result_text:
        add_element(f"p_13_{property}", "headline", "활용 예제")
        add_element(f"p_14_{property}", "unordered_list", result_text)

# 메서드 데이터 처리
def set_method_data(module_name, module_category, method):
    method_soup = get_soup(module_name, module_category, "Method", method)
    if method_soup is None:
        return    

    add_element("m_01"+method, "heading2", method, get_alias_option(module_name, method))
    add_element(f"m_02_{method}", "pre", get_desc_text(method_soup, "Description"))
    add_element(f"m_03_{method}", "headline", "지원 환경")
    add_element(f"m_04_{method}", "table", get_support_table(method_soup), get_table_option()) 

    if method_soup.find('td', class_='sub_title', string="Syntax"):
        add_element(f"m_05_{method}", "headline", "문법")
        add_element(f"m_06_{method}", "command", get_desc_text(method_soup, "Syntax", method))    

    if method_soup.find('td', class_='sub_title', string="Parameters"):
        add_element(f"m_07_{method}", "headline", "파라미터")
        get_table_content(method_soup, "Parameters", "180,120,?", True, method) 

    if method_soup.find('td', class_='sub_title', string="Return"):
        # Return 항목이 없는 경우 "없음"으로 자동 기재되어 있어 해당 건 예외 처리
        content_title_td = method_soup.find('td', class_='sub_title', string="Return")
        content_td = content_title_td.find_next('td', class_='list')
        if content_td.text.strip() != "없음":
            add_element(f"m_08_{method}", "headline", "반환")
            get_table_content(method_soup, "Return", "180,?", True, method)  

    if method_soup.find('td', class_='sub_title', string="Remark"):
        add_element(f"m_09_{method}", "headline", "참고")
        add_element(f"m_10_{method}", "pre", get_desc_text(method_soup, "Remark", method))       

    result_text = find_matching_rows(xml_keyword, module_name, method)
    if result_text:
        add_element(f"m_11_{method}", "headline", "활용 예제")
        add_element(f"m_12_{method}", "unordered_list", result_text)         

# 이벤트 데이터 처리
def set_event_data(module_name, module_category, event):
    event_soup = get_soup(module_name, module_category, "Event", event)     
    if event_soup is None:
        return

    add_element("e_01"+event, "heading2", event, get_alias_option(module_name, event)) 
    add_element(f"e_02_{event}", "pre", get_desc_text(event_soup, "Description"))
    add_element(f"e_03_{event}", "headline", "지원 환경")
    add_element(f"e_04_{event}", "table", get_support_table(event_soup), get_table_option()) 

    if event_soup.find('td', class_='sub_title', string="Syntax"):
        add_element(f"e_05_{event}", "headline", "문법")
        add_element(f"e_06_{event}", "command", get_desc_text(event_soup, "Syntax"), event)    

    add_element(f"e_07_{event}", "headline", "파라미터")
    get_table_content(event_soup, "Parameters", "120,240,?", True, event, None, True) 

    if event_soup.find('td', class_='sub_title', string="Return"):
        # Return 항목이 없는 경우 "없음"으로 자동 기재되어 있어 해당 건 예외 처리
        content_title_td = event_soup.find('td', class_='sub_title', string="Return")
        content_td = content_title_td.find_next('td', class_='list')
        if content_td.text.strip() != "없음":
            add_element(f"e_08_{event}", "headline", "반환")
            get_table_content(event_soup, "Return", "180,?", True, event)  

    if event_soup.find('td', class_='sub_title', string="Remark"):
        add_element(f"e_09_{event}", "headline", "참고")
        add_element(f"e_10_{event}", "pre", get_desc_text(event_soup, "Remark", event))     

    if event_soup.find('td', class_='sub_title', string="Basic Action"):
        add_element(f"e_11_{event}", "headline", "Basic Action")
        add_element(f"e_12_{event}", "pre", get_desc_text(event_soup, "Basic Action", event))   

    if event_soup.find('td', class_='sub_title', string="Default Action"):
        add_element(f"e_13_{event}", "headline", "Default Action")
        add_element(f"e_14_{event}", "pre", get_desc_text(event_soup, "Default Action", event))        

    result_text = find_matching_rows(xml_keyword, module_name, event)
    if result_text:
        add_element(f"e_15_{event}", "headline", "활용 예제")
        add_element(f"e_16_{event}", "unordered_list", result_text)                                 


# (공통 함수) Structure 이미지 파일명 가져오기
# Object > Structure
def get_structure_img(soup):
    structure_title_td = soup.find('td', class_='sub_title', string='Structure')
    if not structure_title_td:
        print("Structure를 포함한 요소를 찾을 수 없습니다.")
        raise ValueError("Structure를 포함한 요소를 찾을 수 없습니다.")
        
    structure_content_td = structure_title_td.find_next('td', class_='list')
    if structure_content_td and structure_content_td.pre:
        structure_img = structure_content_td.pre.find('img')['src'].split('/')[-1]
    else:
        print("Structure 이미지를 포함한 요소를 찾을 수 없습니다.")
    
    return f"<img src='{url_github}/{structure_img}?raw=true'/>"

# (공통 함수) Supported Environments 표 생성
# Object > Supported Environments
def get_support_table(soup):
    support_icon = []
    env_keywords = ["Windows", "macOS", "Edge", "Chrome", "Safari", "Firefox", "Opera", "Android", "iOS/iPadOS", "Android Default Web Browser", "iOS/iPadOS Default Web Browser"]

    support_title_td = soup.find('td', class_='sub_title', string='Supported Environments')    
    if not support_title_td:
        print("Supported Environments 타이틀을 찾을 수 없습니다.")
        raise ValueError("Supported Environments 타이틀을 찾을 수 없습니다.")
    
    for env_keyword in env_keywords:
        if support_title_td:
            keyword_td = support_title_td.find_next('td', string=env_keyword)
            if keyword_td:
                img_src = keyword_td.find_previous_sibling('td').find('img')['src']
                if img_src == "../../support01.gif":
                    support_icon.append("☑");
                else:
                    support_icon.append("☐");
                
            else:
                print(f"{env_keyword} 환경이 지원되지 않습니다.")


    return "<table class='table column_count_7'><caption></caption><thead><tr><th colspan='2'><div>Desktop NRE</div></th><th colspan='5'><div>Desktop WRE</div></th></tr></thead><tbody><tr><td><div>"+support_icon[0]+" Windows</div></td><td><div>"+support_icon[1]+" macOS</div></td><td><div>"+support_icon[2]+" Edge</div></td><td><div>"+support_icon[3]+" Chrome</div></td><td><div>"+support_icon[4]+" Safari</div></td><td><div>"+support_icon[5]+" Firefox</div></td><td><div>"+support_icon[6]+" Opera</div></td></tr><tr><th colspan='2'><div>Mobile NRE</div></th><th colspan='5'><div>Mobile WRE</div></th></tr><tr><td><div>"+support_icon[7]+" Android</div></td><td><div>"+support_icon[8]+" iOS/iPadOS</div></td><td><div>"+support_icon[9]+" Android</div></td><td><div>"+support_icon[10]+" iOS/iPadOS</div></td><td><div></div></td><td><div></div></td><td><div></div></td></tr></tbody></table>"

# (공통 함수) Property Type 표 생성
# Object > Property > Property Type
def get_property_type_table(soup):
    support_icon = []
    env_keywords = ["Enum", "Expr", "Control", "Hidden", "ReadOnly", "Bind", "Collection", "StringResource"]

    property_type_title_td = soup.find('td', class_='sub_title', string='Property Type')    
    if not property_type_title_td:
        print("Property Type 타이틀을 찾을 수 없습니다.")
        raise ValueError("Property Type 타이틀을 찾을 수 없습니다.")
    
    property_type_table_td = property_type_title_td.find_next('td', class_='list')
    td_keywords = property_type_table_td.find_all('input')
    for td_keyword in td_keywords:
        if td_keyword.get('checked') != None:
            support_icon.append("☑");
        else:
            support_icon.append("☐");
                

    return f"<table class='r_no_border_table column_count_8'><caption></caption><tbody><tr><td><div>{support_icon[0]} {env_keywords[0]}</div></td><td><div>{support_icon[1]} {env_keywords[1]}</div></td><td><div>{support_icon[2]} {env_keywords[2]}</div></td><td><div>{support_icon[3]} {env_keywords[3]}</div></td><td><div>{support_icon[4]} {env_keywords[4]}</div></td><td><div>{support_icon[5]} {env_keywords[5]}</div></td><td><div>{support_icon[6]} {env_keywords[6]}</div></td><td><div>{support_icon[7]} {env_keywords[7]}</div></td></tr></tbody></table>"

# (공통 함수) 텍스트 변환
def get_html_text(target_text):
    return target_text.replace("<", "&lt;").replace(">", "&gt;")


# (공통 함수) 표 config
# Object > Supported Environments (110,110,110,110,110,110,110)
def get_table_option(layout="110,110,110,110,110,110,110", bAuto="user"):
    return {
        "table_layout": bAuto,
        "codeLanguage": "Javascript",
        "table_layout_setting": layout
    }

# (공통 함수) alias config
def get_alias_option(module, title):
    return {
        "alias": module+"_"+title
    }

# JSON 파일 생성
elements = []

def add_element(id, type, content, option=None):
    element = {
        "id": id,
        "type": type,
        "content": content
    }
    if option is not None:
        element["option"] = option
    elements.append(element)    

# 파일 처리 시작
def generate_object_file(target_module_name, target_module_cagegory, constructor_except):
    soup = get_soup(target_module_name, target_module_cagegory) 
    if soup is None:
        return

    # Object 정보 처리
    add_element("u_01", "heading1", "개요")
    add_element("u_02", "pre", get_desc_text(soup, "Description"))
    add_element("u_03", "heading2", "지원 환경")
    add_element("u_04", "table", get_support_table(soup), get_table_option())

    if soup.find('td', class_='sub_title', string="Remark"):
        add_element("u_05", "pre", get_desc_text(soup, "Remark"))

    if soup.find('td', class_='sub_title', string="Structure"):
        add_element("u_06", "heading2", "컴포넌트 구조")
        add_element("u_07", "normal", get_structure_img(soup))

    if soup.find('td', class_='sub_title', string="Contents Sizing"):
        add_element("u_08", "heading2", "컴포넌트, 내부 컨텐츠 크기")
        get_table_content(soup, "Contents Sizing", "120,?")

    if soup.find('td', class_='sub_title', string="Basic Key Action"):    
        add_element("u_11", "heading2", "Basic Key Action")
        get_table_content(soup, "Basic Key Action", "120,180,?", True)

    if soup.find('td', class_='sub_title', string="Accessibility Key Action"):  
        add_element("u_12", "heading2", "Accessibility Key Action")
        get_table_content(soup, "Accessibility Key Action", "120,180,?", True)

    if soup.find('td', class_='sub_title', string="Constructor"):      
        add_element("u_13", "heading2", "생성자")
        get_table_content(soup, "Constructor", "120,120,?", True, None, constructor_except)

    if soup.find('td', class_='sub_title', string="Status"):    
        add_element("u_14", "heading2", "Status")
        get_table_content(soup, "Status", "120,120,?", True)

    if soup.find('td', class_='sub_title', string="Control"):  
        add_element("u_15", "heading2", "Control")
        get_table_content(soup, "Control", "120,120,?", True)

    if soup.find('td', class_='sub_title', string="Property"):  
        add_element("u_16", "heading1", "속성")
        set_item_list(soup, target_module_name, target_module_cagegory, "Property")

    if soup.find('td', class_='sub_title', string="Method"): 
        add_element("u_17", "heading1", "메서드")
        set_item_list(soup, target_module_name, target_module_cagegory, "Method")

    if soup.find('td', class_='sub_title', string="Event"): 
        add_element("u_18", "heading1", "이벤트")
        set_item_list(soup, target_module_name, target_module_cagegory, "Event")

    data = {
        "elements": elements
    }

    save_dir = os.path.join(file_path, 'UPLOAD')
    os.makedirs(save_dir, exist_ok=True)
    save_file_path = os.path.join(save_dir, f'{target_module_name}.json')

    # JSON 파일로 저장
    with open(save_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)    

# 개별 파일 테스트 용
# 개별 파일 테스트 시에는 아래 for 문을 주석 처리하고 테스트 진행
'''
target_module_name = 'Grid'
target_module_category = 'Components_Component_'
target_constructor_except = None
generate_object_file(target_module_name, target_module_category, target_constructor_except)
'''

''' '''
# 오브젝트 목록 JSON 파일 읽기
with open('file_list.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

for category in data['categorys']:
    target_module_category = category['name']

    # items 항목 순회
    for item in category['items']:
        elements = []
        target_module_name = item['name']
        target_constructor_except = item.get('except', False)
        temp_target_module_category = item.get('category', target_module_category)
        print(target_module_name)
        generate_object_file(target_module_name, temp_target_module_category, target_constructor_except)
''' '''
        
end_time = time.time()
execution_time = end_time - start_time
print("코드 실행 시간: {:.2f} 초".format(execution_time))
