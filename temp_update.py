import sys

def main():
    # Replace in Server.py
    path1 = 'YoutubeToDoc/Server.py'
    with open(path1, 'r', encoding='utf-8') as f:
        content1 = f.read()
    
    content1 = content1.replace('gemini-2.5-flash', 'gemini-2.0-flash')
    content1 = content1.replace('if translation_model.startswith("gpt-"):', 'if translation_model.startswith("gpt-") or "2.5-flash" in translation_model:')
    
    with open(path1, 'w', encoding='utf-8') as f:
        f.write(content1)
        
    # Replace in admin.html
    path2 = 'YoutubeToDoc/templates/admin.html'
    with open(path2, 'r', encoding='utf-8') as f:
        content2 = f.read()
        
    content2 = content2.replace('2.5-flash', '2.0-flash')
    
    with open(path2, 'w', encoding='utf-8') as f:
        f.write(content2)

    print("Replacements done.")

if __name__ == '__main__':
    main()
