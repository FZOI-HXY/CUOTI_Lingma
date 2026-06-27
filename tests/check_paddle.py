"""
检查 PaddlePaddle 和 PaddleOCR 是否正常工作
"""
import sys
import os

def check_paddle():
    """检查 Paddle 组件"""
    print("=" * 60)
    print("检查 Paddle 组件安装情况")
    print("=" * 60)
    
    # 1. 检查 PaddlePaddle
    try:
        import paddle
        print(f"\n✅ PaddlePaddle 版本: {paddle.__version__}")
        print(f"   GPU 可用: {paddle.device.is_compiled_with_cuda()}")
        
        # 测试基本操作
        x = paddle.to_tensor([1, 2, 3])
        y = x + 1
        print(f"   基本运算测试: [1,2,3] + 1 = {y.numpy().tolist()}")
        
    except Exception as e:
        print(f"\n❌ PaddlePaddle 错误: {e}")
        return False
    
    # 2. 检查 PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print(f"\n✅ PaddleOCR 已安装")
        
        # 尝试初始化（这会下载模型，可能需要一些时间）
        print("\n[提示] 正在初始化 PaddleOCR...")
        print("(首次运行会下载模型文件，请耐心等待)")
        
        ocr = PaddleOCR(lang='ch', use_angle_cls=False)
        print("✅ PaddleOCR 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PaddleOCR 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_paddle()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Paddle 组件检查通过！可以正常使用")
    else:
        print("❌ Paddle 组件存在问题，请检查安装")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
