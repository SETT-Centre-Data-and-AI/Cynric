## v1.7.6 (2026-07-06)

### Feat

- add description normalization and truncation for forms

## v1.7.5 (2026-06-16)

### Fix

- **test_08_config_injection.py**: fixed new default

## v1.7.4 (2026-06-16)

### Feat

- **instantiation**: enforce_no_null_columns = False (fine for csv API)

## v1.7.3 (2026-06-16)

### Feat

- **instantiation**: added enforce_no_null_column valediction injection

### Fix

- **tests**: fixed testing setup to add internal only tests

## v1.7.2 (2026-03-24)

### Feat

- **config.yaml**: fixed repo urls

## v1.7.1 (2026-03-24)

### Feat

- **pk_char_limit**: added valediction override for pk col max length… (#36)

## v1.7.0 (2026-03-05)

### Feat

- **pk_char_limit**: added valediction override for pk col max length of 64
- **utils**: added column_validator to normalise column names to be compatible with BC insight (#29)

### Fix

- **uploading**: columns uppercase before upload

## v1.6.0 (2026-02-06)

### Fix

- **push_demo_data**: fixed issue with unattached data dictionary, and imported data
- **uploading**: fixed retarget_total failure when data are already imported

## v1.5.0 (2026-02-03)

### Fix

- **README.md**: spelling

## v1.3.0 (2026-02-03)

### Feat

- **bigint-&-timestamp**: wired in valediction changes, inc v1.5, timestamp change, and bigint checking

## v1.2.0 (2026-02-02)

### Fix

- **forms**: fix to form and bc dictionary creation so that composite primary keys are assigned auto-incremented integers correctly

### Refactor

- **forms**: renamed function names for creating bc specific files + added to readme

## v1.1.0 (2026-02-02)

### Fix

- **forms**: fix to form and bc dictionary creation so that composite primary keys are assigned auto-incremented integers correctly

### Refactor

- **forms**: renamed function names for creating bc specific files + added to readme

## v1.0.0 (2025-12-18)

### Feat

- **dataset_manager**: Add dataset mapping and filtering utilities
- **api**: Enhance job status logging during file upload process
- **api**: Implement file upload and job queue management with supporting utilities
- **api**: Add job status retrieval and queue management for file uploads

### Refactor

- **imports**: added full cynric.xxx to imports
- Moved api related files to separate api folder

## v0.1.1 (2025-11-26)

### Feat

- **setup**: imported code

### Fix

- **pyproject.toml**: fixed pyproject.toml
