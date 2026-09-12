from pathlib import Path
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI(
    title="Skin Clinic Campaign Analysis API",
    description="Campaign response-rate analysis by customer segment.",
    version="1.0.0",
)

DATA_FILE = Path("../resources/skin clinic campaign.csv")


def response_rate(dataframe: pd.DataFrame, column: str) -> pd.DataFrame:
    """Calculate campaign response rate (%) for each category."""
    result = (
        dataframe.groupby(column)["Response_to_Campaign"]
        .apply(lambda x: (x == "Yes").mean() * 100)
        .reset_index(name="Response Rate (%)")
    )

    result["Response Rate (%)"] = result["Response Rate (%)"].round(2)

    return result


def create_analysis(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create the four analysis tables required by the assignment."""
    data = df.copy()

    # Product usage categories:
    # 1-4, 5-8, and >8 unique products purchased in the last year.
    data["Product_Usage"] = pd.cut(
        data["Unique_Products_Purchased"],
        bins=[0, 4, 8, float("inf")],
        labels=["1-4", "5-8", ">8"],
        include_lowest=True,
    )

    return {
        "Gender vs Campaign Response": response_rate(data, "Gender"),
        "Age Group vs Campaign Response": response_rate(data, "AgeGroup"),
        "Purchase in Last Quarter vs Campaign Response":
            response_rate(data, "Purchase_Last_Quarter"),
        "Product Usage vs Campaign Response":
            response_rate(data, "Product_Usage"),
    }


def load_data() -> pd.DataFrame:
    """Load the campaign CSV and give a useful error if it is missing."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"CSV file not found at: {DATA_FILE}. "
            "Make sure 'skin clinic campaign.csv' is inside the resources folder."
        )

    return pd.read_csv(DATA_FILE)


def build_html(tables: dict[str, pd.DataFrame]) -> str:
    """Build an HTML page containing four tables.

    Returning HTML tables is useful because Excel Power Query can connect
    using Data > Get Data > From Web and extract the tables.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Skin Clinic Campaign Analysis</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 35px;
                background: #f7f7f7;
            }

            h1 {
                color: #222;
            }

            h2 {
                color: #333;
                margin-top: 35px;
            }

            table {
                border-collapse: collapse;
                width: 650px;
                max-width: 100%;
                background: white;
                margin-bottom: 30px;
            }

            th, td {
                border: 1px solid #cccccc;
                padding: 10px;
                text-align: left;
            }

            th {
                background: #eeeeee;
            }

            .updated {
                color: #666666;
                margin-bottom: 25px;
            }
        </style>
    </head>
    <body>
        <h1>Skin Clinic Campaign Analysis</h1>
        <p class="updated">
            Results generated from the latest CSV data available to the API.
        </p>
    """

    for title, table in tables.items():
        html += f"<h2>{title}</h2>"
        html += table.to_html(
            index=False,
            border=0,
            classes="analysis-table",
        )

    html += """
    </body>
    </html>
    """

    return html


@app.get("/", response_class=HTMLResponse)
def home():
    """API landing page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Skin Clinic Campaign Analysis API</title>
    </head>
    <body>
        <h1>Skin Clinic Campaign Analysis API</h1>

        <p>
            <a href="/campaign-analysis">
                View Campaign Analysis
            </a>
        </p>

        <p>
            <a href="/campaign-analysis/json">
                View JSON Results
            </a>
        </p>

        <p>
            <a href="/docs">
                Open FastAPI Swagger Documentation
            </a>
        </p>
    </body>
    </html>
    """


@app.get("/campaign-analysis", response_class=HTMLResponse)
def campaign_analysis():
    """Return all four campaign analyses as HTML tables.

    This is the endpoint to use with:
    Excel -> Data -> Get Data -> From Web
    """
    try:
        df = load_data()
        tables = create_analysis(df)
        return HTMLResponse(content=build_html(tables))
    except Exception as exc:
        return HTMLResponse(
            content=f"""
            <h1>Error loading campaign analysis</h1>
            <p>{exc}</p>
            """,
            status_code=500,
        )


@app.get("/campaign-analysis/json")
def campaign_analysis_json():
    """Optional JSON version of the analysis."""
    df = load_data()
    tables = create_analysis(df)

    return {
        title: table.to_dict(orient="records")
        for title, table in tables.items()
    }