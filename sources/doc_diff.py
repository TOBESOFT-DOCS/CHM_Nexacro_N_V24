import os
import json
import hashlib
from github import Github

# JSON 파일 확장자 확인
def is_json_file(filename):
    return os.path.splitext(filename)[1].lower() == '.json'

# JSON 파일의 해시 계산
def calculate_json_hash(filepath):
    """Calculate the SHA-256 hash of normalized JSON file content, excluding 'id' fields."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
        
        # 'id' 필드를 제거하는 함수
        def remove_id_fields(data):
            if isinstance(data, dict):
                return {k: remove_id_fields(v) for k, v in data.items() if k != "id"}
            elif isinstance(data, list):
                return [remove_id_fields(item) for item in data]
            else:
                return data
        
        sanitized_content = remove_id_fields(json_content)
        normalized_content = json.dumps(sanitized_content, sort_keys=True)  # Normalize JSON
        hash_sha256.update(normalized_content.encode('utf-8'))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file {filepath}: {e}")
    return hash_sha256.hexdigest()

# 폴더에서 JSON 파일과 해시 목록 가져오기
def get_json_files(folder):
    """Get a dictionary of JSON files and their hashes from the specified folder."""
    files = {}
    for root, _, filenames in os.walk(folder):  # Include subdirectories
        for filename in filenames:
            if is_json_file(filename):
                filepath = os.path.join(root, filename)
                files[os.path.relpath(filepath, folder)] = calculate_json_hash(filepath)
    return files

# 두 폴더 비교
def compare_json_folders(folder1, folder2):
    """Compare JSON files in two folders."""
    files1 = get_json_files(folder1)
    files2 = get_json_files(folder2)

    added_files = []
    changed_files = []

    # Check for added or changed files
    for filename, filehash in files2.items():
        if filename not in files1:
            added_files.append(filename)
        elif files1[filename] != filehash:
            changed_files.append(filename)

    return added_files, changed_files

# 결과 출력
def print_results(added_files, changed_files):
    if added_files:
        print("Added files:")
        for file in added_files:
            print(f"  {file}")
    else:
        print("No added files.")

    if changed_files:
        print("Changed files:")
        for file in changed_files:
            print(f"  {file}")
    else:
        print("No changed files.")

# GitHub에 파일 업로드
def upload_to_github(repo, path, filepath, message, github_token):
    """Upload a file to GitHub."""
    g = Github(github_token)
    repo = g.get_repo(repo)
    
    with open(filepath, "rb") as file:
        content = file.read()
    
    github_path = f"{path}/{os.path.basename(filepath)}"  # Ensure correct path format
    try:
        # Check if the file exists
        contents = repo.get_contents(github_path)
        # If it exists, update it
        commit_response = repo.update_file(contents.path, message, content, contents.sha)
        print(f"Updated {github_path} on GitHub.")
    except Exception as e:
        # If file does not exist, create it
        if "404" in str(e):
            commit_response = repo.create_file(github_path, message, content)
            print(f"Uploaded {github_path} to GitHub.")
        else:
            print(f"Failed to upload {github_path}: {e}")
    
    return commit_response['commit'].sha

# GitHub 설정
repo = "TOBESOFT-DOCS/CHM_Nexacro_N_V24"
path = "docs"  # GitHub 내 파일 경로
github_token = ""
tag_message = "24.0.0.400"
tag_name = "24.0.0.400"

# 폴더 경로 지정
previous_folder = "D:\\chm\\24.0.0.300\\KOR\\UPLOAD"
current_folder = "D:\\chm\\24.0.0.400\\KOR\\UPLOAD"

# 폴더 비교 및 결과 출력
added_files, changed_files = compare_json_folders(previous_folder, current_folder)
print_results(added_files, changed_files)

# GitHub에 변경된 파일만 업로드
commit_shas = []
for filename in added_files + changed_files:
    filepath = os.path.join(current_folder, filename)
    sha = upload_to_github(repo, path, filepath, tag_message, github_token)
    commit_shas.append(sha)

# 태그 생성
if commit_shas:
    latest_commit_sha = commit_shas[-1]
    g = Github(github_token)
    repo = g.get_repo(repo)
    try:
        ref = repo.create_git_ref(ref=f"refs/tags/{tag_name}", sha=latest_commit_sha)
        print(f"Created tag {tag_name} on commit {latest_commit_sha}")
    except Exception as e:
        print(f"Failed to create tag: {e}")
