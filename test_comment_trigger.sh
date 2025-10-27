#!/bin/bash
# Test script to validate comment-trigger workflow trigger patterns

echo "Testing DocuCat comment trigger patterns..."
echo

test_pattern() {
    local comment="$1"
    local expected="$2"

    if echo "$comment" | grep -iE '@docu-?cat|run.?docu-?cat' > /dev/null; then
        result="triggers"
    else
        result="no trigger"
    fi

    if [ "$result" = "$expected" ]; then
        echo "✅ PASS: \"$comment\" -> $result"
    else
        echo "❌ FAIL: \"$comment\" -> expected $expected, got $result"
    fi
}

# Test cases that should trigger
echo "Test cases that SHOULD trigger DocuCat:"
test_pattern "@DocuCat" "triggers"
test_pattern "@docu-cat" "triggers"
test_pattern "@docucat" "triggers"
test_pattern "run docu-cat" "triggers"
test_pattern "run docucat" "triggers"
test_pattern "Run Docu-Cat" "triggers"
test_pattern "@DocuCat please update the docs" "triggers"
test_pattern "Can you run docu-cat on this?" "triggers"

echo
echo "Test cases that should NOT trigger DocuCat:"
test_pattern "LGTM!" "no trigger"
test_pattern "Great work on this PR" "no trigger"
test_pattern "Please review" "no trigger"
test_pattern "The documentation looks good" "no trigger"

echo
echo "All tests completed!"
