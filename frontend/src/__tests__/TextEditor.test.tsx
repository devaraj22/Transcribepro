import { useState } from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TextEditor from "../components/ui/TextEditor";

describe("TextEditor Component", () => {
  it("renders with the initial value", () => {
    render(<TextEditor value="Initial transcript text" onChange={() => {}} />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue("Initial transcript text");
  });

  it("calls onChange when text is edited", async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();
    
    function Wrapper() {
      const [val, setVal] = useState("");
      return <TextEditor value={val} onChange={(v) => { setVal(v); handleChange(v); }} />;
    }
    
    render(<Wrapper />);
    const textarea = screen.getByRole("textbox");
    
    await user.type(textarea, "Hello");
    expect(handleChange).toHaveBeenCalledTimes(5);
    expect(handleChange).toHaveBeenLastCalledWith("Hello");
  });

  it("renders with default placeholder if none provided", () => {
    render(<TextEditor value="" onChange={() => {}} />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveAttribute("placeholder", "Your transcript will appear here...");
  });

  it("renders with custom placeholder", () => {
    render(<TextEditor value="" onChange={() => {}} placeholder="Custom placeholder" />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveAttribute("placeholder", "Custom placeholder");
  });
});
