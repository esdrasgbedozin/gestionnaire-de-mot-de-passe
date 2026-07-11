import React from "react";

/**
 * Primitif Card UNIQUE (critique P2 : avant, rounded-lg / rounded-xl / rounded-2xl
 * cohabitaient d'un écran à l'autre). Un seul rayon, une seule élévation.
 */
const Card = ({ as: Tag = "div", className = "", children, ...props }) => (
  <Tag
    className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm ${className}`}
    {...props}
  >
    {children}
  </Tag>
);

export default Card;
