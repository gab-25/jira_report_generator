# jira_report_generator

This script generates a PDF report (`report.pdf`) based on issues from a Jira project. The report groups issues by
application (using Jira labels) and by epic, separating new features from bug fixes.

## Prerequisites

- Python 3.x
- The dependencies listed in the `requirements.txt` file.

## Installation

1. Clone this repository to your computer.
2. Install the necessary dependencies by running the following command from the project root:
   ```bash
   pip install .
   ```

## Configuration

Before running the script, you need to configure your Jira credentials and project specifications.

Create a configuration file named `.env` in the `jira_report_generator/jira_report_generator/` directory. This file must contain the following variables:

- `JIRA_HOST`: The URL of your Jira instance.
- `JIRA_USERNAME`: Your username for Jira access (usually your email).
- `JIRA_API_TOKEN`: An API token generated from Jira for authentication. You can create one by following
  the [official Atlassian guide](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/).

## Usage

Once the configuration is complete, run the script with the following command:

```bash
jira-report-generator --status=<status> --project=<project>
```

The script will connect to Jira, retrieve the issues that match the defined criteria (`project`, `status`, and type
`Sviluppo` or `Bug`), and generate a `report.pdf` file in the project\'s root directory.

The report will be formatted as follows:

- A title with the generation date.
- A section for each "application" (based on issue labels).
- A sub-section for each "epic".
- Bulleted lists for "Features" (issues of type "Sviluppo") and "Bugfixes" (issues of type "Bug").
