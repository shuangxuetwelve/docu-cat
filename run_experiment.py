from langfuse import Evaluation, get_client
from run_docu_cat import main
from experiment import calculate_f1_score


langfuse = get_client()

def task(*, item, **kwargs):
  repo_path = item.input
  return main(repo_path)

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
