# Steps to do an Evaluation

1. **Create a Test set**: Upload an Excel file with sample inputs and, optionally, expected outputs.

2. **Launch an Evaluation**: Select tool, test set, and number of iterations, and start the Evaluation. Check the status of the Evaluation job - once it is `Completed`, it’s ready for analysis.

3. **Analyze results per record**: Go through Evaluation records and check how the LLM performed compared to expected outputs or without comparison. Put scores from 1 to 5 and add notes if necessary.

4. **Get total results**: average score, latency, and cost are calculated automatically. The more evaluation records you score, the more accurate total/average score is.

5. **Improve**: using the Evaluation outcome, go to evaluated tool and improve its configuration. Iterate as many times as possible until you reach an acceptable level of accuracy and consistency.
