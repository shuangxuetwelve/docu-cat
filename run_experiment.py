import os
import argparse
from langfuse import Evaluation, get_client
from run_docu_cat import main as run_docu_cat_main
from experiment import calculate_f1_score


def main():
  parser = argparse.ArgumentParser(
    description='Run DocuCat experiment with evaluation'
  )

  parser.add_argument(
    '--path',
    type=str,
    required=True,
    help='Path to the repository'
  )

  args = parser.parse_args()

  langfuse = get_client()

  def task(*, item, **kwargs):
    repo_path = os.path.join(args.path, item.input)
    return run_docu_cat_main(repo_path)

  def evaluator(*, input, output, expected_output, metadata, **kwargs):
    result = output
    expected_result = expected_output
    documents_updated = result.get("documents_updated")
    expected_documents_updated = expected_result.get("documents_updated")
    return Evaluation(
      name="F1 Score",
      value=calculate_f1_score(documents_updated, expected_documents_updated),
    )

  dataset = langfuse.get_dataset("default")

  result = dataset.run_experiment(
    name="DocuCat Experiment",
    description="Testing DocuCat on local data",
    task=task,
    evaluators=[evaluator],
  )

  print(result.format())


if __name__ == "__main__":
  main()
