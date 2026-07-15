import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProgressBar from "../components/ui/ProgressBar";

describe("ProgressBar Component", () => {
  it("renders correctly when visible", () => {
    render(<ProgressBar percent={50} visible={true} label="Processing..." />);
    
    // Check if progress bar container is present
    const progressTrack = screen.getByRole("progressbar");
    expect(progressTrack).toBeInTheDocument();
    
    // Check ARIA attributes
    expect(progressTrack).toHaveAttribute("aria-valuenow", "50");
    expect(progressTrack).toHaveAttribute("aria-valuemin", "0");
    expect(progressTrack).toHaveAttribute("aria-valuemax", "100");
    
    // Check label text
    expect(screen.getByText("Processing...")).toBeInTheDocument();
  });

  it("does not render when visible is false", () => {
    const { container } = render(<ProgressBar percent={50} visible={false} />);
    expect(container.firstChild).toBeNull();
  });

  it("defaults label to percentage if not provided", () => {
    render(<ProgressBar percent={75.5} visible={true} />);
    // Should round 75.5 to 76
    expect(screen.getByText("76%")).toBeInTheDocument();
  });

  it("renders the fill with correct width", () => {
    const { container } = render(<ProgressBar percent={30} visible={true} />);
    const fill = container.querySelector(".progress-fill");
    expect(fill).toBeInTheDocument();
    expect(fill).toHaveStyle("width: 30%");
  });
});
