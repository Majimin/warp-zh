"""翻译引擎：术语表查找 + 批量翻译记忆。"""
from __future__ import annotations

from typing import Optional

from .glossary import Glossary
from .models import TranslationMemory, TranslationStatus, TranslationUnit


class Translator:
    def __init__(self, glossary: Optional[Glossary] = None) -> None:
        self.glossary = glossary or Glossary()

    def translate_unit(self, unit: TranslationUnit) -> bool:
        if unit.status == TranslationStatus.REVIEWED:
            return True
        result = self.glossary.lookup(unit.entry.source_text)
        if result is not None:
            unit.mark_machine(result)
            return True
        return False

    def translate_memory(self, memory: TranslationMemory) -> dict[str, int]:
        translated = skipped = 0
        for unit in memory.units:
            if self.translate_unit(unit):
                translated += 1
            else:
                skipped += 1
        return {"translated": translated, "skipped": skipped, "total": len(memory.units)}
