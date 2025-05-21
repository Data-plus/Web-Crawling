import argparse
import csv
import json
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
import requests


def fetch_financial_data(ticker: str) -> Dict[str, str]:
    """Fetch financial information for a ticker from Yahoo Finance."""
    base_url = (
        "https://query1.finance.yahoo.com/v11/finance/quoteSummary/"
        f"{ticker}?modules=price%2CsummaryDetail%2CdefaultKeyStatistics"
    )
    response = requests.get(base_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    summary = data.get("quoteSummary", {}).get("result")
    if not summary:
        raise ValueError(f"No data found for ticker {ticker}")

    result = summary[0]
    price = result.get("price", {})
    details = result.get("summaryDetail", {})
    stats = result.get("defaultKeyStatistics", {})

    return {
        "ticker": ticker,
        "price": price.get("regularMarketPrice", {}).get("raw"),
        "currency": price.get("currency"),
        "eps": stats.get("trailingEps", {}).get("raw"),
        "dividendRate": details.get("dividendRate", {}).get("raw"),
        "dividendYield": details.get("dividendYield", {}).get("raw"),
        "sharesOutstanding": stats.get("sharesOutstanding", {}).get("raw"),
    }


def fetch_from_perplexity(ticker: str) -> Dict[str, str]:
    """Fallback to Perplexity API for financial info."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError("PERPLEXITY_API_KEY not set in environment")

    url = "https://api.perplexity.ai/chat/completions"
    prompt = (
        f"Provide the latest price, EPS and dividend info for {ticker} "
        "in JSON with keys price, currency, eps, dividendRate, dividendYield, sharesOutstanding."
    )
    payload = {
        "model": "pplx-70b-online",
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    content = response.json()
    message = content.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    try:
        data = json.loads(message)
    except Exception as exc:
        raise RuntimeError(f"Unexpected AI response: {exc}")

    data["ticker"] = ticker
    return data


def write_csv(rows: List[Dict[str, str]], output: Path) -> None:
    """Write collected rows to a CSV file."""
    fieldnames = [
        "ticker",
        "price",
        "currency",
        "eps",
        "dividendRate",
        "dividendYield",
        "sharesOutstanding",
    ]
    with output.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch financial data from Yahoo Finance")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to fetch")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("financial_data.csv"),
        help="Output CSV file",
    )
    args = parser.parse_args()

    load_dotenv()

    results = []
    for ticker in args.tickers:
        try:
            results.append(fetch_financial_data(ticker))
        except Exception as exc:
            print(f"Failed to fetch data for {ticker}: {exc}")
            try:
                results.append(fetch_from_perplexity(ticker))
            except Exception as ai_exc:
                print(f"Perplexity fallback failed for {ticker}: {ai_exc}")

    write_csv(results, args.output)


if __name__ == "__main__":
    main()
