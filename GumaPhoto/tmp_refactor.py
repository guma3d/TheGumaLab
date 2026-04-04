import re
path = 'd:/TheGumaLab/GumaPhoto/frontend/script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the top declarations
content = re.sub(r'let currentQuery = \'\';\s*\n', '', content)
content = re.sub(r'let currentGalleryFilter = "recent";\s*\n', '', content)
content = re.sub(r'let currentOffset = 0;\s*\n', '', content)
content = re.sub(r'let currentLimit = 20;\s*\n', '', content)
content = re.sub(r'let currentPeople = \[\];\s*\n', '', content)
content = re.sub(r'let currentLocation = \'\';\s*\n', '', content)
content = re.sub(r'let currentScene = \'\';\s*\n', '', content)
content = re.sub(r'let isFetching = false;\s*\n', '', content)
content = re.sub(r'let hasMore = true;\s*\n', '', content)
content = re.sub(r'let totalHits = 0;\s*\n', '', content)
content = re.sub(r'let cachedTags = \{\};\s*\n', '', content)
content = re.sub(r'let advancedStatsData = \{[\s\S]*?\};\s*\n', '', content)
content = re.sub(r'let selectedFeedbackTarget = null;\s*\n', '', content)

# Replace all variables
replacements = {
    r'\bcurrentQuery\b': 'GumaState.currentQuery',
    r'\bcurrentGalleryFilter\b': 'GumaState.currentGalleryFilter',
    r'\bcurrentOffset\b': 'GumaState.currentOffset',
    r'\bcurrentLimit\b': 'GumaState.currentLimit',
    r'\bcurrentPeople\b': 'GumaState.currentPeople',
    r'\bcurrentLocation\b': 'GumaState.currentLocation',
    r'\bcurrentScene\b': 'GumaState.currentScene',
    r'\bisFetching\b': 'GumaState.isFetching',
    r'\bhasMore\b': 'GumaState.hasMore',
    r'\btotalHits\b': 'GumaState.totalHits',
    r'\bcachedTags\b': 'GumaState.cachedTags',
    r'\badvancedStatsData\b': 'GumaState.advancedStatsData',
    r'\bselectedFeedbackTarget\b': 'GumaState.selectedFeedbackTarget'
}

for old, new in replacements.items():
    content = re.sub(old, new, content)

content = content.replace('GumaState.GumaState.', 'GumaState.')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
