#!/bin/bash

# Flow Implementation Orchestration Script
# This script orchestrates the execution of Cursor commands to implement a data flow
# following the template pattern. It reads flow requirements from a markdown file.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
CURSOR_COMMANDS_DIR="${PROJECT_ROOT}/.cursor/commands"
TEMP_DIR="${PROJECT_ROOT}/.template/flows/.temp_outputs"

# Create temp directory for outputs
mkdir -p "${TEMP_DIR}"

# Flow requirements file (required)
FLOW_REQUIREMENTS_FILE=""

# Options
DRY_RUN=false
SKIP_TESTS=false
SKIP_OPTIMIZE=false
START_FROM=""

# Command execution order
COMMANDS=(
    "setup_flow_structure"
    "implement_extract"
    "implement_transform"
    "implement_load"
    "implement_job"
    "optimize_flow"
    "implement_unit_tests"
    "run_and_fix_tests"
    "review_flow_implementation"
)

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 --requirements <requirements_file.md> [OPTIONS]

Orchestrates the implementation of a data flow by executing Cursor commands in sequence.
The requirements file should contain all information needed to implement the flow.

Required Arguments:
  --requirements <file.md>  Path to markdown file with flow requirements

Options:
  --dry-run                 Show what would be executed without running commands
  --skip-tests              Skip test creation and execution
  --skip-optimize           Skip flow optimization step
  --start-from <command>    Start execution from a specific command
  --help                    Show this help message

Available Commands (in execution order):
  - setup_flow_structure
  - implement_extract
  - implement_transform
  - implement_load
  - implement_job
  - optimize_flow
  - implement_unit_tests
  - run_and_fix_tests

Requirements File Format:
The requirements file should be a markdown file containing all information needed
to implement the flow. It will be passed to each command as context.

Example requirements file structure:
  # Flow Requirements
  
  ## Flow Information
  - Name: customers_bronze
  - Purpose: Extract and load raw customer data
  - Layer: Bronze
  
  ## Source Requirements
  - Type: Table
  - Location: catalog.database.table
  - Format: Iceberg
  ...
  
  ## Target Requirements
  ...

Examples:
  # Full flow implementation
  $0 --requirements flow_requirements.md

  # Dry run to see what would be executed
  $0 --requirements flow_requirements.md --dry-run

  # Skip tests
  $0 --requirements flow_requirements.md --skip-tests

  # Start from transform (skip setup and extract)
  $0 --requirements flow_requirements.md --start-from implement_transform

EOF
}

# Function to validate requirements file
validate_requirements_file() {
    local file="$1"
    
    if [[ -z "${file}" ]]; then
        print_error "Requirements file cannot be empty"
        return 1
    fi
    
    if [[ ! -f "${file}" ]]; then
        print_error "Requirements file not found: ${file}"
        return 1
    fi
    
    if [[ ! "${file}" =~ \.md$ ]]; then
        print_warning "Requirements file should be a markdown file (.md)"
    fi
    
    return 0
}

# Function to extract flow name from requirements file
extract_flow_name() {
    local file="$1"
    
    # Try to extract flow name from the file
    # Look for patterns like "Name: flow_name" or "# Flow Name: flow_name"
    local name=$(grep -iE "^[#\s]*-?\s*Name\s*:\s*" "${file}" | head -1 | sed -E 's/^[#\s]*-?\s*Name\s*:\s*//i' | tr -d ' ' || echo "")
    
    if [[ -z "${name}" ]]; then
        # Try alternative patterns
        name=$(grep -iE "flow[_\s]?name\s*[:=]\s*" "${file}" | head -1 | sed -E 's/.*flow[_\s]?name\s*[:=]\s*//i' | tr -d ' ' || echo "")
    fi
    
    echo "${name}"
}

# Function to check if command exists
command_exists() {
    local cmd="$1"
    command -v "$cmd" >/dev/null 2>&1
}

# Function to check if editor CLI is available
check_editor_available() {
    if command_exists cursor; then
        print_info "Cursor CLI found - will open files in Cursor IDE"
        return 0
    elif command_exists code; then
        print_warning "Cursor CLI not found, but VS Code 'code' command is available"
        print_warning "Will use VS Code to open files. You can execute commands in Cursor IDE manually."
        return 0
    else
        print_warning "No editor CLI found (cursor or code)"
        print_warning "You'll need to open files manually and execute commands in Cursor IDE"
        return 0  # Don't fail, just warn
    fi
}

# Function to check if cursor-agent is available
command_exists_agent() {
    command_exists cursor-agent
}

# Function to process streaming JSON output from cursor-agent
process_stream_output() {
    local command_name="$1"
    local accumulated_text=""
    local tool_count=0
    local start_time=$(date +%s)
    local final_result=""
    local final_json=""
    
    while IFS= read -r line; do
        # Skip empty lines
        [[ -z "${line}" ]] && continue
        
        # Try to parse as JSON
        local type=$(echo "${line}" | jq -r '.type // empty' 2>/dev/null || echo "")
        local subtype=$(echo "${line}" | jq -r '.subtype // empty' 2>/dev/null || echo "")
        
        case "${type}" in
            "system")
                if [[ "${subtype}" == "init" ]]; then
                    local model=$(echo "${line}" | jq -r '.model // "unknown"' 2>/dev/null || echo "unknown")
                    echo -e "${BLUE}[INFO]${NC} 🤖 Using model: ${model}"
                fi
                ;;
                
            "assistant")
                # Accumulate incremental text deltas for smooth progress
                local content=$(echo "${line}" | jq -r '.message.content[0].text // empty' 2>/dev/null || echo "")
                if [[ -n "${content}" ]]; then
                    accumulated_text="${accumulated_text}${content}"
                    # Show live progress (updates with each character delta)
                    printf "\r${BLUE}[INFO]${NC} 📝 Generating: %d chars" ${#accumulated_text}
                fi
                ;;
                
            "tool_call")
                if [[ "${subtype}" == "started" ]]; then
                    tool_count=$((tool_count + 1))
                    
                    # Extract tool information
                    if echo "${line}" | jq -e '.tool_call.writeToolCall' > /dev/null 2>&1; then
                        local path=$(echo "${line}" | jq -r '.tool_call.writeToolCall.args.path // "unknown"' 2>/dev/null || echo "unknown")
                        echo -e "\n${BLUE}[INFO]${NC} 🔧 Tool #${tool_count}: Creating ${path}"
                    elif echo "${line}" | jq -e '.tool_call.readToolCall' > /dev/null 2>&1; then
                        local path=$(echo "${line}" | jq -r '.tool_call.readToolCall.args.path // "unknown"' 2>/dev/null || echo "unknown")
                        echo -e "\n${BLUE}[INFO]${NC} 📖 Tool #${tool_count}: Reading ${path}"
                    elif echo "${line}" | jq -e '.tool_call.searchToolCall' > /dev/null 2>&1; then
                        echo -e "\n${BLUE}[INFO]${NC} 🔍 Tool #${tool_count}: Searching codebase"
                    fi
                    
                elif [[ "${subtype}" == "completed" ]]; then
                    # Extract and show tool results
                    if echo "${line}" | jq -e '.tool_call.writeToolCall.result.success' > /dev/null 2>&1; then
                        local lines=$(echo "${line}" | jq -r '.tool_call.writeToolCall.result.success.linesCreated // 0' 2>/dev/null || echo "0")
                        local size=$(echo "${line}" | jq -r '.tool_call.writeToolCall.result.success.fileSize // 0' 2>/dev/null || echo "0")
                        echo -e "   ${GREEN}✅${NC} Created ${lines} lines (${size} bytes)"
                    elif echo "${line}" | jq -e '.tool_call.readToolCall.result.success' > /dev/null 2>&1; then
                        local lines=$(echo "${line}" | jq -r '.tool_call.readToolCall.result.success.totalLines // 0' 2>/dev/null || echo "0")
                        echo -e "   ${GREEN}✅${NC} Read ${lines} lines"
                    elif echo "${line}" | jq -e '.tool_call.searchToolCall.result' > /dev/null 2>&1; then
                        echo -e "   ${GREEN}✅${NC} Search completed"
                    fi
                fi
                ;;
                
            "result")
                local duration=$(echo "${line}" | jq -r '.duration_ms // 0' 2>/dev/null || echo "0")
                local end_time=$(date +%s)
                local total_time=$((end_time - start_time))
                
                # Extract final result
                final_result=$(echo "${line}" | jq -r '.result // empty' 2>/dev/null || echo "")
                
                echo -e "\n\n${GREEN}[SUCCESS]${NC} 🎯 Completed in ${duration}ms (${total_time}s total)"
                echo -e "${BLUE}[INFO]${NC} 📊 Final stats: ${tool_count} tools, ${#accumulated_text} chars generated"
                
                # Try to extract JSON from result
                if [[ -n "${final_result}" ]]; then
                    # Check if result contains a JSON block (```json ... ```)
                    if echo "${final_result}" | grep -q '```json'; then
                        final_json=$(echo "${final_result}" | sed -n '/```json/,/```/p' | grep -v '```' | jq -c . 2>/dev/null || echo "")
                    elif echo "${final_result}" | jq . >/dev/null 2>&1; then
                        # Result is already valid JSON
                        final_json=$(echo "${final_result}" | jq -c . 2>/dev/null || echo "")
                    else
                        # Try to extract JSON from the result string
                        final_json=$(echo "${final_result}" | jq -c . 2>/dev/null || echo "${final_result}")
                    fi
                fi
                ;;
        esac
    done
    
    # Return final JSON if available
    if [[ -n "${final_json}" ]]; then
        echo "${final_json}"
    elif [[ -n "${final_result}" ]]; then
        # Fallback: wrap result in simple JSON
        echo "{\"status\":\"success\",\"output\":\"${final_result}\"}"
    else
        echo "{\"status\":\"success\",\"tools_used\":${tool_count},\"chars_generated\":${#accumulated_text}}"
    fi
}

# Function to execute command using cursor-agent with streaming output
execute_with_cursor_agent() {
    local command_name="$1"
    local requirements_file="$2"
    local previous_outputs="$3"  # JSON string with previous command outputs
    local command_file="${CURSOR_COMMANDS_DIR}/${command_name}.md"
    local output_file="${TEMP_DIR}/${command_name}_output.json"
    
    if ! command_exists_agent; then
        return 1
    fi
    
    # Build prompt with context from previous commands
    local prompt="Execute the command /${command_name}. Using the requirements file: ${requirements_file} as context."
    
    # Add previous outputs as context if available
    if [[ -n "${previous_outputs}" && "${previous_outputs}" != "null" ]]; then
        prompt="${prompt}

        Previous command outputs (for context and continuity):
        ${previous_outputs}

        Use the previous outputs to understand what has been implemented so far and ensure consistency."
    fi
    
    prompt="${prompt}

        After execution, provide a structured summary in JSON format with:
        - status: 'success' or 'error'
        - files_created: [list of file paths created]
        - files_modified: [list of file paths modified]
        - key_decisions: [list of important implementation decisions]
        - schema_info: {input_schema: {...}, output_schema: {...}} (if applicable)
        - next_steps: [list of what the next command should know]
        - errors: [list of errors if any]"
    
    # Execute using cursor-agent with streaming output
    print_info "Invoking cursor-agent to execute command..."
    echo ""
    
    print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_info "Cursor Agent Output (streaming in real-time):"
    print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Execute with streaming JSON output, using --model auto and --force
    local json_output=""
    if json_output=$(cursor-agent -p --force --output-format stream-json --stream-partial-output --model auto --workspace "${PROJECT_ROOT}" "${prompt}" 2>&1 | process_stream_output "${command_name}"); then
        # Save output
        echo "${json_output}" > "${output_file}"
        
        echo ""
        print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_info "Command execution summary:"
        print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        if command_exists jq && [[ -n "${json_output}" ]]; then
            # Pretty print JSON summary
            local status=$(echo "${json_output}" | jq -r '.status // "success"' 2>/dev/null || echo "success")
            print_info "Status: ${status}"
            echo "${json_output}" | jq -r '.files_created // [] | "Files created: \(length)"' 2>/dev/null || true
            echo "${json_output}" | jq -r '.files_modified // [] | "Files modified: \(length)"' 2>/dev/null || true
        else
            # Fallback: show first few lines
            echo "${json_output}" | head -20
        fi
        echo ""
        
        # Return the extracted JSON output for next command
        echo "${json_output}"
        return 0
    else
        # If streaming fails, try regular JSON output as fallback
        print_warning "Streaming output failed, trying regular JSON output..."
        local raw_output=""
        if raw_output=$(cursor-agent --print --output-format json --workspace "${PROJECT_ROOT}" "${prompt}" 2>&1 | tee >(cat >&2)); then
            echo "${raw_output}" > "${output_file}"
            
            # Extract JSON from result
            local json_output=""
            if command_exists jq; then
                local result_text=$(echo "${raw_output}" | jq -r '.result // empty' 2>/dev/null || echo "")
                if echo "${result_text}" | grep -q '```json'; then
                    json_output=$(echo "${result_text}" | sed -n '/```json/,/```/p' | grep -v '```' | jq -c . 2>/dev/null || echo "")
                elif echo "${result_text}" | jq . >/dev/null 2>&1; then
                    json_output=$(echo "${result_text}" | jq -c . 2>/dev/null || echo "")
                else
                    json_output="${raw_output}"
                fi
            else
                json_output="${raw_output}"
            fi
            
            if [[ -n "${json_output}" ]]; then
                echo "${json_output}"
                return 0
            fi
        fi
    fi
    
    return 1
}

# Function to execute a Cursor command with requirements file and previous outputs
execute_cursor_command() {
    local command_name="$1"
    local previous_outputs="$2"  # JSON string with previous command outputs
    local command_file="${CURSOR_COMMANDS_DIR}/${command_name}.md"
    local requirements_file="${FLOW_REQUIREMENTS_FILE}"
    local output_file="${TEMP_DIR}/${command_name}_output.json"

    if [[ ! -f "${command_file}" ]]; then
        print_error "Command file not found: ${command_file}"
        return 1
    fi

    print_info "Executing command: ${command_name}"
    print_info "Requirements file: ${requirements_file}"
    
    if [[ "${DRY_RUN}" == true ]]; then
        print_info "[DRY RUN] Would execute: ${command_name}"
        print_info "Command file: ${command_file}"
        print_info "Requirements file: ${requirements_file}"
        if [[ -n "${previous_outputs}" ]]; then
            print_info "Previous outputs: ${previous_outputs}"
        fi
        return 0
    fi

    # Try to execute using cursor-agent first
    if command_exists_agent; then
        print_info ""
        print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_info "Command to execute: ${command_name}"
        print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_info ""
        print_info "Executing command using cursor-agent..."
        print_info "Command file: ${command_file}"
        print_info "Requirements file: ${requirements_file}"
        if [[ -n "${previous_outputs}" && "${previous_outputs}" != "null" ]]; then
            print_info "Including outputs from previous commands as context"
        fi
        print_info ""
        
        local command_output
        if command_output=$(execute_with_cursor_agent "${command_name}" "${requirements_file}" "${previous_outputs}"); then
            print_success "Command executed via cursor-agent"
            
            # Save output for next command
            if [[ -n "${command_output}" ]]; then
                echo "${command_output}" > "${output_file}"
                echo "${command_output}"  # Return output
            fi
            return 0
        else
            print_warning "cursor-agent execution had issues, falling back to manual execution"
            print_info ""
        fi
    fi
    
    # Fallback: Manual execution instructions
    print_info ""
    print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_info "Command to execute: ${command_name}"
    print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_info ""
    print_info "Files:"
    print_info "  📄 Command: ${command_file}"
    print_info "  📄 Requirements: ${requirements_file}"
    print_info ""
    print_info "How to execute manually:"
    print_info "  1. Open Cursor IDE"
    print_info "  2. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)"
    print_info "  3. Type or search for: /${command_name}"
    print_info "  4. Select and execute the command"
    print_info "  5. The command will read the requirements file for context"
    print_info ""
    
    # Try to open files (optional, may fail due to sandbox restrictions)
    if command_exists cursor || command_exists code; then
        print_info "Attempting to open files in editor..."
        if command_exists cursor; then
            cursor "${command_file}" "${requirements_file}" >/dev/null 2>&1 &
        elif command_exists code; then
            code "${command_file}" "${requirements_file}" >/dev/null 2>&1 &
        fi
        sleep 0.5
    fi
    
    # Wait for user confirmation
    echo ""
    print_info "After executing '${command_name}', press Enter to continue..."
    read -p "> "

    return 0
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Validate requirements file
    if ! validate_requirements_file "${FLOW_REQUIREMENTS_FILE}"; then
        return 1
    fi
    
    # Check if Cursor commands directory exists
    if [[ ! -d "${CURSOR_COMMANDS_DIR}" ]]; then
        print_error "Cursor commands directory not found: ${CURSOR_COMMANDS_DIR}"
        return 1
    fi
    
    # Check if all command files exist
    local missing_commands=()
    for cmd in "${COMMANDS[@]}"; do
        if [[ ! -f "${CURSOR_COMMANDS_DIR}/${cmd}.md" ]]; then
            missing_commands+=("${cmd}")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        print_error "Missing command files:"
        for cmd in "${missing_commands[@]}"; do
            print_error "  - ${cmd}.md"
        done
        return 1
    fi
    
    print_success "All prerequisites met"
    return 0
}

# Function to get command index
get_command_index() {
    local cmd="$1"
    for i in "${!COMMANDS[@]}"; do
        if [[ "${COMMANDS[$i]}" == "${cmd}" ]]; then
            echo "$i"
            return 0
        fi
    done
    return 1
}

# Function to filter commands based on options
filter_commands() {
    local filtered=()
    local start_index=0
    
    # Handle --start-from
    if [[ -n "${START_FROM}" ]]; then
        local idx=$(get_command_index "${START_FROM}")
        if [[ -z "${idx}" ]]; then
            print_error "Invalid command for --start-from: ${START_FROM}"
            return 1
        fi
        start_index=$((idx))
    fi
    
    # Handle --skip-tests
    local skip_tests_cmds=("implement_unit_tests" "run_and_fix_tests")
    
    # Handle --skip-optimize
    local skip_optimize_cmd="optimize_flow"
    
    for i in "${!COMMANDS[@]}"; do
        if [[ $i -lt $start_index ]]; then
            continue
        fi
        
        local cmd="${COMMANDS[$i]}"
        
        # Skip tests if requested
        if [[ "${SKIP_TESTS}" == true ]]; then
            if [[ " ${skip_tests_cmds[*]} " =~ " ${cmd} " ]]; then
                continue
            fi
        fi
        
        # Skip optimize if requested
        if [[ "${SKIP_OPTIMIZE}" == true ]]; then
            if [[ "${cmd}" == "${skip_optimize_cmd}" ]]; then
                continue
            fi
        fi
        
        filtered+=("${cmd}")
    done
    
    echo "${filtered[@]}"
}

# Function to display requirements summary
display_requirements_summary() {
    local file="$1"
    
    print_info "Requirements file: ${file}"
    
    # Extract and display key information
    local flow_name=$(extract_flow_name "${file}")
    if [[ -n "${flow_name}" ]]; then
        print_info "Flow name: ${flow_name}"
    fi
    
    echo ""
    print_info "Requirements file contents:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    head -30 "${file}" | while IFS= read -r line; do
        echo "  ${line}"
    done
    if [[ $(wc -l < "${file}") -gt 30 ]]; then
        echo "  ... (truncated, see full file for details)"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Function to accumulate outputs from previous commands
accumulate_outputs() {
    local current_command="$1"
    local output_json=""
    
    # Build JSON object with all previous command outputs
    local json_parts=()
    
    for cmd in "${COMMANDS[@]}"; do
        # Stop before current command
        if [[ "${cmd}" == "${current_command}" ]]; then
            break
        fi
        
        local cmd_output_file="${TEMP_DIR}/${cmd}_output.json"
        if [[ -f "${cmd_output_file}" ]]; then
            local cmd_output=$(cat "${cmd_output_file}" 2>/dev/null || echo "")
            if [[ -n "${cmd_output}" && "${cmd_output}" != "null" ]]; then
                # Try to parse as JSON, if valid use it, otherwise wrap as string
                if echo "${cmd_output}" | jq . >/dev/null 2>&1; then
                    # Valid JSON, use it as-is
                    local escaped_output=$(echo "${cmd_output}" | jq -c . 2>/dev/null)
                    json_parts+=("\"${cmd}\": ${escaped_output}")
                else
                    # Not valid JSON, wrap as string (for backward compatibility with old outputs)
                    # Remove ANSI color codes and escape properly
                    local escaped=$(echo "${cmd_output}" | sed 's/\x1b\[[0-9;]*m//g' | sed 's/"/\\"/g' | tr '\n' ' ' | sed 's/  */ /g' | sed 's/^ *//;s/ *$//')
                    json_parts+=("\"${cmd}\": \"${escaped}\"")
                fi
            fi
        fi
    done
    
    # Combine into single JSON object
    if [[ ${#json_parts[@]} -gt 0 ]]; then
        output_json="{$(IFS=,; echo "${json_parts[*]}")}"
    fi
    
    echo "${output_json}"
}

# Function to execute command sequence
execute_sequence() {
    local commands_to_execute=($(filter_commands))
    
    if [[ ${#commands_to_execute[@]} -eq 0 ]]; then
        print_warning "No commands to execute after filtering"
        return 0
    fi
    
    print_info "Executing ${#commands_to_execute[@]} command(s) in sequence"
    echo ""
    
    local step=1
    local total=${#commands_to_execute[@]}
    
    for cmd in "${commands_to_execute[@]}"; do
        echo ""
        print_info "Step ${step}/${total}: ${cmd}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Accumulate outputs from previous commands
        local previous_outputs=$(accumulate_outputs "${cmd}")
        
        if [[ -n "${previous_outputs}" && "${previous_outputs}" != "null" ]]; then
            print_info "Including context from previous commands"
        fi
        
        # Execute command with previous outputs
        local command_output
        if command_output=$(execute_cursor_command "${cmd}" "${previous_outputs}"); then
            print_success "Command completed: ${cmd}"
            
            # Save output for next command
            if [[ -n "${command_output}" ]]; then
                echo "${command_output}" > "${TEMP_DIR}/${cmd}_output.json"
            fi
        else
            print_error "Command failed: ${cmd}"
            print_error "Stopping execution"
            return 1
        fi
        
        step=$((step + 1))
        
        # Small delay between commands
        sleep 1
    done
    
    echo ""
    
    # After all commands, check if review found issues
    # If review_flow_implementation was executed, check its output
    local review_issues_found=false
    if [[ " ${commands_to_execute[*]} " =~ " review_flow_implementation " ]]; then
        local review_output_file="${TEMP_DIR}/review_flow_implementation_output.json"
        if [[ -f "${review_output_file}" ]]; then
            if command_exists jq; then
                # Try to extract review status from the output
                local review_json=$(cat "${review_output_file}" | jq -r '.result' 2>/dev/null | grep -oP '\{.*\}' | head -1 || echo "")
                if [[ -n "${review_json}" ]]; then
                    local review_status=$(echo "${review_json}" | jq -r '.status // empty' 2>/dev/null || echo "")
                    if [[ "${review_status}" == "needs_correction" ]]; then
                        review_issues_found=true
                        echo ""
                        print_warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        print_warning "Review found issues that need correction"
                        print_warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        echo ""
                        
                        # Extract and display redirects
                        local redirects=$(echo "${review_json}" | jq -r '.redirects // [] | .[]' 2>/dev/null || echo "")
                        if [[ -n "${redirects}" ]]; then
                            print_info "Commands that need to be re-executed:"
                            echo "${redirects}" | while read -r redirect; do
                                if [[ -n "${redirect}" ]]; then
                                    print_info "  → ${redirect}"
                                fi
                            done
                            echo ""
                            print_info "To fix issues, re-run the script starting from the first redirect:"
                            print_info "  .template/flows/scripts/orchestrate_flow.sh \\"
                            print_info "    --requirements ${FLOW_REQUIREMENTS_FILE} \\"
                            local first_redirect=$(echo "${redirects}" | head -1)
                            if [[ -n "${first_redirect}" ]]; then
                                print_info "    --start-from ${first_redirect}"
                            fi
                        fi
                        
                        # Display issues summary
                        local issues_count=$(echo "${review_json}" | jq -r '.issues // [] | length' 2>/dev/null || echo "0")
                        if [[ "${issues_count}" != "0" ]]; then
                            echo ""
                            print_info "Total issues found: ${issues_count}"
                            print_info "See review output for details: ${review_output_file}"
                        fi
                    fi
                fi
            fi
        fi
    fi
    
    if [[ "${review_issues_found}" == true ]]; then
        return 1
    else
        print_success "All commands executed successfully!"
        print_info "Command outputs saved in: ${TEMP_DIR}"
        return 0
    fi
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --requirements)
                FLOW_REQUIREMENTS_FILE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-optimize)
                SKIP_OPTIMIZE=true
                shift
                ;;
            --start-from)
                START_FROM="$2"
                shift 2
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "${FLOW_REQUIREMENTS_FILE}" ]]; then
        print_error "Requirements file is required"
        show_usage
        exit 1
    fi
    
    # Convert to absolute path if relative
    if [[ ! "${FLOW_REQUIREMENTS_FILE}" =~ ^/ ]]; then
        FLOW_REQUIREMENTS_FILE="$(cd "$(dirname "${FLOW_REQUIREMENTS_FILE}")" && pwd)/$(basename "${FLOW_REQUIREMENTS_FILE}")"
    fi
}

# Main function
main() {
    print_info "Flow Implementation Orchestration Script"
    echo ""
    
    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Display requirements summary
    display_requirements_summary "${FLOW_REQUIREMENTS_FILE}"
    
    # Check editor availability (non-blocking)
    check_editor_available || true
    
    echo ""
    print_info "Starting flow implementation orchestration"
    
    if [[ "${DRY_RUN}" == true ]]; then
        print_warning "DRY RUN MODE - No commands will be executed"
        echo ""
    fi
    
    # Show execution plan
    local commands_to_execute=($(filter_commands))
    print_info "Execution plan:"
    for i in "${!commands_to_execute[@]}"; do
        echo "  $((i + 1)). ${commands_to_execute[$i]}"
    done
    echo ""
    
    # Confirm execution (unless dry-run)
    if [[ "${DRY_RUN}" != true ]]; then
        read -p "Continue with execution? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Execution cancelled"
            exit 0
        fi
    fi
    
    # Execute sequence
    if ! execute_sequence; then
        print_error "Orchestration failed"
        exit 1
    fi
    
    echo ""
    local flow_name=$(extract_flow_name "${FLOW_REQUIREMENTS_FILE}")
    print_success "Flow implementation orchestration completed!"
    if [[ -n "${flow_name}" ]]; then
        print_info "Flow name: ${flow_name}"
    fi
    print_info "Next steps:"
    print_info "  1. Review the implemented flow"
    print_info "  2. Test the flow with sample data"
    print_info "  3. Update documentation if needed"
}

# Run main function
parse_arguments "$@"
main
