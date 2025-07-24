import { render, fireEvent, screen, waitFor } from "@testing-library/react";
import { Form, FormItem, useFormContext, ValidationRule } from "./Form";
import React from "react";

// Test input component that integrates with form
const TestInput: React.FC<{
  name: string;
  placeholder?: string;
  type?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  value?: string;
}> = ({
  name,
  placeholder,
  type = "text",
  onChange,
  onBlur,
  value: propValue,
}) => {
  const { formApi } = useFormContext();
  const value = propValue ?? formApi.getFieldValue(name) ?? "";

  return (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={(e) => {
        formApi.setFieldValue(name, e.target.value);
        onChange?.(e);
      }}
      onBlur={onBlur}
      className="border border-gray-300 rounded px-3 py-2 w-full"
    />
  );
};

describe("Form", () => {
  it("renders form with initial values", () => {
    const initialValues = { name: "John Doe", email: "john@example.com" };

    render(
      <Form initialValues={initialValues} onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
        <FormItem name="email" label="Email">
          <TestInput name="email" />
        </FormItem>
      </Form>,
    );

    expect(screen.getByDisplayValue("John Doe")).toBeInTheDocument();
    expect(screen.getByDisplayValue("john@example.com")).toBeInTheDocument();
  });

  it("handles form submission", async () => {
    const onSubmit = jest.fn();
    const initialValues = { name: "John", email: "john@test.com" };

    render(
      <Form initialValues={initialValues} onSubmit={onSubmit}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
        <FormItem name="email" label="Email">
          <TestInput name="email" />
        </FormItem>
        <button type="submit">Submit</button>
      </Form>,
    );

    fireEvent.click(screen.getByText("Submit"));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        { name: "John", email: "john@test.com" },
        expect.any(Object),
      );
    });
  });

  it("validates required fields", async () => {
    const validationRules = {
      name: [{ required: true }] as ValidationRule[],
      email: [{ required: "Email is required" }] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
        <FormItem name="email" label="Email">
          <TestInput name="email" />
        </FormItem>
        <button type="submit">Submit</button>
      </Form>,
    );

    fireEvent.click(screen.getByText("Submit"));

    await waitFor(() => {
      expect(screen.getByText("name is required")).toBeInTheDocument();
      expect(screen.getByText("Email is required")).toBeInTheDocument();
    });
  });

  it("validates field on change", async () => {
    const validationRules = {
      email: [
        {
          pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
          required: true,
        },
      ] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <FormItem name="email" label="Email">
          <TestInput name="email" />
        </FormItem>
      </Form>,
    );

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "invalid-email" } });

    await waitFor(() => {
      expect(screen.getByText("email format is invalid")).toBeInTheDocument();
    });
  });

  it("validates field on blur", async () => {
    const validationRules = {
      name: [{ required: true }] as ValidationRule[],
    };

    render(
      <Form
        validationRules={validationRules}
        validateOnChange={false}
        onSubmit={jest.fn()}
      >
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const input = screen.getByRole("textbox");
    fireEvent.focus(input);
    fireEvent.blur(input);

    await waitFor(() => {
      expect(screen.getByText("name is required")).toBeInTheDocument();
    });
  });

  it("validates min and max length", async () => {
    const validationRules = {
      password: [{ min: 6, max: 20 }] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <FormItem name="password" label="Password">
          <TestInput name="password" type="password" />
        </FormItem>
      </Form>,
    );

    const input = screen.getByRole("textbox");

    // Test min length
    fireEvent.change(input, { target: { value: "123" } });
    await waitFor(() => {
      expect(
        screen.getByText("password must be at least 6 characters"),
      ).toBeInTheDocument();
    });

    // Test max length
    fireEvent.change(input, { target: { value: "123456789012345678901" } });
    await waitFor(() => {
      expect(
        screen.getByText("password must be at most 20 characters"),
      ).toBeInTheDocument();
    });
  });

  it("validates with custom validation function", async () => {
    const validationRules = {
      username: [
        {
          validate: (value: string) => {
            if (value === "admin") return "Username cannot be admin";
            return undefined;
          },
        },
      ] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <FormItem name="username" label="Username">
          <TestInput name="username" />
        </FormItem>
      </Form>,
    );

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "admin" } });

    await waitFor(() => {
      expect(screen.getByText("Username cannot be admin")).toBeInTheDocument();
    });
  });

  it("displays required mark for required fields", () => {
    const validationRules = {
      name: [{ required: true }] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("handles horizontal layout", () => {
    render(
      <Form layout="horizontal" onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const formItem = screen.getByText("Name").closest("div");
    expect(formItem).toHaveClass("flex", "items-start", "gap-4");
  });

  it("handles inline layout", () => {
    render(
      <Form layout="inline" onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const form = screen.getByRole("form");
    expect(form).toHaveClass("flex", "flex-wrap", "items-start", "gap-4");
  });

  it("applies size classes", () => {
    render(
      <Form size="lg" onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const form = screen.getByRole("form");
    expect(form).toHaveClass("text-base");
  });

  it("handles disabled state", () => {
    render(
      <Form disabled onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const form = screen.getByRole("form");
    expect(form).toHaveClass("opacity-50", "pointer-events-none");
  });

  it("calls onValuesChange when field value changes", () => {
    const onValuesChange = jest.fn();

    render(
      <Form onSubmit={jest.fn()} onValuesChange={onValuesChange}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "John" } });

    expect(onValuesChange).toHaveBeenCalledWith(
      { name: "John" },
      { name: "John" },
    );
  });

  it("resets fields", () => {
    const TestFormWithReset = () => {
      const { formApi } = useFormContext();
      return (
        <div>
          <FormItem name="name" label="Name">
            <TestInput name="name" />
          </FormItem>
          <button type="button" onClick={() => formApi.resetFields()}>
            Reset
          </button>
        </div>
      );
    };

    render(
      <Form initialValues={{ name: "John" }} onSubmit={jest.fn()}>
        <TestFormWithReset />
      </Form>,
    );

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "Jane" } });
    expect(screen.getByDisplayValue("Jane")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Reset"));
    expect(input).toHaveValue("");
  });

  it("validates specific fields", async () => {
    const validationRules = {
      name: [{ required: true }] as ValidationRule[],
      email: [{ required: true }] as ValidationRule[],
    };

    const TestFormWithValidation = () => {
      const { formApi } = useFormContext();
      return (
        <div>
          <FormItem name="name" label="Name">
            <TestInput name="name" />
          </FormItem>
          <FormItem name="email" label="Email">
            <TestInput name="email" />
          </FormItem>
          <button
            type="button"
            onClick={() => formApi.validateFields(["name"])}
          >
            Validate Name Only
          </button>
        </div>
      );
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <TestFormWithValidation />
      </Form>,
    );

    fireEvent.click(screen.getByText("Validate Name Only"));

    await waitFor(() => {
      expect(screen.getByText("name is required")).toBeInTheDocument();
      expect(screen.queryByText("email is required")).not.toBeInTheDocument();
    });
  });

  it("displays help text", () => {
    render(
      <Form onSubmit={jest.fn()}>
        <FormItem
          name="password"
          label="Password"
          help="Password must be at least 8 characters"
        >
          <TestInput name="password" type="password" />
        </FormItem>
      </Form>,
    );

    expect(
      screen.getByText("Password must be at least 8 characters"),
    ).toBeInTheDocument();
  });

  it("hides help text when there is an error", async () => {
    const validationRules = {
      password: [{ required: true }] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <FormItem
          name="password"
          label="Password"
          help="Password must be at least 8 characters"
        >
          <TestInput name="password" type="password" />
        </FormItem>
        <button type="submit">Submit</button>
      </Form>,
    );

    fireEvent.click(screen.getByText("Submit"));

    await waitFor(() => {
      expect(screen.getByText("password is required")).toBeInTheDocument();
      expect(
        screen.queryByText("Password must be at least 8 characters"),
      ).not.toBeInTheDocument();
    });
  });

  it("applies custom className", () => {
    render(
      <Form className="custom-form" onSubmit={jest.fn()}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const form = screen.getByRole("form");
    expect(form).toHaveClass("custom-form");
  });

  it("applies validate status styles", () => {
    render(
      <Form onSubmit={jest.fn()}>
        <FormItem name="name" label="Name" validateStatus="error">
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    const label = screen.getByText("Name:");
    expect(label).toHaveClass("text-red-600");
  });

  it("handles colon display in labels", () => {
    render(
      <Form onSubmit={jest.fn()}>
        <FormItem name="name" label="Name" colon={false}>
          <TestInput name="name" />
        </FormItem>
      </Form>,
    );

    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.queryByText("Name:")).not.toBeInTheDocument();
  });

  it("tracks field touched and dirty state", () => {
    const TestFormState = () => {
      const { formApi } = useFormContext();
      const [touched, setTouched] = React.useState(false);
      const [dirty, setDirty] = React.useState(false);

      return (
        <div>
          <FormItem name="name" label="Name">
            <TestInput
              name="name"
              onBlur={() => setTouched(formApi.isFieldTouched("name"))}
            />
          </FormItem>
          <button
            type="button"
            onClick={() => {
              formApi.setFieldValue("name", "test");
              setDirty(formApi.isFieldDirty("name"));
            }}
          >
            Set Value
          </button>
          <div>Touched: {touched.toString()}</div>
          <div>Dirty: {dirty.toString()}</div>
        </div>
      );
    };

    render(
      <Form onSubmit={jest.fn()}>
        <TestFormState />
      </Form>,
    );

    expect(screen.getByText("Touched: false")).toBeInTheDocument();
    expect(screen.getByText("Dirty: false")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Set Value"));
    expect(screen.getByText("Dirty: true")).toBeInTheDocument();
  });

  it("prevents form submission with validation errors", async () => {
    const onSubmit = jest.fn();
    const validationRules = {
      name: [{ required: true }] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={onSubmit}>
        <FormItem name="name" label="Name">
          <TestInput name="name" />
        </FormItem>
        <button type="submit">Submit</button>
      </Form>,
    );

    fireEvent.click(screen.getByText("Submit"));

    await waitFor(() => {
      expect(screen.getByText("name is required")).toBeInTheDocument();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("handles numeric validation rules", async () => {
    const validationRules = {
      age: [{ min: 18, max: 100 }] as ValidationRule[],
    };

    render(
      <Form validationRules={validationRules} onSubmit={jest.fn()}>
        <FormItem name="age" label="Age">
          <TestInput name="age" type="number" />
        </FormItem>
      </Form>,
    );

    const input = screen.getByRole("spinbutton");

    fireEvent.change(input, { target: { value: "16" } });
    await waitFor(() => {
      expect(screen.getByText("age must be at least 18")).toBeInTheDocument();
    });

    fireEvent.change(input, { target: { value: "101" } });
    await waitFor(() => {
      expect(screen.getByText("age must be at most 100")).toBeInTheDocument();
    });
  });
});
