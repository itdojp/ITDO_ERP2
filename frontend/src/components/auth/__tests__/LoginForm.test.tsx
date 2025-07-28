import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { LoginForm } from "../LoginForm";

// Mock the useAuth hook
vi.mock("../../../hooks/useAuth", () => ({
  useAuth: () => ({
    login: vi.fn().mockResolvedValue({ access_token: "test-token" }),
    loginWithGoogle: vi.fn(),
  }),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("LoginForm", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  const renderLoginForm = () => {
    return render(
      <BrowserRouter>
        <LoginForm />
      </BrowserRouter>,
    );
  };

  it("renders login form with all fields", () => {
    renderLoginForm();

    expect(screen.getByLabelText("メールアドレス")).toBeInTheDocument();
    expect(screen.getByLabelText("パスワード")).toBeInTheDocument();
    expect(screen.getByLabelText("ログイン状態を保持")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "ログイン" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Googleでログイン/ }),
    ).toBeInTheDocument();
  });

  it("shows validation errors for empty fields", async () => {
    renderLoginForm();
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    fireEvent.click(submitButton);

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");

    expect(emailInput).toBeInvalid();
    expect(passwordInput).toBeInvalid();
  });

  it("submits form with valid credentials", async () => {
    const user = userEvent.setup();
    renderLoginForm();

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("handles MFA requirement", async () => {
    const { useAuth } = await import("../../../hooks/useAuth");
    (useAuth as any).mockReturnValue({
      login: vi.fn().mockResolvedValue({
        requires_mfa: true,
        mfa_token: "test-mfa-token",
      }),
      loginWithGoogle: vi.fn(),
    });

    const user = userEvent.setup();
    renderLoginForm();

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/auth/mfa-verify", {
        state: { mfaToken: "test-mfa-token", email: "test@example.com" },
      });
    });
  });

  it("displays error message on login failure", async () => {
    const { useAuth } = await import("../../../hooks/useAuth");
    (useAuth as any).mockReturnValue({
      login: vi.fn().mockRejectedValue(new Error("Invalid credentials")),
      loginWithGoogle: vi.fn(),
    });

    const user = userEvent.setup();
    renderLoginForm();

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "wrongpassword");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("toggles remember me checkbox", async () => {
    const user = userEvent.setup();
    renderLoginForm();

    const rememberMeCheckbox = screen.getByLabelText("ログイン状態を保持");

    expect(rememberMeCheckbox).not.toBeChecked();

    await user.click(rememberMeCheckbox);
    expect(rememberMeCheckbox).toBeChecked();

    await user.click(rememberMeCheckbox);
    expect(rememberMeCheckbox).not.toBeChecked();
  });

  it("navigates to forgot password page", () => {
    renderLoginForm();

    const forgotPasswordLink = screen.getByText("パスワードを忘れた方");
    expect(forgotPasswordLink).toHaveAttribute("href", "/auth/forgot-password");
  });

  it("navigates to registration page", () => {
    renderLoginForm();

    const registerLink = screen.getByText("新規アカウントを作成");
    expect(registerLink).toHaveAttribute("href", "/auth/register");
  });

  it("disables submit button while loading", async () => {
    const user = userEvent.setup();
    renderLoginForm();

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    expect(
      screen.getByRole("button", { name: "ログイン中..." }),
    ).toBeDisabled();
  });
});
