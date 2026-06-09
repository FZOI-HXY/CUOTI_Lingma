"""
简单的 PaddleOCR 测试脚本
用于验证 OCR 识别功能是否正常工作
"""
import sys
import os

# 激活虚拟环境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'venv312', 'Lib', 'site-packages'))

def test_simple_ocr():
    """测试简单的 OCR 识别"""
    print("="*60)
    print("Simple PaddleOCR Test")
    print("="*60)
    
    try:
        from paddleocr import PaddleOCR
        
        # 初始化 OCR
        print("\n[1/3] Initializing PaddleOCR...")
        ocr = PaddleOCR(lang='ch')
        print("✓ PaddleOCR initialized successfully")
        
        # 查找测试图片
        print("\n[2/3] Looking for test images...")
        upload_dir = os.path.join(os.path.dirname(__file__), 'backend', 'uploads')
        
        if os.path.exists(upload_dir):
            images = [f for f in os.listdir(upload_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            if images:
                test_image = os.path.join(upload_dir, images[0])
                print(f"✓ Found test image: {images[0]}")
            else:
                print("✗ No images found in uploads directory")
                print("\nPlease put a test image in the 'uploads' folder and run again.")
                return
        else:
            print("✗ Uploads directory not found")
            print("\nPlease create 'uploads' folder and put a test image in it.")
            return
        
        # 执行 OCR 识别
        print("\n[3/3] Performing OCR recognition...")
        print(f"Processing: {os.path.basename(test_image)}")
        print("-" * 60)
        
        result = ocr.ocr(test_image)
        
        if result and result[0]:
            print("\nRecognition Results:")
            print("="*60)
            for i, line in enumerate(result[0], 1):
                text = line[1][0]
                confidence = line[1][1]
                box = line[0]
                print(f"[{i}] {text}")
                print(f"    Confidence: {confidence:.4f}")
                print(f"    Box: {box}")
                print()
            
            print("="*60)
            print(f"Total lines recognized: {len(result[0])}")
            print("✓ OCR test completed successfully!")
        else:
            print("✗ No text recognized")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_ocr()
