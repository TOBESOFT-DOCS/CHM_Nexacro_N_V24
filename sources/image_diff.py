import os
import hashlib
from github import Github

# 이미지 파일 확장자 목록
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}

def is_image_file(filename):
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS

def calculate_file_hash(filepath):
    """Calculate the SHA-256 hash of the file content."""
    hash_sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_image_files(folder):
    """Get a dictionary of image files and their hashes from the specified folder."""
    files = {}
    for filename in os.listdir(folder):
        if is_image_file(filename):
            filepath = os.path.join(folder, filename)
            files[filename] = calculate_file_hash(filepath)
    return files

def compare_folders(previous_image_folder, current_image_folder):
    """Compare image files in two folders."""
    if previous_image_folder:
        files1 = get_image_files(previous_image_folder)
    else:
        files1 = {}
        
    files2 = get_image_files(current_image_folder)
    
    added_files = []
    changed_files = []

    # Check for added or changed files
    for filename, filehash in files2.items():
        if filename not in files1:
            added_files.append(filename)
        elif files1[filename] != filehash:
            changed_files.append(filename)

    return added_files, changed_files

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

def upload_to_github(repo, path, filepath, message, github_token):
    """Upload a file to GitHub."""
    g = Github(github_token)
    repo = g.get_repo(repo)
    
    with open(filepath, "rb") as file:
        content = file.read()
    
    try:
        # Get the file's current contents if it exists
        contents = repo.get_contents(f"{path}/{os.path.basename(filepath)}")
        commit_response = repo.update_file(contents.path, message, content, contents.sha)
        print(f"Updated {filepath} on GitHub.")
    except:
        # File does not exist, create it
        commit_response = repo.create_file(f"{path}/{os.path.basename(filepath)}", message, content)
        print(f"Uploaded {filepath} to GitHub.")
    
    return commit_response['commit'].sha

def create_github_tag(repo, tag, sha, message, github_token):
    """Create a tag in GitHub."""
    g = Github(github_token)
    repo = g.get_repo(repo)
    
    try:
        ref = repo.create_git_ref(ref=f"refs/tags/{tag}", sha=sha)
        print(f"Created tag {tag} on commit {sha}")
    except Exception as e:
        print(f"Failed to create tag: {e}")

# 폴더 경로 지정
previous_image_folder = ''
current_image_folder = 'D:\\chm\\24.0.0.400'

# GitHub 설정
repo = "TOBESOFT-DOCS/CHM_Nexacro_N_V24"
path = "images"
github_token = ""
tag_message = "24.0.0.400"
tag_name = "24.0.0.400"  # 원하는 태그 이름

# 폴더 비교 및 결과 출력
added_files, changed_files = compare_folders(previous_image_folder, current_image_folder)
print_results(added_files, changed_files)

# 커밋 해시값 저장
commit_shas = []

# 모든 파일 업로드
if not previous_image_folder:
    for filename in os.listdir(current_image_folder):
        if is_image_file(filename):
            filepath = os.path.join(current_image_folder, filename)
            sha = upload_to_github(repo, path, filepath, tag_message, github_token)
            commit_shas.append(sha)
else:
    # 변경된 파일과 추가된 파일만 업로드
    for filename in added_files + changed_files:
        filepath = os.path.join(current_image_folder, filename)
        sha = upload_to_github(repo, path, filepath, tag_message, github_token)
        commit_shas.append(sha)

# 가장 마지막 커밋에 태그 생성
if commit_shas:
    latest_commit_sha = commit_shas[-1]
    create_github_tag(repo, tag_name, latest_commit_sha, tag_message, github_token)
