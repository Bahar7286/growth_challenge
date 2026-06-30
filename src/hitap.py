from __future__ import annotations

import re

KADIN_ISIMLERI = {
    "gülbahar", "elif", "eylül", "sevda", "nazan", "ayten", "sinem", "özgen", "zeynep", "ezgi",
    "birgül", "banu", "gülşah", "duygu", "merve", "büşra", "fatma", "ayşe", "emine", "hatice",
    "aslı", "burcu", "ceren", "deniz", "eda", "gamze", "hazal", "irem", "kübra", "melis",
    "özlem", "pınar", "selin", "tuğba", "yağmur", "yasemin", "gaye", "hande", "didem", "gözde",
    "nihal", "nursen", "şefaat", "sevgi", "tuğçe", "hilal", "aslıhan", "gül", "çiğdem", "esra",
    "pervin", "latife", "ceren", "leyla", "ferda", "müzeyyen", "betül", "yeliz", "şule", "bahar",
    "gizem", "arzu", "şahika", "meral", "inci", "müzeyyen", "latife", "tuğçe", "gökçe", "lale",
}

ERKEK_ISIMLERI = {
    "savaş", "veysel", "berkan", "burak", "recep", "orhan", "onur", "serdal", "ahmet", "mehmet",
    "ali", "mustafa", "can", "cem", "gökhan", "hakan", "volkan", "murat", "fatih", "ibrahim",
    "tarık", "kaan", "kerem", "yiğit", "emre", "ozan", "eren", "batu", "ata", "efe", "arda",
    "aşır", "mesut", "mehmet", "ilker", "çağrı", "onur", "serdal", "türkan",
}


def detect_hitap(first_name: str) -> str:
    name_lower = first_name.lower()
    if name_lower in KADIN_ISIMLERI:
        return "Hanım"
    if name_lower in ERKEK_ISIMLERI:
        return "Bey"
    if name_lower[-1] in ["a", "e", "i", "o", "ö", "u", "ü"]:
        return "Hanım"
    return "Bey"


def apply_hitap(first_name: str, message: str) -> str:
    """Ensure greeting uses 'Ad Hanım' or 'Ad Bey' (e.g. Elif Hanım, Ahmet Bey)."""
    if not message or not first_name:
        return message

    hitap = detect_hitap(first_name)
    correct = f"{first_name} {hitap}"
    escaped = re.escape(first_name)

    if re.search(rf"\b{escaped}\s+(Hanım|Hanim|Bey)\b", message, re.IGNORECASE):
        return re.sub(
            rf"\b{escaped}\s+(Hanım|Hanim|Bey)\b",
            correct,
            message,
            count=1,
            flags=re.IGNORECASE,
        )

    updated = re.sub(
        rf"(Merhaba\s+){escaped}(\s|,)",
        rf"\1{correct}\2",
        message,
        count=1,
        flags=re.IGNORECASE,
    )
    if updated != message:
        return updated

    return re.sub(
        rf"\b{escaped}\b",
        correct,
        message,
        count=1,
        flags=re.IGNORECASE,
    )
