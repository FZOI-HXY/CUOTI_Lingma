"""Download PP-FormulaNet_plus-L model"""
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

os.environ['PADDLE_PDX_CACHE_HOME'] = r'E:\Program Files\PP_Models'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

print("Starting PP-FormulaNet_plus-L download...")
print(f"Cache directory: E:\\Program Files\\PP_Models")
print()

t0 = time.time()

try:
    import paddlex
    
    # Method 1: Try to create the formula recognition pipeline directly
    # This will trigger model download
    print("Downloading PP-FormulaNet_plus-L model...")
    from paddlex.inference.models import create_model
    model = create_model("PP-FormulaNet_plus-L")
    
    elapsed = time.time() - t0
    print(f"\nDownload completed in {elapsed:.1f}s")
    print(f"Model created: {model}")
    
except Exception as e:
    elapsed = time.time() - t0
    print(f"\nFailed after {elapsed:.1f}s: {e}")
    sys.exit(1)

# Verify the download
model_dir = r'E:\Program Files\PP_Models\official_models\PP-FormulaNet_plus-L'
print(f"\nVerifying files in {model_dir}:")

if os.path.isdir(model_dir):
    files = []
    total_size = 0
    for f in sorted(os.listdir(model_dir)):
        fp = os.path.join(model_dir, f)
        if os.path.isfile(fp):
            size = os.path.getsize(fp)
            total_size += size
            files.append((f, size))
            print(f"  {f}: {size / 1024 / 1024:.1f} MB")
    
    print(f"\nTotal files: {len(files)}")
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
    
    # Check critical files
    has_pdiparams = any(f.endswith('.pdiparams') for f, _ in files)
    has_pdmodel = any(f == 'inference.pdmodel' or f == 'model.pdmodel' for f, _ in files)
    
    if has_pdiparams and has_pdmodel:
        print("\n✅ Model files complete!")
    else:
        print(f"\n⚠️  Missing files: pdiparams={has_pdiparams}, pdmodel={has_pdmodel}")
else:
    print(f"\n❌ Model directory not found: {model_dir}")
    sys.exit(1)
