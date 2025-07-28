/**
 * セッション設定コンポーネントのテスト
 * Phase 3: Validation - 失敗するテストを先に作成
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { SessionSettings } from "../SessionSettings";

describe("SessionSettings", () => {
  const mockOnSave = vi.fn();
  const mockSettings = {
    session_timeout_hours: 8,
    idle_timeout_minutes: 30,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("レンダリング", () => {
    it("現在の設定値が表示される", () => {
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const sessionTimeoutInput =
        screen.getByLabelText("セッションタイムアウト（時間）");
      const idleTimeoutInput =
        screen.getByLabelText("アイドルタイムアウト（分）");

      expect(sessionTimeoutInput).toHaveValue(8);
      expect(idleTimeoutInput).toHaveValue(30);
    });

    it("スライダーと数値入力の両方が表示される", () => {
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      // スライダー
      const sessionSlider = screen.getByRole("slider", {
        name: "セッションタイムアウト（時間）",
      });
      const idleSlider = screen.getByRole("slider", {
        name: "アイドルタイムアウト（分）",
      });

      expect(sessionSlider).toBeInTheDocument();
      expect(idleSlider).toBeInTheDocument();

      // 数値入力
      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });
      const idleInput = screen.getByRole("spinbutton", {
        name: "アイドルタイムアウト（分）",
      });

      expect(sessionInput).toBeInTheDocument();
      expect(idleInput).toBeInTheDocument();
    });

    it("保存ボタンが表示される", () => {
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      expect(
        screen.getByRole("button", { name: "設定を保存" }),
      ).toBeInTheDocument();
    });

    it("設定範囲の説明が表示される", () => {
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      expect(
        screen.getByText("1〜24時間の範囲で設定できます"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("15〜120分の範囲で設定できます"),
      ).toBeInTheDocument();
    });
  });

  describe("入力操作", () => {
    it("スライダーで値を変更できる", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const sessionSlider = screen.getByRole("slider", {
        name: "セッションタイムアウト（時間）",
      });
      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });

      // スライダーを動かす
      fireEvent.change(sessionSlider, { target: { value: "4" } });

      await waitFor(() => {
        expect(sessionInput).toHaveValue(4);
      });
    });

    it("数値入力で値を変更できる", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const idleInput = screen.getByRole("spinbutton", {
        name: "アイドルタイムアウト（分）",
      });
      const idleSlider = screen.getByRole("slider", {
        name: "アイドルタイムアウト（分）",
      });

      await user.clear(idleInput);
      await user.type(idleInput, "60");

      await waitFor(() => {
        expect(idleSlider).toHaveValue("60");
      });
    });

    it("変更後に元の値と異なる場合のみ保存ボタンが有効になる", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const saveButton = screen.getByRole("button", { name: "設定を保存" });
      expect(saveButton).toBeDisabled();

      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });
      await user.clear(sessionInput);
      await user.type(sessionInput, "4");

      expect(saveButton).toBeEnabled();
    });
  });

  describe("バリデーション", () => {
    it("セッションタイムアウトの範囲外の値でエラーが表示される", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });

      // 最小値未満
      await user.clear(sessionInput);
      await user.type(sessionInput, "0");
      await user.tab();

      expect(
        await screen.findByText("1時間以上を設定してください"),
      ).toBeInTheDocument();

      // 最大値超過
      await user.clear(sessionInput);
      await user.type(sessionInput, "25");
      await user.tab();

      expect(
        await screen.findByText("24時間以下を設定してください"),
      ).toBeInTheDocument();
    });

    it("アイドルタイムアウトの範囲外の値でエラーが表示される", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const idleInput = screen.getByRole("spinbutton", {
        name: "アイドルタイムアウト（分）",
      });

      // 最小値未満
      await user.clear(idleInput);
      await user.type(idleInput, "10");
      await user.tab();

      expect(
        await screen.findByText("15分以上を設定してください"),
      ).toBeInTheDocument();

      // 最大値超過
      await user.clear(idleInput);
      await user.type(idleInput, "121");
      await user.tab();

      expect(
        await screen.findByText("120分以下を設定してください"),
      ).toBeInTheDocument();
    });

    it("エラーがある場合は保存ボタンが無効になる", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });
      const saveButton = screen.getByRole("button", { name: "設定を保存" });

      await user.clear(sessionInput);
      await user.type(sessionInput, "0");
      await user.tab();

      expect(saveButton).toBeDisabled();
    });
  });

  describe("保存処理", () => {
    it("有効な値で保存すると onSave が呼ばれる", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });
      const idleInput = screen.getByRole("spinbutton", {
        name: "アイドルタイムアウト（分）",
      });
      const saveButton = screen.getByRole("button", { name: "設定を保存" });

      await user.clear(sessionInput);
      await user.type(sessionInput, "4");
      await user.clear(idleInput);
      await user.type(idleInput, "60");

      await user.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith({
        session_timeout_hours: 4,
        idle_timeout_minutes: 60,
      });
    });

    it("保存中は入力とボタンが無効化される", () => {
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={true}
        />,
      );

      expect(
        screen.getByRole("spinbutton", {
          name: "セッションタイムアウト（時間）",
        }),
      ).toBeDisabled();
      expect(
        screen.getByRole("spinbutton", { name: "アイドルタイムアウト（分）" }),
      ).toBeDisabled();
      expect(
        screen.getByRole("slider", { name: "セッションタイムアウト（時間）" }),
      ).toBeDisabled();
      expect(
        screen.getByRole("slider", { name: "アイドルタイムアウト（分）" }),
      ).toBeDisabled();
      expect(screen.getByRole("button", { name: "設定を保存" })).toBeDisabled();
    });
  });

  describe("プリセット", () => {
    it("よく使う設定のプリセットボタンが表示される", () => {
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      expect(
        screen.getByRole("button", { name: "短時間（2時間）" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "標準（8時間）" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "長時間（24時間）" }),
      ).toBeInTheDocument();
    });

    it("プリセットボタンクリックで値が設定される", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const shortPreset = screen.getByRole("button", {
        name: "短時間（2時間）",
      });
      await user.click(shortPreset);

      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });
      expect(sessionInput).toHaveValue(2);
    });
  });

  describe("警告表示", () => {
    it("短いセッション時間を設定すると警告が表示される", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });
      await user.clear(sessionInput);
      await user.type(sessionInput, "1");

      expect(
        await screen.findByText(
          /短いセッション時間は頻繁な再ログインが必要になります/,
        ),
      ).toBeInTheDocument();
    });

    it("長いセッション時間を設定するとセキュリティ警告が表示される", async () => {
      const user = userEvent.setup();
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      const sessionInput = screen.getByRole("spinbutton", {
        name: "セッションタイムアウト（時間）",
      });
      await user.clear(sessionInput);
      await user.type(sessionInput, "24");

      expect(
        await screen.findByText(
          /長いセッション時間はセキュリティリスクが高まります/,
        ),
      ).toBeInTheDocument();
    });
  });

  describe("次回ログイン時の説明", () => {
    it("設定変更が次回ログインから適用される旨が表示される", () => {
      render(
        <SessionSettings
          settings={mockSettings}
          onSave={mockOnSave}
          isLoading={false}
        />,
      );

      expect(
        screen.getByText(/この設定は次回ログイン時から適用されます/),
      ).toBeInTheDocument();
    });
  });
});
