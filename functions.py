import logging
import os
import requests
import httpx
from typing import Optional
import json
import asyncio

logger = logging.getLogger(__name__)

# This is a placeholder for the actual subscription key
SUBSCRIPTION_KEY = os.environ["ITA_API_KEY"]


def bsp_search(categories: Optional[str] = None,
               ita_offices: Optional[str] = None,
               size: int = 3,
               offset: int = 0):
  global last_query, last_aggregate_data
  all_entries = []
  offset = 0

  last_query = {
      "Endpoint": "/bsp_search",
      "categories": categories,
      "ita_offices": ita_offices,
      "size": size,
      "offset": offset
  }
  logger.info(
      f"Starting BSP search with query: categories: {categories}, ITA offices: {ita_offices}, size: {size}, offset : {offset}"
  )

  while True:
    try:
      response = requests.get(
          "https://data.trade.gov/business_service_providers/v1/search",
          headers={"subscription-key": SUBSCRIPTION_KEY},
          params={
              "categories": categories,
              "ita_offices": ita_offices,
              "offset": offset,
              "size": size
          })
      response.raise_for_status()
      data = response.json()
      entries = data.get("results", [])
      if not entries:
        break
      all_entries.extend(entries)
      offset += len(entries)
    except Exception as e:
      logger.exception(f"An error occurred: {e}")
      raise
  return all_entries


async def consolidated_screening_list_search(
    name: Optional[str] = None,
    fuzzy_name: bool = True,
    sources: Optional[str] = None,
    types: Optional[str] = None,
    countries: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    full_address: Optional[str] = None,
    offset: int = 0,
    size: int = 10):
  global last_query
  last_query = {
      "Endpoint": "/consolidated_screening_list_search",
      "name": name,
      "fuzzy_name": fuzzy_name,
      "sources": sources,
      "types": types,
      "countries": countries,
      "address": address,
      "city": city,
      "state": state,
      "postal_code": postal_code,
      "full_address": full_address,
      "offset": offset,
      "size": size
  }

  logger.info(
      f"Starting Consolidated Screening List search with query: {last_query}")

  async with httpx.AsyncClient() as client:
    try:
      response = await client.get(
          "https://data.trade.gov/consolidated_screening_list/v1/search",
          headers={"subscription-key": SUBSCRIPTION_KEY},
          params=last_query)
      response.raise_for_status()
      data = response.json()
    except httpx.HTTPStatusError as http_err:
      logger.error(f"HTTP error occurred: {http_err}")
      raise HTTPException(status_code=http_err.response.status_code,
                          detail=f"HTTP error occurred: {http_err}")
    except Exception as err:
      logger.error(f"An error occurred: {err}")
      raise HTTPException(status_code=500, detail=f"An error occurred: {err}")

    return data


async def trade_leads_search(
    q: Optional[str] = None,
    country_codes: Optional[str] = None,
    tender_start_date_range_from: Optional[str] = None,
    tender_start_date_range_to: Optional[str] = None,
    contract_start_date_range_from: Optional[str] = None,
    contract_start_date_range_to: Optional[str] = None,
    size: int = 10,
    offset: int = 0):
  global last_query
  last_query = {
      "Endpoint": "/trade_leads_search",
      "q": q,
      "country_codes": country_codes,
      "tender_start_date_range_from": tender_start_date_range_from,
      "tender_start_date_range_to": tender_start_date_range_to,
      "contract_start_date_range_from": contract_start_date_range_from,
      "contract_start_date_range_to": contract_start_date_range_to,
      "size": size,
      "offset": offset
  }
  logger.info(f"Starting Trade Leads search with query: {last_query}")

  try:
    response = await httpx.AsyncClient().get(
        "https://data.trade.gov/trade_leads/v1/search",
        headers={"subscription-key": SUBSCRIPTION_KEY},
        params=last_query)
    response.raise_for_status()
    data = response.json()
    logger.info(f"Received response from Trade Leads API: {data}")
    return data
  except httpx.HTTPStatusError as http_err:
    logger.error(f"HTTP error occurred: {http_err}")
    raise httpx.HTTPException(status_code=http_err.response.status_code,
                              detail=f"HTTP error occurred: {http_err}")
  except Exception as err:
    logger.error(f"An error occurred: {err}")
    raise httpx.HTTPException(status_code=500,
                              detail=f"An error occurred: {err}")


async def google_custom_search(query,
                               context=None,
                               country_code=None,
                               date_from=None,
                               date_to=None):
  print("[DEBUG] Google Custom Search Function Called")
  print(
      f"[DEBUG] Query: {query}, Context: {context}, Country: {country_code}, Date From: {date_from}, Date To: {date_to}"
  )

  url = "https://www.googleapis.com/customsearch/v1"
  params = {
      "key": os.environ["GOOGLE_DEV_KEY"],
      "cx": os.environ["SEARCH_ENGINE_ID"],
      "q": f"{query} {context} site:trade.gov",
      "gl": country_code,
      "dateRestrict":
      f"d{date_from},{date_to}" if date_from and date_to else None
  }

  async with httpx.AsyncClient() as client:
    response = await client.get(url, params=params)
    results = response.json()
    print("[DEBUG] Search Results:", json.dumps(results, indent=4))
    return results
