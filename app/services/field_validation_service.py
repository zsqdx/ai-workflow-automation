import re


class FieldValidationService:
    def validate(
        self,
        input_schema: dict,
        extracted_fields: dict,
        confidence: float,
        min_confidence: float,
    ) -> dict:
        missing_fields = []
        validation_errors = []

        if confidence < min_confidence:
            validation_errors.append(
                {
                    "field": "confidence",
                    "message": (
                        f"Extraction confidence {confidence} is below "
                        f"required minimum {min_confidence}"
                    ),
                }
            )

        required_fields = input_schema.get("required_fields", [])

        for field_schema in required_fields:
            name = field_schema["name"]
            value = extracted_fields.get(name)

            if value is None or str(value).strip() == "":
                missing_fields.append(name)
                continue

            expected_type = field_schema.get("type")
            if expected_type == "string" and not isinstance(value, str):
                validation_errors.append(
                    {"field": name, "message": f"{name} must be a string"}
                )
                continue

            validation_regex = field_schema.get("validation_regex")
            if validation_regex and not re.match(validation_regex, value):
                validation_errors.append(
                    {
                        "field": name,
                        "message": f"{name} does not match required format",
                    }
                )

            min_length = field_schema.get("min_length")
            if (
                min_length
                and isinstance(value, str)
                and len(value.strip()) < min_length
            ):
                validation_errors.append(
                    {
                        "field": name,
                        "message": (
                            f"{name} must be at least {min_length} characters"
                        ),
                    }
                )

        is_valid = len(missing_fields) == 0 and len(validation_errors) == 0
        return {
            "is_valid": is_valid,
            "missing_fields": missing_fields,
            "validation_errors": validation_errors,
            "message": self._build_message(
                input_schema,
                missing_fields,
                validation_errors,
            ),
        }

    def _build_message(
        self,
        input_schema: dict,
        missing_fields: list[str],
        validation_errors: list[dict],
    ) -> str:
        if missing_fields:
            questions = []
            for field_schema in input_schema.get("required_fields", []):
                if field_schema["name"] in missing_fields:
                    questions.append(
                        field_schema.get(
                            "missing_field_question",
                            f"Please provide {field_schema['name']}.",
                        )
                    )
            return " ".join(questions)

        if validation_errors:
            return validation_errors[0]["message"]

        return ""


field_validation_service = FieldValidationService()
