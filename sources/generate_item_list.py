import os
import json

def get_json_files_in_folder(folder_path):
    # 지정된 폴더에서 모든 파일을 확인하고 .json 확장자 파일만 필터링
    files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    # 파일 목록을 알파벳 순으로 정렬
    files.sort()
    
    # JSON 형식에 맞는 데이터 구조 생성
    items = [{"id": file_name.replace(".json", ""), "name": file_name.replace(".json", "")} for file_name in files]
    
    # 최종 데이터 구조
    result = {"items": items}
    
    # JSON 파일로 저장
    with open('items_list.json', 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=2)

# 사용할 폴더 경로를 입력해주세요
folder_path = "D:\\chm\\24.0.0.400\\KOR\\UPLOAD"  # 예: "C:/Users/YourUsername/Documents"
get_json_files_in_folder(folder_path)
