#!/usr/bin/env bash
#
# Make a few requests against an animalia server to confirm it works as
# expected. If everything works as expected, not output is shown. If there are
# issues, they are printed to stdout.
#
# Known to work with modern bash (>=4) and curl (>=7.18.0).
#
# Environment variables:
#
#   ANIMALIA_BASE_URL  Base url of the animalia service to test. Defaults to http://localhost:8080
#

ANIMALIA_BASE_URL=${ANIMALIA_BASE_URL:-http://localhost:8080}
# Remove trailing slash, if one is present, from base url.
ANIMALIA_BASE_URL=${ANIMALIA_BASE_URL%/}

# Check that service is available.
CURL="curl -s -H 'Content-Type: application/json' -H 'Accept: application/json'"

# Declare some helper functions.
function get_url() {
    local path=$1;
    # Remove leading slash, if one is present, from path.
    path=${path#/}
    echo ${ANIMALIA_BASE_URL}/${path}
}

# Very crude and fragile method for parsing a field's value out of a json document.
function parse_field() {
    local field=$1
    local body=${@:2}
    echo $body | \
        grep "${field}" | \
        cut -d: -f2 | \
        sed -E 's#.*"([^"]+)".*#\1#g'
}

# POST /animals/facts
function create_fact() {
    local fact=${@}
    local response=$(${CURL} -X POST "$(get_url /animals/facts)" --data "{\"fact\": \"${fact}\"}")
    parse_field id $response
}

# GET /animals/facts/<id>
function get_fact() {
    local id=$1
    local response=$(${CURL} -X GET "$(get_url /animals/facts/${id})")
    parse_field fact $response
}

# GET /animals?q=<question>
function query() {
    local question=$@
    local response=$(${CURL} -X GET "$(get_url /animals)" --get --data-urlencode "q=${question}")
    parse_field fact $response
}

# Count and report errors.
ERROR_COUNT=0
function report() {
    if [ "${ERROR_COUNT}" = "0" ] ; then
        echo "SUCCESS  All checks passed."
    else
        echo "ERROR  ${ERROR_COUNT} checks failed."
    fi
}
trap report EXIT

# Provide some assert utility functions.
function assert_equal() {
    local actual=$1
    local expected=$2
    local msg=$3
    if [ "${actual}" != "${expected}" ] ; then
        ERROR_COUNT=$((${ERROR_COUNT} + 1))
        echo "ERROR ${msg}"
        echo "          Expected '${expected}' but found '${actual}'."
        echo ""
    fi
}

function assert_contains() {
    local actual=$1
    local expected_contains=$2
    local msg=$3
    if [[ "${actual}" != *"${expected_contains}"* ]] ; then
        ERROR_COUNT=$((${ERROR_COUNT} + 1))
        echo "ERROR ${msg}"
        echo "          Expected '${actual}' to contain '${expected_contains}'."
        echo ""
    fi
}

# Add two facts, capture the IDs, and verify the facts can be retrieved.
fact_a="the otter lives in rivers"
id_a=$(create_fact $fact_a)

fact_b="the cormorant is a bird"
id_b=$(create_fact $fact_b)

actual_fact_a=$(get_fact $id_a)
assert_equal "${actual_fact_a}" "${fact_a}" \
             "Retrieving fact by id did not return original fact."

actual_fact_b=$(get_fact $id_b)
assert_equal "${actual_fact_b}" "${fact_b}" \
             "Retrieving fact by id did not return original fact."

# Ask question, verify answer.
question_a="where does the otter live?"
answer_a=$(query $question_a)
assert_contains "${answer_a}" "river" \
                "Querying where otters live did not include river."

# Add fact_b again, verify id is same as original.
fact_b2=${fact_b}
id_b2=$(create_fact $fact_b2)
assert_equal "${id_b2}" "${id_b}" \
             "Creating the same fact did not return the original id."
