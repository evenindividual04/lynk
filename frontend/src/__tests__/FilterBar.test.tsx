import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import FilterBar, { type Filters } from "../components/FilterBar";
import { MemoryRouter } from "react-router-dom";

const DEFAULT_FILTERS: Filters = {
  q: "",
  company: "",
  stage: "",
  tag: "",
  connected_from: "",
  connected_to: "",
  sort: "created_at",
};

function setup(overrides: Partial<Filters> = {}) {
  const filters = { ...DEFAULT_FILTERS, ...overrides };
  const onChange = vi.fn();
  render(
    <MemoryRouter>
      <FilterBar filters={filters} onChange={onChange} />
    </MemoryRouter>,
  );
  return { onChange };
}

describe("FilterBar", () => {
  it("renders search input", () => {
    setup();
    expect(screen.getByPlaceholderText(/search name/i)).toBeInTheDocument();
  });

  it("calls onChange when search text changes", () => {
    const { onChange } = setup();
    fireEvent.change(screen.getByLabelText("Search"), {
      target: { value: "Alice" },
    });
    expect(onChange).toHaveBeenCalledWith({ q: "Alice" });
  });

  it("calls onChange when stage changes", () => {
    const { onChange } = setup();
    fireEvent.change(screen.getByLabelText("Stage"), {
      target: { value: "replied" },
    });
    expect(onChange).toHaveBeenCalledWith({ stage: "replied" });
  });

  it("shows current filter values", () => {
    setup({ q: "Bob", company: "Acme" });
    expect(screen.getByDisplayValue("Bob")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Acme")).toBeInTheDocument();
  });
});
