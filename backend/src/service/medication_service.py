import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from database import DomainError
from port.adapter.medication_repository import MedicationRepository


class MedicationService:
    def __init__(self, repository: MedicationRepository):
        self.repository = repository

    def list_medications(self, family_id: str) -> list[dict[str, Any]]:
        medicines = self.repository.list_medications(family_id)
        for medicine in medicines:
            stock = self._decimal_value(medicine.get("stockQuantity", ""))
            minimum = self._decimal_value(
                medicine.get("minimumStock", "5")
            )
            has_stock = str(medicine.get("stockQuantity", "")).strip() != ""
            medicine["lowStock"] = bool(
                has_stock
                and stock is not None
                and minimum is not None
                and stock > 0
                and stock <= minimum
            )
            medicine["outOfStock"] = bool(
                has_stock and stock is not None and stock <= 0
            )
        return medicines

    def save_medication(
        self,
        family_id: str,
        medication_id: str | None,
        medication: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_medication(medication)
        medication_id = medication_id or f"medication-{uuid4().hex}"
        medication["id"] = medication_id
        medication.setdefault("active", True)
        medication.setdefault("administered", False)
        return self.repository.save_medication(
            family_id, medication_id, medication
        )

    def delete_medication(
        self,
        family_id: str,
        medication_id: str,
    ) -> None:
        def remove_related(medicines, state):
            medicines = [item for item in medicines if item["id"] != medication_id]
            state["doseRecords"] = [
                item for item in state["doseRecords"]
                if item.get("medicineId") != medication_id
            ]
            state["inventoryMovements"] = [
                item for item in state["inventoryMovements"]
                if item.get("medicineId") != medication_id
            ]
            return medicines, state, None

        self.repository.transact_medication_data(family_id, remove_related)

    def toggle_medication(
        self,
        family_id: str,
        medication_id: str,
    ) -> dict[str, Any]:
        def toggle(medicines, state):
            medicine = next(
                (item for item in medicines if item["id"] == medication_id),
                None,
            )
            if medicine is None:
                raise DomainError(404, "Medicamento não encontrado.")
            medicine["active"] = not bool(medicine.get("active", True))
            return medicines, state, medicine

        return self.repository.transact_medication_data(family_id, toggle)

    def get_medication_state(self, family_id: str) -> dict[str, Any]:
        return self.repository.get_medication_state(family_id)

    def get_schedule(
        self,
        family_id: str,
        schedule_date: str,
        timezone_name: str,
    ) -> list[dict[str, Any]]:
        target_date, local_timezone = self._parse_schedule_request(
            schedule_date, timezone_name
        )
        medicines = self.repository.list_medications(family_id)
        state = self.repository.get_medication_state(family_id)
        return self._build_schedule(
            medicines, state["doseRecords"], target_date, local_timezone
        )

    def administer_dose(
        self,
        family_id: str,
        dose_id: str,
        schedule_date: str,
        timezone_name: str,
    ) -> dict[str, Any]:
        target_date, local_timezone = self._parse_schedule_request(
            schedule_date, timezone_name
        )

        def administer(medicines, state):
            schedule = self._build_schedule(
                medicines, state["doseRecords"], target_date, local_timezone
            )
            dose = next((item for item in schedule if item["id"] == dose_id), None)
            if dose is None:
                raise DomainError(404, "Dose não encontrada para a data informada.")
            if dose["status"] == "administered":
                return medicines, state, {"doseId": dose_id}

            medicine = next(
                item for item in medicines if item["id"] == dose["medicine"]["id"]
            )
            stock = self._decimal_value(medicine.get("stockQuantity", ""))
            consumption = self._decimal_value(medicine.get("unitsPerDose", ""))
            stock_unit = str(medicine.get("stockUnit", "")).strip()
            has_stock = bool(
                str(medicine.get("stockQuantity", "")).strip()
                and str(medicine.get("unitsPerDose", "")).strip()
                and stock_unit
            )
            stock_deducted = Decimal("0")
            if has_stock:
                if stock is None or consumption is None or consumption <= 0:
                    raise DomainError(
                        400,
                        "Confira o estoque e o consumo por dose antes de administrar.",
                    )
                if stock < consumption:
                    raise DomainError(
                        400,
                        f"Estoque insuficiente de {medicine['name']}. Disponível: "
                        f"{stock} {stock_unit}. Necessário: {consumption} {stock_unit}.",
                    )
                stock_deducted = consumption
                medicine["stockQuantity"] = self._format_decimal(
                    stock - stock_deducted
                )

            now = datetime.now(timezone.utc).isoformat()
            record = {
                "id": dose_id,
                "medicineId": medicine["id"],
                "scheduledAt": dose["scheduledAt"],
                "administeredAt": now,
                "stockDeducted": float(stock_deducted),
                "stockUnit": stock_unit or None,
            }
            state["doseRecords"].append(record)
            if stock_deducted > 0:
                state["inventoryMovements"].append(
                    self._movement(
                        medicine,
                        "administration",
                        stock_deducted,
                        stock_unit,
                        "Saída por administração de dose",
                        dose_id,
                    )
                )
            return medicines, state, {"doseId": dose_id}

        self.repository.transact_medication_data(family_id, administer)
        return {"doseId": dose_id}

    def undo_dose(self, family_id: str, dose_id: str) -> dict[str, str]:
        def undo(medicines, state):
            record = next(
                (item for item in state["doseRecords"] if item.get("id") == dose_id),
                None,
            )
            if record is None:
                raise DomainError(404, "Registro de dose não encontrado.")
            medicine = next(
                (item for item in medicines if item["id"] == record["medicineId"]),
                None,
            )
            deducted = self._decimal_value(record.get("stockDeducted"))
            if medicine and deducted and deducted > 0:
                current_stock = self._decimal_value(
                    medicine.get("stockQuantity", "")
                )
                if current_stock is None:
                    raise DomainError(400, "A quantidade atual do estoque é inválida.")
                medicine["stockQuantity"] = self._format_decimal(
                    current_stock + deducted
                )
                state["inventoryMovements"].append(
                    self._movement(
                        medicine,
                        "reversal",
                        deducted,
                        str(record.get("stockUnit") or medicine.get("stockUnit") or ""),
                        "Estorno de administração",
                        dose_id,
                    )
                )
            state["doseRecords"] = [
                item for item in state["doseRecords"] if item.get("id") != dose_id
            ]
            return medicines, state, {"doseId": dose_id}

        return self.repository.transact_medication_data(family_id, undo)

    def replenish_stock(
        self,
        family_id: str,
        medicine_id: str,
        quantity: float,
        description: str,
    ) -> dict[str, Any]:
        amount = self._decimal_value(quantity)
        if amount is None or amount <= 0:
            raise DomainError(400, "Informe uma quantidade válida para reposição.")

        def replenish(medicines, state):
            medicine = next(
                (item for item in medicines if item["id"] == medicine_id), None
            )
            if medicine is None:
                raise DomainError(404, "Medicamento não encontrado.")
            stock_unit = str(medicine.get("stockUnit", "")).strip()
            if not stock_unit:
                raise DomainError(
                    400, "Cadastre a unidade de estoque antes de fazer a reposição."
                )
            stock = self._decimal_value(medicine.get("stockQuantity", ""))
            if stock is None:
                raise DomainError(400, "A quantidade atual do estoque é inválida.")
            medicine["stockQuantity"] = self._format_decimal(stock + amount)
            state["inventoryMovements"].append(
                self._movement(
                    medicine,
                    "entry",
                    amount,
                    stock_unit,
                    description.strip() or "Reposição de estoque",
                    None,
                )
            )
            return medicines, state, medicine

        return self.repository.transact_medication_data(family_id, replenish)

    @staticmethod
    def _validate_medication(medicine: dict[str, Any]) -> None:
        for field in ("name", "dosage", "firstTime", "startDate"):
            if not str(medicine.get(field, "")).strip():
                raise DomainError(400, f"Preencha o campo obrigatório: {field}.")
        try:
            time.fromisoformat(medicine["firstTime"])
        except ValueError as error:
            raise DomainError(400, "Horário do medicamento inválido.") from error
        try:
            interval = Decimal(str(medicine.get("intervalHours", "")))
        except InvalidOperation as error:
            raise DomainError(400, "Intervalo do medicamento inválido.") from error
        if not Decimal("1") <= interval <= Decimal("24"):
            raise DomainError(
                400, "O intervalo deve estar entre 1 e 24 horas."
            )
        start = MedicationService._parse_date(medicine["startDate"])
        if start is None:
            raise DomainError(400, "Data de início inválida.")
        if not medicine.get("continuous"):
            end = MedicationService._parse_date(medicine.get("endDate", ""))
            if end is None or end < start:
                raise DomainError(400, "Data final do tratamento inválida.")
        for field in ("stockQuantity", "unitsPerDose", "minimumStock"):
            value = str(medicine.get(field, "")).strip()
            if value and MedicationService._decimal_value(value) is None:
                raise DomainError(400, f"Valor inválido no campo {field}.")
        units = MedicationService._decimal_value(medicine.get("unitsPerDose", ""))
        if units is None or units <= 0:
            raise DomainError(400, "A quantidade por dose deve ser maior que zero.")
        stock = MedicationService._decimal_value(medicine.get("stockQuantity", ""))
        if stock is not None and stock < 0:
            raise DomainError(400, "O estoque não pode ser negativo.")
        minimum = MedicationService._decimal_value(medicine.get("minimumStock", "0"))
        if minimum is not None and minimum < 0:
            raise DomainError(400, "O estoque mínimo não pode ser negativo.")

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_schedule_request(
        schedule_date: str,
        timezone_name: str,
    ) -> tuple[date, ZoneInfo]:
        try:
            target_date = date.fromisoformat(schedule_date)
            local_timezone = ZoneInfo(timezone_name)
        except (ValueError, ZoneInfoNotFoundError) as error:
            raise DomainError(400, "Data ou fuso horário inválido.") from error
        return target_date, local_timezone

    @classmethod
    def _build_schedule(
        cls,
        medicines: list[dict[str, Any]],
        dose_records: list[dict[str, Any]],
        target_date: date,
        local_timezone: ZoneInfo,
    ) -> list[dict[str, Any]]:
        records_by_id = {record.get("id"): record for record in dose_records}
        now = datetime.now(timezone.utc)
        doses = []
        for medicine in medicines:
            if not medicine.get("active", True):
                continue
            start_date = cls._parse_date(medicine.get("startDate", ""))
            end_date = cls._parse_date(medicine.get("endDate", ""))
            if start_date and target_date < start_date:
                continue
            if not medicine.get("continuous") and end_date and target_date > end_date:
                continue
            time_match = re.fullmatch(r"(\d{2}):(\d{2})", str(medicine.get("firstTime", "")))
            if not time_match:
                continue
            try:
                interval_minutes = float(medicine.get("intervalHours")) * 60
            except (TypeError, ValueError):
                continue
            if not 0 < interval_minutes <= 24 * 60:
                continue

            first_local = datetime.combine(
                target_date,
                time(int(time_match.group(1)), int(time_match.group(2))),
                tzinfo=local_timezone,
            )
            first_utc = first_local.astimezone(timezone.utc)
            elapsed_minutes = 0.0
            while elapsed_minutes < 24 * 60:
                scheduled_utc = first_utc + timedelta(minutes=elapsed_minutes)
                scheduled_local = scheduled_utc.astimezone(local_timezone)
                if scheduled_local.date() == target_date:
                    scheduled_at = (
                        scheduled_utc.isoformat(timespec="milliseconds")
                        .replace("+00:00", "Z")
                    )
                    dose_id = f"{medicine['id']}_{scheduled_at}"
                    record = records_by_id.get(dose_id)
                    doses.append(
                        {
                            "id": dose_id,
                            "medicine": medicine,
                            "scheduledAt": scheduled_at,
                            "administeredAt": (
                                record.get("administeredAt") if record else None
                            ),
                            "status": (
                                "administered"
                                if record
                                else "delayed"
                                if scheduled_utc < now
                                else "pending"
                            ),
                        }
                    )
                elapsed_minutes += interval_minutes
        return sorted(doses, key=lambda dose: dose["scheduledAt"])

    @staticmethod
    def _decimal_value(value: Any) -> Decimal | None:
        if value is None or str(value).strip() == "":
            return None
        try:
            result = Decimal(str(value).strip().replace(",", "."))
        except InvalidOperation:
            return None
        return result if result.is_finite() else None

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        return format(value.quantize(Decimal("0.0001")).normalize(), "f")

    @staticmethod
    def _movement(
        medicine: dict[str, Any],
        movement_type: str,
        quantity: Decimal,
        unit: str,
        description: str,
        dose_record_id: str | None,
    ) -> dict[str, Any]:
        return {
            "id": uuid4().hex,
            "medicineId": medicine["id"],
            "medicineName": medicine["name"],
            "type": movement_type,
            "quantity": float(quantity),
            "unit": unit,
            "date": datetime.now(timezone.utc).isoformat(),
            "description": description,
            "doseRecordId": dose_record_id,
        }
