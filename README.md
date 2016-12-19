# KPI Tool

This is the KPI Tool for Mooncake Content Team

## Prerequisite

1. Acom Repo and Acn Repo.

    > **Note**: Macke Sure that the Acom Repo contains a branch with the name as the last sync date, and the Acn Repo contains a branch with the name as the first content refresh date. For example, if you want get the KPI report for December, 2016, you need to have branch "10182016" in Acom, and branch "12052016" in Acn.

1. Install Python 3.5.

1. Use pip to install the requirements.

        pip install -r requirements.txt

## How to

Run the following command.

    python KPI_tool.py /path/to/techcontent/ /path/to/azure-content-pr/

you can get the report in output.csv and output2.csv