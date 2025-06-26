# NixOS Surveys

This repository hosts survey materials, results, and analyses relevant to the NixOS project.
While it was originally created to support our annual community survey, it has been restructured to accommodate multiple types of surveys in the future.

## Structure

Surveys are organized into directories by type.
Each directory typically contains:

- Survey questions and methodology
- Code used to process, analyze, and visualize results
- Aggregated and anonymized data summaries
- Synthetic data
- _Raw data is **not** included to protect respondent privacy_

Current structure:

```
surveys/
├── community/       # Community-wide annual surveys
# └── future/        # Other survey types (e.g., contributor, event, sponsor)
```

## Purpose

Surveys help the NixOS community:

- Understand how users and contributors engage with the project
- Identify areas for improvement in the ecosystem and community
- Track project growth and ecosystem trends over time
- Support data-informed decision-making across teams

## Data Handling and Privacy

We take respondent privacy seriously. To that end:

- **Raw survey results are not published in this repository.**
  These typically contain granular metadata that could risk identification.
- Only aggregated and anonymized results are made public.
- Where possible, we may consider publishing normalized or synthetic data that preserves trends without exposing individual responses.
  This can be used by those who want to contribute to the processing code but do not have access to the raw result data.
- Data processing code in the repository reflect how raw inputs are transformed into public outputs.

## Contributions

Contributions are welcome!
We encourage transparency and community participation in all stages of the survey process, from question design to result interpretation.
If you'd like to propose a new survey or help with analysis, feel free to open an issue or pull request.
For larger proposals, consider discussing them on [Discourse](https://discourse.nixos.org) or in the relevant team meetings (e.g., [Marketing Team](https://github.com/nixos/marketing)).
