#!/usr/bin/env python3
"""
ERP Business Tests Runner
ERP業務テスト実行スクリプト

48時間以内実装 - ERP業務ロジックテスト実行管理
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class ERPBusinessTestRunner:
    """ERP業務テスト実行管理"""

    def __init__(self):
        self.backend_path = Path(__file__).parent.parent
        self.test_results = {}
        self.start_time = None

    def run_test_suite(self, test_type="all", verbose=False, coverage=False):
        """ERP業務テストスイート実行"""
        self.start_time = time.time()

        print("🚀 ERP業務テストスイート開始")
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        test_suites = {
            "basic": {
                "name": "基本業務ロジックテスト",
                "path": "tests/integration/test_erp_business_logic.py",
                "priority": "high",
            },
            "performance": {
                "name": "業務パフォーマンステスト",
                "path": "tests/integration/test_erp_business_performance.py",
                "priority": "high",
            },
            "security": {
                "name": "業務セキュリティテスト",
                "path": "tests/integration/test_erp_business_security.py",
                "priority": "medium",
            },
            "integration": {
                "name": "完全統合業務テスト",
                "path": "tests/integration/test_erp_business_integration_full.py",
                "priority": "high",
            },
        }

        selected_suites = []
        if test_type == "all":
            selected_suites = list(test_suites.keys())
        elif test_type == "critical":
            selected_suites = [
                k for k, v in test_suites.items() if v["priority"] == "high"
            ]
        elif test_type in test_suites:
            selected_suites = [test_type]
        else:
            print(f"❌ 不明なテスト種別: {test_type}")
            return False

        total_tests = len(selected_suites)
        passed_tests = 0

        for i, suite_key in enumerate(selected_suites, 1):
            suite = test_suites[suite_key]
            print(f"\n📋 [{i}/{total_tests}] {suite['name']} 実行中...")

            result = self._run_pytest(suite["path"], verbose, coverage)
            self.test_results[suite_key] = result

            if result["success"]:
                passed_tests += 1
                print(f"✅ {suite['name']} 成功")
            else:
                print(f"❌ {suite['name']} 失敗")

            print(f"   実行時間: {result['duration']:.2f}秒")
            print(f"   テスト数: {result['total_tests']}")
            print(f"   合格数: {result['passed_tests']}")

            if result["failed_tests"] > 0:
                print(f"   失敗数: {result['failed_tests']}")

        # 最終結果サマリー
        total_duration = time.time() - self.start_time
        success_rate = (passed_tests / total_tests) * 100

        print("\n" + "=" * 60)
        print("🏁 ERP業務テストスイート結果サマリー")
        print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"総実行時間: {total_duration:.2f}秒")
        print(f"実行スイート数: {total_tests}")
        print(f"成功スイート数: {passed_tests}")
        print(f"成功率: {success_rate:.1f}%")

        # 詳細結果
        total_test_count = sum(r["total_tests"] for r in self.test_results.values())
        total_passed = sum(r["passed_tests"] for r in self.test_results.values())
        total_failed = sum(r["failed_tests"] for r in self.test_results.values())

        print("\n📊 テスト統計:")
        print(f"   総テスト数: {total_test_count}")
        print(f"   合格テスト数: {total_passed}")
        print(f"   失敗テスト数: {total_failed}")
        print(
            f"   テスト成功率: {(total_passed / total_test_count * 100) if total_test_count > 0 else 0:.1f}%"
        )

        # 結果保存
        self._save_results()

        # パフォーマンス要件チェック
        self._check_performance_requirements()

        return success_rate >= 80.0  # 80%以上の成功率を要求

    def _run_pytest(self, test_path, verbose=False, coverage=False):
        """pytest実行"""
        start_time = time.time()

        cmd = ["python", "-m", "pytest", test_path]

        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        if coverage:
            cmd.extend(["--cov=app", "--cov-report=term-missing"])

        cmd.extend(
            [
                "--tb=short",
                "--disable-warnings",
                f"--junit-xml=test-results/{Path(test_path).stem}_results.xml",
            ]
        )

        try:
            # テスト結果ディレクトリ作成
            (self.backend_path / "test-results").mkdir(exist_ok=True)

            result = subprocess.run(
                cmd,
                cwd=self.backend_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5分タイムアウト
            )

            duration = time.time() - start_time

            # pytest出力解析
            output_lines = result.stdout.split("\n")
            total_tests = 0
            passed_tests = 0
            failed_tests = 0

            for line in output_lines:
                if "passed" in line and "failed" in line:
                    # "5 failed, 10 passed in 2.34s" 形式
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "failed,":
                            failed_tests = int(parts[i - 1])
                        elif part == "passed":
                            passed_tests = int(parts[i - 1])
                elif "passed in" in line:
                    # "15 passed in 3.45s" 形式
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed":
                            passed_tests = int(parts[i - 1])
                elif "failed in" in line:
                    # "5 failed in 1.23s" 形式
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "failed":
                            failed_tests = int(parts[i - 1])

            total_tests = passed_tests + failed_tests

            return {
                "success": result.returncode == 0,
                "duration": duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "duration": 300.0,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "stdout": "",
                "stderr": "テストがタイムアウトしました",
            }
        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "stdout": "",
                "stderr": f"テスト実行エラー: {str(e)}",
            }

    def _save_results(self):
        """テスト結果保存"""
        results_file = (
            self.backend_path
            / "test-results"
            / f"erp_business_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": time.time() - self.start_time,
            "test_suites": self.test_results,
            "summary": {
                "total_suites": len(self.test_results),
                "passed_suites": len(
                    [r for r in self.test_results.values() if r["success"]]
                ),
                "total_tests": sum(
                    r["total_tests"] for r in self.test_results.values()
                ),
                "passed_tests": sum(
                    r["passed_tests"] for r in self.test_results.values()
                ),
                "failed_tests": sum(
                    r["failed_tests"] for r in self.test_results.values()
                ),
            },
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 テスト結果保存: {results_file}")

    def _check_performance_requirements(self):
        """パフォーマンス要件チェック"""
        print("\n🏎️ パフォーマンス要件チェック:")

        performance_requirements = {
            "商品検索応答時間": {"target": 0.1, "unit": "秒"},
            "在庫更新応答時間": {"target": 0.05, "unit": "秒"},
            "同時ユーザー数": {"target": 100, "unit": "ユーザー"},
            "API応答時間": {"target": 0.2, "unit": "秒"},
        }

        for requirement, spec in performance_requirements.items():
            print(f"   📈 {requirement}: 目標 {spec['target']}{spec['unit']}")

        # パフォーマンステスト結果があれば詳細表示
        if "performance" in self.test_results:
            perf_result = self.test_results["performance"]
            if perf_result["success"]:
                print("   ✅ パフォーマンステスト成功 - 要件を満たしています")
            else:
                print("   ❌ パフォーマンステスト失敗 - 要件改善が必要です")

    def run_continuous_testing(self, interval=60):
        """継続的テスト実行"""
        print(f"🔄 継続的ERP業務テスト開始 (間隔: {interval}秒)")

        test_count = 0
        while True:
            test_count += 1
            print(
                f"\n📅 継続テスト実行 #{test_count} - {datetime.now().strftime('%H:%M:%S')}"
            )

            # クリティカルテストのみ実行
            success = self.run_test_suite("critical", verbose=False, coverage=False)

            if not success:
                print("⚠️ クリティカルテストが失敗しました")

            print(f"💤 {interval}秒待機中...")
            time.sleep(interval)


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="ERP業務テスト実行スクリプト")
    parser.add_argument(
        "--type",
        choices=["all", "critical", "basic", "performance", "security", "integration"],
        default="all",
        help="実行するテスト種別",
    )
    parser.add_argument("--verbose", action="store_true", help="詳細出力")
    parser.add_argument("--coverage", action="store_true", help="カバレッジ測定")
    parser.add_argument(
        "--continuous", type=int, metavar="INTERVAL", help="継続的テスト実行（秒間隔）"
    )

    args = parser.parse_args()

    runner = ERPBusinessTestRunner()

    if args.continuous:
        runner.run_continuous_testing(args.continuous)
    else:
        success = runner.run_test_suite(args.type, args.verbose, args.coverage)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
