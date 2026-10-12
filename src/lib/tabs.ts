/** Element ids that wire a tab list to its panel for assistive tech. */
export const tabId = (prefix: string, id: string) => `${prefix}-tab-${id}`;
export const tabPanelId = (prefix: string) => `${prefix}-panel`;
