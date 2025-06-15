#!/usr/bin/env python3
"""
臨時解決時間戳問題的工具
"""

def fix_timestamp_issue():
    """修正時間戳問題"""
    print("🔧 應用臨時修正以解決時間戳問題...")
    
    # 讀取 binance_client.py
    with open('src/binance_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經有修正
    if 'BINANCE_TIMESTAMP_OFFSET' in content:
        print("✅ 時間戳修正已存在")
        return True
    
    # 在檔案開頭添加時間偏移量
    import_section = content.split('\n')
    
    # 找到適當的插入位置
    insert_pos = 0
    for i, line in enumerate(import_section):
        if line.startswith('import time'):
            insert_pos = i + 1
            break
    
    # 插入時間偏移量設定
    offset_lines = [
        "",
        "# 手動時間偏移量設定 (毫秒)",
        "BINANCE_TIMESTAMP_OFFSET = -1000  # 調整為與伺服器同步",
        ""
    ]
    
    for i, line in enumerate(offset_lines):
        import_section.insert(insert_pos + i, line)
    
    # 修改獲取時間戳的方法
    content = '\n'.join(import_section)
    
    # 替換 time.time() 調用
    if 'int(time.time() * 1000)' in content:
        content = content.replace(
            'int(time.time() * 1000)',
            'int(time.time() * 1000) + BINANCE_TIMESTAMP_OFFSET'
        )
        print("✅ 已修正時間戳計算")
    
    # 寫回檔案
    with open('src/binance_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🎉 時間戳修正完成！")
    return True

if __name__ == "__main__":
    fix_timestamp_issue()
