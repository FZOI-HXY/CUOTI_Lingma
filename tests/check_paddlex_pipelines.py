"""
检查 PaddleX 3.6 中可用的版面分析 pipeline
"""
import sys
import os

def check_available_pipelines():
    """检查可用的 pipeline 名称"""
    print("=" * 60)
    print("检查 PaddleX 3.6 可用的 Pipeline")
    print("=" * 60)
    
    try:
        import paddlex
        print(f"\n✅ PaddleX 已安装")
        
        # 尝试不同的 pipeline 名称
        pipeline_names = [
            'ppstructure_v3',
            'layout_parsing',
            'PP-StructureV3',
            'layout_analysis',
            'doc_structure_analysis',
        ]
        
        for name in pipeline_names:
            try:
                print(f"\n尝试: {name}")
                pipeline = paddlex.create_pipeline(pipeline=name, lang='ch')
                print(f"  ✅ 成功! Pipeline 类型: {type(pipeline)}")
                return name
            except Exception as e:
                print(f"  ❌ 失败: {str(e)[:100]}")
        
        print("\n❌ 所有尝试的 pipeline 名称都失败了")
        return None
        
    except Exception as e:
        print(f"\n❌ PaddleX 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = check_available_pipelines()
    
    print("\n" + "=" * 60)
    if result:
        print(f"✅ 找到可用的 pipeline: {result}")
    else:
        print("❌ 未找到可用的版面分析 pipeline")
        print("\n建议:")
        print("1. 查看 PaddleX 官方文档获取正确的 pipeline 名称")
        print("2. 使用纯 OCR 模式（不依赖版面分析）")
    print("=" * 60)
    
    sys.exit(0 if result else 1)
