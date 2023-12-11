import os
import json
from datetime import datetime

import httpx
import click
from click import ClickException
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.api.resources.commons.types.dataset_status import DatasetStatus
from canopy.models.data_models import MessageBase
from canopy_server.models.v1.api_models import ChatRequest

class Error(ClickException):
    def format_message(self) -> str:
        return click.style(self.message, fg='red')

def evaluate():
    try:
        load_dotenv()

        CE_DEBUG_INFO = os.getenv("CE_DEBUG_INFO", "FALSE").lower() == "true"

        if not CE_DEBUG_INFO:
            msg = "Evaluation failed: CE_DEBUG_INFO environment variable must be set to true"
            raise Error(msg)

        missing_vars = []

        for var in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "LANGFUSE_EVALUATION_DATASET_NAME"]:
            if var not in os.environ:
                missing_vars.append(var)
        if missing_vars:
            raise Error(f"Evaluation failed: Missing environment variables: {', '.join(missing_vars)}")

        DATASET_NAME = os.environ.get("LANGFUSE_EVALUATION_DATASET_NAME")

        langfuse = Langfuse()

        # Retrieve the dataset
        langfuse_dataset = langfuse.get_dataset(name=DATASET_NAME)
        dataset_items = langfuse_dataset.items

        # Filter active items
        active_items = [item for item in dataset_items if item.status == DatasetStatus.ACTIVE]

        # Prepare the data
        evaluation_data = []

        # Process each active item
        for item in active_items:

            item_data = {
                'item_id': item.id,
                'input': item.input,
                'expected_output': item.expected_output['content']
            }

            try:
                # Convert inputs to MessageBase objects
                messages = [MessageBase(role=msg["role"], content=msg["content"]) for msg in item.input]

                # Construct the request payload
                payload = ChatRequest(
                    messages=[message.dict() for message in messages]
                ).dict()

                # Send the request to the chat engine
                with httpx.Client(timeout=60) as client:
                    response = client.post(
                        "http://127.0.0.1:8000/v1/chat/completions",
                        json=payload,
                    ).json()

                # Extract the output content from the response
                item_data['output'] = response['choices'][0]['message']['content']
                item_data['context'] = response['debug_info']['context']['content']
                item_data['query_results'] = response['debug_info']['context']['query_results']

                output_block = (
                    f"\n{click.style('ANSWER', fg='yellow')}\n"
                    f"\n{item_data['output']}\n"
                    f"\n{click.style('EXPECTED ANSWER', fg='green')}\n"
                    f"\n{item_data['expected_output']}\n"
                )
                click.echo(output_block)

                click.echo(click.style("\n.", fg="bright_black"))
                click.echo(
                    click.style(
                        f"| {len(evaluation_data) + 1}", fg="bright_black", bold=True
                    ),
                    nl=True,
                )
                click.echo(click.style("˙▔▔▔", fg="bright_black", bold=True), nl=False)
                click.echo(click.style("˙", fg="bright_black", bold=True))

            except Exception as e:
                # Log the error
                click.echo(click.style(f"Error processing item {item.id}: {e}", fg='red'))
                item_data['output'] = None
                item_data['context'] = None
                item_data['query_results'] = None

            # Append the processed data to the evaluation_data list
            evaluation_data.append(item_data)

        os.makedirs('evaluations', exist_ok=True)

        # Write the data to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluations/evaluation_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(evaluation_data, jsonfile, ensure_ascii=False, indent=4)

        click.echo(click.style(f"\nEvaluation finished. Data has been saved to {filename}", fg='blue'))

    except Error as e:
        click.echo(e.format_message(), err=True)
        return

if __name__ == "__main__":
    evaluate()
