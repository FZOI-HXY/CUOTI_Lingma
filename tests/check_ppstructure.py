"""
检查 PP-StructureV3 是否可用
"""
import sys
import os

def check_ppstructure():
    """检查 PP-StructureV3"""
    print("=" * 60)
    print("检查 PP-StructureV3 可用性")
    print("=" * 60)
    
    try:
        import paddlex
        print(f"\n✅ PaddleX 已安装")
        
        # 尝试创建 PP-StructureV3 pipeline
        print("\n[提示] 正在初始化 PP-StructureV3...")
        print("(首次运行会下载模型文件，请耐心等待)")
        
        ppstructure = paddlex.create_pipeline(
            pipeline='ppstructure_v3',
            lang='ch'
        )
        
        print("✅ PP-StructureV3 初始化成功")
        print(f"   Pipeline 类型: {type(ppstructure)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PP-StructureV3 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_ppstructure()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ PP-StructureV3 可用！可以进行版面分析")
    else:
        print("❌ PP-StructureV3 不可用，将使用纯 OCR 模式")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
