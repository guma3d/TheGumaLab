import os
import glob

def delete_all_xmps():
    target_dir = '/app/data/organized'
    print(f"Scanning for .xmp files in {target_dir}...")
    
    # Use recursive glob to find all .xmp files
    xmp_files = glob.glob(os.path.join(target_dir, '**', '*.xmp'), recursive=True)
    count = 0
    
    for xmp_file in xmp_files:
        try:
            os.remove(xmp_file)
            count += 1
        except Exception as e:
            print(f"Failed to delete {xmp_file}: {e}")
            
    print(f"Successfully deleted {count} XMP files.")

if __name__ == '__main__':
    delete_all_xmps()
