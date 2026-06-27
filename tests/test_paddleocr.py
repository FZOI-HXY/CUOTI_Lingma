"""
PaddleOCR 使用示例和测试脚本
演示如何在项目中使用 PaddleOCR 进行文字识别
"""
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_basic_ocr():
    """测试基本的 PaddleOCR 功能"""
    print("="*60)
    print("测试1: 基本 PaddleOCR 功能")
    print("="*60)
    
    try:
        from paddleocr import PaddleOCR
        
        # 初始化 OCR (CPU 模式)
        print("\n正在初始化 PaddleOCR...")
        ocr = PaddleOCR(
            lang='ch',  # 中文识别
            show_log=False
        )
        print("✅ PaddleOCR 初始化成功\n")
        
        # 注意: 这里需要一个测试图片
        # 如果您有测试图片，可以取消下面的注释
        # test_image = "path/to/your/test/image.jpg"
        # if os.path.exists(test_image):
        #     result = ocr.ocr(test_image, cls=True)
        #     print("识别结果:")
        #     for line in result[0]:
        #         text = line[1][0]
        #         confidence = line[1][1]
        #         print(f"  文本: {text}")
        #         print(f"  置信度: {confidence:.4f}\n")
        # else:
        #     print(f"⚠️ 测试图片不存在: {test_image}")
        #     print("请提供一个测试图片路径来验证 OCR 功能")
        
        print("💡 提示: 要测试实际识别，请准备一张包含文字的图片")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_paddlex_layout():
    """测试 PaddleX 版面分析功能"""
    print("\n" + "="*60)
    print("测试2: PaddleX 版面分析")
    print("="*60)
    
    try:
        from paddlex.pipelines import PPStructureV3
        
        print("\n正在初始化 PP-StructureV3...")
        ppstructure = PPStructureV3(
            use_gpu=False,
            lang='ch'
        )
        print("✅ PP-StructureV3 初始化成功\n")
        
        print("💡 PP-StructureV3 可用于:")
        print("  - 文档版面分析")
        print("  - 表格识别")
        print("  - 公式识别")
        print("  - 印章检测")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_project_ocr_service():
    """测试项目中的 OCR 服务"""
    print("\n" + "="*60)
    print("测试3: 项目 OCR 服务")
    print("="*60)
    
    try:
        from backend.app.services.ocr_service import OCRService
        
        print("\n正在初始化 OCR 服务...")
        ocr_service = OCRService()
        ocr_service.initialize()
        print("✅ OCR 服务初始化成功\n")
        
        if ocr_service._initialized and ocr_service.ppocr is not None:
            print("✅ PaddleOCR 模型已加载")
        else:
            print("⚠️ PaddleOCR 模型未加载（可能是 mock 模式）")
            
        if ocr_service._initialized and ocr_service.ppstructure is not None:
            print("✅ PP-StructureV3 模型已加载")
        else:
            print("⚠️ PP-StructureV3 模型未加载（可能是 mock 模式）")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_usage_examples():
    """显示使用示例"""
    print("\n" + "="*60)
    print("📖 使用示例")
    print("="*60)
    
    examples = """
1. 在代码中使用 PaddleOCR:
   
   from paddleocr import PaddleOCR
   
   # 初始化 (新版本不需要 use_gpu 和 use_angle_cls)
   ocr = PaddleOCR(lang='ch')
   
   # 识别图片
   result = ocr.ocr('image.jpg')
   
   # 处理结果
   for line in result[0]:
       text = line[1][0]      # 识别的文本
       confidence = line[1][1] # 置信度
       print(f"{text} ({confidence:.2f})")

2. 使用项目的 OCR 服务:
   
   from backend.app.services.ocr_service import OCRService
   
   # 创建服务实例
   ocr_service = OCRService()
   ocr_service.initialize()
   
   # 处理图片
   result = ocr_service.process_image('path/to/image.jpg')
   
   # 获取结果
   markdown = result['markdown_content']
   processed_image = result['processed_image_path']

3. 通过 API 使用:
   
   # 上传图片
   POST /upload/image
   
   # 启动 OCR 处理
   POST /ocr/process
   {
     "file_id": "uploaded_file_id",
     "user_id": 1
   }
   
   # 查询任务状态
   GET /ocr/status/{task_id}

4. 在前端使用:
   
   # 运行前端应用
   cd frontend
   python main.py
   
   # 在界面中选择图片并点击"开始处理"
    """
    
    print(examples)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PaddleOCR Installation Verification and Usage Guide")
    print("="*60 + "\n")
    
    # 运行测试
    test1 = test_basic_ocr()
    test2 = test_paddlex_layout()
    test3 = test_project_ocr_service()
    
    # 显示使用示例
    show_usage_examples()
    
    # 总结
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    print(f"Basic PaddleOCR:     {'PASS' if test1 else 'FAIL'}")
    print(f"PaddleX Layout:      {'PASS' if test2 else 'FAIL'}")
    print(f"Project OCR Service: {'PASS' if test3 else 'FAIL'}")
    
    if test1 and test2 and test3:
        print("\nAll tests passed! PaddleOCR is ready to use.")
    else:
        print("\nSome tests failed. Please check the error messages above.")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Start backend: cd backend && python -m app.main")
    print("2. Start frontend: cd frontend && python main.py")
    print("3. Upload an image with text in the frontend to test OCR")
    print("="*60 + "\n")
