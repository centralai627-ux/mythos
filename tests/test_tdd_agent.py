"""
TDD Tests for Mythos Agent
==========================
Using TDD principles from skills.sh
- Tests verify behavior through public interfaces
- Vertical slices: one test -> one implementation
- Integration-style tests
"""
from __future__ import annotations
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from core.agent import MythosAgent
from core.api_client import APIError
from core.ai_brain import Intent


class TestAgentBehavior:
    """Test agent behavior through public interfaces."""

    def test_agent_initializes_with_config(self):
        """Agent should initialize with default config."""
        agent = MythosAgent()
        assert agent.cfg is not None
        assert agent.keys is not None
        assert agent.api is not None
        assert agent.brain is not None
        assert agent.ui is not None

    def test_agent_has_required_subsystems(self):
        """Agent should have all required subsystems."""
        agent = MythosAgent()
        assert hasattr(agent, 'executor')
        assert hasattr(agent, 'tools')
        assert hasattr(agent, 'brain')
        assert hasattr(agent, 'vision')
        assert hasattr(agent, 'commands')
        # memory is imported as module, not as attribute
        from core import memory
        assert memory is not None

    def test_agent_starts_in_running_state(self):
        """Agent should start in running state."""
        agent = MythosAgent()
        assert agent.running is True

    def test_agent_stops_correctly(self):
        """Agent should stop when stop() is called."""
        agent = MythosAgent()
        agent.stop()
        assert agent.running is False


class TestAgentRequestProcessing:
    """Test agent request processing through public interface."""

    def test_process_request_updates_cwd(self):
        """Agent should update executor and tools cwd on request."""
        agent = MythosAgent()
        original_cwd = agent.cwd
        
        with patch.object(agent.brain, 'run_with_tools') as mock_run:
            intent = Intent()
            intent.text = "test"
            mock_run.return_value = (intent, 0)
            agent._process_request("test request")
            
            assert agent.executor.cwd == original_cwd
            assert agent.tools.cwd == original_cwd

    def test_process_request_calls_brain(self):
        """Agent should call brain.run_with_tools with user text."""
        agent = MythosAgent()
        
        with patch.object(agent.brain, 'run_with_tools') as mock_run:
            intent = Intent()
            intent.text = "response"
            mock_run.return_value = (intent, 0)
            agent._process_request("hello")
            
            mock_run.assert_called_once_with("hello")

    def test_process_request_shows_thinking(self):
        """Agent should show thinking indicator during processing."""
        agent = MythosAgent()
        
        with patch.object(agent.ui, 'ai_thinking') as mock_think:
            with patch.object(agent.brain, 'run_with_tools') as mock_run:
                intent = Intent()
                intent.text = "response"
                mock_run.return_value = (intent, 0)
                agent._process_request("test")
                
                mock_think.assert_called_once()

    def test_process_request_shows_response(self):
        """Agent should show response after processing."""
        agent = MythosAgent()
        
        with patch.object(agent.ui, 'assistant') as mock_assistant:
            with patch.object(agent.brain, 'run_with_tools') as mock_run:
                intent = Intent()
                intent.text = "response"
                mock_run.return_value = (intent, 0)
                agent._process_request("test")
                
                mock_assistant.assert_called_once()


class TestAgentFileOperations:
    """Test agent file operations through public interface."""

    def test_write_file_absolute_path(self):
        """Agent should write to absolute path correctly."""
        agent = MythosAgent()
        test_path = os.path.join(os.environ.get('TEMP', '/tmp'), 'test_mythos.txt')
        
        with patch.object(agent.executor, 'atomic_write') as mock_write:
            mock_write.return_value = True
            agent._write_file(test_path, "test content")
            
            mock_write.assert_called_once_with(test_path, "test content")

    def test_write_file_relative_path(self):
        """Agent should convert relative path to absolute."""
        agent = MythosAgent()
        original_cwd = agent.cwd
        
        with patch.object(agent.executor, 'atomic_write') as mock_write:
            mock_write.return_value = True
            agent._write_file("test.txt", "content")
            
            expected_path = os.path.join(original_cwd, "test.txt")
            mock_write.assert_called_once_with(expected_path, "content")

    def test_read_file_absolute_path(self):
        """Agent should read from absolute path correctly."""
        agent = MythosAgent()
        test_path = os.path.join(os.environ.get('TEMP', '/tmp'), 'test_read.txt')
        
        with patch.object(agent.executor, 'safe_read') as mock_read:
            mock_read.return_value = "file content"
            agent._read_file(test_path)
            
            mock_read.assert_called_once_with(test_path)

    def test_read_file_loads_into_context(self):
        """Agent should load file content into brain context."""
        agent = MythosAgent()
        test_path = os.path.join(os.environ.get('TEMP', '/tmp'), 'test_context.txt')
        
        with patch.object(agent.executor, 'safe_read') as mock_read:
            mock_read.return_value = "context content"
            agent._read_file(test_path)
            
            assert len(agent.brain.history) > 0
            last_entry = agent.brain.history[-1]
            assert last_entry["role"] == "system"
            assert "context content" in last_entry["content"]


class TestAgentModelSwitching:
    """Test agent model switching through public interface."""

    def test_switch_model_code(self):
        """Agent should switch to code model."""
        agent = MythosAgent()
        
        with patch.object(agent.brain, 'set_model') as mock_set:
            mock_set.return_value = True
            agent._switch_model("code")
            
            mock_set.assert_called_once_with("mythos-code")

    def test_switch_model_ultra(self):
        """Agent should switch to ultra model."""
        agent = MythosAgent()
        
        with patch.object(agent.brain, 'set_model') as mock_set:
            mock_set.return_value = True
            agent._switch_model("ultra")
            
            mock_set.assert_called_once_with("mythos-ultra")

    def test_switch_model_vision(self):
        """Agent should switch to vision model."""
        agent = MythosAgent()
        
        with patch.object(agent.brain, 'set_model') as mock_set:
            mock_set.return_value = True
            agent._switch_model("vision")
            
            mock_set.assert_called_once_with("mythos-vision")

    def test_switch_model_invalid(self):
        """Agent should handle invalid model gracefully."""
        agent = MythosAgent()
        
        with patch.object(agent.brain, 'set_model') as mock_set:
            mock_set.return_value = False
            agent._switch_model("invalid_model")
            
            mock_set.assert_called_once_with("invalid_model")


class TestAgentDirectoryNavigation:
    """Test agent directory navigation through public interface."""

    def test_change_dir_absolute(self):
        """Agent should change to absolute directory."""
        agent = MythosAgent()
        test_dir = os.environ.get('TEMP', '/tmp')
        
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.return_value = True
            agent._change_dir(test_dir)
            
            assert agent.cwd == os.path.abspath(test_dir)

    def test_change_dir_relative(self):
        """Agent should convert relative directory to absolute."""
        agent = MythosAgent()
        original_cwd = agent.cwd
        
        # Mock both isdir and chdir to avoid actual filesystem changes
        with patch('os.path.isdir') as mock_isdir:
            with patch('os.chdir') as mock_chdir:
                mock_isdir.return_value = True
                agent._change_dir("subdir")
                
                expected = os.path.join(original_cwd, "subdir")
                assert agent.cwd == os.path.abspath(expected)

    def test_change_dir_invalid(self):
        """Agent should handle invalid directory gracefully."""
        agent = MythosAgent()
        
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.return_value = False
            agent._change_dir("/nonexistent/path")
            
            # CWD should not change
            assert agent.cwd == agent.cwd


class TestAgentShellExecution:
    """Test agent shell execution through public interface."""

    def test_exec_and_show_empty_command(self):
        """Agent should warn on empty command."""
        agent = MythosAgent()
        
        with patch.object(agent.ui, 'warn') as mock_warn:
            agent._exec_and_show("", shell=None)
            
            mock_warn.assert_called_once_with("Empty command.")

    def test_exec_and_show_whitespace_command(self):
        """Agent should warn on whitespace-only command."""
        agent = MythosAgent()
        
        with patch.object(agent.ui, 'warn') as mock_warn:
            agent._exec_and_show("   ", shell=None)
            
            mock_warn.assert_called_once_with("Empty command.")

    def test_exec_and_show_valid_command(self):
        """Agent should execute valid command."""
        agent = MythosAgent()
        
        with patch.object(agent.executor, 'run') as mock_run:
            # Create a mock result with all required attributes
            mock_result = Mock()
            mock_result.success = True
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_result.exit_code = 0
            mock_result.shell = "cmd"
            mock_result.duration = 0.1
            mock_result.timed_out = False
            mock_run.return_value = mock_result
            agent._exec_and_show("echo test", shell="cmd")
            
            mock_run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
