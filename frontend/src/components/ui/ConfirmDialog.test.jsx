import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import ConfirmDialog from "./ConfirmDialog";

// Critique-P2 (a11y, WCAG 2.4.3) : une modale destructive doit piéger le focus
// (Tab/Shift+Tab bouclent) et offrir une sortie Esc.
describe("ConfirmDialog — focus trap & escape", () => {
  const noop = () => {};

  const setup = (props = {}) =>
    render(
      <ConfirmDialog
        open
        title="Delete?"
        message="This can't be undone."
        variant="danger"
        onCancel={noop}
        onConfirm={noop}
        {...props}
      />,
    );

  test("Tab from the last focusable wraps to the first", () => {
    setup();
    const buttons = screen.getAllByRole("button");
    const last = buttons[buttons.length - 1];
    last.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(buttons[0]);
  });

  test("Shift+Tab from the first focusable wraps to the last", () => {
    setup();
    const buttons = screen.getAllByRole("button");
    const last = buttons[buttons.length - 1];
    buttons[0].focus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(last);
  });

  test("Escape triggers onCancel", () => {
    const onCancel = jest.fn();
    setup({ onCancel });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
