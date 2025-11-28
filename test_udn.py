#!/usr/bin/env python3
# coding=utf-8
"""
UDN 新聞爬取測試腳本

用途：快速測試 UDN 聯合新聞網的爬取功能
使用：python test_udn.py
"""

from main import DataFetcher


def test_udn_basic():
    """基本功能測試"""
    print("=" * 80)
    print("UDN 聯合新聞網爬取測試")
    print("=" * 80)
    print()

    fetcher = DataFetcher()

    print("📡 開始爬取 UDN 新聞...")
    result, platform_id = fetcher.fetch_udn_news()

    if not result:
        print("❌ 爬取失敗！")
        return False

    print(f"✅ 爬取成功！")
    print()
    print(f"📊 統計信息：")
    print(f"   - 平台 ID: {platform_id}")
    print(f"   - 新聞總數: {len(result)} 條")
    print()

    print("📰 前 10 條新聞：")
    print("-" * 80)
    for i, (title, info) in enumerate(list(result.items())[:10], 1):
        rank = info['ranks'][0]
        url = info['url']
        print(f"{i:2d}. [{rank:2d}] {title}")
        print(f"     🔗 {url}")
        print()

    return True


def test_udn_integration():
    """測試與主系統的整合"""
    print("=" * 80)
    print("測試 UDN 與主系統整合")
    print("=" * 80)
    print()

    from main import CONFIG

    # 檢查配置
    udn_configured = any(p['id'] == 'udn' for p in CONFIG['PLATFORMS'])

    if udn_configured:
        print("✅ UDN 已在配置文件中")
    else:
        print("❌ UDN 未在配置文件中")
        return False

    # 測試爬取流程
    fetcher = DataFetcher()
    platform_configs = [(p['id'], p['name']) for p in CONFIG['PLATFORMS']]

    print(f"\n📋 當前配置的平台（共 {len(platform_configs)} 個）：")
    for id_val, name in platform_configs:
        marker = "👉" if id_val == "udn" else "  "
        print(f"{marker} {id_val:20s} - {name}")

    # 僅爬取 UDN
    print(f"\n📡 測試爬取 UDN...")
    results, id_to_name, failed_ids = fetcher.crawl_websites([("udn", "UDN 聯合新聞網")])

    if "udn" in results:
        print(f"✅ UDN 爬取成功（{len(results['udn'])} 條新聞）")
        return True
    else:
        print("❌ UDN 爬取失敗")
        if failed_ids:
            print(f"   失敗的平台: {failed_ids}")
        return False


def test_udn_data_format():
    """測試數據格式兼容性"""
    print("=" * 80)
    print("測試數據格式兼容性")
    print("=" * 80)
    print()

    fetcher = DataFetcher()
    result, platform_id = fetcher.fetch_udn_news()

    if not result:
        print("❌ 無法獲取數據")
        return False

    # 檢查數據格式
    print("🔍 檢查數據格式...")

    required_keys = ['ranks', 'url', 'mobileUrl']
    format_ok = True

    for title, info in list(result.items())[:3]:
        print(f"\n   新聞: {title[:50]}...")
        for key in required_keys:
            if key in info:
                print(f"   ✅ {key}: {info[key]}")
            else:
                print(f"   ❌ 缺少 {key}")
                format_ok = False

    if format_ok:
        print("\n✅ 數據格式符合要求")
    else:
        print("\n❌ 數據格式不符合要求")

    return format_ok


def main():
    """主測試流程"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "UDN 新聞爬取測試套件" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    tests = [
        ("基本功能測試", test_udn_basic),
        ("數據格式測試", test_udn_data_format),
        ("系統整合測試", test_udn_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n❌ 測試出錯: {e}")
            results[test_name] = False

        print()

    # 總結
    print("=" * 80)
    print("測試總結")
    print("=" * 80)
    print()

    for test_name, success in results.items():
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"{status:8s} - {test_name}")

    print()

    all_passed = all(results.values())
    if all_passed:
        print("🎉 所有測試通過！UDN 整合成功！")
    else:
        failed_count = sum(1 for v in results.values() if not v)
        print(f"⚠️  有 {failed_count} 個測試失敗，請檢查上述錯誤信息")

    print()

    return all_passed


if __name__ == "__main__":
    main()
