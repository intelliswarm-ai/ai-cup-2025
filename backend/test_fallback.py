#!/usr/bin/env python3
"""
Test script to verify OpenAI to Ollama fallback mechanism
"""
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentic_teams import AgenticTeamOrchestrator


def test_fallback_scenarios():
    """Test various OpenAI API key scenarios to verify fallback behavior"""

    print("=" * 70)
    print("Testing OpenAI to Ollama Fallback Mechanism")
    print("=" * 70)

    test_cases = [
        (None, "No API key (None)", False),
        ("", "Empty string", False),
        ("   ", "Whitespace only", False),
        ("your_openai_api_key_here", "Placeholder value", False),
        ("your-api-key-here", "Alternative placeholder", False),
        ("REPLACE_ME", "Replace me placeholder", False),
        ("sk-proj-test123", "Valid-looking API key", True),
    ]

    all_passed = True

    for api_key, description, should_use_openai in test_cases:
        orchestrator = AgenticTeamOrchestrator(openai_api_key=api_key)
        uses_openai = orchestrator.use_openai

        # Determine expected behavior
        expected = "OpenAI" if should_use_openai else "Ollama"
        actual = "OpenAI" if uses_openai else "Ollama"

        # Check if test passed
        passed = (uses_openai == should_use_openai)
        status = "✓ PASS" if passed else "✗ FAIL"

        if not passed:
            all_passed = False

        print(f"\n{status} | {description}")
        print(f"  API Key: {repr(api_key)}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All tests passed! Fallback mechanism working correctly.")
    else:
        print("✗ Some tests failed. Please review the fallback logic.")
    print("=" * 70)

    return all_passed


def test_current_env_configuration():
    """Test with the actual environment configuration"""
    print("\n" + "=" * 70)
    print("Testing Current Environment Configuration")
    print("=" * 70)

    # Get current environment variable
    current_key = os.getenv("OPENAI_API_KEY")

    print(f"\nCurrent OPENAI_API_KEY: {repr(current_key)}")

    # Create orchestrator with current config
    from agentic_teams import orchestrator as current_orchestrator

    print(f"Current configuration uses: {'OpenAI' if current_orchestrator.use_openai else 'Ollama'}")

    if current_orchestrator.use_openai:
        print(f"Model: {current_orchestrator.openai_model}")
    else:
        print(f"Ollama URL: {current_orchestrator.ollama_url}")

    print("=" * 70)


if __name__ == "__main__":
    # Run fallback tests
    success = test_fallback_scenarios()

    # Test current environment
    test_current_env_configuration()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
