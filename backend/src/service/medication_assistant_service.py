import re
import unicodedata
from typing import Any


NUMBER_WORDS = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9,
    "dez": 10, "onze": 11, "doze": 12, "treze": 13, "quatorze": 14,
    "catorze": 14, "quinze": 15, "dezesseis": 16, "dezessete": 17,
    "dezoito": 18, "dezenove": 19, "vinte": 20, "vinte e um": 21,
    "vinte e uma": 21, "vinte e dois": 22, "vinte e tres": 23,
    "vinte e quatro": 24,
}

UNIT_MAP = {
    "comprimido": "comprimidos", "comprimidos": "comprimidos",
    "capsula": "cápsulas", "capsulas": "cápsulas",
    "gota": "gotas", "gotas": "gotas", "ml": "ml", "g": "g",
    "ampola": "ampolas", "ampolas": "ampolas",
    "frasco": "frascos", "frascos": "frascos",
    "unidade": "unidades", "unidades": "unidades",
    "caixa": "caixas", "caixas": "caixas",
}


class MedicationAssistantService:
    def process_answer(
        self,
        step: str,
        answer: str,
        draft: dict[str, Any],
    ) -> dict[str, Any]:
        answer = answer.strip()
        updated = {**draft}

        if step == "medication":
            updated.update(self._parse_medication(answer, updated))
            return self._result(
                "startDate", updated,
                "Certo! Agora, qual é a data de início do uso desse medicamento? Informe no formato DD/MM/AAAA.",
            )

        if step == "startDate":
            if not self._valid_date(answer):
                return self._result(
                    step, updated,
                    "Não consegui reconhecer essa data. Informe no formato DD/MM/AAAA, por exemplo: 03/11/2026.",
                )
            updated["startDate"] = answer
            return self._result(
                "continuous", updated,
                "O medicamento será de uso contínuo, sem uma data prevista para terminar?",
            )

        if step == "continuous":
            if self._negative(answer) or self._has_end_date_intent(answer):
                updated.update(continuous=False, endDate="")
                return self._result(
                    "endDate", updated,
                    "Entendi. Então qual será a data de término do tratamento? Informe no formato DD/MM/AAAA.",
                )
            if self._positive(answer):
                updated.update(continuous=True, endDate="")
                return self._stock_question(answer, updated)
            return self._result(
                step, updated,
                'Só para confirmar: o uso será contínuo ou terá uma data para terminar? Responda "contínuo" ou "terá data de término".',
            )

        if step == "endDate":
            if not self._valid_date(answer):
                return self._result(
                    step, updated,
                    "Não consegui reconhecer essa data. Informe no formato DD/MM/AAAA, por exemplo: 20/11/2026.",
                )
            updated["endDate"] = answer
            return self._stock_question(answer, updated)

        if step == "stockQuantity":
            if self._negative(answer):
                updated.update(
                    stockQuantity="", stockUnit="", unitsPerDose="", minimumStock=""
                )
                return self._instructions_question(answer, updated)
            quantity = re.search(r"\d+(?:[.,]\d+)?", answer)
            if not quantity:
                return self._result(
                    step, updated,
                    'Informe uma quantidade numérica, por exemplo: 30. Se não quiser acompanhar o estoque, responda "não controlar".',
                )
            updated["stockQuantity"] = quantity.group().replace(",", ".")
            if updated.get("stockUnit") and updated.get("unitsPerDose"):
                return self._minimum_question(answer, updated)
            return self._result(
                "stockUnit", updated,
                "Qual é a unidade dessa quantidade? Por exemplo: comprimidos, cápsulas, frascos, caixas ou ml.",
            )

        if step == "stockUnit":
            normalized = self._normalize(answer)
            updated["stockUnit"] = UNIT_MAP.get(normalized, answer)
            if updated.get("unitsPerDose"):
                return self._minimum_question(answer, updated)
            return self._result(
                "unitsPerDose", updated,
                "Quantas unidades são utilizadas em cada dose? Por exemplo: 1 comprimido ou 2 cápsulas.",
            )

        if step == "unitsPerDose":
            consumption = self._extract_consumption(answer)
            quantity = re.search(
                r"\d+(?:[.,]\d+)?|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez",
                self._normalize(answer),
            )
            if not quantity:
                return self._result(
                    step, updated,
                    'Informe a quantidade utilizada por dose, por exemplo: 1. Você também pode responder "não sei" e preencher depois.',
                )
            amount = self._number(quantity.group())
            if amount is None:
                return self._result(
                    step, updated,
                    "Não consegui reconhecer essa quantidade. Informe um número, por exemplo: 1 ou 2.",
                )
            updated["unitsPerDose"] = str(amount)
            if consumption:
                updated["stockUnit"] = consumption["unit"]
            return self._minimum_question(answer, updated)

        if step == "minimumStock":
            if self._negative(answer):
                updated["minimumStock"] = ""
            else:
                quantity = re.search(r"\d+(?:[.,]\d+)?", answer)
                if not quantity:
                    return self._result(
                        step, updated,
                        'Informe uma quantidade numérica, por exemplo: 5. Se não quiser receber avisos, responda "não".',
                    )
                updated["minimumStock"] = quantity.group().replace(",", ".")
            return self._instructions_question(answer, updated)

        if step == "instructions":
            updated["instructions"] = (
                "Sem instruções adicionais" if self._negative(answer) else answer
            )
            return self._result(
                "finished", updated,
                "Pronto! Reuni as informações do medicamento, do período de uso e do estoque. Agora você pode conferir os dados e completar o que faltar antes de salvar.",
            )

        return self._result(
            "finished", updated,
            "As perguntas foram concluídas. Você já pode conferir o cadastro.",
        )

    @staticmethod
    def _result(step: str, draft: dict[str, Any], message: str) -> dict[str, Any]:
        return {"step": step, "draft": draft, "assistantText": message}

    def _stock_question(
        self,
        answer: str,
        draft: dict[str, Any],
    ) -> dict[str, Any]:
        return self._result(
            "stockQuantity", draft,
            'Entendi. Agora vamos falar sobre o estoque. Quantas unidades desse medicamento você tem atualmente? Se não quiser controlar o estoque, responda "não controlar".',
        )

    def _minimum_question(
        self,
        answer: str,
        draft: dict[str, Any],
    ) -> dict[str, Any]:
        return self._result(
            "minimumStock", draft,
            'A partir de qual quantidade restante você deseja receber um aviso de estoque baixo? Por exemplo: 5. Se não quiser esse aviso, responda "não".',
        )

    def _instructions_question(
        self,
        answer: str,
        draft: dict[str, Any],
    ) -> dict[str, Any]:
        return self._result(
            "instructions", draft,
            'Agora, para finalizar: existe alguma instrução adicional de uso que você gostaria de registrar? Por exemplo, tomar após as refeições ou não administrar em jejum. Se não houver nenhuma, responda "não".',
        )

    def _parse_medication(
        self,
        message: str,
        current: dict[str, Any],
    ) -> dict[str, Any]:
        result = dict(current)
        text = message.strip()
        extracted_time = self._extract_time(text)
        if extracted_time:
            result["firstTime"] = extracted_time
        interval = self._extract_interval(text)
        if interval:
            result["intervalHours"] = interval
        dosage = re.search(
            r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|UI|%|gotas?)(?:\s*/\s*\d+(?:[.,]?\d+)?\s*(?:ml))?",
            text,
            re.IGNORECASE,
        )
        if dosage:
            result["dosage"] = dosage.group().strip()
        consumption = self._extract_consumption(text)
        if consumption:
            result["unitsPerDose"] = consumption["quantity"]
            result["stockUnit"] = consumption["unit"]
        name_match = re.search(
            r"(?:medicamento\s*:?\s*|rem[eé]dio\s*:?\s*|tomar\s+|tomo\s+|uso\s+)([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*)?)",
            text,
            re.IGNORECASE,
        )
        if name_match:
            result["name"] = name_match.group(1).strip()
        elif not result.get("name") and dosage:
            before_dosage = text[:dosage.start()].strip()
            name = re.sub(
                r"^(?:o|a|meu|minha|medicamento|remédio)\s+",
                "",
                before_dosage,
                flags=re.IGNORECASE,
            )
            name = re.sub(r"[,:;.\-]+$", "", name).strip()
            if name and len(name) <= 50:
                result["name"] = name
        return result

    def _extract_time(self, text: str) -> str | None:
        normalized = self._normalize(text)
        match = re.search(r"\b([01]?\d|2[0-3])\s*:\s*([0-5]\d)\b", normalized)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}"
        match = re.search(
            r"\b([01]?\d|2[0-3])\s*(?:h(?:r|rs|oras?)?)\s*([0-5]\d)?\b",
            normalized,
        )
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2) or '00'}"
        number_expression = (
            "vinte e quatro|vinte e tres|vinte e dois|vinte e uma|vinte e um|"
            "dezenove|dezoito|dezessete|dezesseis|quinze|quatorze|catorze|"
            "treze|doze|onze|dez|nove|oito|sete|seis|cinco|quatro|tres|"
            "duas|dois|uma|um|zero"
        )
        match = re.search(
            rf"\b(?:as?\s+)?({number_expression})(?:\s+e\s+meia|\s+horas?)?(?:\s+da\s+(manha|tarde|noite))?\b",
            normalized,
        )
        if not match:
            match = re.search(
                r"\b([01]?\d|2[0-3])(?:\s+e\s+meia)?(?:\s+da\s+(manha|tarde|noite))\b",
                normalized,
            )
        if not match:
            return None
        hour = self._number(match.group(1))
        if hour is None or hour > 23:
            return None
        period = match.group(2) if match.lastindex and match.lastindex >= 2 else None
        if period in {"tarde", "noite"} and hour < 12:
            hour += 12
        if period == "manha" and hour == 12:
            hour = 0
        return f"{hour:02d}:{'30' if 'e meia' in match.group(0) else '00'}"

    def _extract_interval(self, text: str) -> str:
        normalized = self._normalize(text)
        patterns = (
            r"\bde\s*(\d{1,2})\s*em\s*\d{1,2}\s*(?:h(?:r|rs|oras?)?|horas?)\b",
            r"\b(\d{1,2})\s*em\s*\d{1,2}\s*(?:h(?:r|rs|oras?)?|horas?)\b",
            r"\ba\s*cada\s*(\d{1,2})\s*(?:h(?:r|rs|oras?)?|horas?)\b",
            r"\bcada\s*(\d{1,2})\s*(?:h(?:r|rs|oras?)?|horas?)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                interval = int(match.group(1))
                if 1 <= interval <= 24:
                    return str(interval)
        words = (
            "vinte e quatro|vinte e tres|vinte e dois|vinte e um|dezenove|"
            "dezoito|dezessete|dezesseis|quinze|quatorze|catorze|treze|"
            "doze|onze|dez|nove|oito|sete|seis|cinco|quatro|tres|duas|dois|uma|um"
        )
        patterns = (
            rf"\bde\s*({words})\s*em\s*{words}\s*(?:horas?|h|hr|hrs)\b",
            rf"\ba\s*cada\s*({words})\s*(?:horas?|h|hr|hrs)\b",
            rf"\bcada\s*({words})\s*(?:horas?|h|hr|hrs)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                interval = self._number(match.group(1))
                if interval is not None and 1 <= interval <= 24:
                    return str(interval)
        return ""

    def _extract_consumption(self, text: str) -> dict[str, str] | None:
        normalized = self._normalize(text)
        match = re.search(
            r"\b(\d+(?:[.,]\d+)?|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez)\s*(comprimidos?|capsulas?|gotas?|ml|g|ampolas?|frascos?|unidades?|caixas?)\b",
            normalized,
        )
        if not match:
            return None
        quantity = self._number(match.group(1))
        if quantity is None:
            return None
        return {
            "quantity": str(quantity),
            "unit": UNIT_MAP.get(match.group(2), match.group(2)),
        }

    @staticmethod
    def _number(value: str) -> int | float | None:
        normalized = MedicationAssistantService._normalize(value)
        if normalized in NUMBER_WORDS:
            return NUMBER_WORDS[normalized]
        try:
            number = float(normalized.replace(",", "."))
        except ValueError:
            return None
        return int(number) if number.is_integer() else number

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        normalized = "".join(
            char for char in normalized
            if unicodedata.category(char) != "Mn"
        )
        return normalized.lower().replace("–", "-").replace("—", "-").strip()

    @staticmethod
    def _negative(text: str) -> bool:
        return bool(re.search(
            r"\b(não|nao|não quero|nao quero|sem estoque|não controlar|nao controlar|pular|ignorar)\b",
            text,
            re.IGNORECASE,
        ))

    @staticmethod
    def _has_end_date_intent(text: str) -> bool:
        normalized = MedicationAssistantService._normalize(text)
        return bool(re.search(
            r"\b(?:tera(?: uma)? data (?:prevista )?(?:de termino|para terminar)|"
            r"tem data (?:prevista )?(?:de termino|para terminar)|"
            r"data (?:prevista )?(?:de termino|para terminar))\b",
            normalized,
        ))

    @staticmethod
    def _positive(text: str) -> bool:
        normalized = MedicationAssistantService._normalize(text)
        return bool(re.search(
            r"\b(sim|s|continuo|uso continuo|indefinido|sempre)\b",
            normalized,
        ))

    @staticmethod
    def _valid_date(text: str) -> bool:
        if not re.fullmatch(r"([0-2]\d|3[01])/(0\d|1[0-2])/\d{4}", text.strip()):
            return False
        from datetime import datetime

        try:
            datetime.strptime(text.strip(), "%d/%m/%Y")
        except ValueError:
            return False
        return True
