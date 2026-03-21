with open("frontend/script.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Open file and remove the errant duplicate block
if "document.getElementById('fb-submit-btn');" in lines[1283]: # Line 1284 is index 1283
    del lines[1283:1442] # Delete lines 1284 to 1442
    
    with open("frontend/script.js", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("SUCCESSFULLY DELETED DUPLICATE BLOCK")
else:
    print("COULD NOT FIND THE EXACT ANCHOR AT LINE 1284")
    # Search for it manually
    for i, line in enumerate(lines):
        if "document.getElementById('fb-submit-btn');" in line:
            print(f"Actually found at line {i+1}")
            # Find the closing brace matching this function or just the block we want to kill
            break
