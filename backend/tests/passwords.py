"""
Constante de mot de passe forte, partagée par les tests.

Définie une seule fois et réutilisée partout afin d'éviter de disséminer des
mots de passe faibles dans les fixtures. Choisie pour scorer 4 (le maximum) à
l'échelle zxcvbn (0-4) — donc une marge nette au-dessus du seuil de robustesse
imposé au register par M6 (score >= 3). Cette marge immunise les tests contre
une éventuelle montée future du seuil ou une mise à jour du dictionnaire zxcvbn :
un mot de passe pile sur le seuil (ex. l'ancien « ValidPassword123! », score 3)
virerait au rouge de façon imprévisible.

Contraintes satisfaites : >= 12 caractères, majuscule + minuscule + chiffre +
caractère spécial, aucun mot de dictionnaire.
"""

STRONG_TEST_PASSWORD = "qP4#nZ7!wR2$mD9k"
