#!/usr/bin/env python3
"""测试不同平台的下载方式决策。"""

import sys
sys.path.insert(0, "backend")

from core.media import resolve_download_method

# 测试用例
test_cases = [
    {
        "platform": "抖音",
        "url": "https://v.douyin.com/iRNBho6V/",
        "format_id": "best",
        "expected_method": "direct",
    },
    {
        "platform": "B站（假设）",
        "url": "https://www.bilibili.com/video/BV1xx411c7mD",
        "format_id": "best",
        "expected_method": "stream",
    },
]

print("=" * 60)
print("下载方式决策测试")
print("=" * 60)

for case in test_cases:
    print(f"\n平台：{case['platform']}")
    print(f"URL：{case['url']}")

    try:
        result = resolve_download_method(case["url"], case["format_id"])
        method = result["method"]
        platform = result.get("platform", "未知")

        print(f"✓ 决策结果：{method}")
        print(f"  平台识别：{platform}")

        if method == "direct":
            print(f"  直链地址：{result.get('direct_url', '无')[:80]}...")
        elif method == "stream":
            stream_info = result.get("stream_info", {})
            print(f"  视频地址：{stream_info.get('video_url', '无')[:80]}...")
            print(f"  需要音频：{'是' if stream_info.get('has_audio') else '否'}")
            print(f"  请求头：{list(stream_info.get('headers', {}).keys())}")

        # 检查是否符合预期
        if method == case["expected_method"]:
            print(f"✓ 符合预期（{case['expected_method']}）")
        else:
            print(f"✗ 不符预期！期望 {case['expected_method']}，实际 {method}")

    except Exception as exc:
        print(f"✗ 错误：{exc}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
