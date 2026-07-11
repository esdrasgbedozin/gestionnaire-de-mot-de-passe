import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import PasswordForm from "./PasswordForm";

// Régression critique-P2 : la barre de force calculait sa largeur sur un champ
// `level` que le moteur ne renvoie pas -> `width: NaN%` -> barre jamais remplie
// sur l'écran d'ajout/édition. Ces tests verrouillent une largeur en pourcent
// valide (jamais NaN) et l'absence de barre à vide.
describe("PasswordForm — strength meter width", () => {
  const noop = () => {};

  test("bar width is a valid percent (never NaN%) for a strong password", () => {
    render(<PasswordForm onSave={noop} onCancel={noop} />);
    const input = screen.getByPlaceholderText("Enter a secure password");
    fireEvent.change(input, {
      target: { value: "C0rrect-Horse-Battery9!" },
    });

    const bar = screen.getByTestId("password-strength-bar");
    const width = bar.style.width;

    expect(width).toMatch(/^\d+%$/); // e.g. "100%" — jamais "NaN%"
    expect(width).not.toBe("NaN%");
    expect(width).not.toBe("0%"); // mot de passe fort => remplissage non nul
  });

  test("no strength bar is rendered when the password field is empty", () => {
    render(<PasswordForm onSave={noop} onCancel={noop} />);
    expect(screen.queryByTestId("password-strength-bar")).toBeNull();
  });
});
