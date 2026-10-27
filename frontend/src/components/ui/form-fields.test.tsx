import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  NumberField,
  SelectField,
  TextAreaField,
  TextField,
} from "./form-fields";

/*
 * These assert the accessibility wiring, not the styling.
 *
 * An error message that is visually next to an input but not associated with
 * it is invisible to a screen reader, and a farmer using one would be told a
 * form failed without being told which box to fix. The links between label,
 * hint, error and control are the part that has to keep working.
 */

describe("TextField", () => {
  it("links the label to the control", () => {
    render(<TextField label="Farm name" />);
    expect(screen.getByLabelText(/Farm name/)).toBeInTheDocument();
  });

  it("associates the hint with the control", () => {
    render(<TextField label="Area" hint="In hectares." />);
    const input = screen.getByLabelText(/Area/);
    const describedBy = input.getAttribute("aria-describedby");
    expect(describedBy).toBeTruthy();
    expect(document.getElementById(describedBy!.split(" ")[0])).toHaveTextContent(
      "In hectares.",
    );
  });

  it("marks the control invalid and describes it when there is an error", () => {
    render(<TextField label="Area" error="Area must be greater than zero." />);
    const input = screen.getByLabelText(/Area/);
    expect(input).toHaveAttribute("aria-invalid", "true");

    const message = screen.getByRole("alert");
    expect(message).toHaveTextContent("Area must be greater than zero.");
    expect(input.getAttribute("aria-describedby")).toContain(message.id);
  });

  it("announces the error, so it is not only a colour change", () => {
    render(<TextField label="Area" error="Bad" />);
    // role="alert" is what makes a newly appearing message speak.
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("is not marked invalid when there is no error", () => {
    render(<TextField label="Area" />);
    expect(screen.getByLabelText(/Area/)).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows both the hint and the error at once", () => {
    render(<TextField label="Area" hint="In hectares." error="Too small." />);
    const input = screen.getByLabelText(/Area/);
    expect(input.getAttribute("aria-describedby")?.split(" ")).toHaveLength(2);
    expect(screen.getByText("In hectares.")).toBeInTheDocument();
    expect(screen.getByText("Too small.")).toBeInTheDocument();
  });

  it("renders the unit beside the label rather than inside the value", () => {
    render(<TextField label="Area" unit="hectares" />);
    expect(screen.getByText("hectares")).toBeInTheDocument();
  });

  it("gives each field its own ids when several are on a page", () => {
    render(
      <>
        <TextField label="First" error="A" />
        <TextField label="Second" error="B" />
      </>,
    );
    const [first, second] = screen.getAllByRole("alert");
    expect(first.id).not.toBe(second.id);
  });
});

describe("NumberField", () => {
  it("uses a decimal keypad without the spinner behaviour of type=number", () => {
    // type="number" lets a scroll wheel silently change an entered figure,
    // and here that figure is how much water to apply.
    render(<NumberField label="Water applied" />);
    const input = screen.getByLabelText(/Water applied/);
    expect(input).toHaveAttribute("type", "text");
    expect(input).toHaveAttribute("inputmode", "decimal");
  });
});

describe("SelectField", () => {
  it("renders a native select with its options", () => {
    render(
      <SelectField
        label="Crop"
        placeholder="Choose a crop"
        options={[
          { value: "1", label: "Maize" },
          { value: "2", label: "Paddy" },
        ]}
      />,
    );
    const select = screen.getByLabelText(/Crop/);
    expect(select.tagName).toBe("SELECT");
    expect(screen.getByRole("option", { name: "Maize" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Choose a crop" })).toBeInTheDocument();
  });

  it("carries the error wiring through as well", () => {
    render(<SelectField label="Crop" options={[]} error="Choose a crop." />);
    expect(screen.getByLabelText(/Crop/)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("Choose a crop.");
  });
});

describe("TextAreaField", () => {
  it("links the label and reports errors", () => {
    render(<TextAreaField label="Notes" error="Too long." />);
    const area = screen.getByLabelText(/Notes/);
    expect(area.tagName).toBe("TEXTAREA");
    expect(area).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("Too long.");
  });
});
