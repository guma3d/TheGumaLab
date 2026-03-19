import os
locs = set()
for y in os.listdir('/app/data/organized'):
    yp = os.path.join('/app/data/organized', y)
    if os.path.isdir(yp):
        for d in os.listdir(yp):
            if '_' in d:
                locs.add(d.split('_', 1)[1])
print('UNIQUE_LOCATIONS:', len(locs))
print(list(locs)[:20])
