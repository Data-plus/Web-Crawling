# Web-Crawling
Naver Product Review Crawling

## Financial Data Crawler

The `finance_crawler.py` script collects basic financial information from
Yahoo Finance for the provided ticker symbols. The data includes price,
EPS and dividend information and is written to a CSV file.
It requires the `requests` and `python-dotenv` packages which can be
installed with `pip install requests python-dotenv`.

If the Yahoo Finance request fails for a ticker, the script will attempt
to retrieve the same information using the Perplexity API. Set a
`PERPLEXITY_API_KEY` variable in a `.env` file in the project directory
for this fallback to work.

```bash
python finance_crawler.py GES ARCC -o output.csv
```

If no output path is supplied, `financial_data.csv` is created in the
current directory.
