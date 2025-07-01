import json

import pytest

from voxvibe.window_manager.dbus_strategy import DBusWindowManagerStrategy

# --- Test Configuration ---
TEST_WINDOW_ID = 12345
TEST_WINDOW_TITLE = "Mock Test Window"



def test_focus_and_paste_with_mock_service():
    """Test the full workflow using mocked DBus calls."""
    import unittest.mock

    from PyQt6.QtDBus import QDBusMessage
    
    strategy = DBusWindowManagerStrategy()
    
    # Mock the strategy's internal components
    mock_bus = unittest.mock.MagicMock()
    mock_bus.isConnected.return_value = True
    
    mock_interface = unittest.mock.MagicMock()
    mock_interface.isValid.return_value = True
    
    # Mock GetFocusedWindow call
    mock_reply = unittest.mock.MagicMock()
    mock_reply.type.return_value = QDBusMessage.MessageType.ReplyMessage
    window_info = {"id": TEST_WINDOW_ID, "title": TEST_WINDOW_TITLE}
    mock_reply.arguments.return_value = [json.dumps(window_info)]
    
    # Mock successful FocusAndPaste call
    mock_paste_reply = unittest.mock.MagicMock()
    mock_paste_reply.type.return_value = QDBusMessage.MessageType.ReplyMessage
    mock_paste_reply.arguments.return_value = [True]
    
    # Set up call return values
    mock_interface.call.side_effect = [mock_reply, mock_paste_reply]
    
    # Manually set the mocked components
    strategy._bus = mock_bus
    strategy._interface = mock_interface
    strategy._initialized = True
    
    # Test availability
    assert strategy.is_available()
    
    # Test store_current_window
    strategy.store_current_window()
    assert strategy._stored_window_id == TEST_WINDOW_ID
    assert strategy._stored_window_info is not None
    
    # Test focus_and_paste
    paste_text = "Hello from the test!"
    result = strategy.focus_and_paste(paste_text)
    assert result is True
    
    # Verify the calls were made with correct arguments
    assert mock_interface.call.call_count == 2  # GetFocusedWindow + FocusAndPaste
    
    # Check the calls
    calls = mock_interface.call.call_args_list
    
    # First call should be GetFocusedWindow
    assert calls[0][0][0] == "GetFocusedWindow"
    
    # Second call should be FocusAndPaste
    assert calls[1][0][0] == "FocusAndPaste"
    assert calls[1][0][1] == str(TEST_WINDOW_ID)  # window_id (now as string)
    assert calls[1][0][2] == paste_text      # text


def test_make_focus_and_paste_payload_standalone():
    """Test the payload creation for FocusAndPaste method without mock service."""
    strategy = DBusWindowManagerStrategy()
    
    payload = strategy._make_focus_and_paste_payload(TEST_WINDOW_ID, "text")
    assert payload[0] == str(TEST_WINDOW_ID)  # window_id should be string
    assert payload[1] == "text"


def test_make_focus_and_paste_payload_with_large_id():
    """Test payload creation with a large window ID that needs unsigned conversion."""
    strategy = DBusWindowManagerStrategy(
        bus_name="org.test",
        object_path="/org/test",
        interface="org.test"
    )
    
    # Test with a large window ID that would be negative as signed int
    large_window_id = 0xFFFFFFFF
    payload = strategy._make_focus_and_paste_payload(large_window_id, "test")
    assert payload[0] == str(large_window_id)  # Should be converted to string
    assert payload[1] == "test"


def test_strategy_unavailable_without_dbus():
    """Test that strategy reports unavailable when DBus is not accessible."""
    strategy = DBusWindowManagerStrategy(
        bus_name="org.nonexistent.service",
        object_path="/org/nonexistent/path",
        interface="org.nonexistent.interface"
    )
    
    # Should return False when the service doesn't exist
    assert not strategy.is_available()


def test_focus_and_paste_without_stored_window():
    """Test that focus_and_paste fails when no window is stored."""
    strategy = DBusWindowManagerStrategy(
        bus_name="org.nonexistent.service",
        object_path="/org/nonexistent/path",
        interface="org.nonexistent.interface"
    )
    
    # Should fail because no window is stored and service doesn't exist
    with pytest.raises(RuntimeError, match="DBus strategy not available"):
        strategy.focus_and_paste("test text")


def test_store_current_window_without_dbus():
    """Test that store_current_window fails when DBus is not accessible."""
    strategy = DBusWindowManagerStrategy(
        bus_name="org.nonexistent.service",
        object_path="/org/nonexistent/path",
        interface="org.nonexistent.interface"
    )
    
    # Should fail because service doesn't exist
    with pytest.raises(RuntimeError, match="DBus strategy not available"):
        strategy.store_current_window()


def test_get_strategy_name():
    """Test that get_strategy_name returns the expected name."""
    strategy = DBusWindowManagerStrategy()
    assert strategy.get_strategy_name() == "GNOME Shell DBus Extension"


def test_get_diagnostics_with_mock():
    """Test the diagnostics information collection with mocked DBus."""
    import unittest.mock
    
    strategy = DBusWindowManagerStrategy()
    
    # Mock the strategy's internal components  
    mock_bus = unittest.mock.MagicMock()
    mock_bus.isConnected.return_value = True
    
    mock_interface = unittest.mock.MagicMock()
    mock_interface.isValid.return_value = True
    
    # Manually set the mocked components
    strategy._bus = mock_bus
    strategy._interface = mock_interface
    strategy._initialized = True
    
    # Initialize the strategy
    assert strategy.is_available()
    
    diagnostics = strategy.get_diagnostics()
    
    # Check that diagnostics includes expected keys
    assert "strategy" in diagnostics
    assert "available" in diagnostics
    assert "bus_connected" in diagnostics
    assert "interface_valid" in diagnostics
    assert "stored_window_info" in diagnostics
    assert "stored_window_id" in diagnostics
    assert "bus_name" in diagnostics
    assert "object_path" in diagnostics
    assert "interface_name" in diagnostics
    
    # Check specific values
    assert diagnostics["strategy"] == "GNOME Shell DBus Extension"
    assert diagnostics["available"] is True
    assert diagnostics["bus_connected"] is True
    assert diagnostics["interface_valid"] is True


def test_get_diagnostics_without_dbus():
    """Test the diagnostics information collection when DBus is unavailable."""
    strategy = DBusWindowManagerStrategy(
        bus_name="org.nonexistent.service",
        object_path="/org/nonexistent/path",
        interface="org.nonexistent.interface"
    )
    
    diagnostics = strategy.get_diagnostics()
    
    # Check that diagnostics includes expected keys
    assert "strategy" in diagnostics
    assert "available" in diagnostics
    assert "bus_connected" in diagnostics
    assert "interface_valid" in diagnostics
    assert "stored_window_info" in diagnostics
    assert "stored_window_id" in diagnostics
    assert "bus_name" in diagnostics
    assert "object_path" in diagnostics
    assert "interface_name" in diagnostics
    
    # Check specific values
    assert diagnostics["strategy"] == "GNOME Shell DBus Extension"
    assert diagnostics["available"] is False
