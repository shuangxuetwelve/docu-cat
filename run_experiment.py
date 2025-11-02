import os
import argparse
from langfuse import Evaluation, get_client
from run_docu_cat import run_docu_cat
from experiment import calculate_f1_score


LOCAL_DATASET = [
  {"input": "docu-cat-dataset-next-js", "expected_output": "1. **docs/COMPONENTS.md**\n   - Changed section heading from \"## DocuCatButton\" to \"## ButtonBase\"\n   - Updated import statement from `import { DocuCatButton }` to `import { ButtonBase }`\n   - Updated all code examples to use `<ButtonBase>` instead of `<DocuCatButton>`\n   - Updated description to reflect the new component name\n\n2. **README.md**\n   - Updated component reference in the documentation list from `[DocuCatButton](components/DocuCatButton.tsx)` to `[ButtonBase](components/ButtonBase.tsx)`\n\n3. **components/ButtonSmall.tsx**\n   - Updated JSDoc comment: Changed \"It inherits all the features of the DocuCatButton component\" to \"It inherits all the features of the ButtonBase component\"\n\n4. **components/TextButton.tsx**\n   - Updated TODO comment: Changed \"use the DocuCatButton component as a base\" to \"use the ButtonBase component as a base\""},
]

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

  parser.add_argument(
    '--local',
    action='store_true',
    help='Run the experiment on local data'
  )

  args = parser.parse_args()

  langfuse = get_client()

  def task(*, item, **kwargs):
    print('item', item)
    try:
      input = item["input"]
    except:
      input = item.input
    repo_path = os.path.join(args.path, input)
    return run_docu_cat(repo_path)

  def evaluator(*, input, output, expected_output, metadata, **kwargs):
    result = output
    expected_result = expected_output
    documents_updated = result.get("documents_updated")
    expected_documents_updated = expected_result.get("documents_updated")
    return Evaluation(
      name="F1 Score",
      value=calculate_f1_score(documents_updated, expected_documents_updated),
    )


  if args.local:
    result = langfuse.run_experiment(
      name="DocuCat Experiment",
      description="Testing DocuCat on local data",
      data=LOCAL_DATASET,
      task=task,
      evaluators=[evaluator],
    )
  else:
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
