def calculate_recall(predicted_files, expected_files):
  if len(set(expected_files)):
    return len(set(predicted_files) & set(expected_files)) / len(set(expected_files))
  else:
    return 1

def calculate_precision(predicted_files, expected_files):
  if len(predicted_files):
    return len(set(predicted_files) & set(expected_files)) / len(set(predicted_files))
  else:
    return 1

def calculate_f1_score(predicted_files, expected_files):
  return 2 * (calculate_precision(predicted_files, expected_files) * calculate_recall(predicted_files, expected_files)) / (calculate_precision(predicted_files, expected_files) + calculate_recall(predicted_files, expected_files))
