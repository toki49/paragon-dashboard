import requests

AIRTABLE_API_BASE = "https://api.airtable.com/v0"


def fetch_airtable_table(token, base_id, table_name, view_name=None, max_records=5000, timeout_seconds=20):
    """Fetch Airtable table records into list[dict] of fields."""
    url = f"{AIRTABLE_API_BASE}/{base_id}/{table_name}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"pageSize": 100}
    if view_name:
        params["view"] = view_name

    records = []
    offset = None

    while True:
        if offset:
            params["offset"] = offset
        response = requests.get(url, headers=headers, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()

        page = payload.get("records", [])
        records.extend([rec.get("fields", {}) for rec in page])

        if len(records) >= max_records:
            break
        offset = payload.get("offset")
        if not offset:
            break

    return records[:max_records]
