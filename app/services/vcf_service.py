from io import BytesIO

import vobject


class VCFParseError(ValueError):
    pass


def _text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _address(value) -> str | None:
    if value is None:
        return None

    parts = getattr(value, "box", None), getattr(value, "extended", None), getattr(value, "street", None), getattr(value, "locality", None), getattr(value, "region", None), getattr(value, "code", None), getattr(value, "country", None)
    address = ", ".join(str(part).strip() for part in parts if part and str(part).strip())
    return address or None


def parse_vcf(content: bytes) -> list[dict]:
    if not content:
        raise VCFParseError("Uploaded file is empty.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("utf-16")
        except UnicodeDecodeError:
            try:
                text = content.decode("iso-8859-1")
            except UnicodeDecodeError as exc:
                raise VCFParseError("VCF content could not be decoded.") from exc

    if "BEGIN:VCARD" not in text.upper():
        raise VCFParseError("The uploaded file does not contain valid vCard data.")

    contacts: list[dict] = []
    try:
        components = vobject.readComponents(text)
        for card in components:
            if not hasattr(card, "contents"):
                continue

            contents = card.contents
            fn = _text(contents["fn"][0].value) if "fn" in contents else None

            full_name = fn
            if not full_name and "n" in contents:
                name = contents["n"][0].value
                parts = [
                    getattr(name, "given", ""),
                    getattr(name, "additional", ""),
                    getattr(name, "family", ""),
                ]
                full_name = " ".join(str(part).strip() for part in parts if part and str(part).strip()) or None

            company = None
            if "org" in contents:
                org = contents["org"][0].value
                if isinstance(org, list):
                    company = " ".join(str(part).strip() for part in org if str(part).strip()) or None
                else:
                    company = _text(org)

            job_title = _text(contents["title"][0].value) if "title" in contents else None
            phone = _text(contents["tel"][0].value) if "tel" in contents else None
            email = _text(contents["email"][0].value) if "email" in contents else None
            website = _text(contents["url"][0].value) if "url" in contents else None
            notes = _text(contents["note"][0].value) if "note" in contents else None
            address = _address(contents["adr"][0].value) if "adr" in contents else None

            if any((full_name, company, job_title, phone, email, website, address, notes)):
                contacts.append({
                    "full_name": full_name,
                    "company": company,
                    "job_title": job_title,
                    "phone": phone,
                    "email": email,
                    "website": website,
                    "address": address,
                    "notes": notes,
                })
    except Exception as exc:
        raise VCFParseError("The uploaded file could not be parsed as a valid vCard.") from exc

    if not contacts:
        raise VCFParseError("No contact information was found in the VCF file.")

    return contacts
