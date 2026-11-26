/** Whether a key event lands in a field that takes text, so a shortcut stays out of it. */
export function isEditableElement(element: Element | null): boolean {
  if (!(element instanceof HTMLElement)) {
    return false;
  }

  if (element.isContentEditable) {
    return true;
  }

  return (
    element.closest(
      'input, textarea, select, [contenteditable], [role="textbox"], [role="searchbox"], [role="combobox"]'
    ) !== null
  );
}
