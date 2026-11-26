from typing import Any, Iterable


def _field(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _field_value(field: Any) -> tuple[str | None, float | None]:
    if field is None:
        return None, None
    if isinstance(field, (str, int, float)):
        value = field
        confidence = None
    elif isinstance(field, dict):
        value = field.get("value")
        if value is None:
            value = field.get("content")
        confidence = field.get("confidence")
    else:
        value = getattr(field, "value", None)
        if value is None:
            value = getattr(field, "content", None)
        confidence = getattr(field, "confidence", None)
    while isinstance(value, (list, tuple)):
        value = value[0] if value else None
    if isinstance(value, dict):
        value = value.get("content") or value.get("value")
    elif value is not None and not isinstance(value, (str, int, float)):
        value = getattr(value, "content", None) or getattr(value, "value", None)
    if value is not None:
        value = str(value).strip()
    confidence = float(confidence) if confidence is not None else None
    return (value or None), confidence


def _values(field: Any) -> list[tuple[str | None, float | None]]:
    if field is None:
        return []
    if isinstance(field, (list, tuple)):
        values = list(field)
    elif isinstance(field, dict):
        values = field.get("values")
        if values is None:
            values = field.get("value")
        if isinstance(values, (list, tuple)):
            values = list(values)
        elif values is not None:
            values = [values]
        else:
            values = [field]
    else:
        values = getattr(field, "values", None)
        if values is None:
            values = getattr(field, "value", None)
        if isinstance(values, (list, tuple)):
            values = list(values)
        if values is None:
            values = [field]
    return [_field_value(item) for item in values]


def _list_schema(values: Iterable[tuple[str | None, float | None]]) -> list[dict[str, Any]]:
    return [
        {"value": value, "confidence": confidence}
        for value, confidence in values
        if value
    ]


def _address_component(value_address: Any, *names: str) -> str | None:
    if value_address is None:
        return None
    for name in names:
        value = None
        if isinstance(value_address, dict):
            value = value_address.get(name)
            if value is None:
                # Accept Azure REST-style camelCase names as well as SDK JSON names.
                camel_name = name
                if "_" in name:
                    parts = name.split("_")
                    camel_name = parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])
                value = value_address.get(camel_name)
        else:
            value = getattr(value_address, name, None)
        if value is not None:
            value = str(value).strip()
            if value:
                return value
    return None


def _address_items(field: Any) -> list[Any]:
    if field is None:
        return []
    if isinstance(field, (list, tuple)):
        return list(field)
    if isinstance(field, dict):
        values = field.get("valueArray")
        if values is None:
            values = field.get("values")
        if values is None:
            values = field.get("value")
        if isinstance(values, (list, tuple)):
            return list(values)
        if values is not None:
            return [values]
        return [field]

    values = getattr(field, "values", None)
    if values is None:
        values = getattr(field, "value", None)
    if isinstance(values, (list, tuple)):
        return list(values)
    if values is not None:
        return [values]
    return [field]


def _address_value(item: Any) -> tuple[str | None, float | None]:
    if isinstance(item, dict):
        content = item.get("content")
        confidence = item.get("confidence")
        value_address = item.get("valueAddress")
    else:
        content = getattr(item, "content", None)
        confidence = getattr(item, "confidence", None)
        value_address = getattr(item, "valueAddress", None)
        if value_address is None:
            value_address = getattr(item, "value_address", None)
        if value_address is None:
            value_address = getattr(item, "value", None)

    if not isinstance(content, str):
        content = getattr(content, "content", None) if content is not None else None
    content = str(content).strip() if content else None

    street_address = _address_component(
        value_address,
        "streetAddress",
        "street_address",
    )
    level = _address_component(value_address, "level")

    # Preserve the original OCR text exactly. Only use structured components
    # when it is absent or clearly incomplete.
    value = content
    if not value:
        value = street_address
    if not value:
        components = [
            _address_component(value_address, "houseNumber", "house_number"),
            _address_component(value_address, "road"),
        ]
        value = " ".join(component for component in components if component)
    if value and level and level.lower() not in value.lower():
        value = f"{value} {level}"

    confidence = float(confidence) if confidence is not None else None
    return (value or None), confidence


def map_document(document: Any) -> dict[str, Any]:
    fields = _field(document, "fields") or {}

    def get_field(name: str) -> Any:
        if isinstance(fields, dict):
            return fields.get(name)
        return getattr(fields, name, None)

    def get_subfield(name: str, subname: str) -> tuple[str | None, float | None]:
        field = get_field(name)
        if field is None:
            return None, None
        if isinstance(field, dict):
            value = field.get("value")
        else:
            value = getattr(field, "value", None)
        while True:
            if isinstance(value, (list, tuple)):
                value = value[0] if value else None
            elif isinstance(value, dict):
                nested = value.get(subname)
                break
            elif value is None:
                nested = None
                break
            elif hasattr(value, subname):
                nested = getattr(value, subname)
                break
            else:
                value = getattr(value, "value", None)
        return _field_value(nested)

    names_field = get_field("ContactNames")
    if names_field is None:
        names_field = get_field("Names")
    first_name = get_subfield("ContactNames", "FirstName")
    if not first_name[0]:
        first_name = get_subfield("Names", "FirstName")
    last_name = get_subfield("ContactNames", "LastName")
    if not last_name[0]:
        last_name = get_subfield("Names", "LastName")
    name_value = " ".join(part for part in (first_name[0], last_name[0]) if part)
    full_name = (name_value or _field_value(names_field)[0], None)

    def simple(field_name: str) -> tuple[str | None, float | None]:
        values = _values(get_field(field_name))
        return values[0] if values else (None, None)

    company = simple("CompanyNames")
    if company[0] is None:
        company = simple("Companies")
    department = simple("Departments")
    job_title = simple("JobTitles")

    emails = _values(get_field("Emails"))
    websites = _values(get_field("Websites"))
    mobile = _values(get_field("MobilePhones"))
    work = _values(get_field("WorkPhones"))
    other = _values(get_field("OtherPhones"))
    fax = _values(get_field("Faxes"))
    if not fax:
        fax = _values(get_field("FaxNumbers"))
    addresses = [_address_value(item) for item in _address_items(get_field("Addresses"))]

    all_confidences = [
        confidence
        for confidence in (
            first_name[1], last_name[1], full_name[1],
            company[1], department[1], job_title[1],
            *[item[1] for item in emails + websites + mobile + work + other + fax + addresses],
        )
        if confidence is not None
    ]

    return {
        "first_name": first_name[0],
        "last_name": last_name[0],
        "full_name": full_name[0],
        "company_name": company[0],
        "department": department[0],
        "job_title": job_title[0],
        "emails": _list_schema(emails),
        "websites": _list_schema(websites),
        "mobile_phones": _list_schema(mobile),
        "work_phones": _list_schema(work),
        "other_phones": _list_schema(other),
        "fax_numbers": _list_schema(fax),
        "addresses": _list_schema(addresses),
        "_overall_confidence": (
            round(sum(all_confidences) / len(all_confidences), 4)
            if all_confidences else None
        ),
    }
