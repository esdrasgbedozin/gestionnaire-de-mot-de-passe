import React, { useEffect, useRef } from "react";
import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import Button from "./Button";

/**
 * Modale de confirmation stylée (critique P2 : remplace les window.confirm natifs,
 * hors-marque et sans garde-fou). Esc + clic backdrop = annuler ; focus initial sur
 * "Annuler" (défaut sûr pour une action destructive).
 */
const ConfirmDialog = ({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "primary", // "primary" | "danger"
  onConfirm,
  onCancel,
}) => {
  const cancelRef = useRef(null);
  const dialogRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") {
        onCancel?.();
        return;
      }
      // Piège de focus (WCAG 2.4.3 — critique P2) : Tab/Shift+Tab restent
      // dans la modale. Une action destructive ne doit jamais laisser le
      // focus filer vers le contenu de fond.
      if (e.key === "Tab") {
        const focusables = dialogRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (!focusables || focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    cancelRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={onCancel}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-sm w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-3">
          {variant === "danger" && (
            <ExclamationTriangleIcon
              className="h-6 w-6 text-red-500 flex-shrink-0"
              aria-hidden="true"
            />
          )}
          <div className="flex-1 min-w-0">
            <h3
              id="confirm-title"
              className="text-lg font-semibold text-gray-900 dark:text-white"
            >
              {title}
            </h3>
            {message && (
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {message}
              </p>
            )}
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button ref={cancelRef} variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === "danger" ? "danger" : "primary"}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
