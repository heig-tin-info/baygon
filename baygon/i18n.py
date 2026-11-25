"""Language of the messages shown when a test fails.

The messages are written in English, which is also the key of their
translation. The ``lang`` key of the configuration chooses the language:

>>> set_language("fr")
>>> tr("Invalid exit status: expected {expected}, got {found}.", expected=2, found=1)
'Code de sortie incorrect : 2 attendu, 1 obtenu.'
>>> tr("A text without translation.")
'A text without translation.'
>>> set_language("en")
>>> tr("Invalid exit status: expected {expected}, got {found}.", expected=2, found=1)
'Invalid exit status: expected 2, got 1.'
"""

from __future__ import annotations

from typing import Any

#: Languages of the messages.
LANGUAGES = ("en", "fr")

FRENCH = {
    # Outputs
    "Output {stream} differs from the expected output on line {line}:": (
        "La sortie {stream} diffère de la sortie attendue à la ligne {line} :"
    ),
    "expected: ": "attendu : ",
    "found:    ": "obtenu :  ",
    "(end of output)": "(fin de la sortie)",
    "(empty output)": "(sortie vide)",
    "(empty)": "(vide)",
    "Output {stream} has the expected lines, but {reason}.": (
        "La sortie {stream} a les lignes attendues, mais {reason}."
    ),
    "the newline at the end is missing": "il manque le retour à la ligne final",
    "there is an extra newline at the end": (
        "il y a un retour à la ligne en trop à la fin"
    ),
    "the line endings differ": "les fins de ligne diffèrent",
    'Expected value "{expected}" on {stream}, but got "{found}" instead.': (
        'Valeur "{expected}" attendue sur {stream}, mais "{found}" obtenue.'
    ),
    "Output {found} does not equal '{expected}' on {stream}.": (
        "La sortie {stream} {found} ne vaut pas '{expected}'."
    ),
    "Output {found} should not equal '{expected}' on {stream}.": (
        "La sortie {stream} {found} ne devrait pas valoir '{expected}'."
    ),
    'Output {stream} does not contain {expected}. Found "{found}" instead.': (
        'La sortie {stream} ne contient pas {expected}. Obtenu : "{found}".'
    ),
    'Output {stream} should not contain {expected}. Found "{found}".': (
        'La sortie {stream} ne devrait pas contenir {expected}. Obtenu : "{found}".'
    ),
    'Output {stream} does not match /{pattern}/ on "{found}".': (
        'La sortie {stream} ne correspond pas à /{pattern}/ : "{found}".'
    ),
    'Output {stream} should not match /{pattern}/ on "{found}".': (
        'La sortie {stream} ne devrait pas correspondre à /{pattern}/ : "{found}".'
    ),
    "Output {stream} {found} differs from the reference {reference}: {expected}.": (
        "La sortie {stream} {found} diffère de celle de la référence "
        "{reference} : {expected}."
    ),
    # Numbers and counts
    "Output {stream} is {found}, expected {expected}.": (
        "La sortie {stream} vaut {found}, {expected} attendu."
    ),
    "Output {stream} is {found}, it should not be {expected}.": (
        "La sortie {stream} vaut {found}, elle ne devrait pas valoir {expected}."
    ),
    'Output {stream} is not a number: "{found}" (expected {expected}).': (
        'La sortie {stream} n\'est pas un nombre : "{found}" ({expected} attendu).'
    ),
    "Output {stream} has {count} {unit}, expected {expected}.": (
        "La sortie {stream} a {count} {unit}, {expected} attendu."
    ),
    "Output {stream} has {count} {unit}, it should not have {expected}.": (
        "La sortie {stream} a {count} {unit}, elle ne devrait pas en avoir {expected}."
    ),
    "characters": "caractères",
    "lines": "lignes",
    "exactly {value}": "exactement {value}",
    "between {min} and {max}": "entre {min} et {max}",
    "at least {min}": "au moins {min}",
    "at most {max}": "au plus {max}",
    # Program
    "Invalid exit status: expected {expected}, got {found}.": (
        "Code de sortie incorrect : {expected} attendu, {found} obtenu."
    ),
    "Timeout after {seconds:g} s.": (
        "Le programme ne s'est pas terminé en {seconds:g} s."
    ),
    "Output limit exceeded (more than {limit} bytes), the program was killed.": (
        "Sortie trop longue (plus de {limit} octets), le programme a été arrêté."
    ),
    "Unable to execute {program}: {error}": "Impossible d'exécuter {program} : {error}",
    "Program {program} was not found. Was it compiled?": (
        "Le programme {program} est introuvable. A-t-il bien été compilé ?"
    ),
    "Program {program} cannot be run: {error}": (
        "Le programme {program} ne peut pas être lancé : {error}"
    ),
    "{program} failed: {reason}.": "{program} a échoué : {reason}.",
    "Invalid test: {error}": "Test invalide : {error}",
    # Report
    "Test {id}: {name}": "Test {id} : {name}",
    "PASSED": "RÉUSSI",
    "FAILED": "ÉCHOUÉ",
    "SKIPPED": "IGNORÉ",
    "run {run} of {total}": "essai {run} sur {total}",
    "... ({count} more lines)": "... ({count} lignes de plus)",
    "Ran {total} tests in {seconds:.2f} s.": "{total} tests exécutés en {seconds:.2f} s.",
    "Points: {earned}/{total}": "Points : {earned}/{total}",
    "{failures} failed, {successes} passed ({ratio}% ok).": (
        "{failures} échoué(s), {successes} réussi(s) ({ratio} % ok)."
    ),
    "fail.": "échec.",
    "ok.": "ok.",
    "{count} test(s) skipped, some executables may be missing.": (
        "{count} test(s) ignoré(s), des exécutables manquent peut-être."
    ),
    "Using configuration file: {path}": "Fichier de configuration : {path}",
}

_TRANSLATIONS = {"fr": FRENCH}
_language = "en"


def set_language(language: str | None) -> None:
    """Choose the language of the messages (``None`` is English).

    >>> set_language("de")
    Traceback (most recent call last):
    ...
    ValueError: Unknown language 'de', expected one of: en, fr.
    """
    global _language
    language = language or "en"
    if language not in LANGUAGES:
        raise ValueError(
            f"Unknown language '{language}', expected one of: {', '.join(LANGUAGES)}."
        )
    _language = language


def get_language() -> str:
    """Return the language of the messages."""
    return _language


def tr(text: str, **values: Any) -> str:
    """Translate ``text`` in the chosen language, then fill its ``{values}``."""
    text = _TRANSLATIONS.get(_language, {}).get(text, text)
    return text.format(**values) if values else text
