import argparse
import datetime
import os
import sys

import markdown
import pandas as pd
from dotenv import load_dotenv
from jira import JIRA, Issue
from tqdm import tqdm
from weasyprint import HTML

load_dotenv()

jira_client = JIRA(os.getenv("JIRA_HOST"), basic_auth=(os.getenv("JIRA_USERNAME"), os.getenv("JIRA_API_TOKEN")))  # pyright: ignore[reportArgumentType]


def get_epic(issue: Issue) -> Issue | None:
    """
    Retrieve the epic associated with the given issue.
    """
    if not hasattr(issue.fields, "parent"):
        return None

    parent: Issue = issue.fields.parent

    if parent.fields.issuetype.name == "Story":
        story = jira_client.search_issues(f"key = {parent.key}")[0]
        parent = jira_client.search_issues(f"key = {story.fields.parent.key}")[0]

    return parent


def generate_report(df: pd.DataFrame) -> str:
    """
    Generate a report based on the provided DataFrame.
    """
    content = markdown.Markdown()
    content = f"# ISSUES IN TEST ENVIRONMENT DATE: {datetime.date.today().strftime('%d/%m/%Y')}\n"

    for application in df["issue_labels"].sort_values(na_position="last").explode().unique():  # pyright: ignore[reportCallIssue]
        if application:
            content += f"## {application}\n"
            df_application = pd.DataFrame(df[df["issue_labels"].apply(lambda i: i is not None and application in i)])
        else:
            content += "## Application Unknown\n"
            df_application = pd.DataFrame(df[df["issue_labels"].isna()])

        df_epic = (  # pyright: ignore[reportCallIssue]
            df_application[["epic_key", "epic_name"]].drop_duplicates().sort_values("epic_key", na_position="last")
        )
        for _, epic_key, epic_name in df_epic.itertuples():
            if epic_key:
                content += f"### [{epic_key}]({os.getenv('JIRA_HOST')}/browse/{epic_key}) {epic_name}\n"
                df_issue = pd.DataFrame(df_application[df_application["epic_key"] == epic_key])
            else:
                content += "### Epic Unknown\n"
                df_issue = pd.DataFrame(df_application[df_application["epic_key"].isna()])

            df_features = pd.DataFrame(df_issue[(df_issue["issue_type"] == "Sviluppo")][["issue_key", "issue_name"]])
            if not df_features.empty:
                content += "**Features:**\n\n"
                for _, issue_key, issue_name in df_features.itertuples():
                    content += f"- [{issue_key}]({os.getenv('JIRA_HOST')}/browse/{issue_key}) {issue_name}\n"

            df_bugfixes = pd.DataFrame(df_issue[(df_issue["issue_type"] == "Bug")][["issue_key", "issue_name"]])
            if not df_bugfixes.empty:
                content += "**Bugfixes:**\n\n" if df_features.empty else "\n**Bugfixes:**\n"
                for _, issue_key, issue_name in df_bugfixes.itertuples():
                    content += f"- [{issue_key}]({os.getenv('JIRA_HOST')}/browse/{issue_key}) {issue_name}\n"

    html_content = markdown.markdown(content, extensions=["extra", "codehilite"])
    css_style = """
    <style>
        body { font-family: 'Helvetica', sans-serif; line-height: 1.6; color: #333; padding: 50px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #eee; }
        code { background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
        pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
    """

    return f"<html><head>{css_style}</head><body>{html_content}</body></html>"


def main(date: datetime.date, status: str, project: str):
    """
    Main function to generate the report.
    """
    days_difference = ((datetime.date.today() - date).days if date else 0) + 1
    jira_updated = f"-{days_difference}d"

    df = pd.DataFrame(
        columns=[  # pyright: ignore[reportArgumentType]
            "issue_key",
            "issue_name",
            "issue_description",
            "issue_type",
            "issue_labels",
            "epic_key",
            "epic_name",
            "epic_type",
        ]
    )
    issues = jira_client.search_issues(
        f"project IN ({project}) AND status = {status} AND type IN (Sviluppo,Bug) AND updated >= {jira_updated}",
        maxResults=0,
    )

    print(f"find {len(issues)} issues in the {status} status of the {project} project from last {days_difference} days")
    print("processing issues...")

    for issue in tqdm(issues):
        epic = get_epic(issue)
        df.loc[df.size + 1] = [
            issue.key,
            issue.fields.summary,
            issue.fields.description,
            issue.fields.issuetype.name,
            issue.fields.labels or None,
            epic.key if epic else None,
            epic.fields.summary if epic else None,
            epic.fields.issuetype.name if epic else None,
        ]

    print("generating report...")
    HTML(string=generate_report(df)).write_pdf("report.pdf")
    print(f"writing report to file {os.getcwd()}/report.pdf")


def run():
    """
    Parses command-line arguments and initiates the report generation process.
    """
    parser = argparse.ArgumentParser(description="Generate JIRA report generator")
    parser.add_argument(
        "--date",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        help="Start date for report generation (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--status",
        type=str,
        required=True,
        help="Status of the issues to include in the report",
    )
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Project key to include in the report",
    )
    args = parser.parse_args()
    try:
        main(args.date, args.status, args.project)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    run()
