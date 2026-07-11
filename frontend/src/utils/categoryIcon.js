import {
  UserIcon,
  BriefcaseIcon,
  DevicePhoneMobileIcon,
  BuildingLibraryIcon,
  ShoppingCartIcon,
  KeyIcon,
} from "@heroicons/react/24/outline";

// Mapping catégorie -> icône monochrome (heroicons). Remplace les emoji
// (rendus par l'OS, registre "jouet" incohérent sur un produit de sécurité —
// critique P1) par un jeu d'icônes unique, partagé entre PasswordCard et
// tout autre rendu de catégorie.
const CATEGORY_ICONS = {
  personal: UserIcon,
  work: BriefcaseIcon,
  social: DevicePhoneMobileIcon,
  banking: BuildingLibraryIcon,
  shopping: ShoppingCartIcon,
  other: KeyIcon,
};

export function categoryIcon(category) {
  return CATEGORY_ICONS[category] || KeyIcon;
}
