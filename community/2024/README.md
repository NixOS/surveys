Survey was inserted manually to LimeSurvey.

To get test to easily copy/paste to "Quick add", use the command:

```bash
yq '.questions|map({type,prompt,choices:(.choices // []|join("\n"))})|.[]' survey.yaml  | jq -r '"----------\n[\(.type)]\n\(.prompt)\n\n\(.choices)\n"'
```
