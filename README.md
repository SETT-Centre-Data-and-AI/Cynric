<p align="center">
  <img src="docs/images/cynric.png" alt="cynric", width=300>
</p>

# Cynric
_**Wessex SDE data validation & API uploader**_

**Cynric** is a convenience package for validating research datasets against a **data dictionary** and securely uploading them into the **Wessex Secure Data Environment (SDE)**.

Under the hood, Cynric uses **[Valediction](https://github.com/SETT-Centre-Data-and-AI/Valediction)** for dictionary-driven constraint enforcement, then handles authenticated upload to targeted SDE database tables — including **chunked uploads** for large datasets and **streamed reading** to optimise local RAM usage.

Developed by the Wessex SDE, University of Southampton CIRU, and University Hospital Southampton SETT Centre for use in clinical research workflows, Cynric is designed to fit into reproducible analytical pipelines for automatic SDE validation & data upload.

**Features**:
- **Validates** a user's dataset against an accompanying data dictionary to enforce constraints and data integrity
- **Uploads** validated datasets to targeted Wessex SDE database tables
- **Chunking** for large datasets to support stable transfer and RAM optimisation
- **Secures credentials** via `keyring` to keep API keys out of repositories and retrieves for convenience
- **Checks table access** quickly to confirm user permissions and review table access


# 🧭 Resources
- [Installation](./docs/installation-guide.md)
- [Valediction](https://github.com/SETT-Centre-Data-and-AI/Valediction) (_data dictionary driven validation_)
- [Data Dictionary Template ⬇️](./src/valediction/dictionary/template/PROJECT%20-%20Data%20Dictionary.xltx) (_download_)

# ⚡ Quickstart
### Demo/Test
1) Install: `pip install cynric` (or use your favoured package manager)
2) Contact the Wessex SDE team for your API key and endpoint
3) Request the demo tables be established in your workspace
4) Run the following test using Cynric's inbuilt demo data:

```python
import cynric

## Save Credentials to OS Credential Storage (one-time)
cynric.save_credentials(
    base_url = "https://YOUR_WESSEX_SDE_ENDPOINT",
    token = "YOUR_API_KEY"
)  # Scrub from code once saved for max security


## Identify Tables for Demo Upload
sde_tables = cynric.check_table_access(print=True)
```
```python
## Upload Demo Data
cynric.demo.push_demo_data(
    target_table_map = {  # enter target tables
        "DEMOGRAPHICS": "dsXXXXXX",
        "DIAGNOSES": "dsXXXXXX",
        "LAB_TESTS": "dsXXXXXX",
        "VITALS": "dsXXXXXX",
    }
)
```

### Data Upload
1) Following Wessex SDE setup of workspace & tables, upload your data:

```python
import cynric
from cynric import demo

# Import Data & Dictionary and Review
dataset = cynric.Dataset.create_from(demo.DEMO_DATA)
dataset.import_dictionary(demo.DEMO_DICTIONARY)
dataset
```

```python
# Identify Tables
sde_tables = cynric.check_table_access(print=True)
```

```python
cynric.validate_and_upload(
    dataset,
    target_table_map={
        "TABLE_NAME_1": "dsXXXXXX",
        "TABLE_NAME_2": "dsXXXXXX",
        # etc...
    },
)
```

# 🧠 Function Quicklist
### Preparation
- `save_credentials()` - securely store the Wessex SDE endpoint + API key in your OS's credential manager
- `delete_credentials()` - remove stored credentials from your OS's credential manager
- `check_table_access()` - confirm access/permissions to a target SDE table (useful before upload)

### Validation & Upload
- `Dataset.create_from()` - create a Cynric Dataset from a folder of files, or dictionary of DataFrames
- `validate_and_upload()` - validate the dataset and upload to the target SDE tables (supports chunked upload)

# 🤝 Contributing
Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

# ⚖️ License
This work is licensed under a
[Creative Commons Attribution-NonCommercial 4.0 International License][cc-by-nc].
[![CC BY-NC 4.0][cc-by-nc-shield]][cc-by-nc]

[cc-by-nc]: https://creativecommons.org/licenses/by-nc/4.0/
[cc-by-nc-shield]: https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg

# 🧑‍🔬 Authors
Cynric was developed by Ben Sale, Cai Davis, and Michael George across the Wessex SDE, University Hospital Southampton NHSFT's Data & AI Research Unit (DAIR), and the University of Southampton's Clinical Informatics Research Unit (CIRU)

[CIRU]: https://www.the-ciru.com/
[SETT]: https://github.com/SETT-Centre-Data-and-AI
[WSDE]: https://wessexsde.nhs.uk/

### Collaborators
- [Wessex Secure Data Environment (SDE)][WSDE]
- [Southampton Emerging Therapies and Technology (SETT) Centre][SETT]
- [Clinical Informatics Research Unit (CIRU)][CIRU]

<p align="center">
  <a href="https://github.com/SETT-Centre-Data-and-AI">
    <img src="docs/images/SETT Header.png" alt="NHS UHS SETT Centre">
  </a>
</p>

<p align="center">
  <a href="https://wessexsde.nhs.uk/">
    <img src="docs/images/Wessex SDE Header.png" alt="Wessex SDE">
  </a>
</p>

<p align="center">
  <a href="https://www.the-ciru.com/">
    <img
      src="docs/images/CIRU Header.png"
      alt="CIRU"
      style="width: 100%; max-width: 1900px; height: auto;"
    >
  </a>
</p>
